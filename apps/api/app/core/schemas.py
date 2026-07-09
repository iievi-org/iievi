"""Base request schemas with global sanitisation rules.

Every POST/PUT/PATCH body model inherits SanitizedModel:
- all string fields are stripped of leading/trailing whitespace BEFORE validation
- any string containing a null byte is rejected (database corruption vector)
- display-destined text goes through clean_display_text (bleach) to strip
  HTML and escape entities — stored-XSS defence at the write boundary

Length limits: NAME_MAX 255, DESCRIPTION_MAX 2000, MESSAGE_MAX 10000.
"""

import bleach
from pydantic import BaseModel, ConfigDict, field_validator

NAME_MAX = 255
DESCRIPTION_MAX = 2000
MESSAGE_MAX = 10000


def clean_display_text(value: str) -> str:
    """Strip ALL HTML tags and escape entities for text shown in the frontend."""
    return bleach.clean(value, tags=[], attributes={}, strip=True)


class SanitizedModel(BaseModel):
    """Base for all request bodies."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def _reject_null_bytes(cls, value: object) -> object:
        if isinstance(value, str) and "\x00" in value:
            msg = "null bytes are not allowed"
            raise ValueError(msg)
        return value
