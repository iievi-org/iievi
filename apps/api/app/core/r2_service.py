"""Cloudflare R2 file storage (S3-compatible via boto3).

Object keys: {resource_type}/{tenant_id}/{year}/{month}/{uuid}.{ext}
Only object KEYS are stored in the database — signed URLs are generated
fresh on demand (15 min for display, 10 min for social publishing).

boto3 is synchronous; every call is wrapped in asyncio.to_thread so the
event loop never blocks on network I/O.
"""

import asyncio
import logging
import uuid
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

import boto3
from botocore.config import Config as BotoConfig

from app.core.config import settings
from app.core.exceptions import ExternalAPIError

logger = logging.getLogger(__name__)

DISPLAY_URL_TTL_S = 15 * 60
PUBLISH_URL_TTL_S = 10 * 60


def build_object_key(resource_type: str, tenant_id: uuid.UUID, extension: str) -> str:
    """creatives/550e8400-…/2026/07/a1b2c3d4….png"""
    now = datetime.now(UTC)
    return (
        f"{resource_type}/{tenant_id}/{now.year}/{now.month:02d}/"
        f"{uuid.uuid4().hex}.{extension.lstrip('.')}"
    )


@lru_cache(maxsize=1)
def _get_client() -> Any:  # boto3 clients are dynamically typed  # noqa: ANN401
    if not settings.r2_account_id:
        raise ExternalAPIError("Cloudflare R2 is not configured (R2_ACCOUNT_ID missing)")
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        config=BotoConfig(signature_version="s3v4", retries={"max_attempts": 3}),
        region_name="auto",
    )


class R2Service:
    """Single access point for media storage."""

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> str:
        def _put() -> None:
            _get_client().put_object(
                Bucket=settings.r2_bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                Metadata=metadata or {},
            )

        try:
            await asyncio.to_thread(_put)
        except ExternalAPIError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.error("R2 upload failed", extra={"key": key, "error": str(exc)})
            raise ExternalAPIError("Media storage upload failed") from exc
        return key

    async def generate_signed_url(
        self, key: str, expires_in_seconds: int = DISPLAY_URL_TTL_S
    ) -> str:
        def _sign() -> str:
            return str(
                _get_client().generate_presigned_url(
                    "get_object",
                    Params={"Bucket": settings.r2_bucket, "Key": key},
                    ExpiresIn=expires_in_seconds,
                )
            )

        try:
            return await asyncio.to_thread(_sign)
        except ExternalAPIError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ExternalAPIError("Signed URL generation failed") from exc

    async def delete(self, key: str) -> None:
        def _delete() -> None:
            _get_client().delete_object(Bucket=settings.r2_bucket, Key=key)

        try:
            await asyncio.to_thread(_delete)
        except ExternalAPIError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ExternalAPIError("Media storage delete failed") from exc


r2_service = R2Service()
