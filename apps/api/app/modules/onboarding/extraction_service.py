"""Gemini 2.5 Flash structured extraction for onboarding answers.

Contract with the model (enforced by prompt AND by Pydantic validation):
- extract ONLY what the user explicitly said — never invent
- return ONLY JSON matching the schema
- if a required field is missing, return {"error": "missing_field",
  "field": "<name>"} instead of guessing

Every output is validated with Pydantic before it touches the session or
the database. A failed validation produces a TARGETED clarification question
naming the missing field — never "please repeat everything".
"""

import json
import logging

from pydantic import BaseModel, Field, ValidationError

from app.core import ai
from app.core.exceptions import AIGenerationError

logger = logging.getLogger(__name__)


class ExtractedService(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    price_min_paise: int | None = Field(default=None, ge=0)
    price_max_paise: int | None = Field(default=None, ge=0)
    unit: str = Field(default="per job", max_length=64)


class ExtractedServices(BaseModel):
    services: list[ExtractedService] = Field(min_length=1)


class ExtractedAudience(BaseModel):
    description: str = Field(min_length=10)
    age_range: str | None = None
    locations: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)


class ExtractedCompetitors(BaseModel):
    competitors: list[str] = Field(default_factory=list)
    differentiators: list[str] = Field(default_factory=list)


class ExtractionOutcome(BaseModel):
    """Either validated data or a targeted clarification question."""

    data: dict[str, object] | None = None
    clarification: str | None = None


_SYSTEM_TEMPLATE = """You extract structured data from a business owner's \
onboarding answer for an Indian service business.

Rules — no exceptions:
1. Extract ONLY information the user explicitly stated. NEVER invent, assume,
   or fill in typical values.
2. Respond with ONLY valid JSON matching this schema, no prose, no markdown:
{schema}
3. If a REQUIRED field cannot be found in the user's answer, respond instead
   with exactly: {{"error": "missing_field", "field": "<field name>"}}
4. Prices mentioned in rupees must be converted to integer paise (₹1 = 100).
"""

_CLARIFICATIONS: dict[str, str] = {
    "services": "Could you list at least one service you offer, with a rough price range?",
    "name": "What is that service called? A short name is fine.",
    "description": "Tell me a little more about who your ideal customers are.",
}


async def extract(
    *,
    kind: str,
    user_answer: str,
    session_token: str,
) -> ExtractionOutcome:
    """Run one extraction; returns validated data or a clarification question."""
    schema_model: type[BaseModel]
    if kind == "services":
        schema_model = ExtractedServices
    elif kind == "target_audience":
        schema_model = ExtractedAudience
    elif kind == "competitors":
        schema_model = ExtractedCompetitors
    else:
        msg = f"unknown extraction kind: {kind}"
        raise ValueError(msg)

    system = _SYSTEM_TEMPLATE.format(
        schema=json.dumps(schema_model.model_json_schema(), indent=None)
    )
    raw = await ai.complete(
        system=system,
        user_message=user_answer,
        model=ai.FLASH_MODEL,
        max_tokens=1024,
        trace_name=f"onboarding-extract-{kind}",
        session_id=session_token,
    )

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("extraction returned non-JSON", extra={"kind": kind})
        raise AIGenerationError("Extraction produced unparseable output") from exc

    if isinstance(parsed, dict) and parsed.get("error") == "missing_field":
        field = str(parsed.get("field", ""))
        return ExtractionOutcome(
            clarification=_CLARIFICATIONS.get(
                field, f"I still need one detail: could you tell me your {field}?"
            )
        )

    try:
        validated = schema_model.model_validate(parsed)
    except ValidationError as exc:
        first = exc.errors()[0]
        field = ".".join(str(loc) for loc in first["loc"]) or kind
        logger.warning("extraction failed validation", extra={"kind": kind, "field": field})
        return ExtractionOutcome(
            clarification=_CLARIFICATIONS.get(
                field.split(".")[-1],
                f"One detail didn't come through clearly — could you clarify the {field}?",
            )
        )

    return ExtractionOutcome(data=validated.model_dump())
