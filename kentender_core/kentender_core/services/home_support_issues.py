"""HOME-CHG-001 v0.6 — a Technical Operator's support issues, as Home's technical work.

Support issues were on My Work for the people who hold the technical responsibility (EVL-CHG-001 v0.4 §6, §7.3 last row:
"it clears only on repair and successful reconciliation"). Retiring My Work (owner decision 5 Oct 2026, FU-HOME-46) must
not lose them, so Home carries them. A Technical Operator is a technical reader (HOME §6): no counts and no business
action, so this provider is registered on `kt_home_technical_providers`, the one hook a technical reader is read through,
and never on `kt_home_providers`. It gives My work rows only; the row names the issue's subject (a safe reference, never
business content) and opens the Support Issue record, whose own permission decides who may read it.
"""

from __future__ import annotations

from typing import Any

from kentender_core.services import home_entries as he
from kentender_core.services import support_issues

OWNER = "support"
ACTION = "Repair the failed operation"


def entries(*, user: str, region: str) -> list[dict[str, Any]] | None:
	"""My work for a holder of the technical responsibility; not applicable (None) to anyone else, and to every other region."""
	if region != he.MY_WORK or user not in support_issues.holders(support_issues.TECHNICAL_OPERATOR):
		return None
	return [
		he.make(
			region=he.MY_WORK, owner=OWNER, root=issue["issue_id"], action_id="resolve", title=issue["subject"], reference=issue["issue_id"],
			action=ACTION, destination=["Form", support_issues.ISSUE, issue["issue_id"]], entered_at=issue["opened_at"], entered_verb="Opened",
		)
		for issue in support_issues.for_holder(user)
	]
