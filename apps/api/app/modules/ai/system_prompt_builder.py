"""Three-layer grounded system prompt builder — Prompt 7 Step 2.

Assembles the system prompt for one conversation turn from three layers:

- Layer 1 (base, ALWAYS): business identity, the EXACT services + prices, the
  discount policy verbatim, working hours, service areas, contact details (only
  when present in the profile), and hard prohibitions against inventing anything.
- Layer 2 (stage): the single objective for the current conversation stage.
- Layer 3 (persona, QUALIFYING & PITCH_SENT only): ideal customer, common
  objections, and how to address them.

The prompt is rebuilt on the latency-critical path every turn, so it is kept
well under 3000 tokens (longer system prompts materially increase model
latency). Variable, model-supplied sections are length-capped defensively; the
load-bearing safety sections (services, prices, discount policy, prohibitions)
are never truncated.
"""

import json

from app.db.models import ConversationState
from app.modules.ai.context_service import TenantAIContext

# Verbatim prohibition block (Prompt 7 Step 2). Direct language on purpose —
# it is the last line of defence behind intent grounding and Pydantic
# validation (see .claude/memory/workflow-rules.md #6).
_PROHIBITIONS = (
    "RULES YOU MUST FOLLOW:\n"
    "- You MUST ONLY discuss services in the SERVICES LIST. If asked about any "
    "other service, say '{business} does not offer that. I can help you with: "
    "{service_names}.'\n"
    "- NEVER quote a price that is not in the SERVICES LIST.\n"
    "- NEVER offer a discount that is not in the DISCOUNT POLICY.\n"
    "- NEVER invent a phone number, email address, location, booking link, or "
    "availability. If a detail is not stated above, say you don't have it and "
    "offer to connect the customer with the team.\n"
    "- Do not make claims about being open, available, or able to visit at a "
    "specific time unless WORKING HOURS states it."
)

# One objective per stage. Layer 2 is a single sentence — the turn's goal.
_STAGE_OBJECTIVES: dict[ConversationState, str] = {
    ConversationState.NEW: (
        "Greet the customer warmly on behalf of {business}, acknowledge their "
        "message, and invite them to tell you what they need. One short, friendly reply."
    ),
    ConversationState.GREETED: (
        "Greet the customer warmly on behalf of {business}, acknowledge their "
        "message, and invite them to tell you what they need. One short, friendly reply."
    ),
    ConversationState.QUALIFYING: (
        "Ask ONE clear qualifying question at a time to understand the customer's "
        "need, scope, timing, and location. Do not pitch or quote a price yet. "
        "Keep it conversational."
    ),
    ConversationState.PITCH_SENT: (
        "Recommend the most relevant service(s) from the SERVICES LIST and quote "
        "the EXACT price(s) shown. Explain the value in a sentence or two, then "
        "invite the customer to go ahead."
    ),
    ConversationState.BOOKING_OFFERED: (
        "Present exactly TWO options: (1) book now (share the booking link only if "
        "one is provided) and (2) talk to the team. Be concise and encouraging."
    ),
    ConversationState.BOOKED: (
        "Confirm the booking, thank the customer, and briefly tell them what happens next."
    ),
    ConversationState.HANDED_OFF: (
        "Let the customer know a team member will follow up personally very soon. "
        "Do not attempt to resolve the request further yourself."
    ),
    ConversationState.LOST: (
        "Re-engage warmly: acknowledge it has been a little while, remind them of "
        "the value on offer, and invite them back with one light, no-pressure question."
    ),
}

# Stages that get the Layer 3 persona block.
_PERSONA_STAGES: frozenset[ConversationState] = frozenset(
    {ConversationState.QUALIFYING, ConversationState.PITCH_SENT}
)

# Defensive per-section length caps (characters) for model-supplied content.
_DESCRIPTION_CAP = 400
_HOURS_CAP = 400
_AREAS_CAP = 400
_PERSONA_CAP = 900


def build_system_prompt(context: TenantAIContext, stage: ConversationState) -> str:
    """Assemble the grounded, stage-aware system prompt for one turn."""
    layers = [_base_layer(context), _stage_layer(context, stage)]
    if stage in _PERSONA_STAGES:
        persona = _persona_layer(context)
        if persona:
            layers.append(persona)
    return "\n\n".join(layer for layer in layers if layer)


# ---------------------------------------------------------------------------
# Layer 1 — base (always present)
# ---------------------------------------------------------------------------


def _base_layer(context: TenantAIContext) -> str:
    business = context.business_name
    sections: list[str] = [
        f"You are the WhatsApp assistant for {business}, a {context.category} business. "
        "You speak on the business's behalf to potential customers. Be warm, concise, "
        "and helpful. Only ever use the information in this brief."
    ]
    if context.description:
        sections.append(f"ABOUT:\n{context.description[:_DESCRIPTION_CAP]}")

    service_lines, service_names = _format_services(context.services)
    sections.append(f"SERVICES LIST (the ONLY services and prices you may offer):\n{service_lines}")

    discount = _discount_policy(context.policies)
    sections.append(
        f"DISCOUNT POLICY:\n{discount}"
        if discount
        else "DISCOUNT POLICY:\nNo discounts are offered beyond the prices in the SERVICES LIST."
    )

    hours = _format_hours(context.hours)
    sections.append(
        f"WORKING HOURS:\n{hours}"
        if hours
        else "WORKING HOURS:\nNot specified — do not claim any specific availability."
    )

    areas = _format_areas(context.locations)
    if areas:
        sections.append(f"SERVICE AREAS:\n{areas}")

    contact = _format_contact(context)
    if contact:
        sections.append(f"CONTACT DETAILS (share ONLY these, never invent others):\n{contact}")

    if context.tone:
        sections.append(f"TONE: {context.tone}")

    sections.append(
        _PROHIBITIONS.format(
            business=business, service_names=service_names or "our listed services"
        )
    )
    return "\n\n".join(sections)


def _format_services(services: dict[str, object]) -> tuple[str, str]:
    """Return (numbered list, comma-joined names). Prices are rendered exactly
    from paise; a business with no listed services gets an explicit note."""
    raw_items = services.get("items") if isinstance(services, dict) else None
    items = [it for it in raw_items if isinstance(it, dict)] if isinstance(raw_items, list) else []
    if not items:
        return "(No services are listed. Do not offer or price anything.)", ""

    lines: list[str] = []
    names: list[str] = []
    for index, item in enumerate(items, start=1):
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        names.append(name)
        price = _format_price(item)
        unit = str(item.get("unit", "")).strip()
        line = f"{index}. {name}"
        if price:
            line += f" — {price}"
        if unit:
            line += f" ({unit})"
        lines.append(line)
    return "\n".join(lines), ", ".join(names)


def _rupees(paise: object) -> str | None:
    if isinstance(paise, bool) or not isinstance(paise, int | float):
        return None
    return f"₹{int(paise) // 100:,}"


def _format_price(item: dict[str, object]) -> str:
    """Exact price string from the paise fields — never rounded or invented."""
    lo = _rupees(item.get("price_min_paise"))
    hi = _rupees(item.get("price_max_paise"))
    single = _rupees(item.get("price_paise"))
    if lo and hi:
        return lo if lo == hi else f"{lo}–{hi}"
    if single:
        return single
    if lo:
        return f"from {lo}"
    return ""


def _discount_policy(policies: dict[str, object]) -> str | None:
    for key in ("discount_policy", "discount", "discounts"):
        value = policies.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _scalar(value: object) -> str:
    """Render a JSONB value for the prompt: scalars as-is, structures compactly."""
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def _format_hours(hours: dict[str, object]) -> str:
    if not isinstance(hours, dict) or not hours:
        return ""
    for key in ("text", "summary"):
        value = hours.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()[:_HOURS_CAP]
    parts = [f"{key.replace('_', ' ').title()}: {_scalar(value)}" for key, value in hours.items()]
    return "; ".join(parts)[:_HOURS_CAP]


def _format_areas(locations: dict[str, object]) -> str:
    if not isinstance(locations, dict) or not locations:
        return ""
    for key in ("service_areas", "areas", "cities", "pincodes", "text"):
        value = locations.get(key)
        if isinstance(value, list) and value:
            return ", ".join(str(x) for x in value)[:_AREAS_CAP]
        if isinstance(value, str) and value.strip():
            return value.strip()[:_AREAS_CAP]
    parts = [f"{k}: {v}" for k, v in locations.items() if isinstance(v, str | int)]
    return "; ".join(parts)[:_AREAS_CAP]


def _format_contact(context: TenantAIContext) -> str:
    lines: list[str] = []
    if context.contact_phone:
        lines.append(f"Phone: {context.contact_phone}")
    if context.contact_email:
        lines.append(f"Email: {context.contact_email}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Layer 2 — stage objective
# ---------------------------------------------------------------------------


def _stage_layer(context: TenantAIContext, stage: ConversationState) -> str:
    objective = _STAGE_OBJECTIVES.get(stage, _STAGE_OBJECTIVES[ConversationState.QUALIFYING])
    return f"CURRENT OBJECTIVE ({stage.value}):\n{objective.format(business=context.business_name)}"


# ---------------------------------------------------------------------------
# Layer 3 — persona (QUALIFYING & PITCH_SENT only)
# ---------------------------------------------------------------------------


def _persona_layer(context: TenantAIContext) -> str:
    lines: list[str] = []
    ideal = _describe_audience(context.target_audience)
    if ideal:
        lines.append(f"Ideal customer: {ideal}")
    objections = _describe_objections(context.faqs)
    if objections:
        lines.append(f"Common objections & how to address them:\n{objections}")
    if not lines:
        return ""
    lines.append(
        "When a customer hesitates, acknowledge the concern, reframe around the "
        "value in the SERVICES LIST, and never invent a discount to close."
    )
    body = "\n".join(lines)[:_PERSONA_CAP]
    return f"IDEAL CUSTOMER & OBJECTIONS:\n{body}"


def _describe_audience(audience: dict[str, object]) -> str:
    if not isinstance(audience, dict) or not audience:
        return ""
    for key in ("description", "summary", "profile"):
        value = audience.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    parts = [f"{k}: {v}" for k, v in audience.items() if isinstance(v, str | int)]
    return "; ".join(parts)


def _describe_objections(faqs: dict[str, object]) -> str:
    if not isinstance(faqs, dict) or not faqs:
        return ""
    raw_items = faqs.get("items")
    items = raw_items if isinstance(raw_items, list) else None
    if items:
        rendered = []
        for item in items:
            if isinstance(item, dict):
                question = str(item.get("question") or item.get("q") or "").strip()
                answer = str(item.get("answer") or item.get("a") or "").strip()
                if question and answer:
                    rendered.append(f"- {question} -> {answer}")
        if rendered:
            return "\n".join(rendered)
    parts = [f"- {k} -> {v}" for k, v in faqs.items() if isinstance(v, str)]
    return "\n".join(parts)
