# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""GET helper for persisted electronic bidder submission schema (E1 Phase 1)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr


def _parse_schema(raw: Any) -> dict[str, Any]:
	if not raw:
		return {}
	if isinstance(raw, dict):
		return raw
	text = cstr(raw).strip()
	if not text:
		return {}
	try:
		parsed = json.loads(text)
	except (TypeError, ValueError):
		return {}
	return parsed if isinstance(parsed, dict) else {}


def get_bidder_submission_schema(configuration_id: str) -> dict[str, Any]:
	"""Return persisted schema 10 artifact for a tender configuration."""
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="read"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	schema = _parse_schema(getattr(doc, "bidder_submission_schema", None))
	return {
		"configuration_id": doc.name,
		"configuration_ref": cstr(doc.configuration_ref or doc.name),
		"has_schema": bool(schema),
		"schema": schema,
		"submission_policy": schema.get("submission_policy") if schema else {},
	}
