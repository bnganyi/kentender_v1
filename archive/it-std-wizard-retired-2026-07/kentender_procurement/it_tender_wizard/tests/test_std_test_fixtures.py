# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Regression tests for IT Wizard shared STD fixtures."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.it_tender_wizard.tests.std_test_fixtures import (
	canonical_it_std_is_active,
	ensure_canonical_it_std_active_for_tests,
)
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter


class TestStdTestFixtures(IntegrationTestCase):
	def test_skips_commit_importer_when_canonical_std_already_active(self) -> None:
		if not frappe.db.exists("STD Version", CANONICAL_PACKAGE_ID):
			self.skipTest("Canonical STD Version not on site")
		if not canonical_it_std_is_active():
			ensure_canonical_it_std_active_for_tests(force=True)

		with patch.object(CommitImporter, "run") as importer_run:
			ensure_canonical_it_std_active_for_tests()
			importer_run.assert_not_called()

		self.assertTrue(canonical_it_std_is_active())
