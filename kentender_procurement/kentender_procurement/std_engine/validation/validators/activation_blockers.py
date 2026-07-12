# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Dynamic activation gate findings — unresolved gates only."""

from __future__ import annotations

import frappe

from kentender_procurement.std_engine.constants import LEGAL_REVIEW_APPROVED
from kentender_procurement.std_engine.validation.finding_spec import ValidationFindingSpec
from kentender_procurement.std_engine.validation.validators.context import ValidationContext


class ActivationBlockersValidator:
	validator_code = "activation_blockers"

	def validate(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		if not context.db_checks_enabled:
			return self._validate_from_inspection(context)

		package_id = context.package_id
		findings: list[ValidationFindingSpec] = []

		pending_clauses = frappe.db.count(
			"STD Clause",
			{"package_id": package_id, "validation_status": ["!=", LEGAL_REVIEW_APPROVED]},
		)
		if pending_clauses:
			findings.append(
				ValidationFindingSpec(
					finding_code="ACTIVATION_LEGAL_REVIEW_PENDING",
					severity="BLOCKER",
					object_type="STD Version",
					object_id=package_id,
					description=f"Legal review pending for {pending_clauses} clause(s).",
					lifecycle_gate="ACTIVATION",
				)
			)

		pending_params = frappe.db.sql(
			"""
			SELECT COUNT(*) FROM `tabSTD Parameter`
			WHERE package_id = %s
			  AND validation_status != %s
			  AND (
				parameter_key LIKE %s
				OR parameter_key LIKE %s
			  )
			""",
			(package_id, LEGAL_REVIEW_APPROVED, "%.parameter.tds.%", "%.parameter.scc.%"),
		)[0][0]
		if int(pending_params or 0) > 0:
			findings.append(
				ValidationFindingSpec(
					finding_code="ACTIVATION_PARAMETER_REVIEW_PENDING",
					severity="BLOCKER",
					object_type="STD Version",
					object_id=package_id,
					description=f"Legal review pending for {pending_params} TDS/SCC parameter(s).",
					lifecycle_gate="ACTIVATION",
				)
			)

		if not frappe.db.count("STD Source Document", {"package_id": package_id}):
			findings.append(
				ValidationFindingSpec(
					finding_code="ACTIVATION_SOURCE_DOCUMENT_MISSING",
					severity="BLOCKER",
					object_type="STD Version",
					object_id=package_id,
					description="Official source document must be registered before activation.",
					lifecycle_gate="ACTIVATION",
				)
			)

		return findings

	def _validate_from_inspection(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		inspection = context.inspection
		if not inspection:
			return []
		findings: list[ValidationFindingSpec] = []
		for index, description in enumerate(inspection.activation_blockers or [], start=1):
			findings.append(
				ValidationFindingSpec(
					finding_code=f"ACTIVATION_BLOCKER_{index:03d}",
					severity="BLOCKER",
					object_type="STD Version",
					object_id=context.package_id,
					description=description,
					lifecycle_gate="ACTIVATION",
				)
			)
		return findings
