# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Source document and anchor traceability checks."""

from __future__ import annotations

import frappe

from kentender_procurement.std_engine.validation.finding_spec import ValidationFindingSpec
from kentender_procurement.std_engine.validation.validators.context import ValidationContext


class SourceTraceabilityValidator:
	validator_code = "source_traceability"

	def validate(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		if not context.db_checks_enabled:
			return []

		findings: list[ValidationFindingSpec] = []
		official_docs = frappe.get_all(
			"STD Source Document",
			filters={"package_id": context.package_id, "source_role": "LEGAL_MASTER_SOURCE"},
			fields=["name", "source_document_key", "source_hash", "filename"],
		)
		if not official_docs:
			findings.append(
				ValidationFindingSpec(
					finding_code="OFFICIAL_SOURCE_MISSING",
					severity="BLOCKER",
					object_type="STD Version",
					object_id=context.package_id,
					description="Official LEGAL_MASTER_SOURCE document is not registered for this package",
					lifecycle_gate="ACTIVATION",
					suggested_fix="Register the official PPRA source PDF during package import",
				)
			)
		else:
			for doc in official_docs:
				if not doc.get("source_hash"):
					findings.append(
						ValidationFindingSpec(
							finding_code="OFFICIAL_SOURCE_HASH_MISSING",
							severity="BLOCKER",
							object_type="STD Source Document",
							object_id=doc["name"],
							description=f"Official source document {doc['name']} is missing source_hash",
							lifecycle_gate="ACTIVATION",
						)
					)

		anchors = frappe.get_all(
			"STD Source Anchor",
			filters={"package_id": context.package_id},
			fields=["name", "source_document"],
		)
		for anchor in anchors:
			source_document = anchor.get("source_document")
			if not source_document or not frappe.db.exists("STD Source Document", source_document):
				findings.append(
					ValidationFindingSpec(
						finding_code="ANCHOR_SOURCE_DOCUMENT_MISSING",
						severity="WARNING",
						object_type="STD Source Anchor",
						object_id=anchor["name"],
						description=f"Source anchor {anchor['name']} references missing source document",
						lifecycle_gate="IMPORT",
					)
				)
		return findings
