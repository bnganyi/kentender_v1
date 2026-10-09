# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §6.1/§6.5 — the deterministic findings engine.

Five internal validation groups stay separately traceable in results, tests
and audit; the user sees three tasks derived from them:

| Group                  | Task              |
| request_drawdown       | Request details   |
| equipment_items        | Request details   |
| technical_support      | Requirements      |
| services_acceptance    | Requirements      |
| review_submit          | Review and submit |

Pure and DB-free: every function takes plain dicts projected from the real
documents, so `ValidateRequisition`, routing and authorisation recompute
from exactly the same rules. Money and quantity are exact `Decimal`s (§5.14);
there is no float or epsilon here. `Finding.code` is a closed module-local
vocabulary; a lifecycle command maps Blocking findings onto
`REQ_BLOCKING_FINDINGS` detail, never a new §11 code per finding.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from kentender_procurement.procurement_requisitions.services import precision, restrictive_terms
from kentender_procurement.procurement_requisitions.services import scope as req_scope
from kentender_procurement.procurement_requisitions.services.catalogue import CATALOGUE_BY_KEY, TEXT, required_characteristics
from kentender_procurement.procurement_requisitions.services.catalogue import inapplicable_categories as catalogue_inapplicable

BLOCKING = "Blocking"
WARNING = "Warning"

GROUPS: tuple[str, ...] = ("request_drawdown", "equipment_items", "technical_support", "services_acceptance", "review_submit")
TASKS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
	("request_details", "Request details", ("request_drawdown", "equipment_items")),
	("requirements", "Requirements", ("technical_support", "services_acceptance")),
	("review_submit", "Review and submit", ("review_submit",)),
)
TASK_OF_GROUP: dict[str, str] = {g: key for key, _label, groups in TASKS for g in groups}

NOT_STARTED = "Not started"
NEEDS_ATTENTION = "Needs attention"
COMPLETE = "Complete"

FINDING_CODES: frozenset[str] = frozenset(
	{
		"BALANCE_CHANGED", "DATE_BEYOND_BOUNDARY", "DATE_AFTER_ESTIMATE", "QUANTITY_MISMATCH", "MISSING_ITEM",
		"MISSING_REQUIRED_FIELD", "CONTROL_INVALID", "PACKAGE_REVIEW_REQUIRED", "DUPLICATE_CHARACTERISTIC",
		"RESTRICTIVE_TERM", "SUBJECTIVE_ACCEPTANCE", "MISSING_ACCEPTANCE_ROW", "FILE_UNLINKED", "SERVICE_COMPLEX",
		"SERVICE_ROW_INCOMPLETE", "DIGEST_FAILED", "PRODUCT_UNSUPPORTED", "DEPARTMENT_NOT_CONTRIBUTING",
	}
)

# §6.5: "'Satisfactory', 'acceptable' or similar wording without an
# observable condition is invalid." Blocking only when nothing specific is
# left once these phrases are stripped — a real sentence containing a common
# word is not subjective (a verb allow-list false-positived on §13.1's own
# wording in v1.6 and was rejected).
_SUBJECTIVE_PHRASES: tuple[str, ...] = (
	"satisfactory", "acceptable", "good", "adequate", "fine", "ok", "as required", "to standard", "sufficient",
)
_MIN_SPECIFIC_LENGTH = 10
_COMPLEX_SERVICE_MARKERS: tuple[str, ...] = (
	"develop", "integrat", "migrat", "customi", "software build", "api ", "bespoke", "system implementation",
)


@dataclass
class Finding:
	code: str
	severity: str
	group: str
	section: str
	message: str
	row: dict[str, str] | None = field(default=None)

	def as_dict(self) -> dict[str, Any]:
		return {
			"code": self.code, "severity": self.severity, "group": self.group, "task": TASK_OF_GROUP[self.group],
			"section": self.section, "message": self.message, "row": self.row,
		}


def cstr_(value) -> str:
	return "" if value is None else str(value).strip()


def _row(kind: str, row_id: str) -> dict[str, str]:
	return {"kind": kind, "id": row_id}


def _date(value) -> date | None:
	text = str(value or "")[:10]
	try:
		return date.fromisoformat(text) if text else None
	except ValueError:
		return None


def _long_date(value: date) -> str:
	return f"{value.day} {value.strftime('%b %Y')}"


def is_subjective(pass_condition: str) -> bool:
	text = (pass_condition or "").strip().lower()
	if not text:
		return True
	stripped = text
	for phrase in _SUBJECTIVE_PHRASES:
		stripped = stripped.replace(phrase, "")
	return len(stripped.strip(" .,-")) < _MIN_SPECIFIC_LENGTH


def is_complex_service(service_type: str, required_result: str) -> bool:
	text = (required_result or "").lower()
	return any(marker in text for marker in _COMPLEX_SERVICE_MARKERS)


def _money(value) -> Decimal:
	return precision.stored_money(value)


def _qty(value) -> Decimal:
	return precision.stored_quantity(value)


# --- request_drawdown ------------------------------------------------------


def _request_drawdown(version: dict[str, Any], package: dict[str, Any], eligibility: dict[str, Any], unreviewed: set[str]) -> list[Finding]:
	group = "request_drawdown"
	findings: list[Finding] = []
	lines = version.get("drawdown_lines") or []
	item_quantity: dict[str, int] = {}
	for item in package.get("items") or []:
		item_quantity[item.get("drawdown_line_id")] = item_quantity.get(item.get("drawdown_line_id"), 0) + int(item.get("quantity") or 0)
	if not lines:
		findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, group, "amounts", "Select at least one approved requirement."))
	sources = {s["plan_item_line_id"]: s for s in eligibility.get("sources", [])}
	contributing = set(eligibility.get("contributing_org_unit_ids") or [])
	for line in lines:
		line_id = line.get("drawdown_line_id", "")
		# v1.15 §5.3 — the quantity is the sum of the items; the value is the requester's estimated total cost.
		requested_qty, requested_value = Decimal(item_quantity.get(line_id, 0)), _money(line.get("requested_value"))
		name = line.get("department_name") or line.get("contributing_org_unit") or "this department"
		if contributing and line.get("contributing_org_unit") not in contributing:
			findings.append(Finding("DEPARTMENT_NOT_CONTRIBUTING", BLOCKING, group, "amounts", "This department did not contribute to the approved purchase.", _row("drawdown_line", line_id)))
		if requested_qty <= 0 and requested_value <= 0:
			continue  # an unused source: left out of the submitted snapshot (§5.3)
		if requested_qty > 0 and requested_value <= 0:
			findings.append(Finding("SOURCE_INCOMPLETE", BLOCKING, group, "amounts", f"Enter the estimated total cost for {name}.", _row("drawdown_line", line_id)))
		if requested_qty <= 0 and requested_value > 0:
			findings.append(Finding("SOURCE_INCOMPLETE", BLOCKING, group, "amounts", f"Add the items for {name}, or clear its estimated total cost.", _row("drawdown_line", line_id)))
		if line_id in unreviewed:
			findings.append(Finding("AMOUNTS_REVIEW_REQUIRED", BLOCKING, group, "amounts", f"Review the quantity and estimated total cost for {name}, then save.", _row("drawdown_line", line_id)))
		source = sources.get(line.get("plan_item_line_id"))
		if source is None:
			findings.append(Finding("BALANCE_CHANGED", BLOCKING, group, "amounts", "This approved requirement is no longer available from the approved purchase.", _row("drawdown_line", line_id)))
			continue
		if requested_qty > precision.planning_quantity(source.get("remaining_quantity") or "0") or requested_value > _money(source.get("remaining_amount")):
			findings.append(Finding("BALANCE_CHANGED", BLOCKING, group, "amounts", "The amount still available from the approved purchase changed. Refresh the amounts requested.", _row("drawdown_line", line_id)))

	title = (version.get("requirement_title") or "").strip()
	if not (5 <= len(title) <= 160):
		findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, group, "request_information", "Enter a requirement title of 5–160 characters.", _row("field", "requirement_title")))
	if not version.get("delivery_location"):
		findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, group, "request_information", "Select the delivery location.", _row("field", "delivery_location")))
	latest = _date(version.get("latest_delivery_date"))
	if not latest:
		findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, group, "request_information", "Enter the latest delivery date.", _row("field", "latest_delivery_date")))
		return findings

	# §5.14 — three distinct dates: the source-derived Plan boundary and every
	# selected source's required-by are hard limits; the estimate only warns.
	boundary = _date(eligibility.get("plan_completion_boundary"))
	if boundary and latest > boundary:
		findings.append(Finding("DATE_BEYOND_BOUNDARY", BLOCKING, group, "request_information", f"The latest delivery date is after the plan completion boundary ({_long_date(boundary)}).", _row("field", "latest_delivery_date")))
	selected = {line.get("plan_item_line_id") for line in lines}
	for line_id, source in sources.items():
		required_by = _date(source.get("required_by_date"))
		if line_id in selected and required_by and latest > required_by:
			findings.append(Finding("DATE_BEYOND_BOUNDARY", BLOCKING, group, "request_information", f"The latest delivery date is after an approved requirement's required-by date ({_long_date(required_by)}).", _row("field", "latest_delivery_date")))
			break
	estimate = _date(eligibility.get("estimated_completion_date"))
	if estimate and latest > estimate:
		days = (latest - estimate).days
		findings.append(Finding("DATE_AFTER_ESTIMATE", WARNING, group, "purpose", f"The requested delivery date is {days} day{'s' if days != 1 else ''} after the plan’s estimated completion date."))
	return findings


# --- equipment_items -------------------------------------------------------


def _equipment_items(version: dict[str, Any], package: dict[str, Any]) -> list[Finding]:
	group = "equipment_items"
	findings: list[Finding] = []
	items = package.get("items") or []
	lines = {line.get("drawdown_line_id"): line for line in version.get("drawdown_lines") or []}
	if not items:
		findings.append(Finding("MISSING_ITEM", BLOCKING, group, "equipment", "Add at least one item and enter its estimated total cost."))
	totals: dict[str, Decimal] = {}
	for item in items:
		item_id = item.get("requisition_item_id", "")
		line_id = item.get("drawdown_line_id")
		if line_id not in lines:
			findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, group, "equipment", "Each equipment row must belong to one approved requirement.", _row("item", item_id)))
			continue
		quantity = Decimal(int(item.get("quantity") or 0))
		totals[line_id] = totals.get(line_id, Decimal(0)) + quantity
		if quantity <= 0:
			findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, group, "equipment", "Enter a quantity above zero.", _row("item", item_id)))
		if not (3 <= len((item.get("item_name") or "").strip()) <= 120):
			findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, group, "equipment", "Enter an item name of 3–120 characters.", _row("item", item_id)))
		if not (10 <= len((item.get("intended_use") or "").strip()) <= 500):
			findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, group, "equipment", "Describe the intended use in 10–500 characters.", _row("item", item_id)))
		if not item.get("equipment_category"):
			findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, group, "equipment", "Select the equipment category.", _row("item", item_id)))
	return findings


# --- technical_support -----------------------------------------------------


def _row_categories(row: dict[str, Any], package: dict[str, Any]) -> list[str]:
	"""The equipment categories a technical row applies to: those of the items it
	covers (one, several, or every item for an `All items` row) — REQ v1.18 §5.7A."""
	return req_scope.categories_of(row, package.get("items") or [])


def _restrictive(text: str, *, reason: str = "") -> bool:
	return restrictive_terms.is_restrictive(text, reason=reason)


def _restrictive_message(where: str, *texts: str, can_excuse: bool = False) -> str:
	"""Say WHICH word and WHERE: a bare "a brand lacks equivalent treatment" leaves the requester hunting."""
	terms: list[str] = []
	for text in texts:
		for term in restrictive_terms.find_restrictive_terms(text or ""):
			if term not in terms:
				terms.append(term)
	named = ", ".join(f"“{t}”" for t in terms[:3]) or "A term"
	fix = "Use supplier-neutral wording" + (", or add “or equivalent” and a functional reason." if can_excuse else ".")
	return f"{named} in {where} is a brand or restrictive term. {fix}"


def _restrictive_free_text(version: dict[str, Any], package: dict[str, Any]) -> list[Finding]:
	"""§6.3/§6.5, REQ19-AC-018 — a brand, model, proprietary certification or
	named technology is Blocking in every free-text field that reaches the
	Tender, not only in technical TEXT rows. Rows with no recorded-reason
	column cannot meet the "or equivalent plus a functional reason" test, so
	only brand-free wording clears them."""
	findings: list[Finding] = []

	def check(group: str, section: str, kind: str, row_id: str, where: str, *texts: str) -> None:
		if any(_restrictive(text) for text in texts if text):
			findings.append(Finding("RESTRICTIVE_TERM", BLOCKING, group, section, _restrictive_message(where, *texts), _row(kind, row_id)))

	check("request_drawdown", "request_information", "field", "requirement_title", "the requirement title", version.get("requirement_title") or "")
	for item in package.get("items") or []:
		check("equipment_items", "equipment", "item", item.get("requisition_item_id", ""), f"the item “{(item.get('item_name') or '').strip() or 'unnamed'}”", item.get("item_name") or "", item.get("intended_use") or "")
	check("technical_support", "warranty_support", "field", "support_description", "the support description", package.get("support_description") or "")
	for row in package.get("acceptance_requirements") or []:
		if row.get("row_state") != "Proposed":
			check("services_acceptance", "acceptance", "acceptance", row.get("acceptance_requirement_id", ""), "an acceptance check", row.get("pass_condition") or "", row.get("other_evidence_name") or "")
	for row in package.get("related_services") or []:
		check("services_acceptance", "services", "service", row.get("service_requirement_id", ""), "a related service", row.get("required_result") or "", row.get("quantity_or_coverage") or "", row.get("other_evidence_name") or "")
	for row in package.get("supporting_materials") or []:
		check("services_acceptance", "supporting_materials", "material", row.get("supporting_material_id", ""), f"the supporting material “{(row.get('title') or '').strip() or 'untitled'}”", row.get("title") or "", row.get("purpose") or "", row.get("other_document_type") or "")
	return findings


def _item_completeness(package: dict[str, Any], confirmed: list[dict[str, Any]], group: str) -> list[Finding]:
	"""REQ v1.18 §6.5A — every item is covered, by a confirmed row that applies to it, for each characteristic
	its category's starting rows require. Clearing a row can never leave an item underspecified unseen."""
	findings: list[Finding] = []
	items = package.get("items") or []
	covered: dict[str, set[str]] = {}
	for row in confirmed:
		covered.setdefault(row.get("characteristic_key"), set()).update(req_scope.item_ids(row, items))
	for item in items:
		category = item.get("equipment_category")
		for key in required_characteristics(category):
			if item.get("requisition_item_id") not in covered.get(key, set()):
				label = CATALOGUE_BY_KEY[key].label
				name = (item.get("item_name") or "").strip() or category
				findings.append(Finding("ITEM_SPECIFICATION_INCOMPLETE", BLOCKING, group, "technical", f"{name} ({category}) has no {label} requirement.", _row("item", item.get("requisition_item_id", ""))))
	return findings


def _technical_support(package: dict[str, Any]) -> list[Finding]:
	group = "technical_support"
	findings: list[Finding] = []
	if package.get("standard_package_review_state") == "Review required":
		findings.append(Finding("PACKAGE_REVIEW_REQUIRED", BLOCKING, group, "technical", "Review and use the selected standard requirements."))
	confirmed = [r for r in package.get("technical_requirements") or [] if r.get("row_state") != "Proposed"]
	seen: dict[str, set[str]] = {}
	items = package.get("items") or []
	for row in confirmed:
		row_id = row.get("technical_requirement_id", "")
		ch = CATALOGUE_BY_KEY.get(row.get("characteristic_key"))
		if not ch:
			findings.append(Finding("CONTROL_INVALID", BLOCKING, group, "technical", "This characteristic is not in the released catalogue.", _row("technical_requirement", row_id)))
			continue
		covers = set(req_scope.item_ids(row, items))
		if seen.get(ch.key, set()) & covers and not ch.repeatable:
			findings.append(Finding("DUPLICATE_CHARACTERISTIC", BLOCKING, group, "technical", f"{ch.label} appears more than once for the same equipment.", _row("technical_requirement", row_id)))
		seen.setdefault(ch.key, set()).update(covers)
		if row.get("row_state") == "Needs review":
			findings.append(Finding("ROW_NEEDS_REVIEW", BLOCKING, group, "technical", f"{ch.label} now applies to different items. Review it, then use the selected requirements.", _row("technical_requirement", row_id)))
		if not row.get("required_value_json"):
			findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, group, "technical", f"Enter the value for {ch.label}.", _row("technical_requirement", row_id)))
		missing = catalogue_inapplicable(ch, _row_categories(row, package))
		if missing:
			findings.append(Finding("CONTROL_INVALID", BLOCKING, group, "technical", f"{ch.label} does not apply to {', '.join(missing)} equipment.", _row("technical_requirement", row_id)))
		text_value = ""
		other_text = cstr_(row.get("other_value"))
		try:
			parsed = json.loads(row.get("required_value_json") or "{}")
			text_value = str(parsed.get("value") or parsed.get("other") or "")
			other_text = " ".join(t for t in (other_text, str(parsed.get("other") or "")) if t)
		except (TypeError, ValueError):
			text_value = str(row.get("required_value_json"))
		scanned = text_value if ch.control == TEXT else ""
		if _restrictive(" ".join(t for t in (scanned, other_text) if t), reason=row.get("reason", "")):
			findings.append(Finding("RESTRICTIVE_TERM", BLOCKING, group, "technical", _restrictive_message(f"the {ch.label.lower()} requirement", scanned, other_text, can_excuse=True), _row("technical_requirement", row_id)))
		if ch.key == "other_essential_characteristic" and not (20 <= len((row.get("reason") or "").strip()) <= 300):
			findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, group, "technical", "Give a reason of 20–300 characters for this essential characteristic.", _row("technical_requirement", row_id)))

	if package.get("standard_package_review_state") == "Reviewed":
		findings.extend(_item_completeness(package, confirmed, group))

	months = package.get("minimum_warranty_months")
	if not isinstance(months, int) or isinstance(months, bool) or not (1 <= months <= 120):
		findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, group, "warranty_support", "Enter the minimum warranty in months.", _row("field", "minimum_warranty_months")))
	if package.get("onsite_support_required"):
		hours = package.get("maximum_support_response_hours")
		if not isinstance(hours, int) or isinstance(hours, bool) or not (1 <= hours <= 168):
			findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, group, "warranty_support", "Enter the maximum support response in hours (1–168).", _row("field", "maximum_support_response_hours")))
	if package.get("service_location_constraint") not in ("None", "Within Kenya", "At delivery location"):
		findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, group, "warranty_support", "Select the service location constraint.", _row("field", "service_location_constraint")))
	return findings


# --- services_acceptance ---------------------------------------------------


def _services_acceptance(version: dict[str, Any], package: dict[str, Any]) -> list[Finding]:
	group = "services_acceptance"
	findings: list[Finding] = []
	services = package.get("related_services") or []
	if version.get("related_services_required"):
		if not services:
			findings.append(Finding("SERVICE_ROW_INCOMPLETE", BLOCKING, group, "services", "Add at least one related service, or change the answer to No."))
		for row in services:
			row_id = row.get("service_requirement_id", "")
			if is_complex_service(row.get("service_type", ""), row.get("required_result", "")):
				findings.append(Finding("SERVICE_COMPLEX", BLOCKING, group, "services", "This service shows development, integration or migration, which this release does not support.", _row("service", row_id)))
			for field_name, label in (("required_result", "required result"), ("quantity_or_coverage", "quantity or coverage"), ("completion_date", "completion date"), ("acceptance_evidence", "acceptance evidence")):
				if not row.get(field_name):
					findings.append(Finding("MISSING_REQUIRED_FIELD", BLOCKING, group, "services", f"Enter the service {label}.", _row("service", row_id)))
	acceptance = [r for r in package.get("acceptance_requirements") or [] if r.get("row_state") != "Proposed"]
	if not acceptance:
		findings.append(Finding("MISSING_ACCEPTANCE_ROW", BLOCKING, group, "acceptance", "Keep at least one objective acceptance check."))
	for row in acceptance:
		if is_subjective(row.get("pass_condition", "")):
			findings.append(Finding("SUBJECTIVE_ACCEPTANCE", BLOCKING, group, "acceptance", "State an observable pass condition, not only “satisfactory” or similar wording.", _row("acceptance", row.get("acceptance_requirement_id", ""))))
	structured = {r.get("technical_requirement_id") for r in package.get("technical_requirements") or [] if r.get("row_state") != "Proposed"}
	structured |= {r.get("service_requirement_id") for r in services}
	structured |= {r.get("acceptance_requirement_id") for r in acceptance}
	for material in package.get("supporting_materials") or []:
		if material.get("treatment") != "Forms part of requirement":
			continue
		try:
			linked = json.loads(material.get("linked_requirement_ids_json") or "[]")
		except (TypeError, ValueError):
			linked = []
		if not linked or not any(link in structured for link in linked):
			findings.append(Finding("FILE_UNLINKED", BLOCKING, group, "supporting_materials", "A supporting file cannot be the only statement of an obligation. Link it to a structured requirement.", _row("material", material.get("supporting_material_id", ""))))
	return findings


# --- roll-up ---------------------------------------------------------------


def _started(task: str, version: dict[str, Any], package: dict[str, Any]) -> bool:
	if task == "request_details":
		return True
	if task == "requirements":
		return bool(package.get("technical_requirements") or package.get("acceptance_requirements") or package.get("standard_package_review_state") in ("Review required", "Reviewed"))
	return False


def validate(*, version: dict[str, Any], package: dict[str, Any], eligibility: dict[str, Any], review_findings: list[dict[str, Any]] | None = None, unreviewed_line_ids: set[str] | None = None) -> dict[str, Any]:
	"""Every finding, every group's result and the three visible task
	statuses. `review_findings` carries review-group failures only the caller
	can produce (the canonical preview/digest)."""
	findings = (
		_request_drawdown(version, package, eligibility, set(unreviewed_line_ids or ()))
		+ _equipment_items(version, package)
		+ _technical_support(package)
		+ _services_acceptance(version, package)
		+ _restrictive_free_text(version, package)
	)
	for extra in review_findings or []:
		findings.append(Finding(extra["code"], BLOCKING, "review_submit", "review", extra.get("message", "The canonical preview could not be produced.")))

	groups: dict[str, dict[str, Any]] = {}
	for g in GROUPS:
		blocking = [f for f in findings if f.group == g and f.severity == BLOCKING]
		warnings = [f for f in findings if f.group == g and f.severity == WARNING]
		groups[g] = {"complete": not blocking, "blocking": len(blocking), "warnings": len(warnings)}
	preceding = all(groups[g]["complete"] for g in GROUPS[:4])
	groups["review_submit"]["complete"] = preceding and groups["review_submit"]["blocking"] == 0

	tasks = []
	for key, label, task_groups in TASKS:
		complete = all(groups[g]["complete"] for g in task_groups)
		if key == "review_submit":
			status = NEEDS_ATTENTION if preceding and not complete else NOT_STARTED
		elif complete:
			status = COMPLETE
		else:
			status = NEEDS_ATTENTION if _started(key, version, package) else NOT_STARTED
		tasks.append({"key": key, "label": label, "status": status, "complete": complete, "groups": list(task_groups)})
	return {
		"findings": [f.as_dict() for f in findings],
		"groups": groups,
		"tasks": tasks,
		"ready": groups["review_submit"]["complete"],
		"blocking_count": sum(1 for f in findings if f.severity == BLOCKING),
		"warning_count": sum(1 for f in findings if f.severity == WARNING),
	}
