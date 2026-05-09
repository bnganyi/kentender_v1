# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0110 — WorksContextValidator.

Validate that a ``Tender STD Instance`` may enter Works tender-stage completion.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.services.std_forms_boq_inspectors import (
	_parse_cfg,
)
from kentender_procurement.tender_management.std_instance.binding import (
	TenderStdBindingService,
)
from kentender_procurement.tender_management.std_instance.publication_lock import (
	EDITABLE_INSTANCE_STATUSES,
)

WORKS_CATEGORY = "WORKS"
BOQ_REQUIRED_KEY = "WORKS.BOQ_REQUIRED"

_BLOCKERS: dict[str, str] = {
	"WORKS_INSTANCE_NOT_FOUND": _("Tender STD Instance was not found."),
	"WORKS_INSTANCE_NOT_TENDER_BOUND": _("This STD Instance is not bound to a procurement tender."),
	"WORKS_CATEGORY_INVALID": _("Works completion applies only when Procurement Category is Works."),
	"WORKS_PROFILE_INVALID": _("Template version or applicability profile binding is incomplete or incompatible."),
	"WORKS_TEMPLATE_LINEAGE_MISSING": _("STD Template version or profile does not match this instance binding."),
	"WORKS_INSTANCE_LOCKED": _("This STD Instance cannot be edited in its current status."),
	"WORKS_BOQ_REQUIRED_BY_PROFILE": _("Tender configuration requires a Works BoQ profile but the instance is not Works category."),
}


def _blocker(code: str, message: str | None = None) -> dict[str, str]:
	return {"code": code, "message": message or str(_BLOCKERS.get(code, code))}


def _result(valid: bool, blockers: list[dict[str, str]]) -> dict[str, Any]:
	return {"valid": valid, "blockers": blockers}


def _truthy_cfg(cfg: dict[str, Any], key: str) -> bool:
	v = cfg.get(key)
	if v in (1, True, "1", "true", "True", "yes", "YES"):
		return True
	if isinstance(v, str) and v.strip().lower() in ("true", "yes", "1"):
		return True
	return False


def validate_works_completion_context(
	instance_code: str,
	*,
	allow_return_from_approval_lock: bool = False,
) -> dict[str, Any]:
	"""Return ``{"valid": bool, "blockers": [{"code", "message"}, ...]}`` per WORKS-COMP-0110.

	:param allow_return_from_approval_lock: When ``True``, skip ``WORKS_INSTANCE_LOCKED`` only if
		the instance is ``Locked for Approval`` so ``return_to_preparation`` can re-validate
		tender/Works binding before transitioning back to ``In Configuration``.
	"""
	code = (instance_code or "").strip()
	if not code or not frappe.db.exists("Tender STD Instance", code):
		return _result(False, [_blocker("WORKS_INSTANCE_NOT_FOUND")])

	inst = frappe.get_doc("Tender STD Instance", code)
	pt = (inst.get("procurement_tender") or "").strip()
	if not pt or not frappe.db.exists("Procurement Tender", pt):
		return _result(False, [_blocker("WORKS_INSTANCE_NOT_TENDER_BOUND")])

	tender = frappe.get_doc("Procurement Tender", pt)
	cfg = _parse_cfg(tender)

	icat = (inst.get("procurement_category") or "").strip()
	if icat != WORKS_CATEGORY:
		if _truthy_cfg(cfg, BOQ_REQUIRED_KEY):
			return _result(False, [_blocker("WORKS_BOQ_REQUIRED_BY_PROFILE")])
		return _result(False, [_blocker("WORKS_CATEGORY_INVALID")])

	tv = (inst.get("template_version_code") or "").strip()
	ap = (inst.get("applicability_profile_code") or "").strip()
	if not tv or not ap:
		return _result(False, [_blocker("WORKS_PROFILE_INVALID")])

	st = (tender.get("std_template") or "").strip()
	if not st or not frappe.db.exists("STD Template", st):
		return _result(False, [_blocker("WORKS_TEMPLATE_LINEAGE_MISSING")])

	tpl_cat = (frappe.db.get_value("STD Template", st, "procurement_category") or "").strip()
	if tpl_cat and tpl_cat != WORKS_CATEGORY:
		return _result(False, [_blocker("WORKS_PROFILE_INVALID")])

	try:
		version_code, profile_code = TenderStdBindingService._codes_from_std_template(st)
	except Exception:
		return _result(False, [_blocker("WORKS_TEMPLATE_LINEAGE_MISSING")])

	if version_code.strip() != tv or profile_code.strip() != ap:
		return _result(False, [_blocker("WORKS_TEMPLATE_LINEAGE_MISSING")])

	status = (inst.get("instance_status") or "").strip()
	if status not in EDITABLE_INSTANCE_STATUSES:
		if allow_return_from_approval_lock and status == "Locked for Approval":
			pass
		else:
			return _result(False, [_blocker("WORKS_INSTANCE_LOCKED")])

	return _result(True, [])
