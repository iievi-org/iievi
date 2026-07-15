"""Meta publishers: Facebook Pages and Instagram Business (Graph API v20).

Instagram is a two-step flow — create a media container, then publish it.
The image URL handed to Meta is a FRESH 15-minute signed R2 URL: Meta
fetches the image after receiving the URL, not instantly, so a short-lived
URL generated earlier in the chain could expire between steps.
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

GRAPH = "https://graph.facebook.com/v20.0"


def _meta_error(platform: str, response: httpx.Response) -> PublishError:
    try:
        error = response.json().get("error", {})
    except ValueError:
        error = {}
    return classify_error(
        platform, int(error.get("code", response.status_code)), str(error.get("message", ""))
    )


def _caption_of(post: Any) -> str:  # noqa: ANN401 — Post model, avoids circular import
    caption = str(post.content or "")
    hashtags = (post.meta or {}).get("hashtags") or []
    if hashtags:
        caption = f"{caption}\n\n{' '.join(str(h) for h in hashtags)}"
    return caption


async def _signed_image_url(post: Any) -> str | None:  # noqa: ANN401
    key = (post.media_urls or {}).get("image_r2_key")
    if not key:
        return None
    return await r2_service.generate_signed_url(str(key), expires_in_seconds=PUBLISH_URL_TTL_S)


class MetaFacebookPublisher(Publisher):
    platform = "facebook"

    async def publish(self, credential: DecryptedCredential, post: Any) -> PublishResult:  # noqa: ANN401
        page_id = credential.fields["page_id"]
        token = credential.fields["access_token"]
        caption = _caption_of(post)
        image_url = await _signed_image_url(post)

        async def _run() -> PublishResult:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_S) as client:
                if image_url:
                    response = await logged_request(
                        client,
                        self.platform,
                        "POST",
                        f"{GRAPH}/{page_id}/photos",
                        tenant_id=post.tenant_id,
                        data={"url": image_url, "caption": caption, "access_token": token},
                    )
                else:
                    response = await logged_request(
                        client,
                        self.platform,
                        "POST",
                        f"{GRAPH}/{page_id}/feed",
                        tenant_id=post.tenant_id,
                        data={"message": caption, "access_token": token},
                    )
                if response.status_code != 200:
                    raise _meta_error(self.platform, response)
                payload = response.json()
                post_id = str(payload.get("post_id") or payload.get("id"))
                return PublishResult(
                    platform_post_id=post_id,
                    published_url=f"https://www.facebook.com/{post_id}",
                    published_at=datetime.now(UTC),
                )

        return await get_circuit("meta").call(_run)


class MetaInstagramPublisher(Publisher):
    platform = "instagram"

    async def publish(self, credential: DecryptedCredential, post: Any) -> PublishResult:  # noqa: ANN401
        ig_user_id = credential.fields["business_account_id"]
        token = credential.fields["access_token"]
        caption = _caption_of(post)
        image_url = await _signed_image_url(post)
        if image_url is None:
            raise PublishError(
                "MEDIA_MISSING",
                "Instagram requires an image",
                is_retryable=False,
                recovery_action="Generate a creative before publishing",
            )

        async def _run() -> PublishResult:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_S) as client:
                # Step 1: create the media container
                container = await logged_request(
                    client,
                    self.platform,
                    "POST",
                    f"{GRAPH}/{ig_user_id}/media",
                    tenant_id=post.tenant_id,
                    data={"image_url": image_url, "caption": caption, "access_token": token},
                )
                if container.status_code != 200:
                    raise _meta_error(self.platform, container)
                creation_id = str(container.json()["id"])

                # Step 2: publish the container
                publish = await logged_request(
                    client,
                    self.platform,
                    "POST",
                    f"{GRAPH}/{ig_user_id}/media_publish",
                    tenant_id=post.tenant_id,
                    data={"creation_id": creation_id, "access_token": token},
                )
                if publish.status_code != 200:
                    raise _meta_error(self.platform, publish)
                media_id = str(publish.json()["id"])
                return PublishResult(
                    platform_post_id=media_id,
                    published_url=f"https://www.instagram.com/p/{media_id}",
                    published_at=datetime.now(UTC),
                )

        return await get_circuit("meta").call(_run)
