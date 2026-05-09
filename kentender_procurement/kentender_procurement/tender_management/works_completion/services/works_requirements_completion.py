# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0220 — Works Requirements completion (pack payload + stable blocker codes).

Delegates persistence to ``StdInstanceWorksRequirementService`` and attachments to
``StdInstanceAttachmentService``. Section codes default to the POC STD section
``SPECIFICATIONS`` for component binding unless overridden.

Profile-driven HSE: tender ``tender_config_json`` (``_parse_cfg``) key
``WORKS.REQUIRE_HSE_REQUIREMENTS`` forces non-empty ``HSE_REQUIREMENTS`` row.
Site/env remain behind ``REQUIRE_SITE_INFORMATION`` / future profile keys.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.services.std_forms_boq_inspectors import _parse_cfg
from kentender_procurement.tender_management.std_instance.attachment import StdInstanceAttachmentService
from kentender_procurement.tender_management.std_instance.works_requirement import (
	StdInstanceWorksRequirementService,
)

from kentender_procurement.tender_management.works_completion.audit import (
	WORKS_ATTACHMENT_ADDED,
	WORKS_REQUIREMENTS_CHANGED,
	emit_works_completion_audit,
	emit_works_output_stale_if_new,
	stale_logical_outputs_snapshot,
)
from kentender_procurement.tender_management.works_completion.services.context_validator import (
	validate_works_completion_context,
)

SEVERITY_CRITICAL = "Critical"
SEVERITY_HIGH = "High"

# Nested section dict -> ``works_requirements.component_code``.
SECTION_PAYLOAD_TO_COMPONENT: dict[str, str] = {
	"specifications": "SPECIFICATIONS",
	"site_information": "SITE_INFORMATION",
	"hse_requirements": "HSE_REQUIREMENTS",
	"env_social_requirements": "ENV_SOCIAL_REQUIREMENTS",
	"quality_requirements": "QUALITY_REQUIREMENTS",
}

# Default STD section for Works narrative components (POC sections model).
COMPONENT_TO_SECTION_CODE: dict[str, str] = {
	"SPECIFICATIONS": "SPECIFICATIONS",
	"SITE_INFORMATION": "SPECIFICATIONS",
	"HSE_REQUIREMENTS": "SPECIFICATIONS",
	"ENV_SOCIAL_REQUIREMENTS": "SPECIFICATIONS",
	"QUALITY_REQUIREMENTS": "SPECIFICATIONS",
	"METHOD_STATEMENT": "SPECIFICATIONS",
	"WORK_PROGRAMME": "SPECIFICATIONS",
}

# Phase 1: do not block completion when site row absent unless enabled elsewhere.
REQUIRE_SITE_INFORMATION: bool = False

_CODE_MESSAGES: dict[str, str] = {
	"WORKS_SPECIFICATIONS_MISSING": _("Works specifications (structured summary) are required."),
	"WORKS_ATTACHMENT_NOT_SECTION_BOUND": _("A referenced attachment is missing or not section-bound for its component."),
	"WORKS_SITE_INFORMATION_MISSING": _("Site information is required for this tender."),
	"WORKS_HSE_REQUIREMENTS_MISSING": _("HSE requirements are required for this tender."),
	"WORKS_ENV_SOCIAL_REQUIREMENTS_MISSING": _("Environmental/social requirements are required for this tender."),
	"WORKS_QUALITY_REQUIREMENTS_MISSING": _("Quality requirements are required for this tender."),
	"WORKS_METHOD_STATEMENT_FLAG_MISSING": _("Method statement requirement flag must be resolved."),
	"WORKS_PROGRAMME_FLAG_MISSING": _("Work programme requirement flag must be resolved."),
	"WORKS_INSTANCE_NOT_FOUND": _("Tender STD Instance was not found."),
}


def _norm_cc(value: str | None) -> str:
	return (value or "").strip()


def _tender_cfg_for_instance(instance_name: str) -> dict[str, Any]:
	pt = frappe.db.get_value("Tender STD Instance", instance_name, "procurement_tender")
	if not pt or not frappe.db.exists("Procurement Tender", pt):
		return {}
	tender = frappe.get_doc("Procurement Tender", pt)
	return _parse_cfg(tender)


def _truthy_cfg(val: Any) -> bool:
	if isinstance(val, bool):
		return val
	s = str(val or "").strip().lower()
	return s in ("1", "true", "yes", "y", "on")


def _section_dict(payload: dict[str, Any], key: str) -> dict[str, Any] | None:
	raw = payload.get(key)
	if raw is None:
		return None
	if isinstance(raw, dict):
		return raw
	return None


def _drives_narrative_component() -> dict[str, bool]:
	return {
		"drives_bundle": True,
		"drives_dsm": True,
		"drives_dem": True,
		"drives_dcm": True,
	}


def _drives_flag_component() -> dict[str, bool]:
	"""Pack: method statement / programme flags — Bundle, DSM, DEM only."""
	return {
		"drives_bundle": True,
		"drives_dsm": True,
		"drives_dem": True,
		"drives_dcm": False,
	}


def _merge_structured_data(existing: str | None, attachment_codes: list[str]) -> str:
	prev: dict[str, Any] = {}
	if existing:
		try:
			prev = json.loads(existing)
			if not isinstance(prev, dict):
				prev = {}
		except Exception:
			prev = {}
	prev["attachment_codes"] = attachment_codes
	prev["wr_pack_version"] = 1
	return json.dumps(prev, sort_keys=True)


def _parse_attachment_codes(structured_data: str | None) -> list[str]:
	if not (structured_data or "").strip():
		return []
	try:
		obj = json.loads(structured_data)
		if isinstance(obj, dict):
			raw = obj.get("attachment_codes") or []
			if isinstance(raw, list):
				return [str(x).strip() for x in raw if str(x).strip()]
	except Exception:
		return []
	return []


def _attachments_satisfied(
	doc: Any,
	component_code: str,
	codes: list[str],
) -> bool:
	if not codes:
		return True
	sc_expected = COMPONENT_TO_SECTION_CODE.get(component_code, "SPECIFICATIONS")
	cc_n = _norm_cc(component_code)
	for code in codes:
		found = False
		for row in doc.section_attachments or []:
			if _norm_cc(row.attachment_code) != code:
				continue
			if not _norm_cc(row.section_code):
				return False
			if _norm_cc(row.section_code) != sc_expected:
				return False
			if _norm_cc(row.component_code) and _norm_cc(row.component_code) != cc_n:
				return False
			found = True
			break
		if not found:
			return False
	return True


def _compute_attachment_row_status(
	doc: Any,
	component_code: str,
	attachment_codes: list[str],
	attachment_required: bool,
) -> str:
	if not attachment_required:
		return "Not Required"
	if _attachments_satisfied(doc, component_code, attachment_codes):
		return "Complete"
	return "Missing"


def _save_narrative_section(
	instance_name: str,
	component_code: str,
	section: dict[str, Any],
	user: str | None,
) -> None:
	summary = section.get("structured_summary") or section.get("structuredSummary") or ""
	st = (summary if isinstance(summary, str) else str(summary)).strip()
	atts = section.get("attachments") or []
	codes: list[str] = []
	if isinstance(atts, list):
		codes = [str(x).strip() for x in atts if str(x).strip()]
	elif isinstance(atts, str) and atts.strip():
		codes = [atts.strip()]

	doc = frappe.get_doc("Tender STD Instance", instance_name)
	prev_data = ""
	for row in doc.works_requirements or []:
		if _norm_cc(row.component_code) == component_code:
			prev_data = row.structured_data or ""
			break

	data = _merge_structured_data(prev_data, codes)
	att_req = len(codes) > 0

	StdInstanceWorksRequirementService.set_works_requirement(
		instance_name,
		component_code,
		structured_text=st or None,
		structured_data=data,
		requirement_status="Complete" if st else "In Progress",
		attachment_required=att_req,
		attachment_status="Missing" if att_req else "Not Required",
		user=user,
		**_drives_narrative_component(),
	)

	doc2 = frappe.get_doc("Tender STD Instance", instance_name)
	att_stat = _compute_attachment_row_status(doc2, component_code, codes, att_req)
	row_after = _row_by_component(doc2, component_code)
	if row_after is not None and att_stat != (row_after.attachment_status or ""):
		StdInstanceWorksRequirementService.set_works_requirement(
			instance_name,
			component_code,
			structured_text=st or None,
			structured_data=data,
			requirement_status="Complete" if st else "In Progress",
			attachment_required=att_req,
			attachment_status=att_stat,
			user=user,
			**_drives_narrative_component(),
		)


def _save_boolean_flag(
	instance_name: str,
	component_code: str,
	value: bool,
	user: str | None,
) -> None:
	payload = json.dumps({"flag_resolved": True, "required": bool(value)}, sort_keys=True)
	txt = _("Resolved: {0}").format(_("Yes") if value else _("No"))
	StdInstanceWorksRequirementService.set_works_requirement(
		instance_name,
		component_code,
		structured_text=txt,
		structured_data=payload,
		requirement_status="Complete",
		attachment_required=False,
		attachment_status="Not Required",
		user=user,
		**_drives_flag_component(),
	)


def _row_by_component(doc: Any, component_code: str) -> Any | None:
	cc = _norm_cc(component_code)
	for row in doc.works_requirements or []:
		if _norm_cc(row.component_code) == cc:
			return row
	return None


def _validate_pack_rules(instance_name: str) -> list[dict[str, str]]:
	blockers: list[dict[str, str]] = []
	doc = frappe.get_doc("Tender STD Instance", instance_name)

	spec = _row_by_component(doc, "SPECIFICATIONS")
	if spec is None or not (spec.structured_text or "").strip():
		blockers.append(
			{
				"code": "WORKS_SPECIFICATIONS_MISSING",
				"message": str(_CODE_MESSAGES["WORKS_SPECIFICATIONS_MISSING"]),
				"severity": SEVERITY_CRITICAL,
			}
		)

	if REQUIRE_SITE_INFORMATION:
		si = _row_by_component(doc, "SITE_INFORMATION")
		if si is None or not (si.structured_text or "").strip():
			blockers.append(
				{
					"code": "WORKS_SITE_INFORMATION_MISSING",
					"message": str(_CODE_MESSAGES["WORKS_SITE_INFORMATION_MISSING"]),
					"severity": SEVERITY_HIGH,
				}
			)

	cfg = _tender_cfg_for_instance(instance_name)
	if _truthy_cfg(cfg.get("WORKS.REQUIRE_HSE_REQUIREMENTS")):
		hse = _row_by_component(doc, "HSE_REQUIREMENTS")
		if hse is None or not (hse.structured_text or "").strip():
			blockers.append(
				{
					"code": "WORKS_HSE_REQUIREMENTS_MISSING",
					"message": str(_CODE_MESSAGES["WORKS_HSE_REQUIREMENTS_MISSING"]),
					"severity": SEVERITY_HIGH,
				}
			)

	for comp, err_code in (
		("METHOD_STATEMENT", "WORKS_METHOD_STATEMENT_FLAG_MISSING"),
		("WORK_PROGRAMME", "WORKS_PROGRAMME_FLAG_MISSING"),
	):
		row = _row_by_component(doc, comp)
		if row is None:
			continue
		ok = False
		try:
			obj = json.loads(row.structured_data or "{}")
			if isinstance(obj, dict) and obj.get("flag_resolved") is True:
				ok = True
		except Exception:
			ok = False
		if not ok:
			blockers.append(
				{
					"code": err_code,
					"message": str(_CODE_MESSAGES[err_code]),
					"severity": SEVERITY_HIGH,
				}
			)

	for row in doc.works_requirements or []:
		cc = _norm_cc(row.component_code)
		if not cc:
			continue
		codes = _parse_attachment_codes(row.structured_data)
		if not codes:
			continue
		if int(row.attachment_required or 0) and not _attachments_satisfied(doc, cc, codes):
			blockers.append(
				{
					"code": "WORKS_ATTACHMENT_NOT_SECTION_BOUND",
					"message": str(_CODE_MESSAGES["WORKS_ATTACHMENT_NOT_SECTION_BOUND"]),
					"severity": SEVERITY_CRITICAL,
				}
			)
			break

	return blockers


class WorksRequirementsCompletionService:
	"""Pack-shaped Works requirements save/validate (delegates to STDINST services)."""

	@staticmethod
	def validate_works_requirements(instance_code: str) -> dict[str, Any]:
		"""Return ``{"valid": bool, "blockers": [{"code","message","severity"}, ...]}``."""
		code = _norm_cc(instance_code)
		if not code or not frappe.db.exists("Tender STD Instance", code):
			return {
				"valid": False,
				"blockers": [
					{
						"code": "WORKS_INSTANCE_NOT_FOUND",
						"message": str(_CODE_MESSAGES["WORKS_INSTANCE_NOT_FOUND"]),
						"severity": SEVERITY_CRITICAL,
					}
				],
			}

		std = StdInstanceWorksRequirementService.validate_works_requirements(code)
		blockers: list[dict[str, str]] = []

		if not std.get("ok", False):
			for bc in std.get("blocking") or []:
				blockers.append(
					{
						"code": "WORKS_ATTACHMENT_NOT_SECTION_BOUND",
						"message": str(_CODE_MESSAGES["WORKS_ATTACHMENT_NOT_SECTION_BOUND"]),
						"severity": SEVERITY_CRITICAL,
					}
				)
				break

		blockers.extend(_validate_pack_rules(code))

		# Dedupe by code (keep first message)
		seen: set[str] = set()
		out: list[dict[str, str]] = []
		for b in blockers:
			c = b.get("code") or ""
			if c and c in seen:
				continue
			if c:
				seen.add(c)
			out.append(b)

		return {"valid": not out, "blockers": out}

	@staticmethod
	def save_works_requirements(
		instance_code: str,
		payload: dict[str, Any],
		actor: str | None = None,
	) -> dict[str, Any]:
		"""Persist pack whitelist keys; raises ``ValidationError`` if context invalid."""
		code = _norm_cc(instance_code)
		ctx = validate_works_completion_context(code)
		if not ctx.get("valid"):
			msgs = ", ".join(str(b.get("message") or b.get("code")) for b in (ctx.get("blockers") or []))
			frappe.throw(
				_("Cannot save works requirements: {0}").format(msgs or _("invalid Works completion context")),
				title=_("Works requirements"),
			)

		user = actor or frappe.session.user
		raw = payload if isinstance(payload, dict) else {}

		stale_before = stale_logical_outputs_snapshot(code)

		for key, component in SECTION_PAYLOAD_TO_COMPONENT.items():
			sec = _section_dict(raw, key)
			if sec is not None:
				_save_narrative_section(code, component, sec, user)

		if "method_statement_required" in raw:
			v = raw["method_statement_required"]
			bval = bool(v) if isinstance(v, bool) else str(v).strip().lower() in ("1", "true", "yes", "y", "on")
			_save_boolean_flag(code, "METHOD_STATEMENT", bval, user)

		if "work_programme_required" in raw:
			v = raw["work_programme_required"]
			bval = bool(v) if isinstance(v, bool) else str(v).strip().lower() in ("1", "true", "yes", "y", "on")
			_save_boolean_flag(code, "WORK_PROGRAMME", bval, user)

		val = WorksRequirementsCompletionService.validate_works_requirements(code)
		if not val.get("valid"):
			parts = [str(b.get("message") or b.get("code")) for b in (val.get("blockers") or [])]
			frappe.throw(
				_("Works requirements validation failed: {0}").format("; ".join(parts)),
				title=_("Works requirements"),
			)

		emit_works_completion_audit(
			WORKS_REQUIREMENTS_CHANGED,
			code,
			details={"sections_touched": [k for k in SECTION_PAYLOAD_TO_COMPONENT if _section_dict(raw, k) is not None]},
			performed_by=user,
		)
		emit_works_output_stale_if_new(
			code, stale_before, source="works_requirements", performed_by=user
		)

		return {"ok": True, "instance_code": code}

	@staticmethod
	def attach_works_requirement_file(
		instance_code: str,
		component_code: str,
		*,
		file_name: str,
		file_reference: str,
		section_code: str | None = None,
		file_hash: str | None = None,
		actor: str | None = None,
	) -> Any:
		"""Attach a file to the STD section for ``component_code``; updates attachment row status when possible."""
		code = _norm_cc(instance_code)
		cc = _norm_cc(component_code)
		ctx = validate_works_completion_context(code)
		if not ctx.get("valid"):
			msgs = ", ".join(str(b.get("message") or b.get("code")) for b in (ctx.get("blockers") or []))
			frappe.throw(
				_("Cannot attach file: {0}").format(msgs or _("invalid Works completion context")),
				title=_("Works requirements"),
			)

		sc = _norm_cc(section_code) or COMPONENT_TO_SECTION_CODE.get(cc, "SPECIFICATIONS")
		user = actor or frappe.session.user

		stale_before = stale_logical_outputs_snapshot(code)

		StdInstanceAttachmentService.attach_file_to_section(
			code,
			sc,
			file_name.strip(),
			file_reference.strip(),
			component_code=cc,
			file_hash=file_hash,
			user=user,
			ignore_publication_lock=False,
		)

		doc = frappe.get_doc("Tender STD Instance", code)
		row = _row_by_component(doc, cc)
		if row is None:
			return doc

		codes = _parse_attachment_codes(row.structured_data)
		att_req = int(row.attachment_required or 0) > 0
		new_stat = _compute_attachment_row_status(doc, cc, codes, att_req)
		if new_stat != (row.attachment_status or ""):
			StdInstanceWorksRequirementService.set_works_requirement(
				code,
				cc,
				structured_text=row.structured_text,
				structured_data=row.structured_data,
				requirement_status=row.requirement_status or "In Progress",
				attachment_required=att_req,
				attachment_status=new_stat,
				drives_bundle=bool(row.drives_bundle),
				drives_dsm=bool(row.drives_dsm),
				drives_dem=bool(row.drives_dem),
				drives_dcm=bool(row.drives_dcm),
				user=user,
				ignore_publication_lock=False,
			)

		emit_works_completion_audit(
			WORKS_ATTACHMENT_ADDED,
			code,
			details={
				"component_code": cc,
				"section_code": sc,
				"file_name": file_name.strip(),
			},
			performed_by=user,
		)
		emit_works_output_stale_if_new(
			code, stale_before, source="works_requirement_attachment", performed_by=user
		)

		return frappe.get_doc("Tender STD Instance", code)
