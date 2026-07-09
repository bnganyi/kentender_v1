# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Clause and section anchor coverage checks."""

from __future__ import annotations

import frappe

from kentender_procurement.std_engine.validation.finding_spec import ValidationFindingSpec
from kentender_procurement.std_engine.validation.validators.context import ValidationContext


class ClauseCoverageValidator:
	validator_code = "clause_coverage"

	def validate(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		if context.db_checks_enabled:
			return self._validate_from_database(context)
		return self._validate_from_inspection(context)

	def _validate_from_inspection(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		inspection = context.inspection
		assert inspection is not None
		clauses = (inspection.parsed_payloads.get("clauses") or {}).get("records") or []
		anchors = (inspection.parsed_payloads.get("source_anchors") or {}).get("records") or []
		anchor_keys = {
			str(record.get("source_anchor_key") or record.get("anchor_key") or "")
			for record in anchors
		}
		findings: list[ValidationFindingSpec] = []
		for clause in clauses:
			clause_key = str(clause.get("clause_key") or clause.get("clause_id") or "unknown")
			anchor_key = str(clause.get("source_anchor_key") or "")
			if not anchor_key:
				findings.append(
					ValidationFindingSpec(
						finding_code="CLAUSE_MISSING_ANCHOR",
						severity="WARNING",
						object_type="STD Clause",
						object_id=clause_key,
						description=f"Clause missing source_anchor_key: {clause_key}",
						lifecycle_gate="IMPORT",
					)
				)
				continue
			if anchor_key not in anchor_keys:
				findings.append(
					ValidationFindingSpec(
						finding_code="CLAUSE_DANGLING_ANCHOR",
						severity="WARNING",
						object_type="STD Clause",
						object_id=clause_key,
						description=f"Clause references missing source anchor ({anchor_key}): {clause_key}",
						lifecycle_gate="IMPORT",
					)
				)
		return findings

	def _validate_from_database(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		findings: list[ValidationFindingSpec] = []
		clauses = frappe.get_all(
			"STD Clause",
			filters={"package_id": context.package_id},
			fields=["name", "clause_key", "source_anchor", "section"],
		)
		for clause in clauses:
			if not clause.get("source_anchor"):
				findings.append(
					ValidationFindingSpec(
						finding_code="CLAUSE_MISSING_ANCHOR",
						severity="WARNING",
						object_type="STD Clause",
						object_id=clause["name"],
						description=f"Persisted clause {clause['name']} has no source_anchor link",
						lifecycle_gate="IMPORT",
					)
				)
				continue
			if not frappe.db.exists("STD Source Anchor", clause["source_anchor"]):
				findings.append(
					ValidationFindingSpec(
						finding_code="CLAUSE_DANGLING_ANCHOR",
						severity="WARNING",
						object_type="STD Clause",
						object_id=clause["name"],
						description=f"Persisted clause {clause['name']} references missing anchor {clause['source_anchor']}",
						lifecycle_gate="IMPORT",
					)
				)
			if clause.get("section") and not frappe.db.exists("STD Section", clause["section"]):
				findings.append(
					ValidationFindingSpec(
						finding_code="CLAUSE_MISSING_SECTION",
						severity="BLOCKER",
						object_type="STD Clause",
						object_id=clause["name"],
						description=f"Persisted clause {clause['name']} references missing section {clause['section']}",
						lifecycle_gate="IMPORT",
					)
				)
		return findings
