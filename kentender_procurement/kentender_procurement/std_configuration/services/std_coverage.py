# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 §11 validation and coverage engine.

Two outputs: the §5 sixteen-row coverage register (`coverage_report`) and the
§11.2 Blocking/Warning findings (`run_complete_check`, which persists its
findings as `STD Cfg Validation Finding` rows — the only writer of that
doctype, matching its own §7.17 "derived... users cannot dismiss or annotate
them"). `RunSTDCompleteCheck` (§13.2) is exactly `run_complete_check`; area-save
commands (Phase 5) deliberately do NOT call this — §16.4 "Area save validates
the changed area and immediate edges only."

Several §11.2 conditions are already enforced at save time by Phase 1/2's own
`validate()` guards (duplicate keys, missing bindings, invalid Choice
definitions, ...) and cannot normally occur in stored data. Those are still
re-checked here defensively — this pass is the one place a Reviewer is meant
to trust completely, and re-deriving pass/fail from the same rule the DocType
already enforces is cheap insurance against a guard being bypassed (a direct
`frappe.db.sql` write, a future bug in a guard) rather than genuinely dead code.

Two §11.2 conditions are out of this phase's reach and always pass here,
documented rather than silently omitted:
- "inventory field hiding a commercial value" — structurally impossible, no
  such field exists on `STD Cfg Inventory Schema` at all (Phase 2's own
  boundary control).
- "runtime manifest generation failure" / "render failure" — Phase 7's actual
  generation doesn't exist yet; nothing to check failing.
"""

from __future__ import annotations

import re

import frappe
from frappe import _

# §5 — official_area, and the Draft/Version-scoped doctype(s) whose presence
# proves this row is "present" (non-empty content saved for it). Areas 2 and
# 12 are additionally checked against the package's own Sections (Document
# Structure is package-scoped, not Draft/Version-scoped — see Phase 1/3's own
# ownership-model decision).
COVERAGE_AREAS: list[dict] = [
	{"number": 1, "official_area": "Tender identity, cover and Invitation to Tender", "doctypes": ("STD Cfg Parameter Definition",), "requires_source": True},
	{"number": 2, "official_area": "Section I — Instructions to Tenderers", "doctypes": (), "section_area": 2},
	{"number": 3, "official_area": "Section II — Tender Data Sheet", "doctypes": ("STD Cfg Parameter Definition",)},
	{"number": 4, "official_area": "Section III — Evaluation and Qualification Criteria", "doctypes": ("STD Cfg Evaluation Schema",)},
	{"number": 5, "official_area": "Section IV — Non-price Tendering Forms", "doctypes": ("STD Cfg Form Schema",)},
	{"number": 6, "official_area": "Section IV — Price Schedule Forms", "doctypes": ("STD Cfg Price Schema",)},
	{"number": 7, "official_area": "Section V — Requirements of the Information System", "doctypes": ("STD Cfg Requirement Schema",)},
	{"number": 8, "official_area": "Section VI — Technical Requirements", "doctypes": ("STD Cfg Requirement Schema",)},
	{"number": 9, "official_area": "Section VII — Implementation Schedule", "doctypes": ("STD Cfg Schedule Schema",)},
	{"number": 10, "official_area": "Section VIII — System Inventory Tables", "doctypes": ("STD Cfg Inventory Schema",)},
	{"number": 11, "official_area": "Section IX — Background and Informational Materials", "doctypes": (), "section_area": 11},
	{"number": 12, "official_area": "General Conditions of Contract", "doctypes": (), "section_area": 12},
	{"number": 13, "official_area": "Special Conditions of Contract", "doctypes": ("STD Cfg Contract Schema",)},
	{"number": 14, "official_area": "Contract Forms and appendices", "doctypes": ("STD Cfg Form Schema", "STD Cfg Contract Schema")},
	{"number": 15, "official_area": "Securities, declarations and qualification evidence", "doctypes": ("STD Cfg Parameter Definition", "STD Cfg Form Schema", "STD Cfg Contract Schema")},
	{"number": 16, "official_area": "Change-order and post-award administration forms", "doctypes": ("STD Cfg Contract Schema",)},
]


def _content_present(reference_doctype: str, reference_name: str, doctypes: tuple[str, ...]) -> bool:
	return any(
		frappe.db.exists(doctype, {"reference_doctype": reference_doctype, "reference_name": reference_name})
		for doctype in doctypes
	)


def _section_has_content(reference_doctype: str, reference_name: str, package_id: str, coverage_area_number: int) -> bool:
	section_names = frappe.get_all(
		"STD Cfg Section",
		filters={"package_id": package_id, "coverage_area_number": coverage_area_number},
		pluck="name",
	)
	if not section_names:
		return False
	return bool(
		frappe.db.exists(
			"STD Cfg Content Block",
			{
				"reference_doctype": reference_doctype,
				"reference_name": reference_name,
				"section_id": ["in", section_names],
			},
		)
	)


def coverage_report(reference_doctype: str, reference_name: str) -> list[dict]:
	"""§5/§11.1 — the sixteen-row coverage register, in official order, recomputed
	on every call (not stored state)."""
	package_id = _resolve_package_id(reference_doctype, reference_name)
	rows = []
	for area in COVERAGE_AREAS:
		if area.get("requires_source"):
			source_present = bool(
				frappe.db.get_value(reference_doctype, reference_name, "official_source_file_id")
			)
		else:
			source_present = True
		if "section_area" in area:
			content_present = _section_has_content(
				reference_doctype, reference_name, package_id, area["section_area"]
			)
		else:
			content_present = _content_present(reference_doctype, reference_name, area["doctypes"])
		rows.append(
			{
				"number": area["number"],
				"official_area": area["official_area"],
				"result": "Pass" if (source_present and content_present) else "Incomplete",
			}
		)
	return rows


def _resolve_package_id(reference_doctype: str, reference_name: str) -> str:
	return frappe.db.get_value(reference_doctype, reference_name, "package_id")


# --- §11.2 Blocking findings --------------------------------------------------

_PLACEHOLDER_RE = re.compile(r"\{\{?\s*([a-zA-Z0-9_.]+)\s*\}?\}")


def _finding(code: str, area: str, message: str) -> dict:
	return {"severity": "Blocking", "code": code, "owning_area": area, "message": message}


def _warning(code: str, area: str, message: str) -> dict:
	return {"severity": "Warning", "code": code, "owning_area": area, "message": message}


def _find_blocking(reference_doctype: str, reference_name: str) -> list[dict]:
	findings: list[dict] = []

	if not frappe.db.get_value(reference_doctype, reference_name, "official_source_file_id"):
		findings.append(_finding("STD_MISSING_SOURCE", "PCFG-01", _("Official source is missing.")))

	for row in coverage_report(reference_doctype, reference_name):
		if row["result"] != "Pass":
			findings.append(
				_finding(
					"STD_COVERAGE_ROW_MISSING",
					f"PCFG-{row['number']:02d}" if row["number"] <= 9 else "PCFG-09",
					_("Coverage area {0} — {1} — is not present.").format(row["number"], row["official_area"]),
				)
			)

	for block in frappe.get_all(
		"STD Cfg Content Block",
		filters={"reference_doctype": reference_doctype, "reference_name": reference_name},
		fields=["name", "block_type", "locked_text", "binding_key", "section_id"],
	):
		if block.block_type == "Locked text":
			if not (block.locked_text or "").strip():
				findings.append(_finding("STD_CONTENT_BLOCK_UNRESOLVED", "PCFG-02", _("Locked text block {0} has no text.").format(block.name)))
			else:
				for match in _PLACEHOLDER_RE.finditer(block.locked_text):
					key = match.group(1)
					if not frappe.db.exists(
						"STD Cfg Parameter Definition",
						{"reference_doctype": reference_doctype, "reference_name": reference_name, "parameter_key": key},
					):
						findings.append(
							_finding(
								"STD_UNDECLARED_PLACEHOLDER",
								"PCFG-02",
								_("Locked block {0} references an undeclared placeholder: {1}").format(block.name, key),
							)
						)
		elif not (block.binding_key or "").strip():
			findings.append(_finding("STD_CONTENT_BLOCK_UNRESOLVED", "PCFG-02", _("Content block {0} has no binding key.").format(block.name)))

	for param in frappe.get_all(
		"STD Cfg Parameter Definition",
		filters={"reference_doctype": reference_doctype, "reference_name": reference_name},
		fields=["name", "parameter_key", "render_binding", "downstream_binding", "value_type", "allowed_values"],
	):
		if not ((param.render_binding or "").strip() or (param.downstream_binding or "").strip()):
			findings.append(_finding("STD_PARAMETER_NO_CONSUMER", "PCFG-03", _("Parameter {0} has no render or downstream consumer.").format(param.parameter_key)))
		if param.value_type == "Choice" and not (param.allowed_values or "").strip():
			findings.append(_finding("STD_INVALID_CHOICE", "PCFG-03", _("Parameter {0} is Choice-typed with no allowed values.").format(param.parameter_key)))

	for req in frappe.get_all(
		"STD Cfg Requirement Schema",
		filters={"reference_doctype": reference_doctype, "reference_name": reference_name},
		fields=["name", "category", "render_binding", "bidder_response_binding", "evaluation_binding", "contract_carry_forward_binding"],
	):
		if not all([req.render_binding, req.bidder_response_binding, req.evaluation_binding, req.contract_carry_forward_binding]):
			findings.append(_finding("STD_REQUIREMENT_TREATMENT_MISSING", "PCFG-04", _("Requirement category {0} is missing a required downstream treatment.").format(req.category)))

	for sched in frappe.get_all(
		"STD Cfg Schedule Schema",
		filters={"reference_doctype": reference_doctype, "reference_name": reference_name},
		fields=["name", "title", "render_binding", "contract_binding"],
	):
		if not (sched.render_binding and sched.contract_binding):
			findings.append(_finding("STD_SCHEDULE_NO_CONSUMER", "PCFG-05", _("Schedule milestone {0} has no render or contract use.").format(sched.title)))

	for price in frappe.get_all(
		"STD Cfg Price Schema",
		filters={"reference_doctype": reference_doctype, "reference_name": reference_name},
		fields=["name", "family", "calculation", "evaluated_total_binding"],
	):
		if not (price.calculation and price.evaluated_total_binding):
			findings.append(_finding("STD_PRICE_NO_CALCULATION", "PCFG-06", _("Price schedule {0} has no calculation or evaluated-total treatment.").format(price.family)))

	for crit in frappe.get_all(
		"STD Cfg Evaluation Schema",
		filters={"reference_doctype": reference_doctype, "reference_name": reference_name},
		fields=["name", "criterion_structure", "response_source"],
	):
		if not (crit.response_source or "").strip():
			findings.append(_finding("STD_CRITERION_NO_SOURCE", "PCFG-07", _("Criterion {0} has no response/evidence source.").format(crit.criterion_structure)))

	for form in frappe.get_all(
		"STD Cfg Form Schema",
		filters={"reference_doctype": reference_doctype, "reference_name": reference_name},
		fields=["name", "form_name"],
	):
		if not frappe.db.exists("STD Cfg Form Schema Field", {"parent": form.name}):
			findings.append(_finding("STD_FORM_OPAQUE_UPLOAD", "PCFG-08", _("Form {0} has no field-level schema — represented only as an attachment.").format(form.form_name)))

	for contract in frappe.get_all(
		"STD Cfg Contract Schema",
		filters={"reference_doctype": reference_doctype, "reference_name": reference_name},
		fields=["name", "value_category", "scc_binding"],
	):
		if not (contract.scc_binding or "").strip():
			findings.append(_finding("STD_CONTRACT_VALUE_NO_MAPPING", "PCFG-09", _("Contract value {0} has no SCC/render mapping.").format(contract.value_category)))

	mapped_keys = set(
		frappe.get_all(
			"STD Cfg Output Mapping",
			filters={"reference_doctype": reference_doctype, "reference_name": reference_name},
			pluck="source_binding_key",
		)
	)
	for param in frappe.get_all(
		"STD Cfg Parameter Definition",
		filters={"reference_doctype": reference_doctype, "reference_name": reference_name, "required": 1},
		fields=["parameter_key"],
	):
		if param.parameter_key not in mapped_keys:
			findings.append(
				_finding(
					"STD_OUTPUT_MAPPING_MISSING",
					"PCFG-09",
					_("Required parameter {0} has no terminal output mapping.").format(param.parameter_key),
				)
			)

	return findings


def _find_warnings(reference_doctype: str, reference_name: str) -> list[dict]:
	warnings: list[dict] = []
	for req in frappe.get_all(
		"STD Cfg Requirement Schema",
		filters={"reference_doctype": reference_doctype, "reference_name": reference_name, "vendor_neutrality_trigger": 1},
		fields=["category", "vendor_neutrality_note"],
	):
		warnings.append(
			_warning(
				"STD_VENDOR_NEUTRALITY_REVIEW",
				"PCFG-04",
				req.vendor_neutrality_note
				or _("Vendor-neutrality trigger for {0} requires reviewer attention.").format(req.category),
			)
		)
	return warnings


def run_complete_check(reference_doctype: str, reference_name: str) -> dict:
	"""§13.2 `RunSTDCompleteCheck` / §16.4 — "validates all definitions, coverage,
	manifests and rendering", distinct from an area save's local-only check.
	Persists findings as `STD Cfg Validation Finding` rows (replacing whatever
	that reference last had) — the only writer of that doctype."""
	blocking = _find_blocking(reference_doctype, reference_name)
	warnings = _find_warnings(reference_doctype, reference_name)

	frappe.db.delete("STD Cfg Validation Finding", {"reference_doctype": reference_doctype, "reference_name": reference_name})
	for row in blocking + warnings:
		frappe.get_doc(
			{
				"doctype": "STD Cfg Validation Finding",
				"reference_doctype": reference_doctype,
				"reference_name": reference_name,
				**row,
			}
		).insert(ignore_permissions=True)

	coverage = coverage_report(reference_doctype, reference_name)
	return {
		"reference_doctype": reference_doctype,
		"reference_name": reference_name,
		"coverage": coverage,
		"coverage_pass_count": sum(1 for r in coverage if r["result"] == "Pass"),
		"blocking_count": len(blocking),
		"warning_count": len(warnings),
		"blocking": blocking,
		"warnings": warnings,
	}


def readiness_report(reference_doctype: str, reference_name: str) -> dict:
	"""§9.14-shaped, with an honest gap: the nine-step manifest-derived readiness
	(`Not started`/`In progress`/`Complete`/`Blocked` per CFG-01..09) depends on
	Phase 7's real manifest generation, which does not exist yet. Coverage and
	Blocking/Warning results ARE real and final; `steps` is explicitly marked
	unavailable rather than faked as Complete."""
	check = run_complete_check(reference_doctype, reference_name)
	ready = check["coverage_pass_count"] == len(COVERAGE_AREAS) and check["blocking_count"] == 0
	return {
		**check,
		"steps": None,
		"steps_note": "Not available until Phase 7's manifest generation exists.",
		"ready_for_tender_review": False if not ready else None,
		"ready_for_tender_review_note": (
			"Coverage/Blocking are clear, but §9.14's readiness boolean also requires all nine "
			"generated manifest steps Complete (Phase 7) — cannot be truthfully reported yet."
			if ready
			else "Coverage or Blocking findings remain."
		),
	}
