# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Open or return the single open Draft successor revision."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr

from kentender_procurement.procurement_planning.mvp1_constants import (
	ITEM_ACTIVE,
	ITEM_PROPOSED,
	VALIDATION_NOT_RUN,
	VERSION_APPROVED,
	VERSION_DRAFT,
)
from kentender_procurement.procurement_planning.services._invariants import (
	new_concurrency_token,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	assert_planning_actor,
	assert_planning_scope,
)


def open_or_create_plan_revision(
	*,
	plan: str,
	version_reason: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	actor = assert_planning_actor(user)
	plan_name = cstr(plan).strip()
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		frappe.throw(_("Procurement Plan not found."), title="PLN_PLAN_NOT_FOUND")

	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	assert_planning_scope(
		procuring_entity=cstr(plan_doc.procuring_entity).strip(),
		user=actor,
		require_write=False,
	)
	if plan_doc.lifecycle_state != "Open":
		frappe.throw(
			_("Closed or Cancelled plans do not accept new revisions."),
			title="PLN_PLAN_NOT_OPEN",
		)

	existing = cstr(plan_doc.open_draft_version or "").strip()
	if existing and frappe.db.exists("Procurement Plan Version", existing):
		ver = frappe.get_doc("Procurement Plan Version", existing)
		if ver.status == VERSION_DRAFT:
			return {
				"ok": True,
				"created": False,
				"plan": plan_name,
				"version": ver.name,
				"version_code": ver.version_code,
				"version_number": ver.version_number,
				"actor": actor,
			}

	approved = cstr(plan_doc.current_approved_version or "").strip()
	if not approved:
		frappe.throw(
			_("Approve the initial Draft before opening a successor revision."),
			title="PLN_NO_APPROVED_VERSION",
		)
	src = frappe.get_doc("Procurement Plan Version", approved)
	if src.status != VERSION_APPROVED:
		frappe.throw(_("Current approved version is invalid."), title="PLN_APPROVED_INVALID")

	next_num = int(src.version_number or 0) + 1
	version_code = f"{plan_doc.plan_code}-V{next_num}"
	draft = frappe.get_doc(
		{
			"doctype": "Procurement Plan Version",
			"plan": plan_name,
			"version_number": next_num,
			"version_code": version_code,
			"status": VERSION_DRAFT,
			"open_version_slot": plan_name,
			"version_reason": cstr(version_reason or "Post-approval revision"),
			"source_version": src.name,
			"validation_projection": VALIDATION_NOT_RUN,
			"concurrency_token": new_concurrency_token(),
		}
	)
	draft.insert(ignore_permissions=True)

	# Carry forward Active items with unchanged item versions
	items = frappe.get_all(
		"Procurement Plan Item",
		filters={"plan": plan_name, "baseline_state": ITEM_ACTIVE},
		fields=["name", "plan_item_code", "current_approved_item_version"],
	)
	for row in items:
		src_iv = row.current_approved_item_version
		if not src_iv:
			continue
		src_iv_doc = frappe.get_doc("Procurement Plan Item Version", src_iv)
		iv_code = f"{row.plan_item_code}-{next_num}"
		new_iv = frappe.get_doc(
			{
				"doctype": "Procurement Plan Item Version",
				"plan_item": row.name,
				"plan_version": draft.name,
				"item_version_code": iv_code,
				"source_item_version": src_iv,
				"carry_forward_unchanged": 1,
				"requirement_title": src_iv_doc.requirement_title,
				"requirement_description": src_iv_doc.requirement_description,
				"confirmed_estimate": src_iv_doc.confirmed_estimate,
				"currency": src_iv_doc.currency,
				"procurement_category": src_iv_doc.procurement_category,
				"procurement_method": src_iv_doc.procurement_method,
				"method_basis": src_iv_doc.method_basis,
				"governing_regime": src_iv_doc.governing_regime,
				"recommended_method": src_iv_doc.recommended_method,
				"arrangement": src_iv_doc.arrangement,
				"lotting_decision": src_iv_doc.lotting_decision,
				"expected_lot_count": src_iv_doc.expected_lot_count,
				"lot_basis": src_iv_doc.lot_basis,
				"ms_invitation_published": src_iv_doc.ms_invitation_published,
				"ms_tender_opening": src_iv_doc.ms_tender_opening,
				"ms_evaluation_completed": src_iv_doc.ms_evaluation_completed,
				"ms_award_approval": src_iv_doc.ms_award_approval,
				"ms_notification_of_award": src_iv_doc.ms_notification_of_award,
				"ms_contract_signature": src_iv_doc.ms_contract_signature,
				"ms_delivery_completion": src_iv_doc.ms_delivery_completion,
				"reservation_reference": src_iv_doc.reservation_reference,
				"finance_status": src_iv_doc.finance_status,
				"finance_snapshot_amount": src_iv_doc.finance_snapshot_amount,
				"finance_snapshot_budget_line": src_iv_doc.finance_snapshot_budget_line,
				"finance_confirmed_at": src_iv_doc.finance_confirmed_at,
				"finance_confirmed_by": src_iv_doc.finance_confirmed_by,
				"finance_reservation": src_iv_doc.finance_reservation,
				"finance_owned_reservation": src_iv_doc.finance_owned_reservation,
				"strategy_snapshot": src_iv_doc.strategy_snapshot,
				"pvc_snapshot": src_iv_doc.pvc_snapshot,
				"validation_projection": src_iv_doc.validation_projection or VALIDATION_NOT_RUN,
			}
		)
		new_iv.insert(ignore_permissions=True)
		frappe.db.set_value(
			"Procurement Plan Item",
			row.name,
			{"draft_item_version": new_iv.name, "baseline_state": ITEM_ACTIVE},
			update_modified=False,
		)

	frappe.db.set_value(
		"Procurement Plan",
		plan_name,
		{"open_draft_version": draft.name},
		update_modified=False,
	)

	return {
		"ok": True,
		"created": True,
		"plan": plan_name,
		"version": draft.name,
		"version_code": version_code,
		"version_number": next_num,
		"actor": actor,
	}
