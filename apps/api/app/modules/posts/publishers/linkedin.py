"""LinkedIn publisher — Marketing API three-step image flow:
register the upload → PUT the binary → create the UGC post.

LinkedIn publishing is a Growth/Agency feature; the publishing ENDPOINTS
carry require_plan('growth') — this class only implements the mechanics.
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
    PublishResult,
    classify_error,
    logged_request,
)

logger = logging.getLogger(__name__)

LINKEDIN_API = "https://api.linkedin.com/v2"


class LinkedInPublisher(Publisher):
    platform = "linkedin"

    async def publish(self, credential: DecryptedCredential, post: Any) -> PublishResult:  # noqa: ANN401
        token = credential.fields["access_token"]
        org_id = credential.fields["organization_id"]
        author = f"urn:li:organization:{org_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        caption = str(post.content or "")
        hashtags = (post.meta or {}).get("hashtags") or []
        if hashtags:
            caption = f"{caption}\n\n{' '.join(str(h) for h in hashtags)}"
        image_key = (post.media_urls or {}).get("image_r2_key")

        async def _run() -> PublishResult:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_S) as client:
                asset_urn: str | None = None
                if image_key:
                    # Step 1: register the upload
                    register = await logged_request(
                        client,
                        self.platform,
                        "POST",
                        f"{LINKEDIN_API}/assets?action=registerUpload",
                        tenant_id=post.tenant_id,
                        headers=headers,
                        json={
                            "registerUploadRequest": {
                                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                                "owner": author,
                                "serviceRelationships": [
                                    {
                                        "relationshipType": "OWNER",
                                        "identifier": "urn:li:userGeneratedContent",
                                    }
                                ],
                            }
                        },
                    )
                    if register.status_code not in (200, 201):
                        raise classify_error(self.platform, register.status_code)
                    value = register.json()["value"]
                    upload_url = value["uploadMechanism"][
                        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
                    ]["uploadUrl"]
                    asset_urn = str(value["asset"])

                    # Step 2: upload the binary (fetched fresh from R2)
                    signed = await r2_service.generate_signed_url(
                        str(image_key), expires_in_seconds=PUBLISH_URL_TTL_S
                    )
                    image_response = await client.get(signed)
                    image_response.raise_for_status()
                    upload = await logged_request(
                        client,
                        self.platform,
                        "PUT",
                        upload_url,
                        tenant_id=post.tenant_id,
                        headers={"Authorization": f"Bearer {token}"},
                        content=image_response.content,
                    )
                    if upload.status_code not in (200, 201):
                        raise classify_error(self.platform, upload.status_code)

                # Step 3: create the UGC post
                media = [{"status": "READY", "media": asset_urn}] if asset_urn else []
                ugc = await logged_request(
                    client,
                    self.platform,
                    "POST",
                    f"{LINKEDIN_API}/ugcPosts",
                    tenant_id=post.tenant_id,
                    headers=headers,
                    json={
                        "author": author,
                        "lifecycleState": "PUBLISHED",
                        "specificContent": {
                            "com.linkedin.ugc.ShareContent": {
                                "shareCommentary": {"text": caption},
                                "shareMediaCategory": "IMAGE" if asset_urn else "NONE",
                                "media": media,
                            }
                        },
                        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
                    },
                )
                if ugc.status_code not in (200, 201):
                    raise classify_error(self.platform, ugc.status_code)
                ugc_id = str(ugc.headers.get("x-restli-id") or ugc.json().get("id", ""))
                return PublishResult(
                    platform_post_id=ugc_id,
                    published_url=f"https://www.linkedin.com/feed/update/{ugc_id}",
                    published_at=datetime.now(UTC),
                )

        return await get_circuit("linkedin").call(_run)
