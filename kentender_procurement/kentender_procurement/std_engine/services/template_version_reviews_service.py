"""STD workbench: Template Version reviews & activation checklist (STD-CURSOR-1013)."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.std_engine.services.action_availability_service import (
	_perm_read,
	resolve_std_document,
)
from kentender_procurement.std_engine.services.template_version_mappings_service import (
	build_std_template_version_mappings_catalogue,
)
from kentender_procurement.std_engine.services.template_version_works_service import (
	build_std_template_version_works_configuration,
)


ACTIVATION_LEGAL_IMMUTABILITY_TEXT = str(
	_(
		"I understand this will activate a legally controlled STD template version. "
		"Active versions are immutable and may be used to create tender-specific STD instances."
	)
)


def _to_bool(value) -> bool:
	try:
		return bool(int(value or 0))
	except (TypeError, ValueError):
		return False


def _locked_rows(version_code: str) -> list[dict]:
	return frappe.get_all(
		"STD Section Definition",
		filters={"version_code": version_code, "editability": "Locked"},
		fields=["section_title", "section_code"],
		limit=500,
	)


def _blob(row: dict) -> str:
	return f"{row.get('section_title') or ''} {row.get('section_code') or ''}".lower()


def _roman_matches(sn: str | None, want: str) -> bool:
	u = (sn or "").strip().upper()
	w = want.upper()
	if not u or not w:
		return False
	if u == w:
		return True
	return u.startswith(w + ".") or u.startswith(w + "-")


def _has_section_iii(version_code: str) -> bool:
	for s in frappe.get_all(
		"STD Section Definition",
		filters={"version_code": version_code},
		fields=["section_number"],
		limit=500,
	):
		if _roman_matches(str(s.get("section_number") or ""), "III"):
			return True
	return False


def _dom_params_tds_scoped(version_code: str) -> tuple[bool, str]:
	rows = frappe.get_all(
		"STD Parameter Definition",
		filters={"version_code": version_code, "drives_dom": 1},
		fields=["parameter_code", "label", "parameter_group"],
	)
	if not rows:
		return True, str(_("No DOM-driving parameters; TDS scoping not applicable."))
	bad: list[str] = []
	for r in rows:
		blob = f"{r.get('parameter_code') or ''} {r.get('label') or ''} {r.get('parameter_group') or ''}".lower()
		if "tds" not in blob and "submission" not in blob and "deadline" not in blob and "opening" not in blob:
			bad.append(str(r.get("parameter_code") or ""))
	if bad:
		return False, str(_("DOM-driving parameters should be TDS-scoped (codes: {0}).").format(", ".join(bad[:5])))
	return True, str(_("DOM-driving parameters are TDS-scoped."))


def _dcm_params_scc_scoped(version_code: str) -> tuple[bool, str]:
	rows = frappe.get_all(
		"STD Parameter Definition",
		filters={"version_code": version_code, "drives_dcm": 1},
		fields=["parameter_code", "label", "parameter_group"],
	)
	if not rows:
		return True, str(_("No DCM-driving parameters; SCC scoping not applicable."))
	bad: list[str] = []
	for r in rows:
		blob = f"{r.get('parameter_code') or ''} {r.get('label') or ''} {r.get('parameter_group') or ''}".lower()
		if "scc" not in blob and "contract" not in blob and "particular" not in blob:
			bad.append(str(r.get("parameter_code") or ""))
	if bad:
		return False, str(_("DCM-driving parameters should be SCC/contract-scoped (codes: {0}).").format(", ".join(bad[:5])))
	return True, str(_("DCM-driving parameters are SCC/contract-scoped."))


def build_std_template_version_reviews_approval(version_code: str, actor: str | None = None) -> dict[str, object]:
	"""Return review statuses, activation checklist, and activation-readiness hints."""
	user = (actor or "").strip() or frappe.session.user
	if user in (None, "", "Guest"):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	code = (version_code or "").strip()
	if not code:
		return {"ok": False, "error": "invalid", "message": str(_("Version code is required."))}

	resolved = resolve_std_document("Template Version", code)
	if not resolved:
		return {
			"ok": False,
			"error": "not_found",
			"message": str(_("No document matches this version code.")),
			"version_code": code,
		}
	doctype, name, doc = resolved
	if doctype != "STD Template Version":
		return {"ok": False, "error": "invalid", "message": str(_("Not a template version."))}
	if not _perm_read(doctype, name, user):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	status = str(doc.get("version_status") or "")
	immutable = _to_bool(doc.get("immutable_after_activation"))
	read_only = status == "Active" and immutable

	template_code = str(doc.get("template_code") or "")
	family = (
		frappe.db.get_value(
			"STD Template Family",
			template_code,
			["family_status", "is_active_family", "template_title"],
			as_dict=True,
		)
		if template_code
		else None
	)
	family_active = bool(family and str(family.get("family_status") or "") == "Active" and _to_bool(family.get("is_active_family")))

	mandatory_count = frappe.db.count("STD Section Definition", {"version_code": code, "is_mandatory": 1})
	section_count = frappe.db.count("STD Section Definition", {"version_code": code})
	mandatory_sections_ok = mandatory_count > 0 and section_count > 0

	locked = _locked_rows(code)
	itt_locked = any("itt" in _blob(r) for r in locked)
	gcc_locked = any("gcc" in _blob(r) for r in locked)

	tds_ok, tds_detail = _dom_params_tds_scoped(code)
	scc_ok, scc_detail = _dcm_params_scc_scoped(code)

	map_cat = build_std_template_version_mappings_catalogue(code, actor=user)
	mappings_ok = bool(map_cat.get("ok")) and not (map_cat.get("missing_coverage") or [])
	hi = (map_cat.get("highlights") or {}) if map_cat.get("ok") else {}
	section_iii_dem_rows = hi.get("section_iii_dem") or []
	has_iii = _has_section_iii(code)
	iii_mappings_ok = (not has_iii) or bool(section_iii_dem_rows)

	forms_count = frappe.db.count("STD Form Definition", {"version_code": code})
	forms_ok = forms_count > 0

	works = build_std_template_version_works_configuration(code, actor=user)
	is_works = str(doc.get("procurement_category") or "").strip() == "Works"
	works_profile = (works.get("works_profile") or {}) if works.get("ok") else {}
	works_ok = (not is_works) or bool(works_profile.get("profile_code"))
	boq_required = is_works and _to_bool(works_profile.get("requires_boq"))
	boq_def = (works.get("boq_definition") or {}) if works.get("ok") else {}
	boq_ok = (not boq_required) or bool(boq_def.get("boq_definition_code"))

	readiness_ok = True
	readiness_detail = str(_("Readiness configuration snapshot is clear."))
	if works.get("ok"):
		rules = works.get("readiness_rules") or []
		readiness_ok = all(bool(r.get("status")) for r in rules)
		if not readiness_ok:
			readiness_detail = str(_("Complete Works profile, BOQ, and components readiness on the Works Configuration tab."))

	legal = str(doc.get("legal_review_status") or "")
	policy = str(doc.get("policy_review_status") or "")
	structure = str(doc.get("structure_validation_status") or "")

	legal_cleared = legal in ("Approved", "Not Required")
	policy_cleared = policy in ("Approved", "Not Required")
	structure_ok = structure == "Pass"

	items: list[dict[str, object]] = [
		{
			"id": "family_active",
			"label": str(_("Template family is active")),
			"pass": family_active,
			"detail": str(_("Family: {0}").format(template_code)) if template_code else "",
		},
		{
			"id": "mandatory_sections_present",
			"label": str(_("Mandatory sections present")),
			"pass": mandatory_sections_ok,
			"detail": str(_("{0} mandatory section(s) on {1} total.").format(mandatory_count, section_count)),
		},
		{
			"id": "itt_locked",
			"label": str(_("ITT section locked (standard text)")),
			"pass": itt_locked,
			"detail": str(_("Locked sections detected for ITT.")) if itt_locked else str(_("No ITT lock match in locked sections.")),
		},
		{
			"id": "gcc_locked",
			"label": str(_("GCC section locked (standard text)")),
			"pass": gcc_locked,
			"detail": str(_("Locked sections detected for GCC.")) if gcc_locked else str(_("No GCC lock match in locked sections.")),
		},
		{
			"id": "tds_parameter_only",
			"label": str(_("TDS / DOM parameters scoped")),
			"pass": tds_ok,
			"detail": tds_detail,
		},
		{
			"id": "scc_parameter_only",
			"label": str(_("SCC / DCM parameters scoped")),
			"pass": scc_ok,
			"detail": scc_detail,
		},
		{
			"id": "section_iii_mappings_complete",
			"label": str(_("Section III evaluation (DEM) mappings present")),
			"pass": iii_mappings_ok,
			"detail": str(_("Section III present: {0}").format(_("yes") if has_iii else _("no"))),
		},
		{
			"id": "forms_complete",
			"label": str(_("Forms defined")),
			"pass": forms_ok,
			"detail": str(_("{0} form(s).").format(forms_count)),
		},
		{
			"id": "works_requirements_configured",
			"label": str(_("Works requirements configured")),
			"pass": works_ok,
			"detail": str(_("Works category requires applicability profile.")) if is_works else str(_("Not a Works template.")),
		},
		{
			"id": "boq_configured",
			"label": str(_("BOQ configured where required")),
			"pass": boq_ok,
			"detail": str(_("BOQ required by profile.")) if boq_required else str(_("BOQ not required.")),
		},
		{
			"id": "extraction_mappings_complete",
			"label": str(_("Extraction mappings complete (no gaps)")),
			"pass": mappings_ok,
			"detail": str(_("Open Mappings tab to resolve gaps.")) if not mappings_ok else str(_("No mapping gaps detected.")),
		},
		{
			"id": "readiness_rules_complete",
			"label": str(_("Works readiness snapshot complete")),
			"pass": readiness_ok,
			"detail": readiness_detail,
		},
		{
			"id": "legal_review_cleared",
			"label": str(_("Legal review cleared")),
			"pass": legal_cleared,
			"detail": legal,
		},
		{
			"id": "policy_review_cleared",
			"label": str(_("Policy review cleared")),
			"pass": policy_cleared,
			"detail": policy,
		},
		{
			"id": "structure_validation_passed",
			"label": str(_("Structure validation passed")),
			"pass": structure_ok,
			"detail": structure,
		},
	]

	checklist_all_pass = all(bool(x.get("pass")) for x in items)

	transition_reviews_ok = legal_cleared and policy_cleared and structure_ok
	can_activate_transition = status == "Approved" and transition_reviews_ok and checklist_all_pass

	ui_block_reasons: list[str] = []
	if read_only:
		ui_block_reasons.append(str(_("This version is already active and immutable.")))
	if status != "Approved":
		ui_block_reasons.append(str(_("Template version status must be Approved before activation.")))
	if not transition_reviews_ok:
		ui_block_reasons.append(str(_("Legal review, policy review, and structure validation must be cleared.")))
	if not checklist_all_pass:
		ui_block_reasons.append(str(_("Activation checklist still has failing items.")))
	activation_ui_block_reason = " ".join(ui_block_reasons) if ui_block_reasons else ""

	returned: list[dict[str, str]] = []
	if legal == "Returned":
		returned.append(
			{
				"source": "legal",
				"status": legal,
				"detail": str(_("Legal review was returned; update structure or mappings and resubmit via Desk workflow.")),
			}
		)
	if policy == "Returned":
		returned.append(
			{
				"source": "policy",
				"status": policy,
				"detail": str(_("Policy review was returned; resolve policy findings before approval.")),
			}
		)

	return {
		"ok": True,
		"version_code": code,
		"read_only": read_only,
		"review_summary": {
			"version_status": status,
			"legal_review_status": legal,
			"policy_review_status": policy,
			"structure_validation_status": structure,
		},
		"family": {
			"template_code": template_code,
			"family_title": (family or {}).get("template_title") if family else None,
			"family_status": (family or {}).get("family_status") if family else None,
			"is_active_family": _to_bool((family or {}).get("is_active_family")) if family else False,
			"family_active": family_active,
		},
		"governance_note": str(
			_(
				"Governance approval and version activation are executed through controlled Desk workflows "
				"and `transition_std_object` (e.g. STD_VERSION_ACTIVATE). This tab is read-only visibility."
			)
		),
		"returned_corrections": returned,
		"activation_checklist": items,
		"checklist_all_pass": checklist_all_pass,
		"activation_legal_immutability_text": ACTIVATION_LEGAL_IMMUTABILITY_TEXT,
		"activation_gates": {
			"transition_reviews_ok": transition_reviews_ok,
			"checklist_all_pass": checklist_all_pass,
			"can_activate_transition": can_activate_transition and not read_only,
			"version_status": status,
		},
		"activation_ui_block_reason": activation_ui_block_reason,
		"activation_hint": str(
			_("Use Desk state transitions on this template version when you have authority (e.g. Approve, then Activate).")
		),
	}
