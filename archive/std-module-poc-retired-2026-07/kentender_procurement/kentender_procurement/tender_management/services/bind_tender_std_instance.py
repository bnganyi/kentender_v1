# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §9.2 — bind a ``Tender STD Instance`` to a ``TM2 Tender`` (STD binding row + audit).

Uses :func:`~kentender_procurement.tender_management.services.tm2_std_adapter.create_tender_std_instance`
for §8.2 adapter step 3. Tests: ``tender_management.tests.test_p4_02_bind_tender_std_instance``.
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
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)
from kentender_procurement.tender_management.services.append_tender_audit_event import (
	append_tender_audit_event,
)
from kentender_procurement.tender_management.services.tm2_std_adapter import (
	create_tender_std_instance,
	resolve_std_template_for_version_profile,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService

_ACTION = "TND2_BIND_STD"
_OBJECT_TYPE = "TM2 Tender"

_BIND_TENDER_STATUSES = frozenset({"Draft", "Returned for Correction"})


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


def _has_active_binding(tm2_name: str) -> bool:
	return bool(
		frappe.get_all(
			"TM2 Tender STD Binding",
			filters={
				"tm2_tender": tm2_name,
				"is_active": 1,
				"binding_status": ["not in", ["Cancelled", "Superseded"]],
			},
			limit=1,
			pluck="name",
		)
	)


def bind_tender_std_instance(
	actor: str,
	tender_code: str,
	std_template_version_code: str,
	profile_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 9 §9.2 — availability, template compatibility, adapter create, binding, parent status, audit."""
	ctx = dict(context or ())
	tm2 = _resolve_tm2(tender_code)
	if not tm2:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Tender {0} was not found.").format((tender_code or "").strip()),
		)

	tc = cstr(tm2.tender_code).strip() or tm2.name
	st = cstr(tm2.status).strip()
	if st not in _BIND_TENDER_STATUSES:
		return _deny(
			DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED.value,
			_("Tender status does not allow binding an STD instance."),
			extra={"tender_status": st},
		)

	if _has_active_binding(tm2.name):
		return _deny(
			DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED.value,
			_("An active TM2 Tender STD Binding already exists for this tender."),
		)

	if TenderStdBindingService.get_current_std_instance_for_tm2_tender(tm2.name):
		return _deny(
			DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED.value,
			_("An active Tender STD Instance already exists for this tender."),
		)

	std_name = resolve_std_template_for_version_profile(std_template_version_code, profile_code)
	if not std_name:
		return _deny(
			DenialCode.STD_TEMPLATE_INCOMPATIBLE.value,
			_("No STD Template matches the given version and applicability profile."),
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

	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)
		inst_out = create_tender_std_instance(tc, std_template_version_code, profile_code)
		if not inst_out.get("ok"):
			return inst_out

		si_name = str(inst_out.get("tender_std_instance") or "").strip()
		if not si_name:
			return _deny(
				DenialCode.STD_TEMPLATE_INCOMPATIBLE.value,
				_("Adapter did not return a tender STD instance."),
			)

		bind = frappe.get_doc(
			{
				"doctype": "TM2 Tender STD Binding",
				"tm2_tender": tm2.name,
				"std_template": std_name,
				"std_template_code": frappe.db.get_value("STD Template", std_name, "template_code") or std_name,
				"std_template_version_code": std_template_version_code.strip(),
				"std_applicability_profile_code": profile_code.strip(),
				"tender_std_instance": si_name,
				"is_active": 1,
				"binding_status": "Draft",
				"readiness_status": "Not Ready",
			}
		)
		bind.insert(ignore_permissions=True)

		frappe.db.set_value(
			"TM2 Tender",
			tm2.name,
			{"status": "STD Instance Incomplete"},
			update_modified=False,
		)

		payload = {
			"std_template": std_name,
			"std_template_version_code": std_template_version_code.strip(),
			"std_applicability_profile_code": profile_code.strip(),
			"tender_std_instance_code": si_name,
			"tm2_tender_std_binding": bind.name,
			"binding_code": bind.binding_code,
		}
		append_tender_audit_event(
			tc,
			"Tender STD Bound",
			actor,
			payload,
			related_object_type="Tender STD Instance",
			related_object_code=si_name,
			new_state="STD Instance Incomplete",
			enforce_section_13_2=False,
			tm2_audit_row_extras={
				"std_template_version_code": std_template_version_code.strip(),
				"tender_std_instance_code": si_name,
			},
		)

		return {
			"ok": True,
			"tender_code": tc,
			"tm2_tender": tm2.name,
			"tender_std_instance": si_name,
			"tm2_tender_std_binding": bind.name,
			"binding_code": bind.binding_code,
		}
	except Exception:
		frappe.db.rollback()
		raise
	finally:
		frappe.set_user(prev_user)


def bindTenderStdInstance(
	actor: str,
	tender_code: str,
	std_template_version_code: str,
	profile_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`bind_tender_std_instance`."""
	return bind_tender_std_instance(
		actor, tender_code, std_template_version_code, profile_code, context=context
	)
