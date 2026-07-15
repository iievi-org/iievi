"""Billing event processing — the Celery side of the payment webhooks.

The provider name is IN the task payload: a Razorpay event can never run
through Stripe handling. Event mapping:

- subscription.charged / invoice.payment_succeeded → activate tenant,
  update plan (access tokens carry the plan claim and live ≤15 min, so the
  new plan is fully visible within one token lifetime)
- subscription.halted / invoice.payment_failed → suspend (AI features gate
  on tenant status); payment-failure email lands with the email phase
- subscription.cancelled / customer.subscription.deleted → flag the
  downgrade at period end (the period-end sweep applies it)
"""

import asyncio
import logging
import uuid
from typing import Any

from sqlalchemy import text

from app.worker.celery_app import celery_app
from app.worker.db import worker_session

logger = logging.getLogger(__name__)

_ACTIVATE_EVENTS = {"subscription.charged", "invoice.payment_succeeded"}
_SUSPEND_EVENTS = {"subscription.halted", "invoice.payment_failed"}
_CANCEL_EVENTS = {"subscription.cancelled", "customer.subscription.deleted"}


def _provider_subscription_id(provider: str, payload: dict[str, Any]) -> str:
    if provider == "razorpay":
        entity = (
            payload.get("payload", {}).get("subscription", {}).get("entity", {})
            if isinstance(payload.get("payload"), dict)
            else {}
        )
        return str(entity.get("id", ""))
    # stripe
    data = payload.get("data", {}).get("object", {})
    return str(data.get("subscription") or data.get("id", ""))


@celery_app.task(name="billing.process_event", queue="usage_tracking", ignore_result=True)
def process_billing_event(task_payload: dict[str, Any]) -> None:
    provider = str(task_payload["provider"])
    event_type = str(task_payload["event_type"])
    event_id = uuid.UUID(str(task_payload["event_id"]))
    payload: dict[str, Any] = task_payload.get("payload", {})

    async def _run() -> None:
        from app.db.base import with_tenant_scope
        from app.modules.webhooks.service import mark_event_failed, mark_event_processed

        async with worker_session() as session:
            try:
                subscription_id = _provider_subscription_id(provider, payload)
                if not subscription_id:
                    logger.warning(
                        "billing event without subscription id",
                        extra={"provider": provider, "event_type": event_type},
                    )
                    await mark_event_processed(session, event_id)
                    return

                # SECURITY DEFINER lookup — the billing event arrives before
                # any tenant context exists; subscriptions is RLS-scoped.
                row = (
                    await session.execute(
                        text("SELECT * FROM billing_lookup_subscription(:provider, :sid)"),
                        {"provider": provider, "sid": subscription_id},
                    )
                ).first()
                if row is None:
                    logger.warning(
                        "billing event for unknown subscription",
                        extra={"provider": provider, "subscription_id": subscription_id},
                    )
                    await mark_event_failed(session, event_id)
                    return
                tenant_id, plan = uuid.UUID(str(row[0])), str(row[1])

                if event_type in _ACTIVATE_EVENTS:
                    # tenants carries no RLS — direct update is sanctioned
                    await session.execute(
                        text(
                            "UPDATE tenants SET status = 'active', plan = :plan, "
                            "updated_at = now() WHERE id = :tid"
                        ),
                        {"tid": tenant_id, "plan": plan},
                    )
                    async with with_tenant_scope(session, tenant_id):
                        await _set_subscription_status(session, provider, subscription_id, "active")
                elif event_type in _SUSPEND_EVENTS:
                    await session.execute(
                        text(
                            "UPDATE tenants SET status = 'suspended', updated_at = now() "
                            "WHERE id = :tid"
                        ),
                        {"tid": tenant_id},
                    )
                    async with with_tenant_scope(session, tenant_id):
                        await _set_subscription_status(
                            session, provider, subscription_id, "past_due"
                        )
                elif event_type in _CANCEL_EVENTS:
                    async with with_tenant_scope(session, tenant_id):
                        await session.execute(
                            text(
                                "UPDATE subscriptions SET cancel_at_period_end = true, "
                                "updated_at = now() WHERE provider = :provider "
                                "AND provider_subscription_id = :sid"
                            ),
                            {"provider": provider, "sid": subscription_id},
                        )
                else:
                    logger.info(
                        "unhandled billing event",
                        extra={"provider": provider, "event_type": event_type},
                    )
                await session.commit()
                await mark_event_processed(session, event_id)
                logger.info(
                    "billing event processed",
                    extra={
                        "provider": provider,
                        "event_type": event_type,
                        "tenant_id": str(tenant_id),
                    },
                )
            except Exception:
                await session.rollback()
                await mark_event_failed(session, event_id)
                raise

    asyncio.run(_run())


async def _set_subscription_status(
    session: Any,
    provider: str,
    subscription_id: str,
    status: str,  # noqa: ANN401
) -> None:
    await session.execute(
        text(
            "UPDATE subscriptions SET status = :status, updated_at = now() "
            "WHERE provider = :provider AND provider_subscription_id = :sid"
        ),
        {"status": status, "provider": provider, "sid": subscription_id},
    )
