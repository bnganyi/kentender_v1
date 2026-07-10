# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Locked clause text and hash completeness checks."""

from __future__ import annotations

import frappe

from kentender_procurement.std_engine.validation.finding_spec import ValidationFindingSpec
from kentender_procurement.std_engine.validation.validators.context import ValidationContext

PLACEHOLDER_MARKERS = (
	"PLACEHOLDER",
	"TITLE_EXTRACTED",
	"PENDING",
	"TODO",
)


class ClauseTextHashValidator:
	validator_code = "clause_text_hash"

	def validate(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		if context.db_checks_enabled:
			return self._validate_from_database(context)
		return self._validate_from_inspection(context)

	def _validate_from_inspection(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		clauses = (context.inspection.parsed_payloads.get("clauses") or {}).get("records") or []
		findings: list[ValidationFindingSpec] = []
		for clause in clauses:
			findings.extend(self._validate_clause_record(clause))
		return findings

	def _validate_from_database(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		findings: list[ValidationFindingSpec] = []
		clauses = frappe.get_all(
			"STD Clause",
			filters={"package_id": context.package_id},
			fields=["name", "clause_key", "clause_text", "content_hash", "validation_status"],
		)
		for clause in clauses:
			findings.extend(
				self._validate_clause_record(
					{
						"clause_key": clause.get("clause_key") or clause["name"],
						"full_clause_text": clause.get("clause_text"),
						"normalized_text_hash": clause.get("content_hash"),
						"text_status": clause.get("validation_status"),
					}
				)
			)
		return findings

	def _validate_clause_record(self, clause: dict) -> list[ValidationFindingSpec]:
		findings: list[ValidationFindingSpec] = []
		clause_key = str(clause.get("clause_key") or "unknown")
		text = str(clause.get("full_clause_text") or clause.get("clause_text") or "").strip()
		text_hash = str(clause.get("normalized_text_hash") or clause.get("content_hash") or "").strip()
		status = str(clause.get("text_status") or clause.get("extraction_status") or "").upper()

		if not text:
			findings.append(
				ValidationFindingSpec(
					finding_code="CLAUSE_TEXT_MISSING",
					severity="BLOCKER",
					object_type="STD Clause",
					object_id=clause_key,
					description=f"Locked clause missing full text: {clause_key}",
					lifecycle_gate="ACTIVATION",
				)
			)
		elif any(marker in text.upper() for marker in PLACEHOLDER_MARKERS):
			findings.append(
				ValidationFindingSpec(
					finding_code="EXTRACTION_PLACEHOLDER",
					severity="BLOCKER",
					object_type="STD Clause",
					object_id=clause_key,
					description=f"Clause text still contains placeholder markers: {clause_key}",
					lifecycle_gate="ACTIVATION",
				)
			)

		if not text_hash:
			findings.append(
				ValidationFindingSpec(
					finding_code="TEXT_HASH_MISSING",
					severity="BLOCKER",
					object_type="STD Clause",
					object_id=clause_key,
					description=f"Locked clause missing normalized text hash: {clause_key}",
					lifecycle_gate="ACTIVATION",
				)
			)

		if any(marker in status for marker in PLACEHOLDER_MARKERS):
			findings.append(
				ValidationFindingSpec(
					finding_code="EXTRACTION_PLACEHOLDER",
					severity="BLOCKER",
					object_type="STD Clause",
					object_id=clause_key,
					description=f"Clause extraction status is not complete: {clause_key}",
					lifecycle_gate="ACTIVATION",
				)
			)
		return findings
