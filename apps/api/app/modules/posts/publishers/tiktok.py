"""TikTok publisher — Content Posting API, init-then-publish flow.

TikTok has NO business DM API, so every TikTok post caption ends with the
business's WhatsApp deep link — all TikTok leads must enter the WhatsApp
funnel. The deep link is read from the credential metadata (whatsapp_link)
or derived from the tenant's WhatsApp number.
"""

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.circuit import get_circuit
from app.core.r2_service import PUBLISH_URL_TTL_S, r2_service
from app.modules.credentials.service import DecryptedCredential
from app.modules.posts.publishers.base import (
    HTTP_TIMEOUT_S,
    Publisher,
    PublishError,
    PublishResult,
    classify_error,
    logged_request,
)

logger = logging.getLogger(__name__)

TIKTOK_API = "https://open.tiktokapis.com/v2"


def _tiktok_error(response: httpx.Response) -> PublishError:
    try:
        error = response.json().get("error", {})
    except ValueError:
        error = {}
    return classify_error(
        "tiktok", str(error.get("code", "internal_error")), str(error.get("message", ""))
    )


class TikTokPublisher(Publisher):
    platform = "tiktok"

    async def publish(self, credential: DecryptedCredential, post: Any) -> PublishResult:  # noqa: ANN401
        token = credential.fields["access_token"]
        whatsapp_link = str((post.meta or {}).get("whatsapp_link", "")) or str(
            credential.fields.get("whatsapp_link", "")
        )
        caption = self.build_caption(post, whatsapp_link)

        key = (post.media_urls or {}).get("image_r2_key")
        if not key:
            raise PublishError(
                "MEDIA_MISSING",
                "TikTok photo posts require an image",
                is_retryable=False,
                recovery_action="Generate a creative before publishing",
            )
        image_url = await r2_service.generate_signed_url(
            str(key), expires_in_seconds=PUBLISH_URL_TTL_S
        )

        async def _run() -> PublishResult:
            headers = {"Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_S) as client:
                # Step 1: init the content upload
                init = await logged_request(
                    client,
                    self.platform,
                    "POST",
                    f"{TIKTOK_API}/post/publish/content/init/",
                    tenant_id=post.tenant_id,
                    headers=headers,
                    json={
                        "post_info": {
                            "title": caption,
                            "privacy_level": "PUBLIC_TO_EVERYONE",
                        },
                        "source_info": {
                            "source": "PULL_FROM_URL",
                            "photo_images": [image_url],
                            "photo_cover_index": 0,
                        },
                        "post_mode": "DIRECT_POST",
                        "media_type": "PHOTO",
                    },
                )
                init_error = init.json().get("error", {}).get("code", "ok")
                if init.status_code != 200 or init_error != "ok":
                    raise _tiktok_error(init)
                publish_id = str(init.json()["data"]["publish_id"])

                # Step 2: confirm publish status
                status = await logged_request(
                    client,
                    self.platform,
                    "POST",
                    f"{TIKTOK_API}/post/publish/status/fetch/",
                    tenant_id=post.tenant_id,
                    headers=headers,
                    json={"publish_id": publish_id},
                )
                if status.status_code != 200:
                    raise _tiktok_error(status)
                return PublishResult(
                    platform_post_id=publish_id,
                    published_url="",  # TikTok returns the final URL asynchronously
                    published_at=datetime.now(UTC),
                )

        return await get_circuit("tiktok").call(_run)

    @staticmethod
    def build_caption(post: Any, whatsapp_link: str) -> str:  # noqa: ANN401
        """Caption with hashtags, ALWAYS ending in the WhatsApp deep link."""
        caption = str(post.content or "")
        hashtags = (post.meta or {}).get("hashtags") or []
        if hashtags:
            caption = f"{caption} {' '.join(str(h) for h in hashtags)}"
        link = whatsapp_link or "WhatsApp us to book!"
        return f"{caption}\n{link}"
