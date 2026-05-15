# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §9.6 — publish **TM2 Tender** (publication transaction).

Preconditions: ``Approved for Publication``; active binding; latest **TM2 Publication Readiness**
still **Ready** with outputs current (same gate as §9.5); **TM2 Tender Access Rule** exists;
:func:`~kentender_procurement.tender_management.services.tm2_std_adapter.create_or_get_publication_snapshot_for_tm2`
returns ``ok`` (else ``AUTH_PUBLICATION_SNAPSHOT_MISSING``); :func:`get_action_availability` for
``TND2_PUBLISH``.

On success: insert **TM2 Publication Record**; bind output + snapshot codes on **TM2 Tender STD Binding**
(``Published``); set tender **Published** + ``published_by`` / ``published_at``; lock **Tender STD Instance**
to **Published Locked**; enqueue supplier-facing **TM2 Notification Record** (Publication / Public / Portal);
audit **Tender Published** (TM2-AUD-004 payload with ``publication_snapshot_code`` and output refs).

Tests: ``tender_management.tests.test_p4_06_publish_tender``;
``tender_management.tests.test_o03_tm2_smoke_pub_003_publish_approved_tender_and_bind_publication_snapshot`` (doc 8 TM2-SMOKE-PUB-003 / O-03);
``tender_management.tests.test_o04_tm2_smoke_pub_006_block_publication_without_publication_snapshot_binding`` (doc 8 TM2-SMOKE-PUB-006 / O-04);
``tender_management.tests.test_ex_01_cannot_publish_without_std_binding`` (doc 9 §25 **EX-01**);
``tender_management.tests.test_ex_02_cannot_publish_without_bundle_dsm_dom_dem_dcm`` (doc 9 §25 **EX-02**);
``tender_management.tests.test_ex_03_cannot_publish_without_publication_snapshot`` (doc 9 §25 **EX-03**);
``tender_management.tests.test_ex_16_direct_api_bypass_denied`` (doc 9 §25 **EX-16** / TM2-NB-016 — no **Published** via ``Document.save`` bypass);
``tender_management.tests.tm2_publish_fixture_chain`` (shared **Approved for Publication** chain).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, now_datetime

from kentender_procurement.tender_management.security.action_availability.service import (
	get_action_availability,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.approve_tender_publication import (
	_readiness_still_valid_denial,
)
from kentender_procurement.tender_management.services.submit_tender_for_publication_review import (
	_active_std_binding,
	_latest_publication_readiness,
	_resolve_tm2,
)
from kentender_procurement.tender_management.services.append_tender_audit_event import (
	append_tender_audit_event,
)
from kentender_procurement.tender_management.services.tm2_std_adapter import (
	create_or_get_publication_snapshot_for_tm2,
)

_ACTION = "TND2_PUBLISH"
_OBJECT_TYPE = "TM2 Tender"
_REQUIRED_STATUS = "Approved for Publication"


def _deny(denial_code: str, message: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
	out: dict[str, Any] = {"ok": False, "denial_code": denial_code, "message": message}
	if extra:
		out.update(extra)
	return out


def _map_auth_denial(denial_code: str) -> str:
	if denial_code == DenialCode.STD_AUTH_PERMISSION_DENIED.value:
		return DenialCode.AUTH_ROLE_DENIED.value
	return denial_code


def _publication_visibility_from_access_rule(tm2_name: str) -> str:
	vis = cstr(
		frappe.db.get_value("TM2 Tender Access Rule", {"tm2_tender": tm2_name}, "visibility") or ""
	).strip()
	if vis == "Public":
		return "Public"
	if vis in ("Restricted", "Direct Invitation", "Login Required"):
		return "Restricted"
	return "Internal Preview"


def _insert_publication_notification(
	tm2_name: str,
	tender_code: str,
	pub_name: str,
	snap: dict[str, Any],
) -> str | None:
	"""Best-effort supplier/public notice row (doc 9 §9.6 step 6)."""
	try:
		doc = frappe.get_doc(
			{
				"doctype": "TM2 Notification Record",
				"tm2_tender": tm2_name,
				"tender_code": tender_code,
				"related_object_type": "TM2 Publication Record",
				"related_object_id": pub_name,
				"notification_type": "Publication",
				"recipient_type": "Public",
				"channel": "Portal",
				"message_template_code": "TM2_TENDER_PUBLISHED_PUBLIC",
				"payload_snapshot": {
					"headline": "Tender published",
					"tender_code": tender_code,
					"tm2_publication_record": pub_name,
					"publication_snapshot_code": snap.get("publication_snapshot_code"),
					"bundle_output_code": snap.get("bundle_output_code"),
					"dsm_output_code": snap.get("dsm_output_code"),
					"dom_output_code": snap.get("dom_output_code"),
					"dem_output_code": snap.get("dem_output_code"),
					"dcm_output_code": snap.get("dcm_output_code"),
				},
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name
	except Exception:
		frappe.log_error(frappe.get_traceback(), "publish_tender_notification")
		return None


def publish_tender(actor: str, tender_code: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
	"""Doc 9 §9.6 — gated TM2 publish: snapshot, publication record, binding lock, tender Published, audit."""
	ctx = dict(context or ())
	tm2 = _resolve_tm2(tender_code)
	if not tm2:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Tender {0} was not found.").format((tender_code or "").strip()),
		)

	tc = cstr(tm2.tender_code).strip() or tm2.name
	st = cstr(tm2.status).strip()
	if st == "Published":
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("This tender is already published."),
			extra={"tender_status": st},
		)
	if st != _REQUIRED_STATUS:
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Tender must be Approved for Publication before publish."),
			extra={"tender_status": st},
		)

	if not frappe.db.exists("TM2 Tender Access Rule", {"tm2_tender": tm2.name}):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("TM2 Tender Access Rule is required before publish."),
		)

	bind = _active_std_binding(tm2.name)
	if not bind:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("No active TM2 Tender STD Binding exists for this tender."),
		)

	rd = _readiness_still_valid_denial(tm2.name, bind)
	if rd:
		return rd

	snap = create_or_get_publication_snapshot_for_tm2(tc)
	if not snap.get("ok"):
		return _deny(
			cstr(snap.get("denial_code") or DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value),
			cstr(snap.get("message") or _("Publication snapshot is missing or incomplete.")),
			extra={k: v for k, v in snap.items() if k not in ("ok", "message", "denial_code")},
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

	read_row = _latest_publication_readiness(tm2.name) or {}
	pr_name = cstr(read_row.get("name") or "").strip()
	if not pr_name:
		return _deny(
			DenialCode.AUTH_STD_NOT_READY.value,
			_("No publication readiness run exists."),
		)

	pub_vis = _publication_visibility_from_access_rule(tm2.name)
	payload_snap: dict[str, Any] = {
		"tender_code": tc,
		"publication_snapshot_code": snap.get("publication_snapshot_code"),
		"snapshot_hash": snap.get("snapshot_hash"),
		"snapshot_binding_status": snap.get("status"),
		"bundle_output_code": snap.get("bundle_output_code"),
		"dsm_output_code": snap.get("dsm_output_code"),
		"dom_output_code": snap.get("dom_output_code"),
		"dem_output_code": snap.get("dem_output_code"),
		"dcm_output_code": snap.get("dcm_output_code"),
		"tender_std_instance": snap.get("tender_std_instance"),
	}

	now = now_datetime()
	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)
		pub = frappe.get_doc(
			{
				"doctype": "TM2 Publication Record",
				"tm2_tender": tm2.name,
				"tm2_tender_std_binding": bind.name,
				"tm2_publication_readiness": pr_name,
				"bundle_output_code": snap["bundle_output_code"],
				"bundle_output_hash": snap.get("bundle_output_hash") or "",
				"dsm_output_code": snap["dsm_output_code"],
				"dom_output_code": snap["dom_output_code"],
				"dem_output_code": snap["dem_output_code"],
				"dcm_output_code": snap["dcm_output_code"],
				"publication_snapshot_code": snap["publication_snapshot_code"],
				"publication_channel": "Supplier Portal",
				"visibility": pub_vis,
				"publication_payload_snapshot": payload_snap,
				"status": "Published",
			}
		)
		pub.insert(ignore_permissions=True)

		bdoc = frappe.get_doc("TM2 Tender STD Binding", bind.name)
		bdoc.bundle_output_code = snap["bundle_output_code"]
		bdoc.dsm_output_code = snap["dsm_output_code"]
		bdoc.dom_output_code = snap["dom_output_code"]
		bdoc.dem_output_code = snap["dem_output_code"]
		bdoc.dcm_output_code = snap["dcm_output_code"]
		bdoc.publication_snapshot_code = snap["publication_snapshot_code"]
		bdoc.binding_status = "Published"
		bdoc.save(ignore_permissions=True)

		si_name = cstr(snap.get("tender_std_instance") or "").strip()
		if si_name and frappe.db.exists("Tender STD Instance", si_name):
			frappe.db.set_value(
				"Tender STD Instance",
				si_name,
				{"instance_status": "Published Locked"},
				update_modified=False,
			)

		frappe.db.set_value(
			"TM2 Tender",
			tm2.name,
			{
				"status": "Published",
				"published_by": actor if frappe.db.exists("User", actor) else None,
				"published_at": now,
			},
			update_modified=True,
		)

		ntf = _insert_publication_notification(tm2.name, tc, pub.name, snap)

		audit_payload: dict[str, Any] = {
			"tm2_publication_record": pub.name,
			"publication_code": pub.publication_code,
			"publication_snapshot_code": snap["publication_snapshot_code"],
			"snapshot_hash": snap.get("snapshot_hash"),
			"bundle_output_code": snap["bundle_output_code"],
			"dsm_output_code": snap["dsm_output_code"],
			"dom_output_code": snap["dom_output_code"],
			"dem_output_code": snap["dem_output_code"],
			"dcm_output_code": snap["dcm_output_code"],
			"tender_std_instance": si_name,
			"tm2_publication_readiness": pr_name,
		}
		if ntf:
			audit_payload["tm2_notification_record"] = ntf
		append_tender_audit_event(
			tc,
			"Tender Published",
			actor,
			audit_payload,
			related_object_type="TM2 Publication Record",
			related_object_code=cstr(pub.name),
			previous_state=_REQUIRED_STATUS,
			new_state="Published",
		)

		return {
			"ok": True,
			"tender_code": tc,
			"tm2_tender": tm2.name,
			"tm2_publication_record": pub.name,
			"publication_code": pub.publication_code,
			"publication_snapshot_code": snap["publication_snapshot_code"],
			"status": "Published",
			"tm2_notification_record": ntf,
		}
	except Exception:
		frappe.db.rollback()
		raise
	finally:
		frappe.set_user(prev_user)


def publishTender(actor: str, tender_code: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
	"""CamelCase alias for :func:`publish_tender`."""
	return publish_tender(actor, tender_code, context=context)
