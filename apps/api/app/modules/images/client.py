"""Tenant-keyed image generation client (Gemini 2.5 Flash Image).

Pipeline: tenant Gemini credential → pre-computed brand style prompt +
content description → circuit-protected generation → sanity check (binary
under 50KB almost always means the model produced a failure placeholder) →
Pillow optimisation (PNG compression 8, resize to exact target dimensions)
→ R2 upload → (r2_key, signed_url).

The client is instantiated once at module level; per-call state is only the
tenant's key. [CANVA_NEXT_UPDATE] this is the integration point where Canva
template rendering replaces raw generation for tenants with Canva connected.
"""

import io
import logging
import time
import uuid

from google import genai
from google.genai import types
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.circuit import get_circuit
from app.core.exceptions import AIGenerationError, ExternalAPIError
from app.core.r2_service import build_object_key, r2_service
from app.modules.ai.context_service import assemble_tenant_context
from app.modules.ai.langfuse_client import estimate_cost_usd, track_daily_spend
from app.modules.credentials.service import get_decrypted_credential

logger = logging.getLogger(__name__)

IMAGE_MODEL = "gemini-2.5-flash-image"
MIN_VALID_IMAGE_BYTES = 50 * 1024
PNG_COMPRESS_LEVEL = 8

# Exact output dimensions per post format
FORMAT_DIMENSIONS: dict[str, tuple[int, int]] = {
    "square": (1080, 1080),
    "portrait": (1080, 1350),
    "story": (1080, 1920),
    "landscape": (1200, 628),
}


class ImageGenerationClient:
    """Single access point for tenant image generation."""

    async def generate_image(
        self,
        tenant_id: uuid.UUID,
        content_description: str,
        format: str,  # noqa: A002 — spec-mandated parameter name
        session: AsyncSession,
    ) -> tuple[str, str]:
        """Generate, optimise, and upload one image. Returns (r2_key, signed_url)."""
        raw = await self.generate_bytes(tenant_id, content_description, session)
        optimised = self.optimise(raw, format)
        key = build_object_key("creatives", tenant_id, "png")
        await r2_service.upload(key, optimised, "image/png")
        signed_url = await r2_service.generate_signed_url(key)
        return key, signed_url

    async def generate_bytes(
        self,
        tenant_id: uuid.UUID,
        content_description: str,
        session: AsyncSession,
    ) -> bytes:
        """Circuit-protected generation on the tenant's key; returns raw bytes."""
        credential = await get_decrypted_credential(tenant_id, "gemini", session)
        context = await assemble_tenant_context(tenant_id, session)
        prompt = self._compose_prompt(context.image_style_prompt, content_description)

        started = time.perf_counter()

        async def _raw() -> bytes:
            client = genai.Client(api_key=credential.fields["api_key"])
            try:
                response = await client.aio.models.generate_content(
                    model=IMAGE_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
                )
            except Exception as exc:  # noqa: BLE001 — normalise SDK errors at the boundary
                raise ExternalAPIError("Gemini image call failed") from exc
            usage = getattr(response, "usage_metadata", None)
            input_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
            output_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
            await track_daily_spend(
                tenant_id, estimate_cost_usd(IMAGE_MODEL, input_tokens, output_tokens)
            )
            for candidate in response.candidates or []:
                parts = candidate.content.parts if candidate.content else None
                for part in parts or []:
                    if part.inline_data and part.inline_data.data:
                        return bytes(part.inline_data.data)
            raise AIGenerationError("Image generation returned no image data")

        image_bytes = await get_circuit("gemini").call(_raw)
        latency_ms = int((time.perf_counter() - started) * 1000)

        if len(image_bytes) < MIN_VALID_IMAGE_BYTES:
            logger.warning(
                "generated image suspiciously small",
                extra={"tenant_id": str(tenant_id), "bytes": len(image_bytes)},
            )
            raise AIGenerationError(
                "Image generation likely failed (output under 50KB)",
                details={"bytes": len(image_bytes)},
            )
        logger.info(
            "image generated",
            extra={"tenant_id": str(tenant_id), "latency_ms": latency_ms},
        )
        return image_bytes

    @staticmethod
    def _compose_prompt(style_prompt: str | None, content_description: str) -> str:
        style = style_prompt or "Clean, modern, professional design."
        return (
            f"{content_description}\n\n"
            f"Visual style requirements: {style}\n"
            "No embedded text, watermarks, or logos in the image."
        )

    @staticmethod
    def optimise(image_bytes: bytes, format: str) -> bytes:  # noqa: A002
        """PNG-compress and resize to the exact target dimensions if oversized."""
        dimensions = FORMAT_DIMENSIONS.get(format)
        if dimensions is None:
            msg = f"unknown image format: {format}"
            raise ValueError(msg)
        with Image.open(io.BytesIO(image_bytes)) as img:
            output = img.convert("RGB") if img.mode not in ("RGB", "RGBA") else img
            if output.size != dimensions and (
                output.width > dimensions[0] or output.height > dimensions[1]
            ):
                output = output.resize(dimensions, Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            output.save(buffer, format="PNG", optimize=True, compress_level=PNG_COMPRESS_LEVEL)
            return buffer.getvalue()


image_client = ImageGenerationClient()
