# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0510 — centralized audit event catalogue."""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.events import codes as derived_codes
from kentender_procurement.tender_management.security.audit.event_catalog import (
	ALL_AUDIT_EVENT_CODES,
	APPROVAL_PUBLICATION_EVENTS,
	AuditEventCode,
	DERIVED_MODEL_EVENTS,
	EVIDENCE_AUDIT_EVENTS,
	RELEASE_EVENTS,
	STD_INSTANCE_COMPLETION_EVENTS,
	STD_LIBRARY_TEMPLATE_EVENTS,
	is_known_audit_event_code,
)
from kentender_procurement.tender_management.tender_publication.audit import codes as pub_codes


class TestSecAuditEventCatalog0510(IntegrationTestCase):
	def test_sec_0510_required_groups_present(self) -> None:
		self.assertEqual(len(STD_LIBRARY_TEMPLATE_EVENTS), 10)
		self.assertEqual(len(RELEASE_EVENTS), 8)
		self.assertEqual(len(STD_INSTANCE_COMPLETION_EVENTS), 12)
		self.assertEqual(len(DERIVED_MODEL_EVENTS), 7)
		self.assertEqual(len(APPROVAL_PUBLICATION_EVENTS), 12)
		self.assertEqual(len(EVIDENCE_AUDIT_EVENTS), 5)

	def test_sec_0510_known_codes_lookup(self) -> None:
		self.assertTrue(is_known_audit_event_code("STD_PACKAGE_IMPORTED"))
		self.assertTrue(is_known_audit_event_code(AuditEventCode.TENDER_PUBLISHED))
		self.assertFalse(is_known_audit_event_code("NOT_REAL_EVENT"))

	def test_sec_0510_catalog_has_no_duplicates(self) -> None:
		all_from_groups = (
			STD_LIBRARY_TEMPLATE_EVENTS
			| RELEASE_EVENTS
			| STD_INSTANCE_COMPLETION_EVENTS
			| DERIVED_MODEL_EVENTS
			| APPROVAL_PUBLICATION_EVENTS
			| EVIDENCE_AUDIT_EVENTS
		)
		self.assertEqual(ALL_AUDIT_EVENT_CODES, all_from_groups)
		self.assertEqual(len(ALL_AUDIT_EVENT_CODES), len(set(ALL_AUDIT_EVENT_CODES)))

	def test_sec_0510_derived_codes_use_catalog_constants(self) -> None:
		self.assertEqual(derived_codes.DERIVED_MODEL_GENERATED, AuditEventCode.DERIVED_MODEL_GENERATED)
		self.assertEqual(derived_codes.DERIVED_MODEL_CONSUMPTION_DENIED, AuditEventCode.DERIVED_MODEL_CONSUMPTION_DENIED)

	def test_sec_0510_publication_pack_codes_use_catalog_constants(self) -> None:
		self.assertEqual(pub_codes.PACK_PUBLICATION_READINESS_RUN, AuditEventCode.PUBLICATION_READINESS_RUN)
		self.assertEqual(pub_codes.PACK_TENDER_PUBLISHED, AuditEventCode.TENDER_PUBLISHED)
		self.assertEqual(pub_codes.PACK_EVIDENCE_PACKAGE_EXPORTED, AuditEventCode.EVIDENCE_PACKAGE_EXPORTED)
