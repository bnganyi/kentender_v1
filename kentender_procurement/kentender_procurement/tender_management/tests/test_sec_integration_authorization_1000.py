from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.orchestration import (
	DerivedModelGenerationService,
)
from kentender_procurement.tender_management.security.authorization.integration import (
	enforce_sec_authorization,
)
from kentender_procurement.tender_management.tender_publication.evidence.evidence_package import (
	EvidencePackageService,
)


class TestSecIntegrationAuthorization1000(IntegrationTestCase):
	def test_sec_1000_enforcement_helper_denied_audited(self) -> None:
		with (
			patch(
				"kentender_procurement.tender_management.security.authorization.integration.AuthorizationDecisionEngine.evaluate",
				return_value={
					"allowed": False,
					"denial_code": "STD_AUTH_PERMISSION_DENIED",
					"risk_level": "High",
					"audit_on_attempt": True,
					"message": "blocked",
				},
			),
			patch(
				"kentender_procurement.tender_management.security.authorization.integration.DeniedActionAuditService.record_denied_action"
			) as denied_audit,
		):
			with self.assertRaises(frappe.PermissionError):
				enforce_sec_authorization(
					action_code="PUBLISH_TENDER",
					actor="Administrator",
					object_type="Procurement Tender",
					object_code="PT-SEC-1000",
				)
		denied_audit.assert_called_once()

	def test_sec_1000_generate_output_blocks_on_denial(self) -> None:
		with patch(
			"kentender_procurement.tender_management.derived_models.orchestration.enforce_sec_authorization",
			side_effect=frappe.PermissionError("denied"),
		):
			with self.assertRaises(frappe.PermissionError):
				DerivedModelGenerationService.generate_output("STDINST-SEC-1000", "DSM")

	def test_sec_1000_evidence_export_blocks_on_denial(self) -> None:
		with patch(
			"kentender_procurement.tender_management.tender_publication.evidence.evidence_package.enforce_sec_authorization",
			side_effect=frappe.PermissionError("denied"),
		):
			with self.assertRaises(frappe.PermissionError):
				EvidencePackageService.exportEvidencePackage("PT-SEC-1000", "JSON_MANIFEST")
