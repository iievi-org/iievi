"""Platform publishers — one class per social platform, one shared interface."""

from app.modules.posts.publishers.base import (
    Publisher,
    PublishError,
    PublishResult,
    classify_error,
)
from app.modules.posts.publishers.linkedin import LinkedInPublisher
from app.modules.posts.publishers.meta import MetaFacebookPublisher, MetaInstagramPublisher
from app.modules.posts.publishers.tiktok import TikTokPublisher

PUBLISHERS: dict[str, Publisher] = {
    "facebook": MetaFacebookPublisher(),
    "instagram": MetaInstagramPublisher(),
    "tiktok": TikTokPublisher(),
    "linkedin": LinkedInPublisher(),
}

__all__ = [
    "PUBLISHERS",
    "LinkedInPublisher",
    "MetaFacebookPublisher",
    "MetaInstagramPublisher",
    "PublishError",
    "Publisher",
    "PublishResult",
    "TikTokPublisher",
    "classify_error",
]
