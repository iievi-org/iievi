"""Profile change hooks — downstream effects of profile writes.

after_profile_write(changed_fields, tenant_id) dispatches:
- services updated       → compute_nanobanana_style_prompt
                           [CANVA_NEXT_UPDATE] will also refresh Canva templates
- brand colours updated  → compute_nanobanana_style_prompt
                           [CANVA_NEXT_UPDATE] will call Canva brand kit update API
- working hours updated  → NO downstream effect (AI reads hours fresh per call)
- credential revoked     → cancel_pending_outreach_tasks_for_tenant

Enqueue failures are logged, never raised — a profile save must not fail
because the broker is down.
"""

import logging
import uuid
from collections.abc import Iterable

logger = logging.getLogger(__name__)

_STYLE_TRIGGERS = frozenset({"services", "colors", "fonts", "brand_identity"})


def after_profile_write(changed_fields: Iterable[str], tenant_id: uuid.UUID) -> None:
    changed = set(changed_fields)
    try:
        if changed & _STYLE_TRIGGERS:
            from app.worker.tasks import compute_nanobanana_style_prompt

            compute_nanobanana_style_prompt.delay(str(tenant_id))
        if "credential_revoked" in changed:
            from app.worker.tasks import cancel_pending_outreach_tasks_for_tenant

            cancel_pending_outreach_tasks_for_tenant.delay(str(tenant_id))
    except Exception:  # noqa: BLE001
        logger.warning("profile hook enqueue failed", extra={"tenant_id": str(tenant_id)})
