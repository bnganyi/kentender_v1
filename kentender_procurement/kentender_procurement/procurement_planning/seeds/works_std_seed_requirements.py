# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 3 §16 — STD Template seed post-conditions after controlled loader import.

Used by ``seed_works_stdint_s01`` and tests. Does not import packages; assumes
``upsert_std_template`` (or equivalent) already ran.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint

from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE

# Status values the POC loader may set that still allow handoff when manifest permits tender creation.
_ALLOWED_STD_STATUS_FOR_TENDER = frozenset(("Imported", "POC Approved"))


def verify_std_template_doc3_section_16(template_code: str | None = None) -> str:
	"""Return ``STD Template`` name for ``template_code``; raise if doc 3 §16 is not satisfied.

	:param template_code: defaults to loader ``TEMPLATE_CODE`` (KE-PPRA-WORKS-BLDG-2022-04-POC).
	"""
	code = (template_code or TEMPLATE_CODE).strip()
	if not code:
		frappe.throw(_("STD template code is required."), title=_("WORKS STD §16"))

	if not frappe.db.exists("STD Template", {"template_code": code}):
		frappe.throw(
			_("STD Template {0} is missing (import via std_template_loader only).").format(code),
			title=_("WORKS STD §16"),
		)

	name = frappe.db.get_value("STD Template", {"template_code": code}, "name")
	row = frappe.db.get_value(
		"STD Template",
		name,
		[
			"package_hash",
			"procurement_category",
			"template_family",
			"status",
			"allowed_for_tender_creation",
			"package_version",
		],
		as_dict=True,
	)
	if not row:
		frappe.throw(_("STD Template {0} row incomplete.").format(code), title=_("WORKS STD §16"))

	if not (row.get("package_hash") or "").strip():
		frappe.throw(
			_("STD Template {0} must have package_hash populated (§16).").format(code),
			title=_("WORKS STD §16"),
		)

	cat = (row.get("procurement_category") or "").strip().upper()
	if cat != "WORKS":
		frappe.throw(
			_("STD Template {0} procurement_category must be WORKS (got {1}).").format(code, cat or "—"),
			title=_("WORKS STD §16"),
		)

	fam = (row.get("template_family") or "").upper()
	if "WORKS" not in fam:
		frappe.throw(
			_("STD Template {0} template_family must identify Works (got {1}).").format(
				code, row.get("template_family") or "—"
			),
			title=_("WORKS STD §16"),
		)

	st = (row.get("status") or "").strip()
	if st not in _ALLOWED_STD_STATUS_FOR_TENDER:
		frappe.throw(
			_("STD Template {0} status must be allowed for tender creation (§16); got {1}.").format(code, st or "—"),
			title=_("WORKS STD §16"),
		)

	if frappe.get_meta("STD Template").has_field("allowed_for_tender_creation"):
		if not cint(row.get("allowed_for_tender_creation")):
			frappe.throw(
				_("STD Template {0} must have allowed_for_tender_creation set (§16).").format(code),
				title=_("WORKS STD §16"),
			)

	if not (row.get("package_version") or "").strip():
		frappe.throw(
			_("STD Template {0} must have package_version populated (§16).").format(code),
			title=_("WORKS STD §16"),
		)

	return str(name)
