# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TDS/SCC parameter render-binding checks."""

from __future__ import annotations

import frappe

from kentender_procurement.std_engine.validation.finding_spec import ValidationFindingSpec
from kentender_procurement.std_engine.validation.validators.context import ValidationContext


class ParameterRenderBindingValidator:
	validator_code = "parameter_render_binding"

	def validate(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		if context.db_checks_enabled:
			return self._validate_from_database(context)
		return self._validate_from_inspection(context)

	def _validate_from_inspection(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		parameters = (context.inspection.parsed_payloads.get("parameters") or {}).get("records") or []
		return self._validate_records(parameters)

	def _validate_from_database(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		rows = frappe.get_all(
			"STD Parameter",
			filters={"package_id": context.package_id},
			fields=["parameter_key", "metadata_json"],
		)
		import json

		records = []
		for row in rows:
			meta = json.loads(row.get("metadata_json") or "{}")
			meta["parameter_key"] = row["parameter_key"]
			records.append(meta)
		return self._validate_records(records)

	def _validate_records(self, parameters: list[dict]) -> list[ValidationFindingSpec]:
		findings: list[ValidationFindingSpec] = []
		for parameter in parameters:
			parameter_key = str(parameter.get("parameter_key") or "unknown")
			section_key = str(parameter.get("applies_to_section_key") or "")
			if ".section.tds" not in section_key and ".section.scc" not in section_key:
				continue
			render_bindings = parameter.get("render_binding_keys") or []
			if not render_bindings:
				findings.append(
					ValidationFindingSpec(
						finding_code="PARAMETER_UNBOUND",
						severity="BLOCKER",
						object_type="STD Parameter",
						object_id=parameter_key,
						description=f"TDS/SCC parameter missing render bindings: {parameter_key}",
						lifecycle_gate="ACTIVATION",
					)
				)
		return findings
