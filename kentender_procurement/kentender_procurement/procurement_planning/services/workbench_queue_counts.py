# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP3 workbench queue tab counts."""

from __future__ import annotations

from typing import Any

from frappe.utils import cint

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.services.workbench_item_view_model import (
	SUPPORTED_QUEUES,
	get_workbench_item_view_model,
)

_UI_QUEUE_BY_API_QUEUE = {
	"needs_planning": "needs_planning",
	"draft_packages": "draft_packages",
	"needs_review": "needs_review",
	"ready_release": "ready_to_release",
	"blocked": "blocked",
	"recently_released": "recently_released",
}


def get_workbench_queue_counts(
	*,
	actor: str | None = None,
	include_test_data: bool = False,
) -> dict[str, Any]:
	"""Return per-queue totals for PP3 workbench tabs."""
	user = (actor or "").strip()
	role_key = resolve_pp_role_key(user) or "auditor"
	counts: dict[str, int] = {}
	for queue in sorted(SUPPORTED_QUEUES):
		out = get_workbench_item_view_model(
			queue=queue,
			actor=user or None,
			limit=1,
			start=0,
			include_test_data=include_test_data,
		)
		ui_key = _UI_QUEUE_BY_API_QUEUE.get(queue, queue)
		counts[ui_key] = cint(out.get("total") or 0) if out.get("ok") else 0
	return {
		"ok": True,
		"role_key": role_key,
		"counts": counts,
	}
