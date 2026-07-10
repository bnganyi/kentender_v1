# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Reject register-synthesized clause text in verbatim packages."""

from __future__ import annotations

import frappe

from kentender_procurement.std_engine.validation.finding_spec import ValidationFindingSpec
from kentender_procurement.std_engine.validation.validators.context import ValidationContext

SYNTHETIC_MARKER = (
	"This clause forms part of the Instructions to Tenderers for procurement of information technology "
	"under the Standard Tender Document issued by the Public Procurement Regulatory Authority."
)


class VerbatimSourceValidator:
	validator_code = "verbatim_source"

	def validate(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		if context.db_checks_enabled:
			return self._validate_from_database(context)
		return self._validate_from_inspection(context)

	def _validate_from_inspection(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		clauses = (context.inspection.parsed_payloads.get("clauses") or {}).get("records") or []
		return self._validate_records(clauses)

	def _validate_from_database(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		rows = frappe.get_all(
			"STD Clause",
			filters={"package_id": context.package_id},
			fields=["clause_key", "clause_text", "metadata_json"],
		)
		records: list[dict] = []
		for row in rows:
			metadata = {}
			raw = row.get("metadata_json")
			if raw:
				try:
					import json

					metadata = json.loads(raw)
				except json.JSONDecodeError:
					metadata = {}
			records.append(
				{
					"clause_key": row.get("clause_key") or row["name"],
					"full_clause_text": row.get("clause_text"),
					"clause_text_source": metadata.get("clause_text_source"),
				}
			)
		return self._validate_records(records)

	def _validate_records(self, clauses: list[dict]) -> list[ValidationFindingSpec]:
		findings: list[ValidationFindingSpec] = []
		for clause in clauses:
			clause_key = str(clause.get("clause_key") or "unknown")
			source = str(clause.get("clause_text_source") or "").strip()
			text = str(clause.get("full_clause_text") or clause.get("clause_text") or "")
			if source and source != "PDF_VERBATIM":
				findings.append(
					ValidationFindingSpec(
						finding_code="SOURCE_TEXT_MISMATCH",
						severity="BLOCKER",
						object_type="STD Clause",
						object_id=clause_key,
						description=f"Clause text source must be PDF_VERBATIM, found {source}",
						lifecycle_gate="ACTIVATION",
					)
				)
			if SYNTHETIC_MARKER in text:
				findings.append(
					ValidationFindingSpec(
						finding_code="SOURCE_TEXT_MISMATCH",
						severity="BLOCKER",
						object_type="STD Clause",
						object_id=clause_key,
						description=f"Synthetic template marker detected in clause text: {clause_key}",
						lifecycle_gate="ACTIVATION",
					)
				)
		return findings
