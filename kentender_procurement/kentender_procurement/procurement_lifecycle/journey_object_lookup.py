# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R1-009 / LV-R1-009-01 — object→journey lookup on **Procurement Journey** ref fields.

Navigation aggregate only (ADR-PLC-002). Source modules remain legal authority.

**Index / query strategy**

Each lookup is a single equality predicate on one **Data** ref column that is marked
``search_index`` on the DocType (Frappe emits a DB index suitable for point lookups).
Equivalent SQL::

    SELECT `name`
    FROM `tabProcurement Journey`
    WHERE `<ref_field>` = %s
    ORDER BY `modified` DESC
    LIMIT 2;

``LIMIT 2`` detects accidental duplicate bindings (same code on multiple journeys); the
first row wins deterministically for the return value — duplicates should be treated as
a data-quality issue in R3 aggregation.

For composite filters (e.g. procuring_entity_code + fiscal_year list APIs), use separate
predicates; pack §6.1 lists ``procuring_entity_code + fiscal_year`` as a reporting index
concern, not required for by-object resolution.

**API note** — cursor pack §9.2 ``get_procurement_journey_by_object`` returns a dict for
HTTP responses; this module returns a **minimal** row until R3 wires full aggregation.
"""

from __future__ import annotations

from typing import Final

import frappe

# Normalized object_type (casefold, stripped) → Procurement Journey Data field.
# Keys align with JOURNEY_STEP_CONFIG ``source_object_type`` / pack §9.2 examples where possible.
_OBJECT_TYPE_TO_REF_FIELD: Final[dict[str, str]] = {
	"strategic plan / programme / objective": "strategy_ref",
	"budget line": "budget_line_ref",
	"demand": "demand_ref",
	"procurement plan": "procurement_plan_ref",
	"procurement package": "procurement_package_ref",
	"std template version": "std_template_version_ref",
	"tender std instance": "tender_std_instance_ref",
	"tender std instance / binding": "tender_std_instance_ref",
	"tm2 tender": "tm2_tender_ref",
	"publication snapshot": "publication_snapshot_ref",
	"tm2 opening readiness record": "opening_readiness_ref",
	"opening readiness": "opening_readiness_ref",
}

JOURNEY_OBJECT_LOOKUP_REF_FIELDS: Final[frozenset[str]] = frozenset(_OBJECT_TYPE_TO_REF_FIELD.values())


def _normalize_object_type(object_type: str) -> str:
	return (object_type or "").strip().casefold()


def ref_field_for_object_type(object_type: str) -> str | None:
	"""Return ``Procurement Journey`` fieldname for ``object_type``, or ``None`` if unknown."""
	key = _normalize_object_type(object_type)
	return _OBJECT_TYPE_TO_REF_FIELD.get(key)


def journey_lookup_sql_explanation(object_type: str) -> str:
	"""Human-readable query plan note for reviewers / LV-R1-009-01 evidence."""
	field = ref_field_for_object_type(object_type)
	if not field:
		return (
			"No indexed ref column is mapped for this object_type; "
			"by-object lookup is not supported until mapping is extended."
		)
	return (
		"MySQL evaluates a point lookup on `tabProcurement Journey`: "
		f"WHERE `{field}` = %s ORDER BY `modified` DESC LIMIT 2. "
		f"When `{field}` is indexed (Frappe `search_index`), expect ref/range access on that column."
	)


def resolve_journey_code_for_object(object_type: str, object_code: str) -> str | None:
	"""Return ``journey_code`` (document name) for the first matching journey, or ``None``."""
	field = ref_field_for_object_type(object_type)
	code = (object_code or "").strip()
	if not field or not code:
		return None
	rows = frappe.get_all(
		"Procurement Journey",
		filters={field: code},
		pluck="name",
		order_by="modified desc",
		limit=2,
	)
	if not rows:
		return None
	return rows[0]


def get_procurement_journey_by_object(object_type: str, object_code: str) -> dict | None:
	"""Pack §9.2 — resolve object to journey; returns a minimal dict or ``None``."""
	journey_code = resolve_journey_code_for_object(object_type, object_code)
	if not journey_code:
		return None
	row = frappe.db.get_value(
		"Procurement Journey",
		journey_code,
		["journey_code", "journey_title", "procuring_entity_code", "fiscal_year"],
		as_dict=True,
	)
	return row
