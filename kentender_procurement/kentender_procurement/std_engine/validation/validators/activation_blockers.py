# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Persist activation blockers from the package manifest."""

from __future__ import annotations

from kentender_procurement.std_engine.validation.finding_spec import ValidationFindingSpec
from kentender_procurement.std_engine.validation.validators.context import ValidationContext


class ActivationBlockersValidator:
	validator_code = "activation_blockers"

	def validate(self, context: ValidationContext) -> list[ValidationFindingSpec]:
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
