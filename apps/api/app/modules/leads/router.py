"""Lead inbox API.

Pagination is cursor-based on ({updated_at}:{lead_id}) — offset pagination
shifts under the user's feet as new leads arrive; a compound cursor keeps
the ordering stable. Status changes go through an explicit state machine:
an invalid transition is a 400, not a silent write.
"""

import csv
import io
import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.exceptions import BadRequestError, ResourceNotFoundError
from app.core.permissions import Permission
from app.db.models import Conversation, ConversationRole, Lead, LeadStatus
from app.gateway.dependencies import CurrentUser, ScopedSession, check_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/leads", tags=["leads"])

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100

# Allowed status transitions — anything else is a client error
_TRANSITIONS: dict[LeadStatus, frozenset[LeadStatus]] = {
    LeadStatus.NEW: frozenset({LeadStatus.ENGAGED, LeadStatus.QUALIFIED, LeadStatus.LOST}),
    LeadStatus.ENGAGED: frozenset({LeadStatus.QUALIFIED, LeadStatus.BOOKED, LeadStatus.LOST}),
    LeadStatus.QUALIFIED: frozenset({LeadStatus.BOOKED, LeadStatus.WON, LeadStatus.LOST}),
    LeadStatus.BOOKED: frozenset({LeadStatus.WON, LeadStatus.LOST}),
    LeadStatus.WON: frozenset(),
    LeadStatus.LOST: frozenset({LeadStatus.NEW}),  # re-open
}


def _lead_dict(lead: Lead) -> dict[str, object]:
    return {
        "id": str(lead.id),
        "source": lead.source.value,
        "status": lead.status.value,
        "platform": lead.platform.value,
        "platform_id": lead.platform_id,
        "name": lead.name,
        "phone": lead.phone,
        "email": lead.email,
        "manual_mode": lead.manual_mode,
        "last_inbound_at": lead.last_inbound_at.isoformat() if lead.last_inbound_at else None,
        "metadata": lead.meta or {},
        "created_at": lead.created_at.isoformat(),
        "updated_at": lead.updated_at.isoformat(),
    }


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        raw_ts, raw_id = cursor.rsplit(":", 1)
        return datetime.fromisoformat(raw_ts), uuid.UUID(raw_id)
    except (ValueError, TypeError) as exc:
        raise BadRequestError("Malformed cursor") from exc


@router.get(
    "",
    summary="List leads (cursor-paginated)",
    dependencies=[Depends(check_permission(Permission.LEADS_READ))],
)
async def list_leads(
    user: CurrentUser,
    session: ScopedSession,
    status: Annotated[LeadStatus | None, Query()] = None,
    source: Annotated[str | None, Query()] = None,
    created_after: Annotated[datetime | None, Query()] = None,
    created_before: Annotated[datetime | None, Query()] = None,
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> dict[str, object]:
    query = select(Lead).order_by(Lead.updated_at.desc(), Lead.id.desc())
    if status is not None:
        query = query.where(Lead.status == status)
    if source is not None:
        query = query.where(Lead.source == source)
    if created_after is not None:
        query = query.where(Lead.created_at >= created_after)
    if created_before is not None:
        query = query.where(Lead.created_at <= created_before)
    if cursor:
        cursor_ts, cursor_id = _decode_cursor(cursor)
        query = query.where(
            (Lead.updated_at < cursor_ts) | ((Lead.updated_at == cursor_ts) & (Lead.id < cursor_id))
        )
    leads = (await session.scalars(query.limit(limit + 1))).all()

    has_more = len(leads) > limit
    page = leads[:limit]
    next_cursor = f"{page[-1].updated_at.isoformat()}:{page[-1].id}" if has_more and page else None
    return {
        "leads": [_lead_dict(lead) for lead in page],
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


@router.get(
    "/{lead_id}",
    summary="Lead detail",
    dependencies=[Depends(check_permission(Permission.LEADS_READ))],
)
async def get_lead(
    lead_id: uuid.UUID, user: CurrentUser, session: ScopedSession
) -> dict[str, object]:
    lead = await session.scalar(select(Lead).where(Lead.id == lead_id))
    if lead is None:
        raise ResourceNotFoundError(f"No lead {lead_id}")
    return _lead_dict(lead)


@router.get(
    "/{lead_id}/conversation",
    summary="Full conversation history",
    dependencies=[Depends(check_permission(Permission.CONVERSATIONS_READ))],
)
async def get_conversation(
    lead_id: uuid.UUID, user: CurrentUser, session: ScopedSession
) -> dict[str, object]:
    lead = await session.scalar(select(Lead).where(Lead.id == lead_id))
    if lead is None:
        raise ResourceNotFoundError(f"No lead {lead_id}")
    messages = (
        await session.scalars(
            select(Conversation)
            .where(Conversation.lead_id == lead_id)
            .order_by(Conversation.created_at.asc())
        )
    ).all()
    return {
        "lead_id": str(lead_id),
        "messages": [
            {
                "id": str(m.id),
                "role": m.role.value,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }


class LeadPatch(BaseModel):
    status: LeadStatus | None = None
    manual_mode: bool | None = None


@router.patch(
    "/{lead_id}",
    summary="Update lead status / manual mode",
    dependencies=[Depends(check_permission(Permission.LEADS_WRITE))],
)
async def patch_lead(
    lead_id: uuid.UUID, body: LeadPatch, user: CurrentUser, session: ScopedSession
) -> dict[str, object]:
    lead = await session.scalar(select(Lead).where(Lead.id == lead_id))
    if lead is None:
        raise ResourceNotFoundError(f"No lead {lead_id}")
    if body.status is not None and body.status != lead.status:
        if body.status not in _TRANSITIONS[lead.status]:
            raise BadRequestError(
                f"Cannot move a lead from {lead.status.value} to {body.status.value}",
                details={
                    "allowed": sorted(s.value for s in _TRANSITIONS[lead.status]),
                },
            )
        lead.status = body.status
        from app.modules.realtime.events import EventEmitter

        await EventEmitter.emit(
            user.tenant_id,
            "lead_status_changed",
            {"lead_id": str(lead_id), "status": body.status.value},
        )
    if body.manual_mode is not None:
        lead.manual_mode = body.manual_mode
    await session.flush()
    return _lead_dict(lead)


class ManualMessage(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


@router.post(
    "/{lead_id}/message",
    summary="Send a manual message (manual mode only)",
    dependencies=[Depends(check_permission(Permission.LEADS_WRITE))],
)
async def send_manual_message(
    lead_id: uuid.UUID, body: ManualMessage, user: CurrentUser, session: ScopedSession
) -> dict[str, object]:
    lead = await session.scalar(select(Lead).where(Lead.id == lead_id))
    if lead is None:
        raise ResourceNotFoundError(f"No lead {lead_id}")
    if not lead.manual_mode:
        raise BadRequestError(
            "Manual messages require manual mode — take over the conversation first"
        )

    if lead.platform.value == "whatsapp":
        from app.modules.channels.whatsapp_client import send_session_message
        from app.modules.credentials.service import get_decrypted_credential

        credential = await get_decrypted_credential(user.tenant_id, "whatsapp", session)
        await send_session_message(
            lead.platform_id,
            body.text,
            credential,
            last_inbound_at=lead.last_inbound_at,
            lead_id=lead_id,
            tenant_id=user.tenant_id,
        )
    # Messenger/Instagram manual sends land with the unified inbox phase;
    # the message is recorded either way so the history is complete.
    session.add(
        Conversation(
            tenant_id=user.tenant_id,
            lead_id=lead_id,
            role=ConversationRole.HUMAN_AGENT,
            content=body.text,
        )
    )
    await session.flush()
    return {"sent": True}


@router.patch(
    "/{lead_id}/take-over",
    summary="Enable manual mode (human takes the conversation)",
    dependencies=[Depends(check_permission(Permission.LEADS_WRITE))],
)
async def take_over(
    lead_id: uuid.UUID, user: CurrentUser, session: ScopedSession
) -> dict[str, object]:
    lead = await session.scalar(select(Lead).where(Lead.id == lead_id))
    if lead is None:
        raise ResourceNotFoundError(f"No lead {lead_id}")
    lead.manual_mode = True
    # Remember pending AI work so resume-ai can re-trigger it. Task-id level
    # cancellation lands with the outreach phase's task registry.
    meta = dict(lead.meta or {})
    meta["taken_over_at"] = datetime.now(UTC).isoformat()
    lead.meta = meta
    await session.flush()
    return _lead_dict(lead)


@router.patch(
    "/{lead_id}/resume-ai",
    summary="Disable manual mode (AI resumes)",
    dependencies=[Depends(check_permission(Permission.LEADS_WRITE))],
)
async def resume_ai(
    lead_id: uuid.UUID, user: CurrentUser, session: ScopedSession
) -> dict[str, object]:
    lead = await session.scalar(select(Lead).where(Lead.id == lead_id))
    if lead is None:
        raise ResourceNotFoundError(f"No lead {lead_id}")
    lead.manual_mode = False
    meta = dict(lead.meta or {})
    meta.pop("taken_over_at", None)
    lead.meta = meta
    await session.flush()

    from app.worker.ai_worker import generate_ai_response

    generate_ai_response.delay({"tenant_id": str(user.tenant_id), "lead_id": str(lead_id)})
    return _lead_dict(lead)


@router.post(
    "/export",
    summary="Export leads as CSV (streaming)",
    dependencies=[Depends(check_permission(Permission.LEADS_READ))],
)
async def export_leads(user: CurrentUser, session: ScopedSession) -> StreamingResponse:
    leads = (await session.scalars(select(Lead).order_by(Lead.created_at.asc()))).all()

    def _rows() -> "io.StringIO":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            ["id", "name", "phone", "email", "platform", "source", "status", "created_at"]
        )
        for lead in leads:
            writer.writerow(
                [
                    lead.id,
                    lead.name or "",
                    lead.phone or "",
                    lead.email or "",
                    lead.platform.value,
                    lead.source.value,
                    lead.status.value,
                    lead.created_at.isoformat(),
                ]
            )
        buffer.seek(0)
        return buffer

    return StreamingResponse(
        _rows(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )
