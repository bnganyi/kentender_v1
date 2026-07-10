# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Block activation until legal reviewer approves verbatim clauses and parameters."""

from __future__ import annotations

import json

import frappe

from kentender_procurement.std_engine.validation.finding_spec import ValidationFindingSpec
from kentender_procurement.std_engine.validation.validators.context import ValidationContext

APPROVED_STATUS = "LEGAL_REVIEW_APPROVED"
PENDING_STATUSES = {"PENDING_LEGAL_REVIEW", "MISMATCH_FLAGGED"}


class LegalReviewGateValidator:
	validator_code = "legal_review_gate"

	def validate(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		if context.db_checks_enabled:
			return self._validate_from_database(context)
		return self._validate_from_inspection(context)

	def _validate_from_inspection(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		clauses = (context.inspection.parsed_payloads.get("clauses") or {}).get("records") or []
		parameters = (context.inspection.parsed_payloads.get("parameters") or {}).get("records") or []
		return self._validate_records(clauses, parameters)

	def _validate_from_database(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		clauses = frappe.get_all(
			"STD Clause",
			filters={"package_id": context.package_id},
			fields=["clause_key", "validation_status", "metadata_json"],
		)
		parameters = frappe.get_all(
			"STD Parameter",
			filters={"package_id": context.package_id},
			fields=["parameter_key", "validation_status", "metadata_json"],
		)
		clause_records = [
			{
				"clause_key": row.get("clause_key") or row["name"],
				"clause_code": self._clause_code(row),
				"verification_status": self._resolve_status(row),
			}
			for row in clauses
		]
		param_records = [
			{
				"parameter_key": row.get("parameter_key") or row["name"],
				"parameter_code": self._parameter_code(row),
				"verification_status": self._resolve_status(row),
				"section": self._parameter_section(row),
			}
			for row in parameters
		]
		return self._validate_records(clause_records, param_records)

	def _clause_code(self, row: dict) -> str:
		raw = row.get("metadata_json")
		if raw:
			try:
				metadata = json.loads(raw)
			except json.JSONDecodeError:
				metadata = {}
			code = metadata.get("clause_code")
			if code:
				return str(code)
		return str(row.get("clause_key") or row.get("name") or "unknown")

	def _parameter_code(self, row: dict) -> str:
		raw = row.get("metadata_json")
		if raw:
			try:
				metadata = json.loads(raw)
			except json.JSONDecodeError:
				metadata = {}
			code = metadata.get("parameter_code")
			if code:
				return str(code)
		return str(row.get("parameter_key") or row.get("name") or "unknown")

	def _resolve_status(self, row: dict) -> str:
		status = str(row.get("validation_status") or "").strip()
		if status:
			return status
		raw = row.get("metadata_json")
		if not raw:
			return ""
		try:
			metadata = json.loads(raw)
		except json.JSONDecodeError:
			return ""
		return str(metadata.get("verification_status") or metadata.get("text_status") or "")

	def _parameter_section(self, row: dict) -> str:
		raw = row.get("metadata_json")
		if not raw:
			return ""
		try:
			metadata = json.loads(raw)
		except json.JSONDecodeError:
			return ""
		section_key = str(metadata.get("applies_to_section_key") or "")
		if ".section.tds" in section_key:
			return "TDS"
		if ".section.scc" in section_key:
			return "SCC"
		code = str(metadata.get("parameter_code") or row.get("parameter_key") or "")
		if code.startswith("TDS-"):
			return "TDS"
		if code.startswith("SCC-"):
			return "SCC"
		return ""

	def _validate_records(
		self,
		clauses: list[dict],
		parameters: list[dict],
	) -> list[ValidationFindingSpec]:
		findings: list[ValidationFindingSpec] = []
		for clause in clauses:
			status = str(clause.get("verification_status") or "").strip().upper()
			if status == APPROVED_STATUS:
				continue
			object_id = str(clause.get("clause_code") or clause.get("clause_key") or "unknown")
			findings.append(
				ValidationFindingSpec(
					finding_code="LEGAL_REVIEW_PENDING",
					severity="BLOCKER",
					object_type="STD Clause",
					object_id=object_id,
					description=f"Legal reviewer verification pending for {object_id}",
					lifecycle_gate="ACTIVATION",
				)
			)
		for param in parameters:
			section = str(param.get("section") or self._parameter_section(param) or "").upper()
			if section not in {"TDS", "SCC"}:
				continue
			status = str(param.get("verification_status") or "").strip().upper()
			if status == APPROVED_STATUS:
				continue
			object_id = str(param.get("parameter_code") or param.get("parameter_key") or "unknown")
			findings.append(
				ValidationFindingSpec(
					finding_code="LEGAL_REVIEW_PENDING",
					severity="BLOCKER",
					object_type="STD Parameter",
					object_id=object_id,
					description=f"Legal reviewer verification pending for {object_id}",
					lifecycle_gate="ACTIVATION",
				)
			)
		return findings
