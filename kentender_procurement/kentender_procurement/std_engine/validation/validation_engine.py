# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Run STD validators and persist validation runs + findings."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import frappe

from kentender_procurement.std_engine.validation.finding_spec import ValidationFindingSpec
from kentender_procurement.std_engine.validation.validators.activation_blockers import (
	ActivationBlockersValidator,
)
from kentender_procurement.std_engine.validation.validators.clause_coverage import (
	ClauseCoverageValidator,
)
from kentender_procurement.std_engine.validation.validators.context import ValidationContext
from kentender_procurement.std_engine.validation.validators.package_integrity import (
	PackageIntegrityValidator,
)
from kentender_procurement.std_engine.validation.validators.source_traceability import (
	SourceTraceabilityValidator,
)

from kentender_procurement.std_engine.validation.validators.clause_text_hash import (
	ClauseTextHashValidator,
)
from kentender_procurement.std_engine.validation.validators.parameter_render_binding import (
	ParameterRenderBindingValidator,
)
from kentender_procurement.std_engine.validation.validators.placeholder_extraction import (
	PlaceholderExtractionValidator,
)
from kentender_procurement.std_engine.validation.validators.tender_instance_readiness import (
	EvaluationCriteriaValidator,
	TenderInstanceReadinessValidator,
)

from kentender_procurement.std_engine.validation.validators.legal_review_gate import (
	LegalReviewGateValidator,
)
from kentender_procurement.std_engine.validation.validators.pass_register_reconciliation import (
	PassRegisterReconciliationValidator,
)
from kentender_procurement.std_engine.validation.validators.verbatim_source import (
	VerbatimSourceValidator,
)

DEFAULT_VALIDATORS = (
	ActivationBlockersValidator(),
	PackageIntegrityValidator(),
	SourceTraceabilityValidator(),
	ClauseCoverageValidator(),
	ClauseTextHashValidator(),
	VerbatimSourceValidator(),
	PassRegisterReconciliationValidator(),
	LegalReviewGateValidator(),
	PlaceholderExtractionValidator(),
	ParameterRenderBindingValidator(),
	EvaluationCriteriaValidator(),
	TenderInstanceReadinessValidator(),
)


@dataclass
class ValidationRunResult:
	package_id: str
	run_key: str
	status: str
	summary: dict[str, int] = field(default_factory=dict)
	findings: list[dict[str, Any]] = field(default_factory=list)


class ValidationEngine:
	def __init__(self, validators=DEFAULT_VALIDATORS) -> None:
		self.validators = validators

	def run_for_package(
		self,
		package_id: str,
		*,
		dry_report: dict[str, Any] | None = None,
		inspection=None,
		run_type: str = "POST_IMPORT",
		db_checks_enabled: bool = True,
	) -> ValidationRunResult:
		if not package_id:
			raise ValueError("package_id is required")

		context = ValidationContext(
			package_id=package_id,
			dry_report=dry_report,
			inspection=inspection,
			db_checks_enabled=db_checks_enabled,
		)
		specs = self.collect_findings(context)
		return self.persist_findings(
			package_id,
			specs,
			run_type=run_type,
		)

	def collect_findings(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		specs: list[ValidationFindingSpec] = []
		seen_keys: set[str] = set()
		for validator in self.validators:
			for spec in validator.validate(context):
				key = spec.finding_key(context.package_id)
				if key in seen_keys:
					continue
				seen_keys.add(key)
				specs.append(spec)
		return specs

	def persist_findings(
		self,
		package_id: str,
		specs: list[ValidationFindingSpec],
		*,
		run_type: str,
	) -> ValidationRunResult:
		run_key = f"VAL-{package_id}"
		now = datetime.now(timezone.utc).replace(tzinfo=None)

		if frappe.db.exists("STD Validation Run", run_key):
			frappe.db.set_value(
				"STD Validation Run",
				run_key,
				{
					"status": "COMPLETED",
					"run_type": run_type,
					"completed_at": now,
				},
				update_modified=False,
			)
		else:
			frappe.get_doc(
				{
					"doctype": "STD Validation Run",
					"package_id": package_id,
					"run_key": run_key,
					"run_type": run_type,
					"status": "COMPLETED",
					"started_at": now,
					"completed_at": now,
					"summary_json": "{}",
				}
			).insert(ignore_permissions=True)

		persisted: list[dict[str, Any]] = []
		active_keys = {spec.finding_key(package_id) for spec in specs}
		for spec in specs:
			finding_key = spec.finding_key(package_id)
			if frappe.db.exists("STD Validation Finding", finding_key):
				frappe.db.set_value(
					"STD Validation Finding",
					finding_key,
					{
						"severity": spec.severity,
						"description": spec.description,
						"suggested_fix": spec.suggested_fix,
						"lifecycle_gate": spec.lifecycle_gate,
						"status": "OPEN",
					},
					update_modified=False,
				)
				persisted.append(_finding_row(finding_key))
				continue
			doc = frappe.get_doc(
				{
					"doctype": "STD Validation Finding",
					"package_id": package_id,
					"finding_key": finding_key,
					"validation_run": run_key,
					"severity": spec.severity,
					"finding_code": spec.finding_code,
					"object_type": spec.object_type,
					"object_id": spec.object_id,
					"description": spec.description,
					"suggested_fix": spec.suggested_fix,
					"lifecycle_gate": spec.lifecycle_gate,
					"status": "OPEN",
				}
			)
			doc.insert(ignore_permissions=True)
			persisted.append(_finding_row(finding_key))

		for stale in frappe.get_all(
			"STD Validation Finding",
			filters={"package_id": package_id, "status": "OPEN"},
			pluck="name",
		):
			if stale not in active_keys:
				frappe.db.set_value("STD Validation Finding", stale, "status", "RESOLVED", update_modified=False)

		summary = _summary_from_database(package_id)
		frappe.db.set_value(
			"STD Validation Run",
			run_key,
			"summary_json",
			json.dumps(summary, sort_keys=True),
			update_modified=False,
		)

		if frappe.db.exists("STD Version", package_id):
			frappe.db.set_value(
				"STD Version",
				package_id,
				"validation_status",
				_resolve_version_validation_status(summary),
				update_modified=False,
			)
			from kentender_procurement.std_engine.services.activation_readiness_service import (
				sync_activation_flags,
			)

			sync_activation_flags(package_id)

		return ValidationRunResult(
			package_id=package_id,
			run_key=run_key,
			status="COMPLETED",
			summary=summary,
			findings=persisted,
		)


def summarize_findings(specs: list[ValidationFindingSpec]) -> dict[str, int]:
	summary = {"blockers": 0, "warnings": 0, "info": 0}
	for spec in specs:
		severity = (spec.severity or "").upper()
		if severity == "BLOCKER":
			summary["blockers"] += 1
		elif severity == "WARNING":
			summary["warnings"] += 1
		else:
			summary["info"] += 1
	return summary


def get_validation_summary(package_id: str) -> dict[str, int]:
	run_key = f"VAL-{package_id}"
	if not frappe.db.exists("STD Validation Run", run_key):
		return {"blockers": 0, "warnings": 0, "info": 0}
	summary_json = frappe.db.get_value("STD Validation Run", run_key, "summary_json") or "{}"
	try:
		summary = json.loads(summary_json)
	except json.JSONDecodeError:
		summary = {}
	return {
		"blockers": int(summary.get("blockers") or 0),
		"warnings": int(summary.get("warnings") or 0),
		"info": int(summary.get("info") or 0),
	}


def _summary_from_database(package_id: str) -> dict[str, int]:
	rows = frappe.get_all(
		"STD Validation Finding",
		filters={"package_id": package_id, "status": "OPEN"},
		fields=["severity"],
	)
	summary = {"blockers": 0, "warnings": 0, "info": 0}
	for row in rows:
		severity = (row.get("severity") or "").upper()
		if severity == "BLOCKER":
			summary["blockers"] += 1
		elif severity == "WARNING":
			summary["warnings"] += 1
		else:
			summary["info"] += 1
	return summary


def _resolve_version_validation_status(summary: dict[str, int]) -> str:
	if summary.get("blockers", 0) > 0:
		return "BLOCKED"
	if summary.get("warnings", 0) > 0:
		return "WARNINGS"
	return "CLEAR"


def _finding_row(finding_key: str) -> dict[str, Any]:
	return frappe.db.get_value(
		"STD Validation Finding",
		finding_key,
		[
			"finding_key",
			"finding_code",
			"severity",
			"object_type",
			"object_id",
			"description",
			"lifecycle_gate",
			"status",
		],
		as_dict=True,
	) or {}
