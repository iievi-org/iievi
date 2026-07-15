"""Conversation state machine DoD (Prompt 7 Step 1) — pure logic, no DB."""

from types import SimpleNamespace

import pytest

from app.core.exceptions import InvalidStateTransitionError
from app.db.models import ConversationState as S
from app.db.models import LeadStatus
from app.modules.conversations import state_machine as sm


def sig(**kw: bool) -> SimpleNamespace:
    base = {
        "lead_ready": False,
        "requested_human": False,
        "objection_expressed": False,
        "all_questions_answered": False,
    }
    base.update(kw)
    return SimpleNamespace(**base)


def test_valid_transitions_allowed() -> None:
    assert sm.transition(S.NEW, S.GREETED) == S.GREETED
    assert sm.transition(S.QUALIFYING, S.PITCH_SENT) == S.PITCH_SENT
    assert sm.transition(S.PITCH_SENT, S.BOOKING_OFFERED) == S.BOOKING_OFFERED
    assert sm.transition(S.LOST, S.GREETED) == S.GREETED  # re-engagement path


@pytest.mark.parametrize(
    ("frm", "to"),
    [
        (S.NEW, S.BOOKED),
        (S.NEW, S.PITCH_SENT),
        (S.HANDED_OFF, S.GREETED),  # terminal for the AI
        (S.BOOKED, S.QUALIFYING),
        (S.QUALIFYING, S.BOOKING_OFFERED),  # can't skip PITCH_SENT
    ],
)
def test_invalid_transition_raises(frm: S, to: S) -> None:
    with pytest.raises(InvalidStateTransitionError):
        sm.transition(frm, to)


def test_handoff_overrides_everything() -> None:
    # requested_human wins over qualification/booking signals
    assert (
        sm.determine_transition(
            S.QUALIFYING, sig(requested_human=True, all_questions_answered=True)
        )
        == S.HANDED_OFF
    )
    assert sm.determine_transition(S.NEW, sig(requested_human=True)) == S.HANDED_OFF
    # already terminal — no re-handoff
    assert sm.determine_transition(S.HANDED_OFF, sig(requested_human=True)) is None


def test_opening_stages_advance_automatically() -> None:
    assert sm.determine_transition(S.NEW, sig()) == S.GREETED
    assert sm.determine_transition(S.GREETED, sig()) == S.QUALIFYING


def test_qualification_and_booking_are_gated() -> None:
    assert sm.determine_transition(S.QUALIFYING, sig()) is None
    assert sm.determine_transition(S.QUALIFYING, sig(all_questions_answered=True)) == S.PITCH_SENT
    assert sm.determine_transition(S.PITCH_SENT, sig()) is None
    assert sm.determine_transition(S.PITCH_SENT, sig(lead_ready=True)) == S.BOOKING_OFFERED


def test_objection_alone_does_not_move_state() -> None:
    assert sm.determine_transition(S.QUALIFYING, sig(objection_expressed=True)) is None


def test_full_path_new_to_booking_offered_is_all_legal() -> None:
    # The DoD conversation: first message -> BOOKING_OFFERED, every hop legal.
    state = S.NEW
    for next_signals in (sig(), sig(), sig(all_questions_answered=True), sig(lead_ready=True)):
        nxt = sm.determine_transition(state, next_signals)
        assert nxt is not None
        sm.transition(state, nxt)  # must not raise
        state = nxt
    assert state == S.BOOKING_OFFERED


def test_crm_status_mapping() -> None:
    assert sm.crm_status_for(S.NEW) == LeadStatus.NEW
    assert sm.crm_status_for(S.QUALIFYING) == LeadStatus.ENGAGED
    assert sm.crm_status_for(S.PITCH_SENT) == LeadStatus.QUALIFIED
    assert sm.crm_status_for(S.BOOKING_OFFERED) == LeadStatus.QUALIFIED
    assert sm.crm_status_for(S.BOOKED) == LeadStatus.BOOKED
    assert sm.crm_status_for(S.LOST) == LeadStatus.LOST
    # HANDED_OFF keeps the CRM status (manual_mode is flipped instead)
    assert sm.crm_status_for(S.HANDED_OFF) is None
