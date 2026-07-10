# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Evaluation criteria and tender-instance readiness checks."""

from __future__ import annotations

import json

import frappe

from kentender_procurement.std_engine.validation.finding_spec import ValidationFindingSpec
from kentender_procurement.std_engine.validation.validators.context import ValidationContext


class EvaluationCriteriaValidator:
	validator_code = "evaluation_criteria"

	def validate(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		findings: list[ValidationFindingSpec] = []
		schemas = []
		if context.inspection:
			schemas = (context.inspection.parsed_payloads.get("evaluation_schemas") or {}).get("records") or []
		elif context.db_checks_enabled:
			for row in frappe.get_all(
				"STD Evaluation Schema",
				filters={"package_id": context.package_id},
				fields=["evaluation_schema_key", "metadata_json"],
			):
				meta = json.loads(row.get("metadata_json") or "{}")
				meta["evaluation_schema_key"] = row["evaluation_schema_key"]
				schemas.append(meta)
		for schema in schemas:
			criteria = schema.get("criteria") or []
			schema_key = str(schema.get("evaluation_schema_key") or "unknown")
			if not criteria:
				findings.append(
					ValidationFindingSpec(
						finding_code="EVALUATION_CRITERION_UNMAPPED",
						severity="BLOCKER",
						object_type="STD Evaluation Schema",
						object_id=schema_key,
						description=f"Evaluation schema has no criteria: {schema_key}",
						lifecycle_gate="ACTIVATION",
					)
				)
		return findings


class TenderInstanceReadinessValidator:
	validator_code = "tender_instance_readiness"

	def validate(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		findings: list[ValidationFindingSpec] = []
		if not context.inspection:
			return findings
		optional = getattr(context.inspection, "parsed_payloads", {})
		instances = (optional.get("sample_tender_instances") or {}).get("records") or []
		if not instances:
			findings.append(
				ValidationFindingSpec(
					finding_code="SAMPLE_TENDER_INSTANCE_MISSING",
					severity="BLOCKER",
					object_type="STD Package",
					object_id=context.package_id,
					description="Package is missing sample_tender_instances.json records",
					lifecycle_gate="ACTIVATION",
				)
			)
		return findings
