# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Surface verbatim reconciliation blockers from package tests payload."""

from __future__ import annotations

import frappe

from kentender_procurement.std_engine.validation.finding_spec import ValidationFindingSpec
from kentender_procurement.std_engine.validation.validators.context import ValidationContext

RECONCILIATION_BLOCKER_CODES = {
	"CLAUSE_TEXT_MISSING",
	"PARAMETER_SOURCE_TEXT_MISSING",
	"EXTRACTION_LOW_CONFIDENCE",
	"ANCHOR_DRIFT",
	"PARAMETER_SOURCE_MISMATCH",
	"SOURCE_TEXT_MISMATCH",
}


class PassRegisterReconciliationValidator:
	validator_code = "pass_register_reconciliation"

	def validate(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		payload = self._load_reconciliation(context)
		if not payload:
			return []
		findings: list[ValidationFindingSpec] = []
		for row in payload.get("findings") or []:
			code = str(row.get("finding_code") or "")
			if code not in RECONCILIATION_BLOCKER_CODES:
				continue
			severity = str(row.get("severity") or "WARNING").upper()
			if severity not in {"BLOCKER", "WARNING", "INFO"}:
				severity = "WARNING"
			findings.append(
				ValidationFindingSpec(
					finding_code=code,
					severity=severity,
					object_type=str(row.get("object_type") or "STD Package"),
					object_id=str(row.get("object_id") or context.package_id),
					description=str(row.get("description") or code),
					lifecycle_gate=str(row.get("lifecycle_gate") or "ACTIVATION"),
				)
			)
		return findings

	def _load_reconciliation(self, context: ValidationContext) -> dict | None:
		if context.inspection:
			payload = context.inspection.parsed_payloads.get("verbatim_reconciliation")
			if isinstance(payload, dict):
				return payload
		path = frappe.db.get_value("STD Version", context.package_id, "metadata_json")
		if path:
			try:
				import json

				meta = json.loads(path)
				if isinstance(meta.get("verbatim_reconciliation"), dict):
					return meta["verbatim_reconciliation"]
			except json.JSONDecodeError:
				pass
		return context.extra.get("verbatim_reconciliation")
