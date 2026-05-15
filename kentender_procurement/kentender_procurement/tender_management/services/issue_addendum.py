# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §10.5 — issue an **approved** **TM2 Addendum** (orchestration).

1. :func:`get_action_availability` for ``ADD2_ISSUE``;
2. structural addenda require a **TM2 Addendum Impact Record**;
3. :func:`~kentender_procurement.tender_management.services.tm2_std_adapter.regenerate_outputs_for_addendum`;
4. refresh publication snapshot via :func:`~kentender_procurement.tender_management.services.tm2_std_adapter.create_or_get_publication_snapshot_for_tm2`;
5. resync **TM2 Tender STD Binding** output refs + ``published_snapshot_hash`` (uses
   ``flags.allow_tm2_tsb_published_output_resync`` — published bindings are otherwise immutable);
6. optional timeline shift when ``affects_deadline`` or impact record ``deadline_extension_required``;
7. **TM2 Addendum Acknowledgement** rows when required;
8. **TM2 Notification Record** (**Addendum** / **Supplier** / **Portal**) per **TM2 Supplier Participation**;
9. set addendum **Issued**; audit **Addendum Issued**.

``context`` (optional):

- ``revised_submission_deadline_at`` / ``revised_opening_scheduled_at`` — ``Datetime`` or ISO string;
  when deadline extension applies and both are omitted, each deadline is shifted by **7 days** from
  the current **TM2 Tender Timeline** values.

Preconditions: addendum ``status`` is **Approved**; tender **Published** (typical post-publish path).

Tests: ``tender_management.tests.test_p5_05_issue_addendum`` (incl. doc 9 §25 **EX-13** ``test_EX_13_*``).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint, cstr, get_datetime

from kentender_procurement.tender_management.security.action_availability.service import (
	get_action_availability,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.append_tender_audit_event import append_tender_audit_event
from kentender_procurement.tender_management.services.tm2_std_adapter import (
	create_or_get_publication_snapshot_for_tm2,
	regenerate_outputs_for_addendum,
)

_ACTION = "ADD2_ISSUE"
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


def _primary_is_structural(add: Document) -> bool:
	return cstr(add.get("primary_impact_type") or "").strip() != "No Structural Impact"


def _air_row(add_name: str) -> dict[str, Any] | None:
	return frappe.db.get_value(
		"TM2 Addendum Impact Record",
		{"tm2_addendum": add_name},
		[
			"name",
			"deadline_extension_required",
			"supplier_acknowledgement_required",
		],
		as_dict=True,
	)


def _maybe_shift_timeline(
	tm2_name: str,
	add: Document,
	air: dict[str, Any] | None,
	ctx: dict[str, Any],
) -> dict[str, Any] | None:
	deadline_row = bool(cint(add.get("affects_deadline")))
	if air:
		deadline_row = deadline_row or bool(cint(air.get("deadline_extension_required")))
	if not deadline_row:
		return None

	tl_name = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2_name}, "name")
	if not tl_name:
		return None

	tl = frappe.get_doc("TM2 Tender Timeline", tl_name)
	prev_sub = tl.submission_deadline_at
	prev_open = tl.opening_scheduled_at

	rs = ctx.get("revised_submission_deadline_at")
	ro = ctx.get("revised_opening_scheduled_at")
	if rs is not None and ro is not None:
		tl.submission_deadline_at = get_datetime(rs)
		tl.opening_scheduled_at = get_datetime(ro)
	elif prev_sub and prev_open:
		tl.submission_deadline_at = add_days(prev_sub, 7)
		tl.opening_scheduled_at = add_days(prev_open, 7)
	else:
		return None

	tl.flags.allow_tm2_ttl_addendum_deadline_patch = True
	tl.save(ignore_permissions=True)
	return {
		"submission_deadline_at": str(tl.submission_deadline_at),
		"opening_scheduled_at": str(tl.opening_scheduled_at),
	}


def _ensure_acknowledgements(tm2_name: str, add: Document, air: dict[str, Any] | None) -> list[str]:
	need = bool(cint(add.get("requires_supplier_acknowledgement")))
	if air:
		need = need or bool(cint(air.get("supplier_acknowledgement_required")))
	if not need:
		return []

	created: list[str] = []
	for row in frappe.get_all(
		"TM2 Supplier Participation",
		filters={"tm2_tender": tm2_name},
		pluck="supplier",
	):
		if not row or frappe.db.exists(
			"TM2 Addendum Acknowledgement",
			{"tm2_addendum": add.name, "supplier": row},
		):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "TM2 Addendum Acknowledgement",
				"tm2_addendum": add.name,
				"supplier": row,
				"required": 1,
				"acknowledged": 0,
			}
		)
		doc.insert(ignore_permissions=True)
		created.append(doc.name)
	return created


def _notify_participating_suppliers(
	tm2_name: str,
	tender_code: str,
	add_name: str,
	add_code: str,
	snap: dict[str, Any],
) -> list[str]:
	out: list[str] = []
	for sup in frappe.get_all(
		"TM2 Supplier Participation",
		filters={"tm2_tender": tm2_name},
		pluck="supplier",
	):
		if not sup:
			continue
		try:
			doc = frappe.get_doc(
				{
					"doctype": "TM2 Notification Record",
					"tm2_tender": tm2_name,
					"tender_code": tender_code,
					"related_object_type": "TM2 Addendum",
					"related_object_id": add_name,
					"notification_type": "Addendum",
					"recipient_type": "Supplier",
					"recipient_ref": sup,
					"channel": "Portal",
					"message_template_code": "TM2_ADDENDUM_ISSUED_SUPPLIER",
					"payload_snapshot": {
						"headline": "Addendum issued",
						"tender_code": tender_code,
						"addendum_code": add_code,
						"tm2_addendum": add_name,
						"publication_snapshot_code": snap.get("publication_snapshot_code"),
						"snapshot_hash": snap.get("snapshot_hash"),
						"bundle_output_code": snap.get("bundle_output_code"),
						"dsm_output_code": snap.get("dsm_output_code"),
						"dom_output_code": snap.get("dom_output_code"),
						"dem_output_code": snap.get("dem_output_code"),
						"dcm_output_code": snap.get("dcm_output_code"),
					},
					"delivery_status": "Pending",
				}
			)
			doc.insert(ignore_permissions=True)
			out.append(doc.name)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "issue_addendum_notification")
	return out


def issue_addendum(
	actor: str,
	addendum_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 9 §10.5 — regenerate, snapshot, binding resync, timeline/acks/notifications, **Issued**."""
	ctx = dict(context or {})

	ad = _resolve_addendum(addendum_code)
	if not ad:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Addendum {0} was not found.").format((addendum_code or "").strip()),
		)

	ac = cstr(ad.addendum_code or "").strip()
	if cstr(ad.status or "").strip() != "Approved":
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Only an approved addendum can be issued."),
			extra={"addendum_status": ad.status},
		)

	tc = cstr(ad.tender_code or "").strip()
	if not tc:
		return _deny(DenialCode.AUTH_CONTEXT_DENIED.value, _("Addendum is missing tender_code."))

	tm2_name = cstr(ad.tm2_tender or "").strip()
	if not tm2_name:
		return _deny(DenialCode.AUTH_CONTEXT_DENIED.value, _("Addendum is missing tm2_tender."))

	air = _air_row(ad.name) if _primary_is_structural(ad) else None
	if _primary_is_structural(ad) and not air:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Structural addendum requires an addendum impact record before issue."),
		)

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

	regen = regenerate_outputs_for_addendum(ac)
	if not regen.get("ok"):
		return _deny(
			cstr(regen.get("denial_code") or DenialCode.AUTH_CONTEXT_DENIED.value),
			cstr(regen.get("message") or _("Output regeneration failed.")),
			extra={k: v for k, v in regen.items() if k not in ("ok", "message", "denial_code")},
		)

	snap = create_or_get_publication_snapshot_for_tm2(tc)
	if not snap.get("ok"):
		return _deny(
			cstr(snap.get("denial_code") or DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value),
			cstr(snap.get("message") or _("Publication snapshot could not be refreshed.")),
			extra={k: v for k, v in snap.items() if k not in ("ok", "message", "denial_code")},
		)

	bind_name = cstr(snap.get("tm2_tender_std_binding") or "").strip()
	if not bind_name or not frappe.db.exists("TM2 Tender STD Binding", bind_name):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("No TM2 Tender STD Binding found for snapshot refresh."),
		)

	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)

		ack_names = _ensure_acknowledgements(tm2_name, ad, air)
		timeline_patch = _maybe_shift_timeline(tm2_name, ad, air, ctx)

		bdoc = frappe.get_doc("TM2 Tender STD Binding", bind_name)
		bdoc.bundle_output_code = snap["bundle_output_code"]
		bdoc.dsm_output_code = snap["dsm_output_code"]
		bdoc.dom_output_code = snap["dom_output_code"]
		bdoc.dem_output_code = snap["dem_output_code"]
		bdoc.dcm_output_code = snap["dcm_output_code"]
		bdoc.publication_snapshot_code = snap["publication_snapshot_code"]
		bdoc.published_snapshot_hash = cstr(snap.get("snapshot_hash") or "")
		bdoc.flags.allow_tm2_tsb_published_output_resync = True
		bdoc.save(ignore_permissions=True)

		ad.reload()
		ad.status = "Issued"
		ad.save(ignore_permissions=True)

		ntf_names = _notify_participating_suppliers(tm2_name, tc, ad.name, ac, snap)

		audit_payload: dict[str, Any] = {
			"addendum_code": ac,
			"tender_code": tc,
			"publication_snapshot_code": snap.get("publication_snapshot_code"),
			"snapshot_hash": snap.get("snapshot_hash"),
			"bundle_output_code": snap.get("bundle_output_code"),
			"dsm_output_code": snap.get("dsm_output_code"),
			"dom_output_code": snap.get("dom_output_code"),
			"dem_output_code": snap.get("dem_output_code"),
			"dcm_output_code": snap.get("dcm_output_code"),
			"regeneration": {k: v for k, v in regen.items() if k in ("affected_outputs", "change_types")},
		}
		if timeline_patch:
			audit_payload["timeline"] = timeline_patch
		if ack_names:
			audit_payload["tm2_addendum_acknowledgements"] = ack_names
		if ntf_names:
			audit_payload["tm2_notification_records"] = ntf_names

		append_tender_audit_event(
			tc,
			"Addendum Issued",
			actor,
			audit_payload,
			related_object_type="TM2 Addendum",
			related_object_code=ad.name,
		)

		return {
			"ok": True,
			"addendum_code": ac,
			"tm2_addendum": ad.name,
			"tender_code": tc,
			"addendum_status": "Issued",
			"publication_snapshot_code": snap.get("publication_snapshot_code"),
			"snapshot_hash": snap.get("snapshot_hash"),
			"tm2_tender_std_binding": bind_name,
			"tm2_addendum_acknowledgements": ack_names,
			"tm2_notification_records": ntf_names,
			"timeline": timeline_patch,
		}
	except frappe.ValidationError as ex:
		msg = cstr(getattr(ex, "message", None) or str(ex)).strip() or _("Validation failed.")
		return _deny(DenialCode.AUTH_CONTEXT_DENIED.value, msg)
	finally:
		frappe.set_user(prev_user)


def issueAddendum(actor: str, addendum_code: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
	"""CamelCase alias for :func:`issue_addendum`."""
	return issue_addendum(actor, addendum_code, context=context)
