# Copyright (c) 2026, KenTender and contributors

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.procuring_entity_canonical import (
	CANONICAL_MOH_ENTITY,
	LEGACY_MOH_ENTITY,
	normalize_procuring_entity,
)
from kentender_core.seeds._common import ensure_procuring_entity


class TestProcuringEntityCanonical(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_procuring_entity(LEGACY_MOH_ENTITY, "Ministry of Health Legacy")
		ensure_procuring_entity(CANONICAL_MOH_ENTITY, "Ministry of Health")

	def test_normalize_moh_to_pe_moh(self):
		self.assertEqual(normalize_procuring_entity(LEGACY_MOH_ENTITY), CANONICAL_MOH_ENTITY)

	def test_canonical_entity_unchanged(self):
		self.assertEqual(normalize_procuring_entity(CANONICAL_MOH_ENTITY), CANONICAL_MOH_ENTITY)

	def test_other_entity_unchanged(self):
		other = ensure_procuring_entity("PE-TEST-001", "Test Entity")
		self.assertEqual(normalize_procuring_entity(other), other)
