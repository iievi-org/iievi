"""Conversation state machine — Prompt 7 Step 1.

The backbone of the grounded conversation engine. It enforces a strict
transition graph (``transition`` rejects any pair not in ``VALID_TRANSITIONS``)
and derives the next state from detected intent signals
(``determine_transition``). Every transition is an auditable business event:
``record_transition`` writes a ``system`` event to ``conversations`` AND an
``audit_logs`` entry, and maps the AI stage onto the CRM ``Lead.status`` pipeline.

``conversation_state`` is the AI's own progression, distinct from the CRM
``Lead.status``:

    NEW -> GREETED -> QUALIFYING -> PITCH_SENT -> BOOKING_OFFERED -> BOOKED

with HANDED_OFF (escalation, terminal for the AI) and LOST (dropped, but
re-engageable back to GREETED by a 24-48h follow-up) as the two off-ramps.
"""

import logging
import uuid
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidStateTransitionError
from app.db.models import AuditAction, ConversationState, LeadStatus
from app.modules.audit.service import log_event

logger = logging.getLogger(__name__)

S = ConversationState


class IntentSignalsLike(Protocol):
    """Structural contract for the signals the state machine reads.

    The concrete ``IntentSignals`` model (ai/intent_detection_service.py)
    satisfies this. Using a Protocol keeps the state machine free of the
    AI-stack imports so its logic stays pure and fast to unit-test.
    """

    lead_ready: bool
    requested_human: bool
    objection_expressed: bool
    all_questions_answered: bool


# The transition graph. transition(current, new) with `new` absent from the
# set for `current` raises InvalidStateTransitionError. Every live stage can
# escalate (HANDED_OFF) or drop (LOST); LOST re-engages to GREETED.
VALID_TRANSITIONS: dict[ConversationState, frozenset[ConversationState]] = {
    S.NEW: frozenset({S.GREETED, S.HANDED_OFF, S.LOST}),
    S.GREETED: frozenset({S.QUALIFYING, S.HANDED_OFF, S.LOST}),
    S.QUALIFYING: frozenset({S.PITCH_SENT, S.HANDED_OFF, S.LOST}),
    S.PITCH_SENT: frozenset({S.BOOKING_OFFERED, S.HANDED_OFF, S.LOST}),
    S.BOOKING_OFFERED: frozenset({S.BOOKED, S.HANDED_OFF, S.LOST}),
    S.BOOKED: frozenset({S.HANDED_OFF}),
    S.HANDED_OFF: frozenset(),
    S.LOST: frozenset({S.GREETED, S.HANDED_OFF}),
}

# Terminal for the AI engine: determine_transition never advances out of these
# on its own (a human owns HANDED_OFF).
TERMINAL_STATES: frozenset[ConversationState] = frozenset({S.HANDED_OFF})

# AI stage -> CRM pipeline status. HANDED_OFF is deliberately absent: escalation
# keeps the lead's CRM status and flips manual_mode instead.
_STATUS_MAP: dict[ConversationState, LeadStatus] = {
    S.NEW: LeadStatus.NEW,
    S.GREETED: LeadStatus.ENGAGED,
    S.QUALIFYING: LeadStatus.ENGAGED,
    S.PITCH_SENT: LeadStatus.QUALIFIED,
    S.BOOKING_OFFERED: LeadStatus.QUALIFIED,
    S.BOOKED: LeadStatus.BOOKED,
    S.LOST: LeadStatus.LOST,
}


def can_transition(current: ConversationState, new: ConversationState) -> bool:
    """True if ``current -> new`` is in the transition graph."""
    return new in VALID_TRANSITIONS.get(current, frozenset())


def is_terminal(state: ConversationState) -> bool:
    return state in TERMINAL_STATES


def transition(current_state: ConversationState, new_state: ConversationState) -> ConversationState:
    """Validate and return ``new_state``; raise on an illegal pair.

    Any code that moves a conversation between states funnels through here, so
    an invalid pair can never be persisted.
    """
    if not can_transition(current_state, new_state):
        raise InvalidStateTransitionError(
            f"illegal conversation transition {current_state.value} -> {new_state.value}",
            details={"from": current_state.value, "to": new_state.value},
        )
    return new_state


def crm_status_for(state: ConversationState) -> LeadStatus | None:
    """The CRM Lead.status a conversation stage maps to, or None to leave it."""
    return _STATUS_MAP.get(state)


def determine_transition(
    current_state: ConversationState, intent_signals: IntentSignalsLike
) -> ConversationState | None:
    """Derive the next state from intent signals, or None to stay put.

    Priority order (Prompt 7 Step 1):
    1. ``requested_human`` overrides everything -> HANDED_OFF (unless terminal).
    2. Opening stages advance automatically (NEW -> GREETED -> QUALIFYING).
    3. QUALIFYING -> PITCH_SENT when ``all_questions_answered``.
    4. PITCH_SENT -> BOOKING_OFFERED when ``lead_ready``.
    Otherwise stay (e.g. an objection is handled by the persona, not a move).
    """
    if intent_signals.requested_human and current_state not in TERMINAL_STATES:
        return S.HANDED_OFF
    if current_state is S.NEW:
        return S.GREETED
    if current_state is S.GREETED:
        return S.QUALIFYING
    if current_state is S.QUALIFYING and intent_signals.all_questions_answered:
        return S.PITCH_SENT
    if current_state is S.PITCH_SENT and intent_signals.lead_ready:
        return S.BOOKING_OFFERED
    return None


async def record_transition(
    session: AsyncSession,
    *,
    lead_id: uuid.UUID,
    tenant_id: uuid.UUID,
    from_state: ConversationState,
    to_state: ConversationState,
    signals: IntentSignalsLike | None = None,
    actor_user_id: uuid.UUID | None = None,
) -> None:
    """Apply a validated transition and record it everywhere it matters.

    Updates ``leads.conversation_state`` (+ the mapped CRM ``status``), appends
    a ``system`` event to ``conversations``, and writes an ``audit_logs`` entry
    — state machine transitions are auditable business events (Prompt 7 Step 1).

    MUST run inside an active tenant scope: ``conversations`` is RLS-protected.
    Does not commit — it participates in the caller's transaction.
    """
    transition(from_state, to_state)  # raises on an illegal pair

    new_status = crm_status_for(to_state)
    await session.execute(
        text(
            "UPDATE leads SET conversation_state = :cs, "
            "status = COALESCE(:st, status), updated_at = now() WHERE id = :id"
        ),
        {"cs": to_state.value, "st": new_status.value if new_status else None, "id": lead_id},
    )
    await session.execute(
        text(
            "INSERT INTO conversations (tenant_id, lead_id, role, content) "
            "VALUES (:tid, :lid, 'system', :content)"
        ),
        {
            "tid": tenant_id,
            "lid": lead_id,
            "content": f"state_transition: {from_state.value} -> {to_state.value}",
        },
    )
    signal_meta: dict[str, object] = (
        {
            "lead_ready": signals.lead_ready,
            "requested_human": signals.requested_human,
            "objection_expressed": signals.objection_expressed,
            "all_questions_answered": signals.all_questions_answered,
        }
        if signals is not None
        else {}
    )
    await log_event(
        session,
        action=AuditAction.UPDATE,
        resource_type="lead_conversation_state",
        resource_id=lead_id,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        old_values={"conversation_state": from_state.value},
        new_values={"conversation_state": to_state.value},
        metadata={"signals": signal_meta} if signal_meta else {},
    )
    logger.info(
        "conversation transition",
        extra={
            "tenant_id": str(tenant_id),
            "lead_id": str(lead_id),
            "from_state": from_state.value,
            "to_state": to_state.value,
        },
    )
