"""Outreach Celery tasks — Prompt 7 Step 5.

Thin task shells on the ``lead_outreach`` queue (NO auto-retry, per queue
policy). All logic lives in ``conversations.outreach_service.run_outreach_step``;
each task self-guards on ``conversation_state``, so a lead who has already
engaged is never messaged even if the task wasn't revoked in time.
"""

import asyncio
import uuid

from app.modules.conversations.outreach_service import run_outreach_step
from app.worker.celery_app import celery_app


def _run(step: str, payload: dict[str, str]) -> None:
    asyncio.run(
        run_outreach_step(step, uuid.UUID(payload["tenant_id"]), uuid.UUID(payload["lead_id"]))
    )


@celery_app.task(name="outreach.send_initial_contact", queue="lead_outreach", ignore_result=True)
def send_initial_contact(payload: dict[str, str]) -> None:
    _run("initial", payload)


@celery_app.task(name="outreach.send_followup_one", queue="lead_outreach", ignore_result=True)
def send_followup_one(payload: dict[str, str]) -> None:
    _run("followup_one", payload)


@celery_app.task(name="outreach.send_followup_two", queue="lead_outreach", ignore_result=True)
def send_followup_two(payload: dict[str, str]) -> None:
    _run("followup_two", payload)


@celery_app.task(name="outreach.send_lost_reengagement", queue="lead_outreach", ignore_result=True)
def send_lost_reengagement(payload: dict[str, str]) -> None:
    _run("lost_reengage", payload)
