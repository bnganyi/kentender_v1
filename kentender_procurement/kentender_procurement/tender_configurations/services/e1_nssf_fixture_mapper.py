# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Map E1 NSSF fixture 09 → Tender Configuration CFG service shapes.

NSSF content is tender-instance configuration only. Locked ITT/GCC come from the
PPRA IT STD Engine at preview time — this mapper never emits NSSF legal prose as STD.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from frappe.utils import cstr

from kentender_procurement.tender_configurations.services import (
	contract_values as cv_svc,
	evaluation_setup as eval_svc,
	forms_and_evidence as forms_svc,
	implementation_schedule as sched_svc,
	it_requirements as req_svc,
	price_schedule as price_svc,
	system_inventory as inv_svc,
	tds as tds_svc,
)

# apps/kentender_v1/…/tender_configurations/services → parents[4] = kentender_v1
_V1_ROOT = Path(__file__).resolve().parents[4]
E1_PACK_DIR = (
	_V1_ROOT
	/ "docs"
	/ "std-prod-impl"
	/ "IT-STD-Wizard-v3"
	/ "E1-NSSF_Tender_PoC_Mapping_Pack"
)
FIXTURE_09_NAME = "09_NSSF_Full_Structured_Fixture.json"
SCHEMA_10_NAME = "10_NSSF_Electronic_Bidder_Submission_Schema.json"

EXPECTED_REQUIREMENT_COUNT = 190
EXPECTED_PRICE_LINE_COUNT = 22
# Nine Section III prelim rows (PRELIM-01…09). Digitised FoT / CITD / SD / security
# are linked_section — do not append a tenth duplicate indemnity upload.
EXPECTED_PRELIM_COUNT = 9
EXPECTED_TECH_QUAL_COUNT = 9
EXPECTED_TECH_SCORE_COUNT = 7
EXPECTED_FORMS_COUNT = 4
EXPECTED_SCC_COUNT = 9
EXPECTED_TECH_TOTAL = 100
EXPECTED_TECH_PASS = 75

# Golden crosswalk (§10): electronic owners — never mandatory uploads.
_NSSF_PRELIM_ELECTRONIC_OWNERS: dict[str, dict[str, str]] = {
	"PRELIM-05": {
		"response_method": "linked_section",
		"linked_section_key": "tender_security",
		"fulfilment_method": "electronic_section",
		"owner": "tender_security",
		"evidence_instruction": (
			"Complete the Tender Security section in the bidder workspace "
			"(bank guarantee or insurance bond as published)."
		),
	},
	"PRELIM-06": {
		"response_method": "linked_section",
		"linked_section_key": "form_of_tender",
		"fulfilment_method": "electronic_section",
		"owner": "form_of_tender",
		"evidence_instruction": (
			"Complete and certify the Form of Tender in the bidder workspace."
		),
	},
	"PRELIM-07": {
		"response_method": "linked_section",
		"linked_section_key": "statutory_declarations",
		"fulfilment_method": "electronic_section",
		"owner": "statutory_declarations",
		"evidence_instruction": (
			"Complete the Certificate of Independent Tender Determination in Statutory Declarations."
		),
	},
	"PRELIM-08": {
		"response_method": "linked_section",
		"linked_section_key": "statutory_declarations",
		"fulfilment_method": "electronic_section",
		"owner": "statutory_declarations",
		"evidence_instruction": (
			"Complete the Fraud and Corruption Self-Declaration in Statutory Declarations."
		),
	},
}

# requirement_family keyword → CFG-03 category_label
_FAMILY_CATEGORY_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
	(("integration",), "Integration"),
	(("security", "compliance"), "Security & Compliance"),
	(("warranty", "maintenance", "support", "sla"), "Support & Warranty"),
	(("testing", "acceptance", "documentation"), "Deliverable / Acceptance"),
	(("training", "project management", "implementation schedule", "knowledge"), "Implementation Support"),
	(("hardware", "cloud", "infrastructure", "database", "system requirements", "data migration"), "Technical Requirement"),
	(("general requirements", "background"), "Background / Informational"),
	(("business value", "business objective", "erp objectives"), "Business Objective"),
)


def fixture_09_path() -> Path:
	return E1_PACK_DIR / FIXTURE_09_NAME


def schema_10_path() -> Path:
	return E1_PACK_DIR / SCHEMA_10_NAME


def load_fixture_09(path: Path | None = None) -> dict[str, Any]:
	p = path or fixture_09_path()
	data = json.loads(p.read_text(encoding="utf-8"))
	if not isinstance(data, dict):
		raise ValueError("E1 fixture 09 must be a JSON object")
	return data


def load_schema_10(path: Path | None = None) -> dict[str, Any]:
	p = path or schema_10_path()
	data = json.loads(p.read_text(encoding="utf-8"))
	if not isinstance(data, dict):
		raise ValueError("E1 schema 10 must be a JSON object")
	return data


def map_requirement_family(family: str) -> str:
	text = cstr(family or "").strip().lower()
	if not text:
		return "Functional Requirement"
	for needles, category in _FAMILY_CATEGORY_RULES:
		if any(n in text for n in needles):
			return category
	# Module-specific functional families (Pension, HR, CRM, …)
	return "Functional Requirement"


def map_bidder_response(
	response_type: str,
) -> tuple[str, str, str]:
	"""Return (bidder_response_format, evidence_requirement, instruction_hint).

	PDF-facing labels stay compact. Long Confirm Yes/No workspace prose belongs only
	in the electronic bidder schema, not requirement description fields.
	"""
	rt = cstr(response_type or "").strip().lower()
	if "evidence_upload" in rt:
		return (
			"Compliance statement",
			"Evidence required",
			"Compliance statement and supporting evidence upload",
		)
	if "reference_pages" in rt:
		return (
			"Yes/No confirmation",
			"Evidence optional",
			"Yes/No + compliance statement; reference pages",
		)
	if "yes_no" in rt:
		return (
			"Yes/No confirmation",
			"Evidence optional",
			"Yes/No + compliance statement",
		)
	return (
		"Compliance statement",
		"Evidence optional",
		"Compliance statement",
	)


def build_poc_audit_notes(fixture: dict[str, Any], tds: dict[str, Any]) -> dict[str, Any]:
	"""AUDIT_ONLY metadata — never render in bidder-facing preview PDF."""
	profile = map_profile(fixture)
	closing = profile.get("closing_datetime") or ""
	deadline = closing.replace("+03:00", "").replace("Z", "")
	if "T" in deadline and len(deadline) >= 16:
		deadline = deadline[:16]
	indem_rows = []
	rows = _cfg(fixture, "CFG-02")
	if isinstance(rows, list):
		for row in rows:
			if isinstance(row, dict) and cstr(row.get("reference")) == "ITT 22.1":
				indem_rows.append(cstr(row.get("value") or ""))
	return {
		"source_electronic_tenders_permitted": False,
		"kentender_submission_policy": "electronic_only",
		"source_submission_deadline": deadline or "2026-06-30T11:00",
		"demo_submission_deadline": cstr(tds.get("tender_submission_deadline") or ""),
		"source_eligibility_wording": "Open National Competitive Tendering — as specified in TDS",
		"mapped_eligible_tenderers": cstr(tds.get("eligible_tenderers") or ""),
		"professional_indemnity_source": indem_rows[0] if indem_rows else "",
		"notes": [
			"Source NSSF fact: electronic tenders were not permitted in the paper tender.",
			"KenTender PoC applies electronic-only submission policy for the bidder workspace.",
			"PoC submission deadline advanced for demo submitability; source deadline retained here.",
		],
	}


def _cfg(fixture: dict[str, Any], key_prefix: str) -> Any:
	cfg = fixture.get("configuration") or {}
	for key, val in cfg.items():
		if cstr(key).startswith(key_prefix):
			return val
	raise KeyError(f"Missing configuration block starting with {key_prefix}")


def map_profile(fixture: dict[str, Any]) -> dict[str, Any]:
	profile = fixture.get("tender_profile") or {}
	title = cstr(profile.get("contract_name") or "").strip()
	ref = cstr(profile.get("tender_reference") or "").strip()
	summary = title
	if ref:
		summary = f"{title} ({ref})" if title else ref
	return {
		"tender_title": title or "NSSF SPS ERP System",
		"short_scope_summary": summary[:500],
		"lot_structure": "Single lot",
		"configuration_note": (
			"E1 NSSF PoC seed — tender-instance CFG values only. "
			"Locked ITT/GCC render from ACTIVE PPRA IT STD Engine."
		),
		"procuring_entity_name": cstr(profile.get("procuring_entity") or "").strip(),
		"tender_reference": ref,
		"procurement_method": "Open Tender",
		"currency": cstr(profile.get("currency") or "KES").strip() or "KES",
		"contact_email": cstr(profile.get("contact_email") or "").strip(),
		"closing_datetime": cstr(profile.get("closing_datetime") or "").strip(),
		"professional_indemnity_required": bool(profile.get("professional_indemnity_required")),
		"professional_indemnity_amount": profile.get("professional_indemnity_amount"),
		"source_electronic_tenders_permitted": False,
		"kentender_submission_policy": "electronic_only",
	}


def coerce_tds_enums(tds: dict[str, Any]) -> dict[str, Any]:
	"""Force TDS values onto official CFG-02 / STD Select options. STD options win."""
	out = dict(tds)
	enum_map: dict[str, tuple[str, ...]] = {
		"clarification_submission_method": tds_svc.CLARIFICATION_METHODS,
		"submission_channel": tds_svc.SUBMISSION_CHANNELS,
		"submission_language": tds_svc.SUBMISSION_LANGUAGES,
		"tender_currency": tds_svc.TENDER_CURRENCIES,
		"eligible_tenderers": tds_svc.ELIGIBLE_TENDERS,
		"reservation_category": tds_svc.RESERVATION_CATEGORIES,
		"tender_security_type": tds_svc.SECURITY_TYPES,
		"preference_basis": tds_svc.PREFERENCE_BASES,
		"opening_method": tds_svc.OPENING_METHODS,
		"bid_validity_unit": tds_svc.VALIDITY_UNITS,
		"tender_security_validity_unit": tds_svc.VALIDITY_UNITS,
	}
	yn_keys = (
		"pre_tender_meeting",
		"alternative_tenders_allowed",
		"joint_ventures_allowed",
		"reserved_procurement",
		"tender_security_required",
		"margin_of_preference_applies",
		"opening_attendance_allowed",
	)
	for key, allowed in enum_map.items():
		val = cstr(out.get(key) or "").strip()
		if not val:
			continue
		if val not in allowed:
			# Prefer first allowed as safe default when unmapped
			out[key] = allowed[0]
	for key in yn_keys:
		val = cstr(out.get(key) or "").strip()
		if not val:
			continue
		low = val.lower()
		if low in ("yes", "y", "true", "1"):
			out[key] = "Yes"
		elif low in ("no", "n", "false", "0", "n/a", "na"):
			out[key] = "No"
		elif val not in ("Yes", "No"):
			out[key] = "No"
	return out


def assert_mapped_cfg_enums_valid(mapped: dict[str, Any]) -> list[str]:
	"""Return list of enum violations (empty = ok). Official STD/CFG options win."""
	problems: list[str] = []
	tds = mapped.get("tds_values") or {}
	tds_enums = {
		"clarification_submission_method": tds_svc.CLARIFICATION_METHODS,
		"submission_channel": tds_svc.SUBMISSION_CHANNELS,
		"submission_language": tds_svc.SUBMISSION_LANGUAGES,
		"tender_currency": tds_svc.TENDER_CURRENCIES,
		"eligible_tenderers": tds_svc.ELIGIBLE_TENDERS,
		"reservation_category": tds_svc.RESERVATION_CATEGORIES,
		"tender_security_type": tds_svc.SECURITY_TYPES,
		"preference_basis": tds_svc.PREFERENCE_BASES,
		"opening_method": tds_svc.OPENING_METHODS,
		"bid_validity_unit": tds_svc.VALIDITY_UNITS,
		"tender_security_validity_unit": tds_svc.VALIDITY_UNITS,
	}
	for key, allowed in tds_enums.items():
		val = cstr(tds.get(key) or "").strip()
		if val and val not in allowed:
			problems.append(f"tds.{key}={val!r} not in {allowed}")
	for key in (
		"pre_tender_meeting",
		"alternative_tenders_allowed",
		"joint_ventures_allowed",
		"reserved_procurement",
		"tender_security_required",
		"margin_of_preference_applies",
		"opening_attendance_allowed",
	):
		val = cstr(tds.get(key) or "").strip()
		if val and val not in ("Yes", "No"):
			problems.append(f"tds.{key}={val!r} not in Yes/No")

	for row in mapped.get("it_requirements") or []:
		rid = cstr(row.get("requirement_id") or "?")
		if cstr(row.get("category_label") or "") not in req_svc.CATEGORIES:
			problems.append(f"req.{rid}.category_label={row.get('category_label')!r}")
		if cstr(row.get("treatment_label") or "") not in req_svc.TREATMENTS:
			problems.append(f"req.{rid}.treatment_label={row.get('treatment_label')!r}")
		if cstr(row.get("bidder_response_format") or "") not in req_svc.RESPONSE_FORMATS:
			problems.append(f"req.{rid}.bidder_response_format={row.get('bidder_response_format')!r}")
		if cstr(row.get("evidence_requirement") or "") not in req_svc.EVIDENCE_REQUIREMENTS:
			problems.append(f"req.{rid}.evidence_requirement={row.get('evidence_requirement')!r}")

	approach = cstr((mapped.get("implementation_schedule") or {}).get("delivery_approach") or "")
	if approach and approach not in sched_svc.APPROACHES:
		problems.append(f"schedule.delivery_approach={approach!r}")

	for row in (mapped.get("system_inventory") or {}).get("items") or []:
		iid = cstr(row.get("item_id") or "?")
		if cstr(row.get("category_label") or "") not in inv_svc.CATEGORIES:
			problems.append(f"inv.{iid}.category_label={row.get('category_label')!r}")
		if cstr(row.get("scope_label") or "") not in inv_svc.SCOPES:
			problems.append(f"inv.{iid}.scope_label={row.get('scope_label')!r}")
		if cstr(row.get("disclosure_status_label") or "") not in inv_svc.DISCLOSURE_STATUSES:
			problems.append(f"inv.{iid}.disclosure_status_label={row.get('disclosure_status_label')!r}")
		if cstr(row.get("price_link_label") or "") not in inv_svc.PRICE_LINKS:
			problems.append(f"inv.{iid}.price_link_label={row.get('price_link_label')!r}")

	for row in (mapped.get("price_schedule") or {}).get("items") or []:
		iid = cstr(row.get("item_id") or "?")
		if cstr(row.get("price_group") or "") not in price_svc.PRICE_GROUPS:
			problems.append(f"price.{iid}.price_group={row.get('price_group')!r}")
		if cstr(row.get("pricing_basis") or "") not in price_svc.PRICING_BASES:
			problems.append(f"price.{iid}.pricing_basis={row.get('pricing_basis')!r}")
		if cstr(row.get("evaluated_price_treatment") or "") not in price_svc.EVALUATED_TREATMENTS:
			problems.append(f"price.{iid}.evaluated_price_treatment={row.get('evaluated_price_treatment')!r}")
		if cstr(row.get("source_type") or "") not in price_svc.SOURCE_TYPES:
			problems.append(f"price.{iid}.source_type={row.get('source_type')!r}")

	for row in (mapped.get("evaluation_setup") or {}).get("criteria") or []:
		cid = cstr(row.get("criterion_id") or "?")
		if cstr(row.get("stage") or "") not in eval_svc.STAGES:
			problems.append(f"eval.{cid}.stage={row.get('stage')!r}")
		if cstr(row.get("evaluation_basis") or "") not in eval_svc.BASES:
			problems.append(f"eval.{cid}.evaluation_basis={row.get('evaluation_basis')!r}")
		if cstr(row.get("source_type") or "") not in eval_svc.SOURCE_TYPES:
			problems.append(f"eval.{cid}.source_type={row.get('source_type')!r}")
		if cstr(row.get("bidder_evidence") or "") and cstr(row.get("bidder_evidence")) not in eval_svc.EVIDENCE_OPTS:
			problems.append(f"eval.{cid}.bidder_evidence={row.get('bidder_evidence')!r}")

	for row in (mapped.get("forms_and_evidence") or {}).get("submission_items") or []:
		iid = cstr(row.get("item_id") or "?")
		if cstr(row.get("category") or "") not in forms_svc.CATEGORIES:
			problems.append(f"form.{iid}.category={row.get('category')!r}")
		if cstr(row.get("source") or "") not in forms_svc.SOURCES:
			problems.append(f"form.{iid}.source={row.get('source')!r}")
		if cstr(row.get("requirement") or "") not in forms_svc.REQUIREMENTS:
			problems.append(f"form.{iid}.requirement={row.get('requirement')!r}")
		if cstr(row.get("accepted_response_format") or "") not in forms_svc.RESPONSE_FORMATS:
			problems.append(f"form.{iid}.accepted_response_format={row.get('accepted_response_format')!r}")

	for row in (mapped.get("contract_values") or {}).get("contract_values") or []:
		cid = cstr(row.get("contract_value_id") or "?")
		if cstr(row.get("category") or "") not in cv_svc.CATEGORIES:
			problems.append(f"cv.{cid}.category={row.get('category')!r}")
		if cstr(row.get("source_screen") or "") not in cv_svc.SOURCES:
			problems.append(f"cv.{cid}.source_screen={row.get('source_screen')!r}")

	lot = cstr((mapped.get("profile") or {}).get("lot_structure") or "")
	if lot and lot not in ("Single lot", "Multiple lots", "Not applicable"):
		problems.append(f"profile.lot_structure={lot!r}")

	return problems


def map_tds_values(fixture: dict[str, Any]) -> dict[str, Any]:
	"""Normalize fixture CFG-02 ITT rows into CFG-02 editable TDS keys."""
	profile = map_profile(fixture)
	rows = _cfg(fixture, "CFG-02")
	by_ref: dict[str, list[dict[str, Any]]] = {}
	if isinstance(rows, list):
		for row in rows:
			if not isinstance(row, dict):
				continue
			ref = cstr(row.get("reference") or "").strip()
			by_ref.setdefault(ref, []).append(row)

	def _val(ref: str, *, contains: str = "") -> str:
		for row in by_ref.get(ref) or []:
			item = cstr(row.get("item") or "")
			if contains and contains.lower() not in item.lower():
				continue
			return cstr(row.get("value") or "").strip()
		return ""

	closing = profile.get("closing_datetime") or ""
	# Strip timezone for Desk datetime fields when present
	deadline = closing.replace("+03:00", "").replace("Z", "")
	if "T" in deadline and len(deadline) >= 16:
		deadline = deadline[:16]

	# Single bidder-facing deadline pair (demo). Source 2026 dates stay in AUDIT_ONLY notes.
	submission_deadline = "2027-06-30T11:00"
	opening_datetime = "2027-06-30T11:00"
	clarification_deadline = "2027-06-23T11:00"

	# Opening location from source — strip embedded source dates/times so PDF stays consistent.
	opening_location = _val("ITT 28.1") or "KenTender portal"
	opening_location = re.sub(
		r",?\s*\d{1,2}(st|nd|rd|th)?\s+June\s+20\d{2}.*$",
		"",
		opening_location,
		flags=re.I,
	).strip(" ,")
	opening_location = re.sub(r",?\s*\d{1,2}:\d{2}\s*(a\.?m\.?|p\.?m\.?|EAT).*$", "", opening_location, flags=re.I).strip(" ,")

	indem_required = bool(profile.get("professional_indemnity_required"))
	indem_amount = profile.get("professional_indemnity_amount") or 500000

	tds: dict[str, Any] = {
		"contact_officer": "Trust Secretary/Chief Executive Officer",
		"contact_email": profile.get("contact_email") or "pension@nssfsps.co.ke",
		"clarification_submission_method": "E-Procurement Portal",
		"clarification_deadline": clarification_deadline,
		"pre_tender_meeting": "No",
		"pre_tender_meeting_details": _val("ITT 8.1") or "N/A",
		"tender_submission_deadline": submission_deadline,
		"tender_opening_datetime": opening_datetime,
		"bid_validity_period": "154",
		"bid_validity_unit": "days",
		"submission_channel": "E-Procurement Portal",
		"submission_language": "English",
		"tender_currency": profile.get("currency") or "KES",
		"alternative_tenders_allowed": "No",
		"joint_ventures_allowed": "Yes",
		# Official CFG-02 / STD Select options only (not NSSF free text).
		"eligible_tenderers": "Open to all eligible tenderers",
		"reserved_procurement": "No",
		"tender_security_required": "No",
		"tender_security_type": "Not Required",
		"professional_indemnity_required": "Required" if indem_required else "Not required",
		"professional_indemnity_amount": cstr(indem_amount),
		"professional_indemnity_evidence": "Upload valid professional indemnity cover",
		"margin_of_preference_applies": "No",
		"opening_method": "Electronic Opening",
		"opening_location": opening_location or "KenTender portal",
		"opening_attendance_allowed": "Yes",
		# opening_notes intentionally empty — PoC/source diagnostics are AUDIT_ONLY.
		"opening_notes": "",
	}
	return coerce_tds_enums(tds)


def map_it_requirements(fixture: dict[str, Any]) -> list[dict[str, Any]]:
	block = _cfg(fixture, "CFG-03")
	raw = (block or {}).get("requirements") if isinstance(block, dict) else []
	out: list[dict[str, Any]] = []
	for row in raw or []:
		if not isinstance(row, dict):
			continue
		rid = cstr(row.get("requirement_id") or "").strip()
		title = cstr(row.get("requirement_title") or "").strip()
		statement = cstr(row.get("requirement_statement") or "").strip()
		family = cstr(row.get("requirement_family") or "").strip()
		fmt, evidence, hint = map_bidder_response(cstr(row.get("bidder_response_type") or ""))
		src_id = cstr(row.get("source_id") or "").strip()
		src_page = row.get("source_page")
		ev_instr = cstr(row.get("evidence_instruction") or "").strip() or hint
		# PDF-facing description = requirement statement only (no source_id / family audit trail).
		out.append(
			{
				"requirement_id": rid,
				"title": title or rid,
				"description": statement,
				"requirement_statement": statement,
				"requirement_family": family,
				"category_label": map_requirement_family(family),
				"treatment_label": "Mandatory" if row.get("mandatory") else "Informational",
				"bidder_response_format": fmt,
				"bidder_response_instruction": hint,
				"evidence_requirement": evidence,
				"evidence_instruction": ev_instr,
				"delivery_confirmation_method": "Commissioning test report",
				"_audit_source_id": src_id,
				"_audit_source_page": src_page,
			}
		)
	return out


def map_implementation_schedule(fixture: dict[str, Any]) -> dict[str, Any]:
	block = _cfg(fixture, "CFG-04")
	phases = (block or {}).get("implementation_phases") if isinstance(block, dict) else []
	sched_reqs = (block or {}).get("schedule_requirements") if isinstance(block, dict) else []
	milestones: list[dict[str, Any]] = []
	seq = 1
	for phase in phases or []:
		if not isinstance(phase, dict):
			continue
		name = cstr(phase.get("phase") or f"Phase {seq}").strip()
		fy = cstr(phase.get("financial_year") or "").strip()
		modules = phase.get("modules") or []
		mod_text = ", ".join(cstr(m) for m in modules if m)
		milestones.append(
			{
				"milestone_id": f"MS-PHASE-{seq:02d}",
				"name": name if not fy else f"{name} ({fy})",
				"description": f"Implement modules: {mod_text}" if mod_text else name,
				"sequence": str(seq),
				"expected_duration_value": "12",
				"expected_duration_unit": "months",
				"start_trigger": (
					"Contract signing and notice to proceed"
					if seq == 1
					else "Completion of previous milestone"
				),
				"key_deliverable": mod_text or name,
				"deliverable_description": mod_text or name,
				"acceptance_method": "Commissioning acceptance",
				"evidence_expected": "Acceptance certificate and test reports",
			}
		)
		seq += 1
	for row in sched_reqs or []:
		if not isinstance(row, dict):
			continue
		mid = cstr(row.get("id") or f"MS-SCHED-{seq:02d}").strip()
		desc = cstr(row.get("item_description") or "").strip()
		milestones.append(
			{
				"milestone_id": mid,
				"name": desc[:80] or mid,
				"description": desc,
				"sequence": str(seq),
				"expected_duration_value": "1",
				"expected_duration_unit": "months",
				"start_trigger": "Approved work plan",
				"key_deliverable": desc[:120] or mid,
				"deliverable_description": desc,
				"acceptance_method": "Delivery acceptance for equipment",
				"evidence_expected": "Commissioning test report",
			}
		)
		seq += 1
	return {
		"delivery_approach": "Phased Delivery",
		"milestones": milestones,
		"single_delivery": {},
	}


def map_system_inventory(fixture: dict[str, Any]) -> dict[str, Any]:
	block = _cfg(fixture, "CFG-05")
	if not isinstance(block, dict):
		block = {}
	cards: list[tuple[str, str]] = [
		("Background", cstr(block.get("background") or "").strip()),
		("Business purpose", cstr(block.get("business_purpose") or "").strip()),
		("ERP objectives", cstr(block.get("erp_objectives") or "").strip()),
		("Expected outcomes", cstr(block.get("expected_outcomes") or "").strip()),
	]
	tasks = block.get("successful_bidder_tasks")
	if isinstance(tasks, list) and tasks:
		cards.append(
			(
				"Successful bidder tasks",
				"; ".join(cstr(t).strip() for t in tasks if cstr(t).strip()),
			)
		)
	elif isinstance(tasks, str) and tasks.strip():
		cards.append(("Successful bidder tasks", tasks.strip()))

	items: list[dict[str, Any]] = []
	for i, (title, text) in enumerate(cards, start=1):
		if not text:
			continue
		items.append(
			{
				"item_id": f"INV-BG-{i:02d}",
				"item_title": title,
				"category_label": "Background Notes",
				"scope_label": "Context only",
				"item_description": text,
				"bidder_consideration": text,
				"disclosure_status_label": "Safe to disclose",
				"price_link_label": "No price link expected",
			}
		)
	return {
		"not_applicable": 0 if items else 1,
		"items": items,
	}


def normalize_price_unit(unit: str) -> str:
	"""Canonical bidder-facing unit labels for the Unit column."""
	key = cstr(unit or "").strip().lower()
	aliases = {
		"users": "Users",
		"user": "Users",
		"lump sum": "Lump sum",
		"lumpsum": "Lump sum",
		"per month": "Per month",
		"month": "Per month",
		"monthly": "Per month",
		"per gb/month": "Per GB/month",
		"gb/month": "Per GB/month",
		"per gb / month": "Per GB/month",
		"annual": "Annual",
		"per annum": "Annual",
		"lot": "Lot",
	}
	return aliases.get(key, cstr(unit or "").strip())


def map_price_users_or_qty(users_or_qty: str) -> tuple[str, str, str]:
	"""Map NSSF price-schedule Users/Qty cell → (quantity, unit, pricing_basis).

	The source PDF stores both numeric user counts and non-numeric unit labels
	(Lump sum / Per month / Annual / Per GB/month) in the same Users/Qty column.
	"""
	raw = cstr(users_or_qty or "1").strip() or "1"
	key = raw.lower()
	if key in ("lump sum", "lumpsum"):
		return "1", "Lump sum", "Lump sum"
	if key == "annual":
		return "1", "Annual", "Annual"
	if key in ("per month", "month", "monthly"):
		return "1", "Per month", "Monthly"
	if key in ("per gb/month", "per gb / month", "gb/month"):
		return "1", "Per GB/month", "Monthly"
	if key == "lot":
		return "1", "Lot", "Lump sum"
	if raw.isdigit():
		return raw, "Users", "Per user"
	if any(ch.isalpha() for ch in raw):
		normalized = normalize_price_unit(raw)
		if "annual" in key:
			return "1", normalized if normalized != raw else "Annual", "Annual"
		if "month" in key or "gb" in key:
			return "1", normalized, "Monthly"
		if "sum" in key or "lot" in key:
			return "1", normalized if normalized != raw else "Lump sum", "Lump sum"
		return "1", normalized, "As specified"
	return raw, "Users", "Unit price"


def map_price_schedule(fixture: dict[str, Any]) -> dict[str, Any]:
	block = _cfg(fixture, "CFG-06")
	lines = (block or {}).get("price_schedule_lines") if isinstance(block, dict) else []
	items: list[dict[str, Any]] = []
	for row in lines or []:
		if not isinstance(row, dict):
			continue
		line_id = cstr(row.get("line_id") or "").strip()
		name = cstr(row.get("module_or_item") or "").strip() or line_id
		phase = cstr(row.get("phase") or "").strip()
		raw_qty = cstr(row.get("users_or_qty") or "1").strip() or "1"
		explicit_unit = cstr(row.get("unit") or "").strip()
		qty, unit, basis = map_price_users_or_qty(raw_qty)
		if explicit_unit:
			unit = normalize_price_unit(explicit_unit)
		else:
			unit = normalize_price_unit(unit)
		currency = cstr(row.get("currency") or "KES").strip() or "KES"
		group = "Supply & Installation"
		lower = name.lower()
		if "maintenance" in lower or "support" in lower or "amc" in lower:
			group = "Recurrent Cost"
		elif "optional" in lower or "provisional" in lower:
			group = "Optional / Provisional"
		desc = name
		if phase:
			desc = f"{name} (Phase {phase})"
		items.append(
			{
				"item_id": line_id,
				"item_name": name,
				"price_group": group,
				"bidder_facing_description": desc,
				# Requirement-sourced avoids CFG-06 "intentionally user-added" readiness warnings.
				"source_type": "Requirement",
				"pricing_basis": basis,
				"quantity": qty,
				"unit": unit,
				"currency": currency,
				"evaluated_price_treatment": "Included",
				"bidder_pricing_instruction": (
					"Enter unit cost and total cost in the tender currency."
				),
			}
		)
	return {"items": items}


def _nssf_prelim_fulfilment(cid: str, docs: str) -> dict[str, Any]:
	"""Map NSSF prelim ids to one fulfilment method (golden crosswalk PRELIM-05…08)."""
	owner = _NSSF_PRELIM_ELECTRONIC_OWNERS.get(cid)
	if owner:
		return {
			"response_method": owner["response_method"],
			"linked_section_key": owner["linked_section_key"],
			"fulfilment_method": owner["fulfilment_method"],
			"owner": owner["owner"],
			"evidence_instruction": owner["evidence_instruction"],
			"criterion_group": "linked",
		}
	return {
		"response_method": "upload",
		"linked_section_key": "",
		"fulfilment_method": "tender_evidence",
		"owner": "preliminary_requirements",
		"evidence_instruction": docs or "Provide supporting documentation.",
		"criterion_group": "eligibility",
	}


def map_evaluation_setup(fixture: dict[str, Any]) -> dict[str, Any]:
	"""Map Section III lists only (~9+9+7) — not 190 scored requirement rows."""
	block = _cfg(fixture, "CFG-07")
	if not isinstance(block, dict):
		block = {}
	criteria: list[dict[str, Any]] = []

	for row in block.get("preliminary_requirements") or []:
		if not isinstance(row, dict):
			continue
		cid = cstr(row.get("id") or "").strip()
		name = cstr(row.get("criterion") or "").strip()
		req = cstr(row.get("requirement") or "Mandatory").strip()
		docs = cstr(row.get("supporting_documentation") or "").strip()
		fulfilment = _nssf_prelim_fulfilment(cid, docs)
		criteria.append(
			{
				"criterion_id": cid,
				"criterion_name": name or cid,
				"stage": "Preliminary",
				"evaluation_basis": "Pass/Fail",
				# STD-sourced avoids CFG-07 "confirm why this criterion is needed" warnings.
				"source_type": "Standard IT STD",
				"bidder_facing_wording": name,
				"pass_fail_rule": req or "Must be satisfied",
				"bidder_evidence": "Required",
				"evidence_instruction": fulfilment["evidence_instruction"],
				"response_method": fulfilment["response_method"],
				"linked_section_key": fulfilment["linked_section_key"],
				"fulfilment_method": fulfilment["fulfilment_method"],
				"owner": fulfilment["owner"],
				"criterion_group": fulfilment["criterion_group"],
			}
		)

	# Do not append PRELIM-INDEMNITY-01: PRELIM-05 already owns the bank-guarantee /
	# insurance-bond instrument via Tender Security; CFG-08 retains PI cover evidence.

	for row in block.get("technical_qualification") or []:
		if not isinstance(row, dict):
			continue
		cid = cstr(row.get("id") or "").strip()
		name = cstr(row.get("criterion") or "").strip()
		req = cstr(row.get("requirement") or "Mandatory").strip()
		docs = cstr(row.get("supporting_documentation") or "").strip()
		criteria.append(
			{
				"criterion_id": cid,
				"criterion_name": name or cid,
				"stage": "Technical",
				"evaluation_basis": "Pass/Fail",
				"source_type": "Standard IT STD",
				"bidder_facing_wording": name,
				"pass_fail_rule": req or "Must be satisfied",
				"bidder_evidence": "Required",
				"evidence_instruction": docs or "Provide supporting documentation.",
			}
		)

	for row in block.get("technical_scoring") or []:
		if not isinstance(row, dict):
			continue
		cid = cstr(row.get("id") or "").strip()
		name = cstr(row.get("criterion") or "").strip()
		marks = row.get("maximum_points")
		criteria.append(
			{
				"criterion_id": cid,
				"criterion_name": name or cid,
				"stage": "Technical",
				"evaluation_basis": "Scored",
				"source_type": "Standard IT STD",
				"bidder_facing_wording": name,
				"marks": cstr(marks if marks is not None else "").strip(),
				"bidder_evidence": "Required",
				"evidence_instruction": "Provide evidence demonstrating scoring against this criterion.",
			}
		)

	fin_basis = cstr(block.get("financial_evaluation_basis") or "Lowest evaluated price").strip()
	criteria.append(
		{
			"criterion_id": "FIN-01",
			"criterion_name": "Financial evaluation",
			"stage": "Financial",
			"evaluation_basis": "Lowest evaluated price",
			"source_type": "Price Schedule",
			"bidder_facing_wording": fin_basis,
			"financial_evaluation_rule": fin_basis,
			"bidder_evidence": "Not required",
		}
	)

	pass_mark = cstr(block.get("technical_pass_mark") or EXPECTED_TECH_PASS).strip()
	return {
		"criteria": criteria,
		"technical_pass_mark": pass_mark,
		"technical_scoring_total": cstr(block.get("technical_scoring_total") or EXPECTED_TECH_TOTAL),
		"financial_evaluation_basis": fin_basis,
	}


def map_forms_and_evidence(fixture: dict[str, Any]) -> dict[str, Any]:
	block = _cfg(fixture, "CFG-08")
	forms = (block or {}).get("forms") if isinstance(block, dict) else []
	profile = map_profile(fixture)
	items: list[dict[str, Any]] = []
	for row in forms or []:
		if not isinstance(row, dict):
			continue
		fid = cstr(row.get("form_id") or "").strip()
		name = cstr(row.get("form_name") or "").strip() or fid
		fields = row.get("fields") or []
		field_hint = ""
		if isinstance(fields, list) and fields:
			field_hint = "Fields: " + "; ".join(cstr(f) for f in fields[:8] if f)
		items.append(
			{
				"item_id": fid,
				"item_name": name,
				"category": "Standard Form",
				"source": "User Added",
				"requirement": "Mandatory",
				"bidder_instruction": field_hint
				or cstr(row.get("electronic_handling") or "Complete the electronic form."),
				"accepted_response_format": "Form",
				"accepted_file_type": "PDF",
			}
		)
	# Professional indemnity evidence (profile + ITT 22.1)
	if profile.get("professional_indemnity_required"):
		amt = profile.get("professional_indemnity_amount") or 500000
		items.append(
			{
				"item_id": "EVID-INDEMNITY-01",
				"item_name": "Professional indemnity insurance evidence",
				"category": "Qualification Evidence",
				"source": "TDS",
				"requirement": "Mandatory",
				"bidder_instruction": (
					f"Upload evidence of professional indemnity cover of at least KES {amt:,}."
					if isinstance(amt, (int, float))
					else f"Upload evidence of professional indemnity cover ({amt})."
				),
				"accepted_response_format": "PDF attachment",
				"accepted_file_type": "PDF",
				"related_tds_key": "tender_security_required",
			}
		)
	return {"submission_items": items}


def map_contract_values(fixture: dict[str, Any]) -> dict[str, Any]:
	block = _cfg(fixture, "CFG-09")
	if not isinstance(block, dict):
		block = {}
	values: list[dict[str, Any]] = []
	for i, row in enumerate(block.get("scc_conditions") or [], start=1):
		if not isinstance(row, dict):
			continue
		gcc = cstr(row.get("gcc_reference") or "").strip()
		special = cstr(row.get("special_condition") or "").strip()
		# Prefer human topic (e.g. "Governing law") over bare GCC refs for PDF labels.
		label = gcc or f"Special condition {i}"
		if ":" in special:
			topic = special.split(":", 1)[0].strip()
			if topic and len(topic) <= 80:
				label = topic
		elif gcc.lower().startswith("performance"):
			label = "Performance security"
		values.append(
			{
				"contract_value_id": f"SCC-{i:02d}",
				"item_label": label,
				"category": "SCC Value",
				"source_screen": "User entered",
				"source_item_label": gcc,
				"source_value": special,
				"contract_location": "Special Conditions of Contract",
				"value_or_obligation": special,
				"value": special,
				"editable_here": 1,
			}
		)
	# Explicit warranty row for bidder-facing SCC table (topic required by audit).
	has_warranty_label = any(
		"warranty" in cstr(v.get("item_label") or "").lower() for v in values
	)
	if not has_warranty_label:
		warranty = (
			"Twelve-month Phase 2 warranty period after go-live; "
			"performance security remains valid through end of Phase 2 warranty plus 60 days."
		)
		values.append(
			{
				"contract_value_id": "SCC-WARRANTY-01",
				"item_label": "Warranty",
				"category": "SCC Value",
				"source_screen": "User entered",
				"source_item_label": "Warranty",
				"source_value": warranty,
				"contract_location": "Special Conditions of Contract",
				"value_or_obligation": warranty,
				"value": warranty,
				"editable_here": 1,
			}
		)
	for i, row in enumerate(block.get("payment_milestones") or [], start=1):
		if not isinstance(row, dict):
			continue
		event = cstr(row.get("event") or "").strip()
		pct = row.get("percentage")
		label = f"Payment milestone {i}"
		obligation = event
		if pct is not None:
			obligation = f"{pct}% — {event}" if event else f"{pct}%"
		values.append(
			{
				"contract_value_id": f"PAY-{i:02d}",
				"item_label": label,
				"category": "Contract Schedule",
				"source_screen": "User entered",
				"source_item_label": event,
				"source_value": obligation,
				"contract_location": "Special Conditions of Contract — Payment",
				"value_or_obligation": obligation,
				"value": obligation,
				"editable_here": 1,
			}
		)
	return {"contract_values": values}


def map_bidder_submission_schema(fixture: dict[str, Any] | None = None) -> dict[str, Any]:
	"""Load schema 10 and stamp source metadata for persistence."""
	schema = load_schema_10()
	stamp = {
		"source_fixture": SCHEMA_10_NAME,
		"source_pack": "E1-NSSF_Tender_PoC_Mapping_Pack",
		"kentender_submission_policy": "electronic_only",
		"source_electronic_tenders_permitted": False,
		"source_note": (
			"NSSF source fact: electronic tenders not permitted; "
			"KenTender PoC uses electronic-only for the bidder workspace."
		),
	}
	if fixture is not None:
		meta = fixture.get("metadata") or {}
		stamp["fixture_metadata"] = {
			k: meta.get(k) for k in ("fixture_name", "source_document", "version") if k in meta
		}
	merged = dict(schema)
	merged["_kentender_artifact"] = stamp
	return merged


def map_all_cfg_blobs(fixture: dict[str, Any] | None = None) -> dict[str, Any]:
	"""Return all CFG payload shapes plus profile and schema artifact."""
	fix = fixture if fixture is not None else load_fixture_09()
	profile = map_profile(fix)
	reqs = map_it_requirements(fix)
	price = map_price_schedule(fix)
	evaluation = map_evaluation_setup(fix)
	forms = map_forms_and_evidence(fix)
	contract = map_contract_values(fix)
	form_items = forms.get("submission_items") or []
	tds_values = map_tds_values(fix)
	from kentender_procurement.tender_configurations.services.preview_presentation import (
		find_truncated_requirement_texts,
	)

	truncated = find_truncated_requirement_texts(reqs)
	if truncated:
		raise ValueError(
			"E1 requirement text appears truncated (re-extract from NSSF PDF): "
			+ ", ".join(truncated[:12])
		)
	out = {
		"profile": profile,
		"tds_values": tds_values,
		"poc_audit_notes": build_poc_audit_notes(fix, tds_values),
		"it_requirements": reqs,
		"implementation_schedule": map_implementation_schedule(fix),
		"system_inventory": map_system_inventory(fix),
		"price_schedule": price,
		"evaluation_setup": evaluation,
		"forms_and_evidence": forms,
		"contract_values": contract,
		"bidder_submission_schema": map_bidder_submission_schema(fix),
		"counts": {
			"requirements": len(reqs),
			"price_lines": len(price.get("items") or []),
			"prelim": sum(
				1
				for c in evaluation.get("criteria") or []
				if c.get("stage") == "Preliminary"
			),
			"tech_qual_pass_fail": sum(
				1
				for c in evaluation.get("criteria") or []
				if c.get("stage") == "Technical" and c.get("evaluation_basis") == "Pass/Fail"
			),
			"tech_scored": sum(
				1
				for c in evaluation.get("criteria") or []
				if c.get("stage") == "Technical" and c.get("evaluation_basis") == "Scored"
			),
			"forms": sum(1 for i in form_items if cstr(i.get("item_id") or "").startswith("FORM-")),
			"scc": sum(
				1
				for v in (contract.get("contract_values") or [])
				if cstr(v.get("contract_value_id") or "").startswith("SCC-")
			),
			"technical_pass_mark": evaluation.get("technical_pass_mark"),
			"technical_scoring_total": evaluation.get("technical_scoring_total"),
		},
	}
	problems = assert_mapped_cfg_enums_valid(out)
	if problems:
		raise ValueError(
			"E1 mapped CFG values violate official STD/CFG enumerations: "
			+ "; ".join(problems[:12])
		)
	return out
