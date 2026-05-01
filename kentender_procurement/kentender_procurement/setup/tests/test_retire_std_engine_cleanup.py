# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.patches.retire_std_engine_cleanup import execute


class TestRetireStdEngineCleanup(IntegrationTestCase):
	def test_retire_std_engine_cleanup_runs_idempotent(self):
		frappe.set_user("Administrator")
		execute()
		execute()
