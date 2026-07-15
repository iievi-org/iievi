"""Five universal grounding invariants across every business category (Prompt 7 Step 9).

Each case sends an adversarial message through the REAL grounded pipeline
(build_system_prompt + a real Gemini call) and uses a Gemini judge to confirm
the reply didn't hallucinate. The suite runs in CI on every merge; a single
failing invariant blocks deployment.

Coverage note: rather than one near-identical file per category, the five
invariants are parametrized across all categories — same coverage, no
duplication. Total cases = 5 invariants x len(CATEGORIES).
"""

from typing import Any

import pytest

from app.modules.profiles.categories import CATEGORIES
from tests.hallucination.harness import (
    CATEGORY_KEYS,
    INVARIANTS,
    build_controlled_context,
    build_facts,
    generate_reply,
    judge,
)

pytestmark = pytest.mark.hallucination


@pytest.mark.parametrize("category_key", CATEGORY_KEYS)
@pytest.mark.parametrize("invariant", INVARIANTS, ids=[inv["id"] for inv in INVARIANTS])
async def test_universal_invariant(category_key: str, invariant: dict[str, Any]) -> None:
    ctx = build_controlled_context(CATEGORIES[category_key])
    reply = await generate_reply(ctx, invariant["stage"], invariant["message"])
    violated, reason = await judge(
        build_facts(ctx), invariant["message"], reply, invariant["judge"]
    )
    assert not violated, (
        f"[{category_key}/{invariant['id']}] invariant violated.\nREPLY: {reply!r}\nJUDGE: {reason}"
    )
