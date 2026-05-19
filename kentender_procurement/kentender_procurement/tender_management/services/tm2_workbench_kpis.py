# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-04 / P9-05 — TM2 workbench KPI + **queue bar** counts (doc 9 §14.6–14.7, doc 6 §6–8).

Counts respect the **session user's** read permission on underlying DocTypes
(``frappe.get_list`` / ``frappe.get_all``).

``queue_counts`` keys are URL slugs (``?queue=std-incomplete``). Overlapping KPI/queue
buckets use the same filters so **STD Incomplete** stays aligned with
``tm2-kpi-std-incomplete`` / ``tm2-queue-std-incomplete`` (doc 7 §28.2).

Tests: ``tender_management.tests.test_p9_04_workbench_kpis``,
``tender_management.tests.test_p9_05_workbench_queue_bar``.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import add_to_date, now_datetime

_KPI_KEYS: tuple[str, ...] = (
	"tm2-kpi-draft",
	"tm2-kpi-std-incomplete",
	"tm2-kpi-publication-review",
	"tm2-kpi-published",
	"tm2-kpi-closing-soon",
	"tm2-kpi-clarifications",
	"tm2-kpi-addenda",
	"tm2-kpi-opening-ready",
)

_ACTIVE = {"is_active": 1}

_CLAR_PENDING = ("Submitted", "Under Review", "Response Drafted", "Pending Approval")

_QUEUE_SLUGS: tuple[str, ...] = (
	"draft",
	"std-incomplete",
	"ready-review",
	"returned",
	"approved",
	"published",
	"clarifications",
	"addenda",
	"closing-soon",
	"closed",
	"opening-ready",
	"evaluation-ready",
	"cancelled",
)


def _count_tenders(filters: dict[str, Any], *, active_only: bool = True) -> int:
	base: dict[str, Any] = dict(filters)
	if active_only:
		base = {**_ACTIVE, **base}
	names = frappe.get_list("TM2 Tender", filters=base, pluck="name", limit=10_000)
	return len(names or [])


def get_workbench_kpi_counts(_user: str | None = None) -> dict[str, Any]:
	"""Return KPI ``counts`` (§14.6) and ``queue_counts`` keyed by §14.7 URL slug."""
	# _user reserved for future impersonation tests; session user drives permissions.
	counts: dict[str, int] = {k: 0 for k in _KPI_KEYS}

	counts["tm2-kpi-draft"] = _count_tenders({"status": "Draft"})
	counts["tm2-kpi-std-incomplete"] = _count_tenders({"status": "STD Instance Incomplete"})
	counts["tm2-kpi-publication-review"] = _count_tenders({"status": "Ready for Publication Review"})
	counts["tm2-kpi-published"] = _count_tenders({"status": "Published"})
	counts["tm2-kpi-addenda"] = _count_tenders({"status": "Addendum Pending"})
	counts["tm2-kpi-opening-ready"] = _count_tenders({"status": "Opening Ready"})

	published_names = frappe.get_list(
		"TM2 Tender",
		filters={**_ACTIVE, "status": "Published"},
		pluck="name",
		limit=10_000,
	) or []
	now = now_datetime()
	soon = add_to_date(now, days=7, as_datetime=True)
	if published_names:
		tl_rows = frappe.get_all(
			"TM2 Tender Timeline",
			filters={
				"tm2_tender": ["in", published_names],
				"submission_deadline_at": ["between", [now, soon]],
			},
			pluck="tm2_tender",
			limit=10_000,
		)
		counts["tm2-kpi-closing-soon"] = len(set(tl_rows or []))

	clar_parents = frappe.get_list(
		"TM2 Clarification Request",
		filters={"status": ["in", list(_CLAR_PENDING)]},
		pluck="tm2_tender",
		limit=10_000,
	) or []
	counts["tm2-kpi-clarifications"] = len(set(clar_parents))

	queue_counts: dict[str, int] = {slug: 0 for slug in _QUEUE_SLUGS}
	queue_counts["draft"] = counts["tm2-kpi-draft"]
	queue_counts["std-incomplete"] = counts["tm2-kpi-std-incomplete"]
	queue_counts["ready-review"] = counts["tm2-kpi-publication-review"]
	queue_counts["published"] = counts["tm2-kpi-published"]
	queue_counts["clarifications"] = counts["tm2-kpi-clarifications"]
	queue_counts["addenda"] = counts["tm2-kpi-addenda"]
	queue_counts["closing-soon"] = counts["tm2-kpi-closing-soon"]
	queue_counts["opening-ready"] = counts["tm2-kpi-opening-ready"]
	queue_counts["returned"] = _count_tenders({"status": "Returned for Correction"})
	queue_counts["approved"] = _count_tenders({"status": "Approved for Publication"})
	queue_counts["evaluation-ready"] = _count_tenders({"status": "Evaluation Ready"})
	queue_counts["closed"] = _count_tenders(
		{"status": ["in", ["Closed", "Closed - No Valid Submissions"]]},
		active_only=False,
	)
	queue_counts["cancelled"] = _count_tenders({"status": "Cancelled"}, active_only=False)

	total_accessible = _count_tenders({})

	return {
		"ok": True,
		"counts": counts,
		"queue_counts": queue_counts,
		"total_accessible": total_accessible,
	}
