# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP3 workbench filter metadata (facets + counts)."""

from __future__ import annotations

from collections import Counter
from typing import Any

from frappe.utils import flt, getdate

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.services.workbench_item_view_model import (
	SUPPORTED_QUEUES,
	get_workbench_item_view_model,
)

_SORT_OPTIONS: tuple[dict[str, str], ...] = (
	{"id": "newest", "label": "Newest"},
	{"id": "oldest", "label": "Oldest"},
	{"id": "value_high_low", "label": "Value High-Low"},
	{"id": "value_low_high", "label": "Value Low-High"},
	{"id": "title_asc", "label": "Title A-Z"},
	{"id": "title_desc", "label": "Title Z-A"},
)


def _text(value: Any) -> str:
	return str(value or "").strip()


def _parse_date(value: Any):
	text = _text(value)
	if not text:
		return None
	try:
		return getdate(text)
	except Exception:
		return None


def _value_range_bucket(amount: Any) -> str:
	value = flt(amount or 0)
	if value < 100_000_000:
		return "under_kes_100m"
	if value <= 500_000_000:
		return "kes_100m_500m"
	return "over_kes_500m"


def get_workbench_filter_metadata(
	*,
	queue: str,
	actor: str | None = None,
	include_test_data: bool = False,
	search: str | None = None,
) -> dict[str, Any]:
	"""Return filter facets for one workbench queue within current scope."""
	queue_key = _text(queue)
	if queue_key not in SUPPORTED_QUEUES:
		return {
			"ok": False,
			"error_code": "PP_INVALID_QUEUE",
			"message": f"Unsupported workbench queue: {queue_key}",
			"queue": queue_key,
			"role_key": resolve_pp_role_key(actor or "") or "auditor",
			"total": 0,
			"facets": {},
		}

	user = _text(actor)
	role_key = resolve_pp_role_key(user) or "auditor"
	out = get_workbench_item_view_model(
		queue=queue_key,
		actor=user or None,
		start=0,
		limit=1000,
		include_test_data=include_test_data,
		search=search,
	)
	if not out.get("ok"):
		return {
			"ok": False,
			"error_code": out.get("error_code") or "PP_QUEUE_ERROR",
			"message": out.get("message") or "Unable to load queue metadata.",
			"queue": queue_key,
			"role_key": out.get("role_key") or role_key,
			"total": 0,
			"facets": {},
		}

	items = out.get("items") or []
	dept_counts = Counter()
	category_counts = Counter()
	range_counts = Counter()
	dates = []
	for item in items:
		dept = _text(item.get("department_label"))
		if dept:
			dept_counts[dept] += 1
		category = _text(item.get("category_label"))
		if category:
			category_counts[category] += 1
		range_counts[_value_range_bucket(item.get("estimated_value_number"))] += 1
		if (d := _parse_date(item.get("created_on"))):
			dates.append(d)

	date_bounds = {
		"min": dates and str(min(dates)) or None,
		"max": dates and str(max(dates)) or None,
	}

	return {
		"ok": True,
		"queue": queue_key,
		"role_key": out.get("role_key") or role_key,
		"total": int(out.get("total") or len(items)),
		"facets": {
			"departments": [
				{"id": name, "label": name, "count": count}
				for name, count in sorted(dept_counts.items(), key=lambda row: row[0].lower())
			],
			"categories": [
				{"id": name, "label": name, "count": count}
				for name, count in sorted(category_counts.items(), key=lambda row: row[0].lower())
			],
			"value_ranges": [
				{
					"id": "under_kes_100m",
					"label": "Under KES 100M",
					"count": int(range_counts.get("under_kes_100m") or 0),
				},
				{
					"id": "kes_100m_500m",
					"label": "KES 100M - 500M",
					"count": int(range_counts.get("kes_100m_500m") or 0),
				},
				{
					"id": "over_kes_500m",
					"label": "Over KES 500M",
					"count": int(range_counts.get("over_kes_500m") or 0),
				},
			],
			"created_date_bounds": date_bounds,
			"sort_options": list(_SORT_OPTIONS),
		},
	}
