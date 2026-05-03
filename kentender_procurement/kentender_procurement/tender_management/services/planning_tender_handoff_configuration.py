# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Planning-to-tender handoff ``configuration_json`` (doc 2 sec. 14–15, Tracker B7).

Builds the initial STD configuration dict from:

1. **Safe defaults** from bundled ``fields.json`` only (sec. 15.3) — never ``sample_tender.json``.
2. **Inherited** package/plan values applied on ``Procurement Tender`` columns and merged via the
   officer registry overlay (sec. 14.1–14.2).
3. ``merge_officer_overlay_into_configuration`` — single coercion path for ``field_code`` keys.

Real package release must **not** silently hydrate from ``sample_tender.json`` (contrast officer POC
flows that call ``load_sample_tender`` in Desk/tests).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.model.document import Document
from frappe.utils import flt

from kentender_procurement.tender_management.services.officer_guided_field_registry import (
	load_raw_fields_document,
)
from kentender_procurement.tender_management.services.officer_tender_config import (
	merge_officer_overlay_into_configuration,
)


def load_plan_for_handoff(pkg: Document) -> Document | None:
	"""Read-only ``Procurement Plan`` for ``pkg.plan_id``, or ``None``."""
	pid = (pkg.get("plan_id") or "").strip()
	if not pid or not frappe.db.exists("Procurement Plan", pid):
		return None
	return frappe.get_doc("Procurement Plan", pid)


def procurement_category_code_from_template(template_id: str | None) -> str:
	"""Map planning ``Procurement Template.category`` to ``Procurement Tender.procurement_category``."""
	if not template_id:
		return "WORKS"
	raw = (frappe.db.get_value("Procurement Template", template_id, "category") or "").strip().upper()
	return {
		"WORKS": "WORKS",
		"GOODS": "GOODS",
		"SERVICES": "SERVICES",
		"CONSULTING": "CONSULTING",
		"DISPOSAL": "DISPOSAL",
	}.get(raw, "WORKS")


def _truthy_default(v: Any) -> bool:
	if isinstance(v, bool):
		return v
	if isinstance(v, str):
		return v.strip().lower() in ("1", "true", "yes", "y")
	return bool(v)


def collect_safe_std_field_defaults() -> dict[str, Any]:
	"""Conservative ``fields.json`` defaults only (sec. 15.3) — booleans, small ints, short SELECT."""
	out: dict[str, Any] = {}
	for row in load_raw_fields_document().get("fields") or []:
		if not row.get("ordinary_user_editable", True):
			continue
		fc = row.get("field_code")
		if not fc:
			continue
		dv = row.get("default_value")
		if dv is None:
			continue
		ft = str(row.get("field_type") or "")
		if ft == "LONG_TEXT":
			continue
		if ft == "TEXT" and isinstance(dv, str) and len(dv) > 120:
			continue
		if ft == "BOOLEAN":
			out[str(fc)] = _truthy_default(dv)
			continue
		if ft in ("INTEGER", "DURATION_DAYS", "DURATION_MONTHS"):
			try:
				iv = int(dv)
				if abs(iv) <= 10_000_000:
					out[str(fc)] = iv
			except (TypeError, ValueError):
				continue
			continue
		if ft in ("DECIMAL", "MONEY", "PERCENT"):
			try:
				fv = float(dv)
				if abs(fv) <= 1e12:
					out[str(fc)] = fv
			except (TypeError, ValueError):
				continue
			continue
		if ft == "SELECT" and isinstance(dv, str) and 0 < len(dv) <= 80:
			out[str(fc)] = dv
	return out


def build_inherited_handoff_config_overlay(pkg: Document, plan: Document | None) -> dict[str, Any]:
	"""Flat config keys from package/plan not covered by ``og_*`` columns (extensible; v1 often empty)."""
	overlay: dict[str, Any] = {}
	ev = flt(pkg.get("estimated_value"))
	if ev > 0:
		overlay["TENDER.ESTIMATED_COST"] = ev
	cur = (pkg.get("currency") or "").strip()
	if cur:
		overlay["SECURITY.TENDER_SECURITY_CURRENCY"] = cur
	if plan and (plan.get("procuring_entity") or "").strip():
		pe = plan.procuring_entity.strip()
		overlay["TENDER.PROCURING_ENTITY_REF"] = pe
		en = frappe.db.get_value("Procuring Entity", pe, "entity_name")
		if en:
			overlay["TENDER.PROCURING_ENTITY_NAME"] = str(en)
	return overlay


def apply_inherited_package_plan_to_tender(t: Any, pkg: Document, plan: Document | None) -> None:
	"""Set guided ``Procurement Tender`` columns from package/plan before configuration merge."""
	ev = flt(pkg.get("estimated_value"))
	if ev > 0:
		t.set("og_tender_estimated_cost", ev)
	cur = (pkg.get("currency") or "").strip()
	if cur:
		t.set("og_security_tender_security_currency", cur)
	if plan and (plan.get("procuring_entity") or "").strip():
		pe = plan.procuring_entity.strip()
		t.set("og_tender_procuring_entity_ref", pe)
		en = frappe.db.get_value("Procuring Entity", pe, "entity_name")
		if en:
			t.set("og_tender_procuring_entity_name", str(en))


def apply_handoff_posture_on_new_tender(t: Any) -> None:
	"""Sec. 15.5–15.6: validation not run; generated pack cleared (child tables start empty on insert)."""
	t.set("validation_status", "Not Validated")
	t.set("generated_tender_pack_html", "")


def build_handoff_configuration_json(t: Any, pkg: Document, plan: Document | None) -> str:
	"""Assemble ``configuration_json`` for a new tender from package handoff (never ``sample_tender``)."""
	base = collect_safe_std_field_defaults()
	base.update(build_inherited_handoff_config_overlay(pkg, plan))
	merged = merge_officer_overlay_into_configuration(base, t)
	return json.dumps(merged, ensure_ascii=False)
