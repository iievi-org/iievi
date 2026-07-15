"""Transactional email via Resend — Prompt 7 Step 7.

Each email is a typed Pydantic template carrying only its data. It renders an
inlined-CSS Jinja2 body from ``templates/`` and exposes ``to_resend_payload()``
— the exact dict the Resend API expects. ``send_email`` posts it through the
shared ``resend`` circuit breaker; a missing ``RESEND_API_KEY`` degrades to a
logged no-op so non-production environments never hard-fail on email.

Email templates never reference external stylesheets — every style is inlined
on the element (``templates/_base.html`` is the shared wrapper) for maximum
email-client compatibility.
"""

import asyncio
import logging
from pathlib import Path
from typing import ClassVar

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel

from app.core.circuit import get_circuit
from app.core.config import settings
from app.core.exceptions import ExternalAPIError

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def _render(template_name: str, context: dict[str, object]) -> str:
    return _env.get_template(template_name).render(**context)


def _rupees(paise: int) -> str:
    return f"₹{int(paise) // 100:,}"


class EmailTemplate(BaseModel):
    """Base for typed email templates.

    Subclasses set the ``template`` file and implement ``_subject``/``_context``.
    The shared machinery renders the HTML and shapes the Resend payload so no
    call site ever hand-builds one.
    """

    template: ClassVar[str]
    to: str
    business_name: str

    def _subject(self) -> str:
        raise NotImplementedError

    def _body_context(self) -> dict[str, object]:
        raise NotImplementedError

    def _context(self) -> dict[str, object]:
        # Vars every template's _base.html wrapper needs, merged with the body's.
        return {
            "subject": self._subject(),
            "business_name": self.business_name,
            "dashboard_url": settings.dashboard_url,
            **self._body_context(),
        }

    def to_resend_payload(self) -> dict[str, object]:
        """Return the exact payload the Resend send API expects."""
        return {
            "from": settings.resend_from_email,
            "to": [self.to],
            "subject": self._subject(),
            "html": _render(self.template, self._context()),
        }


class WelcomeEmail(EmailTemplate):
    template: ClassVar[str] = "welcome.html"
    owner_name: str

    def _subject(self) -> str:
        return f"Welcome to IIEVI, {self.business_name}"

    def _body_context(self) -> dict[str, object]:
        return {"owner_name": self.owner_name}


class PaymentFailureEmail(EmailTemplate):
    template: ClassVar[str] = "payment_failure.html"
    amount_paise: int
    update_url: str

    def _subject(self) -> str:
        return "Action needed: your IIEVI payment didn't go through"

    def _body_context(self) -> dict[str, object]:
        return {"amount": _rupees(self.amount_paise), "update_url": self.update_url}


class LeadHandoffEmail(EmailTemplate):
    template: ClassVar[str] = "lead_handoff.html"
    lead_name: str
    lead_summary: str
    conversation_url: str

    def _subject(self) -> str:
        return f"A lead needs you: {self.lead_name}"

    def _body_context(self) -> dict[str, object]:
        return {
            "lead_name": self.lead_name,
            "lead_summary": self.lead_summary,
            "conversation_url": self.conversation_url,
        }


class PostPublishedEmail(EmailTemplate):
    template: ClassVar[str] = "post_published.html"
    platform: str
    post_url: str

    def _subject(self) -> str:
        return f"Your post is live on {self.platform.title()}"

    def _body_context(self) -> dict[str, object]:
        return {"platform": self.platform.title(), "post_url": self.post_url}


class PostFailedEmail(EmailTemplate):
    template: ClassVar[str] = "post_failed.html"
    platform: str
    reason: str

    def _subject(self) -> str:
        return f"A post couldn't be published on {self.platform.title()}"

    def _body_context(self) -> dict[str, object]:
        return {"platform": self.platform.title(), "reason": self.reason}


class CredentialExpiredEmail(EmailTemplate):
    template: ClassVar[str] = "credential_expired.html"
    service: str

    def _subject(self) -> str:
        return f"Reconnect your {self.service.title()} account"

    def _body_context(self) -> dict[str, object]:
        return {"service": self.service.title()}


class WeeklyPerformanceEmail(EmailTemplate):
    template: ClassVar[str] = "weekly_performance.html"
    leads_received: int
    ai_conversation_rate: int  # percent, 0-100
    posts_published: int
    ad_spend_paise: int
    bookings_closed: int

    def _subject(self) -> str:
        # Dynamic subject (Prompt 7 Step 12) — the value the owner opens for.
        return f"You got {self.leads_received} leads last week — here's how they converted"

    def _body_context(self) -> dict[str, object]:
        return {
            "leads_received": self.leads_received,
            "ai_conversation_rate": self.ai_conversation_rate,
            "posts_published": self.posts_published,
            "ad_spend": _rupees(self.ad_spend_paise),
            "bookings_closed": self.bookings_closed,
        }


class NotificationEmail(EmailTemplate):
    """Generic notification email used by the dispatch fan-out (Step 10) — the
    email channel for any in-app notification the user also wants by email."""

    template: ClassVar[str] = "notification.html"
    title: str
    body: str
    action_url: str

    def _subject(self) -> str:
        return self.title

    def _body_context(self) -> dict[str, object]:
        return {"title": self.title, "body": self.body, "action_url": self.action_url}


async def send_email(template: EmailTemplate) -> str | None:
    """Send one email; return the Resend message id, or None if email is
    disabled (no API key). Raises ExternalAPIError on a provider failure so the
    caller's circuit breaker and retry policy apply."""
    if not settings.resend_api_key:
        logger.info(
            "email skipped: RESEND_API_KEY not set",
            extra={"template": type(template).__name__, "to": template.to},
        )
        return None

    payload = template.to_resend_payload()

    async def _run() -> str | None:
        import resend

        resend.api_key = settings.resend_api_key
        # The resend SDK is synchronous; run it off the event loop.
        result = await asyncio.to_thread(resend.Emails.send, payload)  # type: ignore[arg-type]
        email_id = result.get("id") if isinstance(result, dict) else getattr(result, "id", None)
        logger.info(
            "email sent",
            extra={"template": type(template).__name__, "to": template.to, "email_id": email_id},
        )
        return str(email_id) if email_id else None

    try:
        return await get_circuit("resend").call(_run)
    except ExternalAPIError:
        raise
    except Exception as exc:  # noqa: BLE001 — normalise SDK errors at the boundary
        logger.error("resend email send failed", extra={"template": type(template).__name__})
        raise ExternalAPIError("Resend email send failed") from exc
