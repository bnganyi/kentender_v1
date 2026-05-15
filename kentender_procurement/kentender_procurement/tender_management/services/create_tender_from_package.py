# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §9.1 — create TM2 Tender from a released procurement package.

Preconditions, STD eligibility (via :mod:`tm2_std_adapter`), default access rule,
and **Tender Created** audit on ``TM2 Tender Audit Event``.

Tests: ``tender_management.tests.test_p4_01_create_tender_from_package``.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr

from kentender_procurement.procurement_planning.doctype.procurement_package.procurement_package import (
	ST_APPROVED,
	ST_READY_FOR_TENDER,
	ST_RELEASED_TO_TENDER,
)
from kentender_procurement.tender_management.security.action_availability.service import (
	get_action_availability,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)
from kentender_procurement.tender_management.services.append_tender_audit_event import (
	append_tender_audit_event,
)
from kentender_procurement.tender_management.services.planning_tender_handoff_duplicates import (
	TM2_STATUSES_RELEASING_PACKAGE_FOR_NEW_TENDER,
)
from kentender_procurement.tender_management.services.std_template_handoff_resolution import (
	resolve_std_template_for_handoff,
)
from kentender_procurement.tender_management.services.tm2_std_adapter import (
	get_eligible_std_templates,
	load_procurement_package_by_code,
)

_ACTION = "TND2_CREATE_FROM_PACKAGE"
_OBJECT_TYPE = "Procurement Package"

_AUTHORIZED_PACKAGE_STATUSES = frozenset(
	{
		ST_APPROVED,
		ST_READY_FOR_TENDER,
		ST_RELEASED_TO_TENDER,
	}
)

def active_tm2_tender_name_for_package(package_name: str) -> str | None:
	"""Return the name of an active ``TM2 Tender`` for this package, if any."""
	for row in frappe.get_all(
		"TM2 Tender",
		filters={"procurement_package": package_name},
		pluck="name",
	):
		st = cstr(frappe.db.get_value("TM2 Tender", row, "status") or "").strip()
		if st and st not in TM2_STATUSES_RELEASING_PACKAGE_FOR_NEW_TENDER:
			return row
	return None


def _has_active_tm2_for_package(package_name: str) -> bool:
	return active_tm2_tender_name_for_package(package_name) is not None


def _deny(
	denial_code: str,
	message: str,
	*,
	extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
	out: dict[str, Any] = {
		"ok": False,
		"denial_code": denial_code,
		"message": message,
	}
	if extra:
		out.update(extra)
	return out


def _map_auth_denial(denial_code: str) -> str:
	if denial_code == DenialCode.STD_AUTH_PERMISSION_DENIED.value:
		return DenialCode.AUTH_ROLE_DENIED.value
	return denial_code


def _package_business_code(pkg: Document) -> str:
	return cstr(pkg.get("package_code") or pkg.name).strip()


def _tm2_category_from_planning_template(template_id: str | None) -> str:
	if not template_id:
		return "Goods"
	raw = (frappe.db.get_value("Procurement Template", template_id, "category") or "").strip().lower()
	if raw == "works":
		return "Works"
	if raw == "consultancy":
		return "Consultancy"
	if raw == "services":
		return "Services"
	return "Goods"


def _maybe_create_timeline(
	tm2_name: str,
	tender_code: str,
	wizard: dict[str, Any] | None,
) -> str | None:
	if not wizard:
		return None
	clar = wizard.get("clarification_deadline_at")
	sub = wizard.get("submission_deadline_at")
	opn = wizard.get("opening_scheduled_at")
	tvd = wizard.get("tender_validity_days")
	if not (clar and sub and opn and tvd is not None):
		return None
	tl = frappe.get_doc(
		{
			"doctype": "TM2 Tender Timeline",
			"tm2_tender": tm2_name,
			"tender_code": tender_code,
			"clarification_deadline_at": clar,
			"submission_deadline_at": sub,
			"opening_scheduled_at": opn,
			"tender_validity_days": int(tvd),
			"timezone": cstr(wizard.get("timezone") or "Africa/Nairobi").strip() or "Africa/Nairobi",
			"planned_publication_at": wizard.get("planned_publication_at"),
			"addendum_cutoff_at": wizard.get("addendum_cutoff_at"),
		}
	)
	tl.insert(ignore_permissions=True)
	return tl.name


def create_tender_from_package(
	actor: str,
	package_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 9 §9.1 — create a **Draft** ``TM2 Tender`` from a released package.

	:param context: Optional ``granted_permissions`` / ``security_role_codes`` for
		§7.3 availability; optional ``retender_of_tender_code`` / ``supersedes_tender_code``
		to skip the active-tender duplicate check; optional ``wizard_timeline_dates``
		dict to create a timeline row when all required deadline fields are present;
		optional ``preferred_std_template`` (``STD Template`` name) when several
		eligible templates exist (P9-07 wizard selection);
		optional ``bypass_tnd2_create_from_package_availability`` (internal): when true, skips
		``TND2_CREATE_FROM_PACKAGE`` action-availability — only after ``RELEASE_PACKAGE_TO_TENDER``
		sec-auth in :func:`release_procurement_package_to_tender`.
	:returns: ``ok`` plus ``tender_code`` / ``tm2_tender`` on success.
	"""
	ctx = dict(context or())
	pkg = load_procurement_package_by_code(package_code)
	if not pkg:
		return _deny(
			DenialCode.PACKAGE_NOT_AUTHORIZED.value,
			_("Procurement package was not found or is not authorized for tender creation."),
		)

	business_code = _package_business_code(pkg)
	status = cstr(pkg.get("status") or "").strip()
	if status not in _AUTHORIZED_PACKAGE_STATUSES:
		return _deny(
			DenialCode.PACKAGE_NOT_AUTHORIZED.value,
			_("Package must be Approved, Ready for Tender, or Released to Tender before creating a TM2 tender."),
		)

	skip_active_check = bool(
		cstr(ctx.get("retender_of_tender_code") or "").strip()
		or cstr(ctx.get("supersedes_tender_code") or "").strip()
	)
	if not skip_active_check and _has_active_tm2_for_package(pkg.name):
		return _deny(
			DenialCode.ACTIVE_TENDER_EXISTS.value,
			_("An active TM2 tender already exists for this procurement package."),
		)

	if not ctx.get("bypass_tnd2_create_from_package_availability"):
		avail = get_action_availability(
			_ACTION,
			_OBJECT_TYPE,
			business_code,
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

	std_row = resolve_std_template_for_handoff(pkg)
	eligible = get_eligible_std_templates(business_code)
	eligible_std_names = frozenset(
		cstr(e.get("std_template") or "").strip()
		for e in eligible
		if cstr(e.get("std_template") or "").strip()
	)
	pref = cstr(ctx.get("preferred_std_template") or "").strip()
	pref_ok = bool(pref and pref in eligible_std_names)
	if pref and not pref_ok:
		return _deny(
			DenialCode.STD_NO_ELIGIBLE_TEMPLATE.value,
			_("The selected STD template is not eligible for this procurement package."),
			extra={"preferred_std_template": pref},
		)
	if not eligible:
		return _deny(
			DenialCode.STD_NO_ELIGIBLE_TEMPLATE.value,
			_("No eligible active STD template is available for this package."),
		)
	if (std_row.is_ambiguous or len(eligible) > 1) and not pref_ok:
		cands: list[str] = []
		if std_row.is_ambiguous:
			cands = [cstr(x).strip() for x in (std_row.ambiguous_candidates or ()) if cstr(x).strip()]
		elif len(eligible) > 1:
			cands = [cstr(e.get("std_template") or "").strip() for e in eligible if cstr(e.get("std_template") or "").strip()]
		return _deny(
			DenialCode.STD_MULTIPLE_ELIGIBLE_REQUIRES_SELECTION.value,
			_("Multiple eligible STD templates match this package; resolve ambiguity before creating a tender."),
			extra={"ambiguous_candidates": cands},
		)
	std_name_for_audit = pref if pref_ok else cstr(std_row.std_name or "").strip()
	if not std_name_for_audit:
		ex: dict[str, Any] = {"resolution_path": std_row.path}
		if std_row.invalid_default_link:
			ex["invalid_default_link"] = std_row.invalid_default_link
		return _deny(
			DenialCode.STD_NO_ELIGIBLE_TEMPLATE.value,
			_("No eligible active STD template is available for this package."),
			extra=ex,
		)
	if std_name_for_audit not in eligible_std_names:
		return _deny(
			DenialCode.STD_NO_ELIGIBLE_TEMPLATE.value,
			_("Resolved STD template is not in the eligible list for this package."),
			extra={"std_template": std_name_for_audit},
		)

	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)
		title = cstr(pkg.get("package_name") or business_code).strip() or business_code
		tpl_id = pkg.get("template_id")
		proc_cat = _tm2_category_from_planning_template(tpl_id)
		tm2 = frappe.get_doc(
			{
				"doctype": "TM2 Tender",
				"tender_title": title,
				"tender_description": cstr(pkg.get("package_name") or "").strip(),
				"status": "Draft",
				"procurement_package": pkg.name,
				"procurement_plan": pkg.plan_id,
				"procurement_category": proc_cat,
				"tender_visibility": "Public",
				"retender_of_tender_code": cstr(ctx.get("retender_of_tender_code") or "").strip() or None,
				"supersedes_tender_code": cstr(ctx.get("supersedes_tender_code") or "").strip() or None,
			}
		)
		tm2.insert(ignore_permissions=True)
		tender_code = cstr(tm2.tender_code).strip()

		frappe.get_doc(
			{
				"doctype": "TM2 Tender Access Rule",
				"tm2_tender": tm2.name,
				"tender_code": tender_code,
				"visibility": "Public",
				"requires_supplier_login_for_documents": 0,
				"requires_invitation": 0,
				"allows_public_notice": 1,
				"allows_public_document_download": 0,
				"eligibility_service_required": 0,
			}
		).insert(ignore_permissions=True)

		append_tender_audit_event(
			tender_code,
			"Tender Created",
			actor,
			{
				"package_code": business_code,
				"procurement_package": pkg.name,
				"std_template": std_name_for_audit,
				"std_resolution_path": std_row.path,
				"preferred_std_template": pref if pref_ok else None,
				"eligible_std_templates": eligible,
			},
			related_object_type="Procurement Package",
			related_object_code=business_code,
			new_state="Draft",
			enforce_section_13_2=False,
		)

		timeline_name = _maybe_create_timeline(tm2.name, tender_code, ctx.get("wizard_timeline_dates"))

		out: dict[str, Any] = {
			"ok": True,
			"tender_code": tender_code,
			"tm2_tender": tm2.name,
			"eligible_std_templates": eligible,
		}
		if timeline_name:
			out["tm2_tender_timeline"] = timeline_name
		return out
	except Exception:
		frappe.db.rollback()
		raise
	finally:
		frappe.set_user(prev_user)


def createTenderFromPackage(
	actor: str,
	package_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`create_tender_from_package`."""
	return create_tender_from_package(actor, package_code, context=context)
