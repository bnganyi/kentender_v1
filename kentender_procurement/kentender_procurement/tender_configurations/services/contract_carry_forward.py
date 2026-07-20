# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-09 → contract carry-forward bundle (PoC; no full award UI).

Payment milestone authority is CFG-09 / pack 06 (not CFG-02 narrative Phase 2 text).
"""

from __future__ import annotations

import json
import re
from typing import Any

import frappe
from frappe.utils import cstr


BUNDLE_CATEGORIES = (
	"payment",
	"performance_security",
	"warranty",
	"sla",
	"escrow",
	"subcontracting",
)


def _parse_blob(raw: Any) -> dict[str, Any]:
	if not raw:
		return {}
	if isinstance(raw, dict):
		return raw
	try:
		parsed = json.loads(raw)
		return parsed if isinstance(parsed, dict) else {}
	except (TypeError, ValueError):
		return {}


def _classify(label: str, obligation: str) -> str:
	text = f"{label} {obligation}".lower()
	if "payment" in text or "milestone" in text or "%" in text:
		return "payment"
	if "performance security" in text or "performance bond" in text:
		return "performance_security"
	if "warranty" in text:
		return "warranty"
	if "sla" in text or "service level" in text or "support" in text and "level" in text:
		return "sla"
	if "escrow" in text:
		return "escrow"
	if "subcontract" in text:
		return "subcontracting"
	if "security" in text and "performance" not in text:
		return "performance_security"
	return "other"


def build_carry_forward_bundle_from_contract_values(contract_blob: dict[str, Any]) -> dict[str, Any]:
	rows = contract_blob.get("contract_values") or []
	bucket: dict[str, list[dict[str, Any]]] = {k: [] for k in BUNDLE_CATEGORIES}
	bucket["other"] = []
	payment_total_pct = 0.0
	for row in rows:
		if not isinstance(row, dict):
			continue
		cid = cstr(row.get("contract_value_id") or "").strip()
		label = cstr(row.get("item_label") or "").strip()
		obligation = cstr(row.get("value_or_obligation") or row.get("source_value") or "").strip()
		# PAY-* rows are authoritative payment milestones (CFG-09 / pack 06)
		if cid.startswith("PAY-"):
			cat = "payment"
		else:
			cat = _classify(label, obligation)
			if cat == "payment":
				# Avoid double-counting SCC narrative payment text as milestones
				cat = "other"
		item = {
			"contract_value_id": cid,
			"item_label": label,
			"value_or_obligation": obligation,
			"category": cstr(row.get("category") or "").strip(),
			"contract_location": cstr(row.get("contract_location") or "").strip(),
		}
		bucket.setdefault(cat, []).append(item)
		if cid.startswith("PAY-"):
			m = re.search(r"(\d+(?:\.\d+)?)\s*%", obligation)
			if m:
				payment_total_pct += float(m.group(1))
	return {
		"categories": {k: bucket.get(k) or [] for k in BUNDLE_CATEGORIES},
		"payment_milestones": [i for i in (bucket.get("payment") or []) if cstr(i.get("contract_value_id")).startswith("PAY-")],
		"payment_percentage_total": payment_total_pct,
		"performance_security": bucket.get("performance_security") or [],
		"warranty": bucket.get("warranty") or [],
		"sla": bucket.get("sla") or [],
		"escrow": bucket.get("escrow") or [],
		"subcontracting": bucket.get("subcontracting") or [],
		"source": "CFG-09",
	}


def get_carry_forward_bundle(configuration_id: str) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="read"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	blob = _parse_blob(getattr(doc, "contract_values", None))
	bundle = build_carry_forward_bundle_from_contract_values(blob)
	bundle["configuration_id"] = doc.name
	bundle["configuration_ref"] = cstr(doc.configuration_ref or doc.name)
	bundle["std_version"] = cstr(doc.std_version or "")
	return bundle
