"""Publisher interface and error classification.

The is_retryable distinction is the load-bearing part of this module:
- PERMANENT errors (TOKEN_EXPIRED, PAGE_NOT_FOUND, PERMISSION_REVOKED) will
  NEVER succeed with the same credential — retrying them creates an infinite
  loop that burns rate limit budget and masks the real problem.
- TRANSIENT errors (RATE_LIMIT_EXCEEDED, NETWORK_TIMEOUT, PLATFORM_DOWN)
  succeed on retry with backoff — failing them permanently loses posts.

Every known Meta / TikTok / LinkedIn error code is mapped below; anything
unmapped is treated as TRANSIENT (safer to retry an unknown once than to
permanently fail a recoverable publish — the retry cap bounds the damage).
"""

import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

import httpx

from app.modules.credentials.service import DecryptedCredential

logger = logging.getLogger(__name__)

HTTP_TIMEOUT_S = 30.0


@dataclass(frozen=True)
class PublishResult:
    platform_post_id: str
    published_url: str
    published_at: datetime


class PublishError(Exception):
    """A publish attempt failed — carries the retry classification."""

    def __init__(
        self,
        error_code: str,
        error_message: str,
        *,
        is_retryable: bool,
        recovery_action: str,
    ) -> None:
        super().__init__(f"{error_code}: {error_message}")
        self.error_code = error_code
        self.error_message = error_message
        self.is_retryable = is_retryable
        self.recovery_action = recovery_action


# (is_retryable, canonical_code, recovery_action)
_Classification = tuple[bool, str, str]

# Meta Graph API numeric error codes
META_ERROR_MAP: dict[int, _Classification] = {
    190: (False, "TOKEN_EXPIRED", "Reconnect the Facebook/Instagram account"),
    100: (False, "PAGE_NOT_FOUND", "Verify the page/account id in credentials"),
    10: (False, "PERMISSION_DENIED", "Re-grant publish permissions"),
    200: (False, "PERMISSION_DENIED", "Re-grant publish permissions"),
    294: (False, "PERMISSION_DENIED", "Re-grant manage_pages permission"),
    4: (True, "RATE_LIMIT_EXCEEDED", "Retry with backoff"),
    17: (True, "RATE_LIMIT_EXCEEDED", "Retry with backoff"),
    32: (True, "RATE_LIMIT_EXCEEDED", "Retry with backoff"),
    613: (True, "RATE_LIMIT_EXCEEDED", "Retry with backoff"),
    1: (True, "PLATFORM_ERROR", "Retry with backoff"),
    2: (True, "PLATFORM_DOWN", "Retry with backoff"),
    368: (False, "POLICY_BLOCK", "Content blocked by Meta policy — review the post"),
    9007: (False, "MEDIA_EXPIRED", "Regenerate the signed media URL and retry manually"),
}

# TikTok Content Posting API string error codes
TIKTOK_ERROR_MAP: dict[str, _Classification] = {
    "access_token_invalid": (False, "TOKEN_EXPIRED", "Reconnect the TikTok account"),
    "scope_not_authorized": (False, "PERMISSION_DENIED", "Re-authorize with video.publish scope"),
    "rate_limit_exceeded": (True, "RATE_LIMIT_EXCEEDED", "Retry with backoff"),
    "spam_risk_too_many_posts": (True, "RATE_LIMIT_EXCEEDED", "Retry after cool-down"),
    "spam_risk_user_banned_from_posting": (False, "ACCOUNT_BANNED", "Resolve with TikTok"),
    "reached_active_user_cap": (True, "RATE_LIMIT_EXCEEDED", "Retry tomorrow"),
    "internal_error": (True, "PLATFORM_ERROR", "Retry with backoff"),
}

# LinkedIn uses HTTP status semantics
LINKEDIN_STATUS_MAP: dict[int, _Classification] = {
    401: (False, "TOKEN_EXPIRED", "Reconnect the LinkedIn organization"),
    403: (False, "PERMISSION_DENIED", "Re-grant w_organization_social"),
    404: (False, "PAGE_NOT_FOUND", "Verify the organization id"),
    422: (False, "INVALID_CONTENT", "Post content violates LinkedIn rules"),
    429: (True, "RATE_LIMIT_EXCEEDED", "Retry with backoff"),
    500: (True, "PLATFORM_ERROR", "Retry with backoff"),
    502: (True, "PLATFORM_DOWN", "Retry with backoff"),
    503: (True, "PLATFORM_DOWN", "Retry with backoff"),
}


def classify_error(platform: str, code: int | str, message: str = "") -> PublishError:
    """Map a platform error code to a classified PublishError."""
    entry: _Classification | None = None
    if platform in ("facebook", "instagram", "meta"):
        entry = META_ERROR_MAP.get(int(code)) if str(code).lstrip("-").isdigit() else None
    elif platform == "tiktok":
        entry = TIKTOK_ERROR_MAP.get(str(code))
    elif platform == "linkedin":
        entry = LINKEDIN_STATUS_MAP.get(int(code)) if str(code).isdigit() else None

    if entry is None:
        # Unknown code: transient (bounded by the retry cap) — see module docstring
        return PublishError(
            f"UNKNOWN_{code}",
            message or "unclassified platform error",
            is_retryable=True,
            recovery_action="Retry with backoff; classify this code",
        )
    is_retryable, canonical, recovery = entry
    return PublishError(canonical, message, is_retryable=is_retryable, recovery_action=recovery)


class Publisher(ABC):
    """One social platform's publish flow."""

    platform: str = "base"

    @abstractmethod
    async def publish(self, credential: DecryptedCredential, post: object) -> PublishResult:
        """Publish `post` with `credential`; raise PublishError on failure."""


async def logged_request(
    client: httpx.AsyncClient,
    platform: str,
    method: str,
    url: str,
    tenant_id: uuid.UUID | str | None = None,
    **kwargs: object,
) -> httpx.Response:
    """Every platform API call goes through here: structured log with method,
    URL, status, latency — NEVER the access token (tokens travel only in
    params/headers, which are not logged)."""
    started = time.perf_counter()
    response = await client.request(method, url, **kwargs)  # type: ignore[arg-type]
    latency_ms = int((time.perf_counter() - started) * 1000)
    logger.info(
        "platform api call",
        extra={
            "platform": platform,
            "method": method,
            "url": url.split("?")[0],  # never log query strings (tokens)
            "status": response.status_code,
            "latency_ms": latency_ms,
            "tenant_id": str(tenant_id) if tenant_id else "",
        },
    )
    return response
