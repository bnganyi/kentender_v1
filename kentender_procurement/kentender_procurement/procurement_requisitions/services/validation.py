# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §6.5 — the deterministic findings engine and step
completion derivation.

Pure and DB-free by design: every function here takes plain dicts projected
from the real Frappe documents (never the documents themselves), so it is
testable without a fixture world and so `ValidateRequisition`/submission/
authorisation all recompute from the exact same function, never a
duplicated, drifting copy of the rules.

`Finding.code` is a closed, module-local vocabulary distinct from §11's
service error codes — a submission or authorisation with any Blocking
finding maps them onto `REQ_BLOCKING_FINDINGS`'s `detail` (services/*.py),
never invents a new §11 code per finding.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from kentender_procurement.procurement_requisitions.services import restrictive_terms
from kentender_procurement.procurement_requisitions.services.catalogue import CATALOGUE_BY_KEY

BLOCKING = "Blocking"
WARNING = "Warning"

FINDING_CODES: frozenset[str] = frozenset(
	{
		"BALANCE_CHANGED", "DATE_BEYOND_BOUNDARY", "QUANTITY_MISMATCH", "MISSING_ITEM", "MISSING_TECHNICAL_ROW",
		"BASELINE_UNCONFIRMED", "RESTRICTIVE_TERM", "SUBJECTIVE_ACCEPTANCE", "MISSING_ACCEPTANCE_ROW",
		"FILE_UNLINKED", "SERVICE_COMPLEX", "SERVICE_ROW_INCOMPLETE", "CONTRADICTION", "MISSING_REQUIRED_FIELD",
		"DIGEST_FAILED", "PRODUCT_UNSUPPORTED", "DATE_MATCHES_PLAN_COMPLETION",
	}
)

# §6.5: "'Satisfactory', 'acceptable' or similar wording without an
# observable condition is invalid." The rule is deliberately about
# TRIVIALITY, not vocabulary: a pass condition is Blocking only when it is
# nothing more than one of these phrases (nothing specific left once they
# are stripped out) — not whenever a real, specific sentence happens to
# contain a common word. A closed "must contain this exact observable
# verb" allowlist was tried and rejected: it false-positived on the
# §13.9 fixture's own legitimate wording ("quantities equal the
# authorised schedule", "complies with all mandatory technical rows"),
# neither of which uses any of the verb stems such a list would need to
# anticipate in advance.
_SUBJECTIVE_PHRASES: tuple[str, ...] = (
	"satisfactory", "acceptable", "good", "adequate", "fine", "ok", "as required", "to standard", "sufficient",
)
_MIN_SPECIFIC_LENGTH = 10


@dataclass
class Finding:
	code: str
	severity: str
	step: int
	message: str
	row: dict[str, str] | None = field(default=None)

	def as_dict(self) -> dict[str, Any]:
		return {"code": self.code, "severity": self.severity, "step": self.step, "message": self.message, "row": self.row}


def _row(kind: str, row_id: str) -> dict[str, str]:
	return {"kind": kind, "id": row_id}


def _is_subjective(pass_condition: str) -> bool:
	text = (pass_condition or "").strip().lower()
	if not text:
		return True
	stripped = text
	for phrase in _SUBJECTIVE_PHRASES:
		stripped = stripped.replace(phrase, "")
	stripped = stripped.strip(" .,-")
	return len(stripped) < _MIN_SPECIFIC_LENGTH


_COMPLEX_SERVICE_MARKERS: tuple[str, ...] = (
	"develop", "integrat", "migrat", "customi", "software build", "api ", "bespoke", "system implementation",
)


def _is_complex_service(service_type: str, required_result: str) -> bool:
	if service_type == "Other":
		return True
	text = (required_result or "").lower()
	return any(marker in text for marker in _COMPLEX_SERVICE_MARKERS)


def _step1_findings(version: dict[str, Any], eligibility: dict[str, Any]) -> list[Finding]:
	findings: list[Finding] = []
	lines = version.get("drawdown_lines") or []
	if not lines:
		findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, 1, "At least one drawdown line is required."))
	sources_by_id = {s["plan_source_allocation_id"]: s for s in eligibility.get("sources", [])}
	for line in lines:
		source = sources_by_id.get(line.get("plan_item_line_id"))
		requested_qty = line.get("requested_quantity") or 0
		requested_value = line.get("requested_value") or 0
		if requested_qty <= 0 or requested_value <= 0:
			findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, 1, "A drawdown quantity and value must both be positive.", _row("drawdown_line", line.get("drawdown_line_id", ""))))
		if source and (requested_qty > (source.get("remaining_quantity") or 0) + 1e-6 or requested_value > (source.get("remaining_amount") or 0) + 1e-6):
			findings.append(Finding("BALANCE_CHANGED", BLOCKING, 1, "Remaining quantity or value changed. Refresh the drawdown step.", _row("drawdown_line", line.get("drawdown_line_id", ""))))
	for field_name in ("requirement_title", "delivery_location", "latest_delivery_date"):
		if not version.get(field_name):
			findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, 1, f"{field_name.replace('_', ' ').title()} is required."))
	boundary = eligibility.get("planned_dates", {}).get("delivery_completion_date") or eligibility.get("planned_dates", {}).get("completion_date")
	if boundary and version.get("latest_delivery_date"):
		if str(version["latest_delivery_date"]) > str(boundary):
			findings.append(Finding("DATE_BEYOND_BOUNDARY", BLOCKING, 1, "The delivery date exceeds the approved Plan boundary."))
		elif str(version["latest_delivery_date"]) == str(boundary):
			# §13.9's own review-screen fixture: not an error — merely worth a
			# visible nudge that there is zero slack against the Plan's own
			# completion date.
			findings.append(Finding("DATE_MATCHES_PLAN_COMPLETION", WARNING, 1, "Delivery date is the same as the latest approved Plan completion date."))
	return findings


def _step2_findings(version: dict[str, Any], package: dict[str, Any]) -> list[Finding]:
	findings: list[Finding] = []
	items = package.get("items") or []
	if not items:
		findings.append(Finding("MISSING_ITEM", BLOCKING, 2, "At least one equipment item is required."))
	requested_by_line = {l.get("drawdown_line_id"): l.get("requested_quantity") or 0 for l in (version.get("drawdown_lines") or [])}
	summed: dict[str, float] = {}
	for item in items:
		line_id = item.get("plan_item_line_id")
		summed[line_id] = summed.get(line_id, 0) + (item.get("quantity") or 0)
		for field_name in ("item_name", "equipment_category", "intended_use", "quantity"):
			if not item.get(field_name):
				findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, 2, f"Item {field_name.replace('_', ' ')} is required.", _row("item", item.get("requisition_item_id", ""))))
	for line_id, requested_qty in requested_by_line.items():
		if abs(summed.get(line_id, 0) - requested_qty) > 1e-6:
			findings.append(Finding("QUANTITY_MISMATCH", BLOCKING, 2, "Item quantities do not reconcile to the requested drawdown quantity.", _row("drawdown_line", line_id)))
	return findings


def _step3_findings(package: dict[str, Any]) -> list[Finding]:
	findings: list[Finding] = []
	for row in package.get("technical_requirements") or []:
		row_id = row.get("technical_requirement_id", "")
		if row.get("row_status") == "Proposed":
			findings.append(Finding("BASELINE_UNCONFIRMED", BLOCKING, 3, "A proposed baseline characteristic must be confirmed or removed.", _row("technical_requirement", row_id)))
		ch = CATALOGUE_BY_KEY.get(row.get("characteristic_key"))
		text_value = ""
		if row.get("required_value_json"):
			try:
				parsed = json.loads(row["required_value_json"])
				text_value = str(parsed.get("value") or parsed.get("other") or "")
			except (TypeError, ValueError):
				text_value = str(row.get("required_value_json"))
		if ch and ch.control == "TEXT" and restrictive_terms.is_restrictive(text_value, reason=row.get("reason", "")):
			findings.append(Finding("RESTRICTIVE_TERM", BLOCKING, 3, "A brand or restrictive term lacks permitted equivalent treatment.", _row("technical_requirement", row_id)))
		if ch and ch.key == "other_essential_characteristic" and len((row.get("reason") or "")) < 20:
			findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, 3, "A reason of 20-300 characters is required for Other essential characteristic.", _row("technical_requirement", row_id)))
	return findings


def _step4_findings(version: dict[str, Any], package: dict[str, Any]) -> list[Finding]:
	findings: list[Finding] = []
	if version.get("related_services_required"):
		services = package.get("related_services") or []
		if not services:
			findings.append(Finding("SERVICE_ROW_INCOMPLETE", BLOCKING, 4, "At least one related-service row is required when related services are Yes."))
		for row in services:
			row_id = row.get("service_requirement_id", "")
			if _is_complex_service(row.get("service_type", ""), row.get("required_result", "")):
				findings.append(Finding("SERVICE_COMPLEX", BLOCKING, 4, "This service shows complex development, integration or migration, which this product does not support.", _row("service", row_id)))
			for field_name in ("required_result", "quantity_or_coverage", "completion_date", "acceptance_evidence"):
				if not row.get(field_name):
					findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, 4, f"Service {field_name.replace('_', ' ')} is required.", _row("service", row_id)))
	acceptance = package.get("acceptance_requirements") or []
	if not acceptance:
		findings.append(Finding("MISSING_ACCEPTANCE_ROW", BLOCKING, 4, "At least one objective acceptance row is required."))
	for row in acceptance:
		row_id = row.get("acceptance_requirement_id", "")
		if _is_subjective(row.get("pass_condition", "")):
			findings.append(Finding("SUBJECTIVE_ACCEPTANCE", BLOCKING, 4, "\"Satisfactory\" or similar wording without an observable condition is invalid.", _row("acceptance", row_id)))
	linked_ids: set[str] = set()
	for row in acceptance:
		linked_ids.add(row.get("acceptance_requirement_id", ""))
	for row in package.get("technical_requirements") or []:
		linked_ids.add(row.get("technical_requirement_id", ""))
	for row in package.get("related_services") or []:
		linked_ids.add(row.get("service_requirement_id", ""))
	for material in package.get("supporting_materials") or []:
		material_id = material.get("supporting_material_id", "")
		if material.get("treatment") == "Forms part of requirement":
			linked = []
			if material.get("linked_requirement_ids_json"):
				try:
					linked = json.loads(material["linked_requirement_ids_json"])
				except (TypeError, ValueError):
					linked = []
			if not linked or not any(l in linked_ids for l in linked):
				findings.append(Finding("FILE_UNLINKED", BLOCKING, 4, "A supporting file cannot be the only statement of an obligation.", _row("material", material_id)))
	return findings


def validate(*, version: dict[str, Any], package: dict[str, Any], eligibility: dict[str, Any]) -> dict[str, Any]:
	"""§6.5 — every finding, plus per-step completion derived exactly per
	the table: 1 needs a valid drawdown; 2 needs items reconciling to it;
	3 needs every baseline row confirmed; 4 needs acceptance (+ services
	when required); 5 needs 1-4 complete and zero Blocking findings."""
	findings = (
		_step1_findings(version, eligibility)
		+ _step2_findings(version, package)
		+ _step3_findings(package)
		+ _step4_findings(version, package)
	)
	blocking_by_step = {1: [], 2: [], 3: [], 4: []}
	warnings_by_step = {1: [], 2: [], 3: [], 4: []}
	for f in findings:
		bucket = blocking_by_step if f.severity == BLOCKING else warnings_by_step
		bucket.setdefault(f.step, []).append(f)
	steps = {
		step: {"complete": not blocking_by_step.get(step), "blocking": len(blocking_by_step.get(step, [])), "warnings": len(warnings_by_step.get(step, []))}
		for step in (1, 2, 3, 4)
	}
	# §13.9's own fixture is "Ready for departmental submission" with 0
	# Blocking and 1 Warning — a Warning is a visible nudge, never something
	# that withholds readiness. `steps[s]["complete"]` for 1-4 is already
	# "zero Blocking findings on that step" (a Warning-only step still
	# reports complete), so this needs no separate `findings`/severity check.
	steps[5] = {"complete": all(steps[s]["complete"] for s in (1, 2, 3, 4)), "blocking": sum(steps[s]["blocking"] for s in (1, 2, 3, 4)), "warnings": sum(steps[s]["warnings"] for s in (1, 2, 3, 4))}
	return {
		"findings": [f.as_dict() for f in findings],
		"steps": steps,
		"blocking_count": sum(1 for f in findings if f.severity == BLOCKING),
		"warning_count": sum(1 for f in findings if f.severity == WARNING),
	}
