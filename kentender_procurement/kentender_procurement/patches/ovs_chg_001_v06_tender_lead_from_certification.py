# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Set each Tender's lead department to the certified lead of the Requisition
Version it consumed (OVS-CHG-001 v0.6 §4.1; plan D15; owner approval 4 Oct
2026, "OVS6-0311:  Yes").

Until 4 October 2026 a Tender took the alphabetically first of its
contributing units as its lead, because the handoff lists contributors in
sorted order and the Requisition field the code read does not exist on the
doctype. The certified lead is carried in the handoff payload
(`departmental_certification.lead_org_unit_id`). This patch corrects a Tender
whose stored lead differs from it. It reads only the immutable handoff, writes
only `lead_org_unit`, leaves the modified timestamp alone, and is safe to run
again."""

from __future__ import annotations

import json

import frappe


def reconcile() -> list[dict[str, str]]:
	"""Correct every Tender whose lead is not the certified lead; return what changed."""
	changed = []
	for t in frappe.get_all("Tender", fields=["name", "tender_reference", "requisition_handoff", "lead_org_unit"]):
		if not t.requisition_handoff:
			continue
		payload = json.loads(frappe.db.get_value("Authorised Requisition Handoff", t.requisition_handoff, "payload_json") or "{}")
		certified = (payload.get("departmental_certification") or {}).get("lead_org_unit_id")
		if certified and certified != t.lead_org_unit and frappe.db.exists("Organisation Unit", certified):
			frappe.db.set_value("Tender", t.name, "lead_org_unit", certified, update_modified=False)
			changed.append({"tender": t.tender_reference, "was": t.lead_org_unit or "", "now": certified})
	return changed


def execute():
	if not frappe.db.exists("DocType", "Tender") or not frappe.db.exists("DocType", "Authorised Requisition Handoff"):
		return
	changed = reconcile()
	frappe.db.commit()
	if changed:
		print("Tender lead department corrected: " + "; ".join(f"{c['tender']} {c['was'] or 'none'} -> {c['now']}" for c in changed))
