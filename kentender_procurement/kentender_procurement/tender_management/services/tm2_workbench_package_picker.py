# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-03 — package picker data for **New Tender** (doc 9 §14.5, §15.1–15.3).

Returns released/approved packages with ``selectable`` + denial hints aligned with
:func:`~kentender_procurement.tender_management.services.create_tender_from_package.create_tender_from_package`
gates (action availability, active TM2, STD handoff / eligibility).

Tests: ``tender_management.tests.test_p9_03_new_tender_package_picker``.
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
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.create_tender_from_package import (
	_has_active_tm2_for_package,
)
from kentender_procurement.tender_management.services.std_template_handoff_resolution import (
	resolve_std_template_for_handoff,
)
from kentender_procurement.tender_management.services.tm2_std_adapter import (
	get_eligible_std_templates,
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


def _package_business_code(pkg: Document) -> str:
	return cstr(pkg.get("package_code") or pkg.name).strip()


def _preview_row(pkg: Document, actor: str) -> dict[str, Any]:
	business_code = _package_business_code(pkg)
	row: dict[str, Any] = {
		"name": pkg.name,
		"package_code": business_code,
		"package_name": cstr(pkg.get("package_name") or "").strip(),
		"status": cstr(pkg.get("status") or "").strip(),
		"selectable": False,
		"denial_code": None,
		"user_message": None,
	}

	if row["status"] not in _AUTHORIZED_PACKAGE_STATUSES:
		row["denial_code"] = DenialCode.PACKAGE_NOT_AUTHORIZED.value
		row["user_message"] = _("Package is not in an authorized planning status.")
		return row

	if _has_active_tm2_for_package(pkg.name):
		row["denial_code"] = DenialCode.ACTIVE_TENDER_EXISTS.value
		row["user_message"] = _("An active TM2 tender already exists for this procurement package.")
		return row

	avail = get_action_availability(
		_ACTION,
		_OBJECT_TYPE,
		business_code,
		actor,
		context={"object_exists": True},
	)
	if not avail.get("allowed"):
		row["denial_code"] = str(avail.get("denial_code") or DenialCode.AUTH_ROLE_DENIED.value)
		row["user_message"] = str(
			avail.get("user_message") or avail.get("message") or row["denial_code"],
		)
		return row

	std_row = resolve_std_template_for_handoff(pkg)
	eligible = get_eligible_std_templates(business_code)
	if not eligible:
		row["denial_code"] = DenialCode.STD_NO_ELIGIBLE_TEMPLATE.value
		row["user_message"] = _("No eligible active STD template is available for this package.")
		return row

	needs_std_wizard_choice = bool(std_row.is_ambiguous or len(eligible) > 1)
	if needs_std_wizard_choice:
		row["selectable"] = True
		row["requires_std_wizard_choice"] = True
		return row

	if not std_row.std_name:
		row["denial_code"] = DenialCode.STD_NO_ELIGIBLE_TEMPLATE.value
		row["user_message"] = _("No eligible active STD template is available for this package.")
		return row

	row["selectable"] = True
	row["requires_std_wizard_choice"] = False
	return row


def list_packages_for_new_tender(
	actor: str,
	search: str | None = None,
	*,
	limit: int = 50,
) -> dict[str, Any]:
	"""Return packages the actor can see in the **New Tender** picker (P9-03)."""
	act = cstr(actor or "").strip()
	if not act or not frappe.db.exists("User", act):
		return {"ok": False, "message": _("A valid user is required.")}

	if not frappe.has_permission("Procurement Package", "read", user=act):
		return {"ok": False, "message": _("You do not have permission to read procurement packages.")}

	prev = frappe.session.user
	try:
		frappe.set_user(act)
		lim = int(limit) if limit else 50
		if lim < 1:
			lim = 1
		if lim > 200:
			lim = 200

		rows = frappe.get_all(
			"Procurement Package",
			filters={"status": ["in", list(_AUTHORIZED_PACKAGE_STATUSES)]},
			fields=["name", "package_code", "package_name"],
			limit_page_length=min(300, max(lim * 4, lim)),
			order_by="modified desc",
		)
		sq = cstr(search or "").strip().lower()
		if sq:
			rows = [
				r
				for r in rows
				if sq in cstr(r.get("package_code") or "").lower()
				or sq in cstr(r.get("package_name") or "").lower()
			]
		names = [cstr(r.get("name") or "").strip() for r in rows[:lim] if r.get("name")]

		packages: list[dict[str, Any]] = []
		for nm in names:
			if not nm or not frappe.db.exists("Procurement Package", nm):
				continue
			pkg = frappe.get_doc("Procurement Package", nm)
			packages.append(_preview_row(pkg, act))

		return {"ok": True, "packages": packages}
	finally:
		frappe.set_user(prev)
