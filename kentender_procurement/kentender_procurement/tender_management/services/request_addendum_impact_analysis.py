# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §10.4 — request STD **addendum impact analysis** (TM2 orchestration).

1. :func:`get_action_availability` for ``ADD2_REQUEST_IMPACT_ANALYSIS``;
2. :func:`~kentender_procurement.tender_management.services.tm2_std_adapter.analyze_addendum_impact`;
3. insert **TM2 Addendum Impact Record** (``AIR-{addendum_code}``) with previous/revised output refs from the adapter;
4. set **TM2 Addendum** ``status`` → **Impact Analysis Complete**;
5. audit **Addendum Impact Analysis Completed**.

``context`` may include ``proposed_changes`` (passed through to the adapter as the second argument).

Preconditions: **TM2 Addendum** exists; ``status`` is **Draft**; no **TM2 Addendum Impact Record** yet for that addendum.

Tests: ``tender_management.tests.test_p5_04_request_addendum_impact_analysis``.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr

from kentender_procurement.tender_management.security.action_availability.service import (
	get_action_availability,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.append_tender_audit_event import (
	append_tender_audit_event,
)
from kentender_procurement.tender_management.services.tm2_std_adapter import analyze_addendum_impact

_ACTION = "ADD2_REQUEST_IMPACT_ANALYSIS"
_OBJECT_TYPE = "TM2 Tender"


def _deny(denial_code: str, message: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
	out: dict[str, Any] = {"ok": False, "denial_code": denial_code, "message": message}
	if extra:
		out.update(extra)
	return out


def _map_auth_denial(denial_code: str) -> str:
	if denial_code == DenialCode.STD_AUTH_PERMISSION_DENIED.value:
		return DenialCode.AUTH_ROLE_DENIED.value
	return denial_code


def _resolve_addendum(addendum_code: str) -> Document | None:
	ac = (addendum_code or "").strip()
	if not ac:
		return None
	name = frappe.db.get_value("TM2 Addendum", {"addendum_code": ac}, "name")
	if name and frappe.db.exists("TM2 Addendum", name):
		return frappe.get_doc("TM2 Addendum", name)
	if frappe.db.exists("TM2 Addendum", ac):
		return frappe.get_doc("TM2 Addendum", ac)
	return None


def _safe_impact_payload(analysis: dict[str, Any]) -> dict[str, Any]:
	out: dict[str, Any] = {}
	for k, v in analysis.items():
		if isinstance(v, (str, int, float, bool)) or v is None:
			out[k] = v
		elif isinstance(v, dict):
			out[k] = v
		elif isinstance(v, (list, tuple)):
			out[k] = [x for x in v]
	return out


def _deadline_extension_flag(add: Document, analysis: dict[str, Any]) -> int:
	pit = cstr(add.get("primary_impact_type") or "").strip()
	if pit == "Deadline Change":
		return 1
	for ct in analysis.get("change_types") or []:
		if "DEADLINE" in cstr(ct).upper():
			return 1
	return 0


def _bid_resubmission_flag(analysis: dict[str, Any]) -> int:
	for o in analysis.get("affected_outputs") or []:
		if cstr(o).strip() == "DSM":
			return 1
	return 0


def request_addendum_impact_analysis(
	actor: str,
	addendum_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 9 §10.4 — adapter impact analysis + **TM2 Addendum Impact Record** + addendum status update."""
	ctx = dict(context or {})

	ad = _resolve_addendum(addendum_code)
	if not ad:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Addendum {0} was not found.").format((addendum_code or "").strip()),
		)

	ac = cstr(ad.addendum_code or "").strip()
	if cstr(ad.status or "").strip() != "Draft":
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Impact analysis can only be requested while the addendum is in Draft."),
			extra={"addendum_status": ad.status},
		)

	if frappe.db.exists("TM2 Addendum Impact Record", {"tm2_addendum": ad.name}):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("An addendum impact record already exists for this addendum."),
		)

	tc = cstr(ad.tender_code or "").strip()
	if not tc:
		return _deny(DenialCode.AUTH_CONTEXT_DENIED.value, _("Addendum is missing tender_code."))

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

	proposed = ctx.get("proposed_changes")
	if proposed is not None and not isinstance(proposed, dict):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("proposed_changes in context must be a dict when provided."),
		)
	proposed_changes: dict[str, Any] = proposed if isinstance(proposed, dict) else {}

	analysis = analyze_addendum_impact(ac, proposed_changes)
	if not analysis.get("ok"):
		return _deny(
			cstr(analysis.get("denial_code") or DenialCode.AUTH_CONTEXT_DENIED.value),
			cstr(analysis.get("message") or _("Impact analysis failed.")),
			extra={k: v for k, v in analysis.items() if k not in ("ok", "message", "denial_code")},
		)

	std_code = f"STDIA-{ac}-TM2"
	impact_payload = _safe_impact_payload(dict(analysis))

	air_fields: dict[str, Any] = {
		"doctype": "TM2 Addendum Impact Record",
		"tm2_addendum": ad.name,
		"std_impact_analysis_code": std_code,
		"impact_payload": impact_payload,
		"deadline_extension_required": _deadline_extension_flag(ad, analysis),
		"supplier_acknowledgement_required": int(bool(analysis.get("requires_supplier_notification"))),
		"bid_resubmission_required": _bid_resubmission_flag(analysis),
	}
	for key in (
		"previous_bundle_output_code",
		"revised_bundle_output_code",
		"previous_dsm_output_code",
		"revised_dsm_output_code",
		"previous_dom_output_code",
		"revised_dom_output_code",
		"previous_dem_output_code",
		"revised_dem_output_code",
		"previous_dcm_output_code",
		"revised_dcm_output_code",
		"previous_publication_snapshot_code",
		"revised_publication_snapshot_code",
	):
		if key in analysis:
			air_fields[key] = cstr(analysis.get(key) or "").strip()

	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)
		air = frappe.get_doc(air_fields)
		air.insert(ignore_permissions=True)
		air.reload()

		adc = frappe.get_doc("TM2 Addendum", ad.name)
		adc.status = "Impact Analysis Complete"
		adc.save(ignore_permissions=True)

		tm2_name = cstr(ad.tm2_tender or "").strip()
		audit_snap = {
			"addendum_code": ac,
			"impact_record_code": air.impact_record_code,
			"std_impact_analysis_code": std_code,
			"tender_code": tc,
		}
		append_tender_audit_event(
			tc,
			"Addendum Impact Analysis Completed",
			actor,
			audit_snap,
			related_object_type="TM2 Addendum Impact Record",
			related_object_code=air.name,
			enforce_section_13_2=False,
		)

		return {
			"ok": True,
			"addendum_code": ac,
			"tm2_addendum": ad.name,
			"tender_code": tc,
			"impact_record": air.name,
			"impact_record_code": air.impact_record_code,
			"addendum_status": "Impact Analysis Complete",
		}
	except frappe.ValidationError as ex:
		msg = cstr(getattr(ex, "message", None) or str(ex)).strip() or _("Validation failed.")
		return _deny(DenialCode.AUTH_CONTEXT_DENIED.value, msg)
	finally:
		frappe.set_user(prev_user)


def requestAddendumImpactAnalysis(
	actor: str,
	addendum_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`request_addendum_impact_analysis`."""
	return request_addendum_impact_analysis(actor, addendum_code, context=context)
