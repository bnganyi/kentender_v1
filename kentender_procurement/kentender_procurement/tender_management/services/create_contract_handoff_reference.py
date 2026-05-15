# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §12.4 — ``create_contract_handoff_reference`` / ``createContractHandoffReference``.

Preconditions:

1. **TM2 Tender** status **Awarded**;
2. **TM2 Evaluation Handoff Record** exists (evaluation handoff gate);
3. ``award_decision_code`` is non-empty and matches ``context["award"]["award_decision_code"]``;
4. ``context["award"]`` supplies **Award** facts until a formal Award DocType exists: ``awarded_supplier``,
   ``final_evaluated_price``, ``currency``, ``final_boq_reference`` (Works — TM2-CHR-003);
5. **DCM** exists (consumable current output) and aligns with **publication snapshot V2** (binding + live
   output vs :func:`get_tender_std_output_refs`);
6. Corrected evaluated price must **not** be the pack forbidden uncorrected Works total **96,750,000** KES
   (:func:`AUTH_CONTRACT_PRICE_SOURCE_INVALID`);
7. :func:`~kentender_procurement.tender_management.security.action_availability.service.get_action_availability`
   for **CON2_CREATE_CONTRACT_HANDOFF**.

On success:

1. Insert **TM2 Contract Handoff Reference** (``CHR-{tender_code}``) with DCM ref, award metadata, refs-only
   ``addendum_history_refs`` and ``contract_handoff_payload`` (no ad-hoc contract term injection — TM2-CHR-004);
2. Set tender **Contract Handoff Completed**;
3. Audit **Contract Handoff Reference Created**.

Tests: ``tender_management.tests.test_p7_04_create_contract_handoff_reference``;
``tender_management.tests.test_o11_tm2_smoke_con_003_contract_price_must_use_corrected_evaluated_boq_total`` (O-11 / doc 8 TM2-SMOKE-CON-003);
``tender_management.tests.test_p9_18_contract_handoff_tab`` (``test_EX_10_*`` / doc 9 §25 **EX-10**).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, flt, now_datetime

from kentender_procurement.tender_management.security.action_availability.service import (
	get_action_availability,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
	is_known_denial_code,
)
from kentender_procurement.tender_management.services.append_tender_audit_event import (
	append_tender_audit_event,
)
from kentender_procurement.tender_management.services.tm2_std_adapter import (
	get_current_dcm,
	get_tender_std_output_refs,
)

_ACTION = "CON2_CREATE_CONTRACT_HANDOFF"
_OBJECT_TYPE = "TM2 Tender"

# Doc 9 §12.4 / doc 8 — uncorrected submitted-total probe (must deny).
_FORBIDDEN_UNCORRECTED_WORKS_TOTAL_KES = 96_750_000


def _deny(denial_code: str, message: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
	out: dict[str, Any] = {"ok": False, "denial_code": denial_code, "message": message}
	if extra:
		out.update(extra)
	return out


def _map_auth_denial(denial_code: str) -> str:
	if denial_code == DenialCode.STD_AUTH_PERMISSION_DENIED.value:
		return DenialCode.AUTH_ROLE_DENIED.value
	return denial_code


def _resolve_tm2(tender_code: str) -> Document | None:
	tc = (tender_code or "").strip()
	if not tc:
		return None
	name = frappe.db.get_value("TM2 Tender", {"tender_code": tc}, "name")
	if name and frappe.db.exists("TM2 Tender", name):
		return frappe.get_doc("TM2 Tender", name)
	if frappe.db.exists("TM2 Tender", tc):
		return frappe.get_doc("TM2 Tender", tc)
	return None


def _active_binding_row(tm2_name: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"TM2 Tender STD Binding",
		filters={
			"tm2_tender": tm2_name,
			"is_active": 1,
			"binding_status": ["not in", ["Cancelled", "Superseded"]],
		},
		fields=[
			"name",
			"tender_std_instance",
			"publication_snapshot_code",
			"dcm_output_code",
		],
		limit=1,
	)
	return dict(rows[0]) if rows else None


def _issued_addendum_codes(tm2_name: str) -> list[str]:
	out: list[str] = []
	for row in frappe.get_all(
		"TM2 Addendum",
		filters={"tm2_tender": tm2_name, "status": "Issued"},
		fields=["name", "addendum_code"],
		order_by="creation asc",
	):
		code = cstr(row.get("addendum_code") or row.get("name") or "").strip()
		if code:
			out.append(code)
	return sorted(set(out))


def create_contract_handoff_reference(
	actor: str,
	tender_code: str,
	award_decision_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""§12.4 — create **TM2 Contract Handoff Reference** after award, using STD **DCM** + corrected price."""
	ctx = dict(context or {})
	tm2 = _resolve_tm2(tender_code)
	if not tm2:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Tender {0} was not found.").format(cstr(tender_code).strip()),
		)

	tc = cstr(tm2.tender_code).strip() or tm2.name
	st = cstr(tm2.status).strip()

	if frappe.db.exists("TM2 Contract Handoff Reference", {"tm2_tender": tm2.name}):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("A contract handoff reference already exists for this tender."),
		)

	if st != "Awarded":
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Contract handoff requires the tender to be in Awarded state."),
			extra={"tender_status": st},
		)

	if not frappe.db.exists("TM2 Evaluation Handoff Record", {"tm2_tender": tm2.name}):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("TM2 Evaluation Handoff Record is required before contract handoff."),
		)

	ac_param = cstr(award_decision_code or "").strip()
	if not ac_param:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Award decision code is required."),
		)

	aw = ctx.get("award")
	if not isinstance(aw, dict):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Award details are required in context under key \"award\"."),
		)
	ac_ctx = cstr(aw.get("award_decision_code") or "").strip()
	if not ac_ctx or ac_ctx != ac_param:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Award decision code must match the award payload."),
			extra={"award_decision_code": ac_param, "award_payload_code": ac_ctx},
		)

	supplier = cstr(aw.get("awarded_supplier") or "").strip()
	if not supplier or not frappe.db.exists("Supplier", supplier):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Awarded supplier is missing or does not exist."),
		)

	currency = cstr(aw.get("currency") or "").strip() or cstr(tm2.currency or "").strip() or "KES"
	price_raw = aw.get("final_evaluated_price")
	price_f = flt(price_raw)
	price_i = int(price_f) if price_f else 0

	if int(price_i) == _FORBIDDEN_UNCORRECTED_WORKS_TOTAL_KES:
		return _deny(
			DenialCode.AUTH_CONTRACT_PRICE_SOURCE_INVALID.value,
			_("This price matches the forbidden uncorrected Works total; use the corrected evaluated BOQ total."),
			extra={"final_evaluated_price": price_i},
		)

	proc_cat = cstr(frappe.db.get_value("TM2 Tender", tm2.name, "procurement_category") or "").strip()
	boq_ref = cstr(aw.get("final_boq_reference") or "").strip()
	if proc_cat == "Works":
		if price_i <= 0:
			return _deny(
				DenialCode.AUTH_CONTEXT_DENIED.value,
				_("Final evaluated price must be positive for Works tenders."),
			)
		if not boq_ref:
			return _deny(
				DenialCode.AUTH_CONTEXT_DENIED.value,
				_("Final BOQ reference is required for Works tenders."),
			)

	bind = _active_binding_row(tm2.name)
	if not bind or not cstr(bind.get("tender_std_instance")).strip():
		return _deny(
			DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value,
			_("No active TM2 Tender STD Binding with a Tender STD Instance."),
		)
	si = cstr(bind["tender_std_instance"]).strip()

	refs = get_tender_std_output_refs(tc)
	if not refs.get("ok"):
		dc = cstr(refs.get("denial_code") or DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value).strip()
		if not dc or not is_known_denial_code(dc):
			dc = DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value
		return _deny(
			dc,
			str(refs.get("message") or _("Publication snapshot could not be resolved.")),
			extra={"snapshot": {k: refs.get(k) for k in ("denial_code", "message", "missing_fields") if k in refs}},
		)

	bind_pub = cstr(bind.get("publication_snapshot_code") or "").strip()
	snap_pub = cstr(refs.get("publication_snapshot_code") or "").strip()
	if not bind_pub:
		return _deny(
			DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value,
			_("Active binding is missing a publication snapshot reference."),
		)
	if bind_pub != snap_pub:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Active binding publication snapshot does not match the current STD publication snapshot."),
			extra={"binding_publication_snapshot_code": bind_pub, "resolved_publication_snapshot_code": snap_pub},
		)

	ref_dcm = cstr(refs.get("dcm_output_code") or "").strip()
	bind_dcm = cstr(bind.get("dcm_output_code") or "").strip()
	if bind_dcm and ref_dcm and bind_dcm != ref_dcm:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("DCM output on the binding does not match the publication snapshot."),
		)

	dcm_live = get_current_dcm(si)
	if not dcm_live.get("ok"):
		return _deny(
			DenialCode.AUTH_DCM_MISSING_OR_STALE.value,
			str(dcm_live.get("message") or _("DCM is missing or not consumable.")),
			extra={"dcm_resolution": dcm_live},
		)
	dcm_code = cstr(dcm_live.get("output_code") or "").strip()
	if not dcm_code or dcm_code != ref_dcm:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("DCM output does not match the publication snapshot binding."),
			extra={"dcm_output_code": dcm_code, "snapshot_dcm_output_code": ref_dcm},
		)

	addendum_codes = _issued_addendum_codes(tm2.name)
	addendum_refs: dict[str, list[str]] | None = {"refs": addendum_codes} if addendum_codes else None

	avail = get_action_availability(
		_ACTION,
		_OBJECT_TYPE,
		tc,
		actor,
		context={**ctx, "object_exists": True},
	)
	if not avail.get("allowed"):
		dc = _map_auth_denial(str(avail.get("denial_code") or ""))
		return _deny(
			dc,
			str(avail.get("user_message") or avail.get("message") or dc),
			extra={"availability": avail},
		)

	now = now_datetime()
	handoff_payload: dict[str, Any] = {
		"tender_code": tc,
		"publication_snapshot_code": snap_pub,
		"snapshot_hash": cstr(refs.get("snapshot_hash") or ""),
		"award_decision_code": ac_param,
		"dcm_output_code": dcm_code,
		"awarded_supplier": supplier,
		"final_evaluated_price": price_i if proc_cat == "Works" else price_f,
		"currency": currency,
		"final_boq_reference": boq_ref,
		"addendum_history_count": len(addendum_codes),
		"procurement_category": proc_cat,
	}

	chr_fields: dict[str, Any] = {
		"doctype": "TM2 Contract Handoff Reference",
		"tm2_tender": tm2.name,
		"tender_code": tc,
		"award_decision_code": ac_param,
		"awarded_supplier": supplier,
		"dcm_output_code": dcm_code,
		"tender_std_instance_code": si,
		"currency": currency,
		"addendum_history_refs": addendum_refs,
		"contract_handoff_payload": handoff_payload,
		"handoff_status": "Ready",
		"created_by": actor,
		"created_at": now,
	}
	if proc_cat == "Works":
		chr_fields["final_evaluated_price"] = price_f
		chr_fields["final_boq_reference"] = boq_ref
	else:
		chr_fields["final_evaluated_price"] = flt(price_raw or 0)
		chr_fields["final_boq_reference"] = None

	chr_row = frappe.get_doc(chr_fields)
	chr_row.insert(ignore_permissions=True)
	chr_row.reload()

	frappe.db.set_value("TM2 Tender", tm2.name, {"status": "Contract Handoff Completed"}, update_modified=True)

	audit_payload = {
		"tender_code": tc,
		"contract_handoff_code": chr_row.contract_handoff_code,
		"tm2_contract_handoff_reference": chr_row.name,
		"award_decision_code": ac_param,
		"dcm_output_code": dcm_code,
		"publication_snapshot_code": snap_pub,
		"awarded_supplier": supplier,
		"final_evaluated_price": price_i if proc_cat == "Works" else price_f,
		"currency": currency,
		"tender_std_instance_code": si,
	}
	append_tender_audit_event(
		tc,
		"Contract Handoff Reference Created",
		actor,
		audit_payload,
		related_object_type="TM2 Contract Handoff Reference",
		related_object_code=chr_row.name,
		previous_state="Awarded",
		new_state="Contract Handoff Completed",
		enforce_section_13_2=False,
	)

	return {
		"ok": True,
		"actor": actor,
		"tender_code": tc,
		"tm2_tender": tm2.name,
		"tender_status": "Contract Handoff Completed",
		"tm2_contract_handoff_reference": chr_row.name,
		"contract_handoff_code": chr_row.contract_handoff_code,
		"dcm_output_code": dcm_code,
		"publication_snapshot_code": snap_pub,
		"award_decision_code": ac_param,
		"contract_handoff_payload": handoff_payload,
	}


def createContractHandoffReference(
	actor: str,
	tender_code: str,
	award_decision_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`create_contract_handoff_reference`."""
	return create_contract_handoff_reference(actor, tender_code, award_decision_code, context=context)
