# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-07 — New Tender Wizard (doc 9 §15 / doc 6 §26).

Lists selectable STD template rows for a package (excluding deprecated version
codes) and completes **create draft + bind STD** in one server call.

Tests: ``tender_management.tests.test_p9_07_new_tender_wizard``.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr

from kentender_procurement.tender_management.services.bind_tender_std_instance import (
	bind_tender_std_instance,
)
from kentender_procurement.tender_management.services.create_tender_from_package import (
	create_tender_from_package,
)
from kentender_procurement.tender_management.services.tm2_std_adapter import (
	get_eligible_std_templates,
	load_procurement_package_by_code,
)
from kentender_procurement.tender_management.services.tm2_workbench_actor_context import (
	tm2_workbench_desk_security_context,
)

# Doc 9 §15.4 — fixture explicitly excludes this deprecated Works version label.
_DEPRECATED_STD_TEMPLATE_VERSION_CODES: frozenset[str] = frozenset({"STDTV-WORKS-2020-REV1"})


def _works_building_civil_profile_requirements(profile_code: str) -> dict[str, bool]:
	"""Doc 9 §15.5 — seven activated requirement flags for the canonical Works profile."""
	pc = (profile_code or "").strip().upper()
	if "WORKS-PROFILE-BUILDING-CIVIL" in pc:
		return {
			"boq": True,
			"drawings": True,
			"site_information": True,
			"key_personnel": True,
			"equipment": True,
			"hse": True,
			"environmental_and_social": True,
		}
	return {
		"boq": True,
		"drawings": False,
		"site_information": False,
		"key_personnel": False,
		"equipment": False,
		"hse": False,
		"environmental_and_social": False,
	}


def list_new_tender_wizard_std_options(actor: str, package_code: str) -> dict[str, Any]:
	"""Return enriched STD rows for wizard steps 3–4 (version + profile + requirements)."""
	act = cstr(actor or "").strip()
	pc = cstr(package_code or "").strip()
	if not act or not frappe.db.exists("User", act):
		return {"ok": False, "message": _("A valid user is required.")}
	if not pc:
		return {"ok": False, "message": _("Package code is required.")}
	if not frappe.has_permission("Procurement Package", "read", user=act):
		return {"ok": False, "message": _("You do not have permission to read procurement packages.")}

	pkg = load_procurement_package_by_code(pc)
	if not pkg:
		return {"ok": False, "message": _("Procurement package was not found.")}

	if not frappe.has_permission("Procurement Package", "read", doc=pkg, user=act):
		return {"ok": False, "message": _("You are not permitted to read this procurement package.")}

	business_code = cstr(pkg.get("package_code") or pkg.name).strip()
	prev = frappe.session.user
	try:
		frappe.set_user(act)
		raw = get_eligible_std_templates(business_code)
		options: list[dict[str, Any]] = []
		for row in raw:
			std_name = cstr(row.get("std_template") or "").strip()
			if not std_name or not frappe.db.exists("STD Template", std_name):
				continue
			st_row = (
				frappe.db.get_value(
					"STD Template",
					std_name,
					[
						"template_code",
						"template_name",
						"lifecycle_status",
						"template_version",
						"version_label",
						"procurement_method_profile",
						"active_profile_key",
						"template_family",
					],
					as_dict=True,
				)
				or {}
			)
			ver = cstr(st_row.get("template_version") or st_row.get("version_label") or "").strip()
			if ver in _DEPRECATED_STD_TEMPLATE_VERSION_CODES:
				continue
			prof = cstr(st_row.get("procurement_method_profile") or "").strip()
			if not prof:
				prof = cstr(st_row.get("active_profile_key") or "").strip()
			if not prof:
				prof = cstr(st_row.get("template_family") or "").strip()
			if not prof:
				prof = "DEFAULT"
			if not ver:
				continue
			options.append(
				{
					"std_template": std_name,
					"template_code": cstr(row.get("template_code") or st_row.get("template_code") or "").strip(),
					"template_name": cstr(row.get("template_name") or st_row.get("template_name") or "").strip(),
					"template_version_code": ver,
					"applicability_profile_code": prof,
					"lifecycle_status": cstr(row.get("lifecycle_status") or st_row.get("lifecycle_status") or "").strip(),
					"profile_requirements": _works_building_civil_profile_requirements(prof),
				}
			)
		return {
			"ok": True,
			"package_code": business_code,
			"procurement_package": pkg.name,
			"options": options,
		}
	finally:
		frappe.set_user(prev)


def submit_new_tender_wizard_completion(
	actor: str,
	package_code: str,
	preferred_std_template: str,
	std_template_version_code: str,
	applicability_profile_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Create a Draft ``TM2 Tender`` from ``package_code`` then bind STD (P9-07 step 5)."""
	ctx = dict(context or ())
	ctx.update(tm2_workbench_desk_security_context(actor))
	ctx["preferred_std_template"] = cstr(preferred_std_template or "").strip()
	out_c = create_tender_from_package(actor, package_code, context=ctx)
	if not out_c.get("ok"):
		return out_c
	tcode = cstr(out_c.get("tender_code") or "").strip()
	if not tcode:
		return {"ok": False, "message": _("Create succeeded but tender code is missing.")}

	out_b = bind_tender_std_instance(
		actor,
		tcode,
		std_template_version_code,
		applicability_profile_code,
		context=tm2_workbench_desk_security_context(actor),
	)
	if not out_b.get("ok"):
		frappe.db.rollback()
		return {
			**out_b,
			"tender_code": tcode,
			"tm2_tender": out_c.get("tm2_tender"),
			"wizard_create_succeeded": True,
		}
	return {
		"ok": True,
		"tender_code": tcode,
		"tm2_tender": out_c.get("tm2_tender"),
		"tm2_tender_timeline": out_c.get("tm2_tender_timeline"),
		"tender_std_instance": out_b.get("tender_std_instance"),
		"tm2_tender_std_binding": out_b.get("tm2_tender_std_binding"),
		"binding_code": out_b.get("binding_code"),
	}
