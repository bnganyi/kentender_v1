# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-014 — immutable Planning Handoff Snapshot (no TM2 Tender create)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, now_datetime

from kentender_procurement.procurement_planning.mvp1_constants import (
	ALLOC_EFFECTIVE,
	DOCTYPE_HANDOFF,
	FINANCE_CONFIRMED,
	ITEM_ACTIVE,
)
from kentender_procurement.procurement_planning.services.plan_item_finance import (
	effective_finance_status,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	CAP_PLAN_HANDOFF,
	require_capability,
)


def _existing_handoff(plan_item: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		DOCTYPE_HANDOFF,
		filters={"plan_item": plan_item},
		fields=["name", "handoff_code", "tender_reference", "plan", "plan_version"],
		limit=1,
	)
	return rows[0] if rows else None


def create_planning_handoff_snapshot(
	*,
	plan_item: str,
	tender_reference: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	if not actor or actor == "Guest":
		return {"ok": False, "errors": {"form": "Login required."}}

	item_name = cstr(plan_item).strip()
	if not item_name or not frappe.db.exists("Procurement Plan Item", item_name):
		return {"ok": False, "errors": {"form": "Plan Item not found."}}

	item = frappe.get_doc("Procurement Plan Item", item_name)
	plan_name = cstr(item.plan)
	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	pe = cstr(plan_doc.procuring_entity).strip()
	ou = cstr(plan_doc.coordinating_org_unit or "").strip() or None
	try:
		require_capability(
			CAP_PLAN_HANDOFF,
			procuring_entity=pe,
			org_unit=ou,
			user=actor,
			require_write=True,
		)
	except frappe.PermissionError as exc:
		return {
			"ok": False,
			"errors": {"form": str(exc).split(":", 1)[-1].strip() or "Not permitted"},
		}

	existing = _existing_handoff(item_name)
	if existing:
		return {
			"ok": True,
			"idempotent": True,
			"handoff": existing.name,
			"handoff_code": existing.handoff_code,
			"tender_reference": cstr(existing.tender_reference or ""),
			"plan": existing.plan,
			"plan_version": existing.plan_version,
			"plan_item": item_name,
		}

	if cstr(item.baseline_state) != ITEM_ACTIVE:
		return {
			"ok": False,
			"errors": {"form": "Only Active Approved Plan Items can be handed off."},
		}

	approved = cstr(plan_doc.current_approved_version or "").strip()
	if not approved:
		return {
			"ok": False,
			"errors": {"form": "Handoff requires a current Approved Version."},
		}

	iv_name = cstr(item.current_approved_item_version or "").strip()
	if not iv_name:
		iv_name = cstr(
			frappe.db.get_value(
				"Procurement Plan Item Version",
				{"plan_item": item_name, "plan_version": approved},
				"name",
			)
			or ""
		)
	if not iv_name:
		return {"ok": False, "errors": {"form": "Approved Plan Item Version not found."}}

	iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
	if effective_finance_status(iv) != FINANCE_CONFIRMED:
		return {
			"ok": False,
			"errors": {"form": "Handoff requires confirmed funding on the Approved item."},
		}

	allocs = frappe.get_all(
		"Plan Demand Allocation",
		filters={"plan_item": item_name, "status": ALLOC_EFFECTIVE},
		fields=["demand", "demand_item", "allocated_amount", "status"],
		order_by="creation asc",
	)
	if not allocs:
		allocs = frappe.get_all(
			"Plan Demand Allocation",
			filters={"plan_item": item_name},
			fields=["demand", "demand_item", "allocated_amount", "status"],
			order_by="creation asc",
		)

	tender_ref = cstr(tender_reference or "").strip()
	rsv_name = cstr(
		getattr(iv, "finance_reservation", None)
		or getattr(iv, "reservation_reference", None)
		or ""
	).strip()
	rsv_code = ""
	if rsv_name and frappe.db.exists("Funding Reservation", rsv_name):
		rsv_code = cstr(
			frappe.db.get_value("Funding Reservation", rsv_name, "generated_reference")
			or rsv_name
		)
	elif rsv_name:
		rsv_code = rsv_name
	version_code = cstr(
		frappe.db.get_value("Procurement Plan Version", approved, "version_code") or ""
	)
	payload = {
		"plan": plan_name,
		"plan_code": plan_doc.plan_code,
		"plan_version": approved,
		"plan_version_code": version_code,
		"plan_item": item_name,
		"plan_item_code": item.plan_item_code,
		"requirement_title": cstr(iv.requirement_title or ""),
		"owner_org_unit": cstr(item.owner_org_unit or ""),
		"confirmed_estimate": flt(iv.confirmed_estimate),
		"currency": plan_doc.currency or "KES",
		"finance_status": FINANCE_CONFIRMED,
		"finance": {
			"status": FINANCE_CONFIRMED,
			"reservation_id": rsv_name,
			"reservation_code": rsv_code,
			"confirmed_by": cstr(iv.finance_confirmed_by or ""),
		},
		"strategy_snapshot": cstr(iv.strategy_snapshot or ""),
		"pvc_snapshot": cstr(iv.pvc_snapshot or ""),
		"demand_allocations": [
			{
				"demand": cstr(a.demand),
				"demand_code": cstr(
					frappe.db.get_value("Demand", a.demand, "demand_code") or ""
				),
				"demand_item": cstr(a.demand_item or ""),
				"allocated_amount": flt(a.allocated_amount),
				"status": cstr(a.status),
			}
			for a in allocs
		],
		"tender_reference": tender_ref,
	}
	blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
	digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
	code = f"HO-{cstr(item.plan_item_code)}-{digest[:8].upper()}"

	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE_HANDOFF,
			"plan": plan_name,
			"plan_version": approved,
			"plan_item": item_name,
			"handoff_code": code,
			"snapshot_json": blob,
			"snapshot_hash": digest,
			"tender_reference": tender_ref,
			"created_by_user": actor,
			"handed_off_at": now_datetime(),
		}
	)
	doc.insert(ignore_permissions=True)
	return {
		"ok": True,
		"idempotent": False,
		"handoff": doc.name,
		"handoff_code": doc.handoff_code,
		"tender_reference": tender_ref,
		"plan": plan_name,
		"plan_version": approved,
		"plan_item": item_name,
		"snapshot_hash": digest,
	}
