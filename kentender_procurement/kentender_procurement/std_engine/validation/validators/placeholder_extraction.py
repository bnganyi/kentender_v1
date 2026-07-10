# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Detect placeholder extraction markers across package payloads."""

from __future__ import annotations

import json

import frappe

from kentender_procurement.std_engine.validation.finding_spec import ValidationFindingSpec
from kentender_procurement.std_engine.validation.validators.clause_text_hash import (
	_status_has_placeholder_marker,
)
from kentender_procurement.std_engine.validation.validators.context import ValidationContext


class PlaceholderExtractionValidator:
	validator_code = "placeholder_extraction"

	def validate(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		findings: list[ValidationFindingSpec] = []
		if context.inspection:
			for key, payload in context.inspection.parsed_payloads.items():
				records = (payload or {}).get("records") or []
				for record in records:
					findings.extend(self._scan_record(key, record))
		if context.db_checks_enabled:
			for doctype in ("STD Render Block", "STD Form Schema"):
				for row in frappe.get_all(
					doctype,
					filters={"package_id": context.package_id},
					fields=["name", "object_key", "metadata_json", "validation_status"],
				):
					findings.extend(
						self._scan_record(
							doctype,
							{
								**(json.loads(row.get("metadata_json") or "{}")),
								"object_key": row.get("object_key") or row["name"],
								"validation_status": row.get("validation_status"),
							},
						)
					)
		return findings

	def _scan_record(self, bucket: str, record: dict) -> list[ValidationFindingSpec]:
		findings: list[ValidationFindingSpec] = []
		object_id = str(record.get("object_key") or record.get("clause_key") or record.get("form_key") or "unknown")
		for field in ("template_status", "text_status", "extraction_status", "validation_status"):
			value = str(record.get(field) or "").upper()
			if not value:
				continue
			if _status_has_placeholder_marker(value):
				findings.append(
					ValidationFindingSpec(
						finding_code="EXTRACTION_PLACEHOLDER",
						severity="BLOCKER",
						object_type=str(bucket),
						object_id=object_id,
						description=f"Placeholder extraction marker detected in {bucket}.{field}: {object_id}",
						lifecycle_gate="ACTIVATION",
					)
				)
		return findings
