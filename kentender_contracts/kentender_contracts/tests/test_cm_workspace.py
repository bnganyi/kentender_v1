# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 §9.0, §10.3, §6.2 (tracker CM8-315): who may open the Contracts workspace, and the shared read it returns. The workspace opens for anyone in some reader
audience (a responsibility at any unit, a supplier binding, a technical account); anyone else gets the stable denial (D-DENIED) as data, not an error; a contract the reader
cannot read is neither listed nor counted."""

from __future__ import annotations

from unittest import mock

import frappe
from frappe.tests import IntegrationTestCase

from kentender_contracts.api import workspace
from kentender_contracts.services import audience, records
from kentender_contracts.tests.test_cm_audience import Fake, SupplierProvider


class TestWorkspaceAudiences(IntegrationTestCase):
	def test_a_site_wide_responsibility_opens_the_workspace(self):
		with Fake({("Finance approval", "")}):
			self.assertEqual(audience.workspace_audiences("f@x"), ["finance"])

	def test_a_unit_responsibility_opens_it_through_any_unit_the_user_is_assigned_to(self):
		with Fake({("Contract preparation", "OU-A")}), mock.patch.object(audience, "assignment_units", return_value=["OU-A"]):
			self.assertEqual(audience.workspace_audiences("p@x"), ["preparer"])
		with Fake({("Contract preparation", "OU-A")}), mock.patch.object(audience, "assignment_units", return_value=["OU-B"]):
			self.assertEqual(audience.workspace_audiences("p@x"), [])

	def test_a_responsibility_without_an_appointment_still_opens_the_workspace_but_reads_no_contract(self):
		with Fake({("Contract inspection", "")}):
			self.assertEqual(audience.workspace_audiences("i@x"), ["appointee"])
			self.assertEqual(audience.grants("i@x", audience.Facts(case="CM-1")), [])

	def test_a_supplier_with_an_active_binding_and_a_technical_account_open_it(self):
		frappe.flags.kt_supplier_account_provider = SupplierProvider({"rep@s": [{"organisation_id": "ORG-1", "responsibility": "Supplier Representative", "active": True}]})
		try:
			with Fake():
				self.assertEqual(audience.workspace_audiences("rep@s"), ["supplier"])
				self.assertEqual(audience.workspace_audiences("stranger@x"), [])
		finally:
			frappe.flags.kt_supplier_account_provider = None
		with Fake(technical=True):
			self.assertEqual(audience.workspace_audiences("daniel@x"), ["technical"])

	def test_a_departmental_author_with_no_contract_relationship_opens_nothing(self):
		with Fake({("Departmental Author", "OU-A")}):
			self.assertEqual(audience.workspace_audiences("grace@x"), [])


class TestWorkspaceRead(IntegrationTestCase):
	def setUp(self):
		frappe.flags.kt_cm_fixture_namespace = "CM_TEST"
		self.addCleanup(self._wipe)

	def _wipe(self):
		frappe.flags.kt_cm_fixture_namespace = ""
		records.wipe("CM_TEST")
		frappe.db.commit()

	def test_the_workspace_is_whitelisted_and_is_a_read(self):
		self.assertIn(workspace.get_contract_workspace, frappe.whitelisted)

	def test_a_reader_with_an_audience_gets_the_empty_workspace_with_their_audiences(self):
		with mock.patch.object(audience, "workspace_audiences", return_value=["office"]), mock.patch.object(audience, "readable", return_value=[]):
			result = workspace.get_contract_workspace()
		self.assertEqual((result["ok"], result["screen"], result["audiences"], result["total"], result["rows"]), (True, "workspace", ["office"], 0, []))

	def test_a_user_with_no_audience_gets_the_stable_denial_as_data(self):
		with mock.patch.object(audience, "workspace_audiences", return_value=[]):
			result = workspace.get_contract_workspace()
		self.assertEqual((result["ok"], result["screen"]), (True, "workspace-forbidden"))
		self.assertNotIn("rows", result)

	def test_a_contract_the_reader_cannot_read_is_neither_listed_nor_counted(self):
		records.new("Contract Case", contract_id="CM-WS-1", source_kind="External record")
		records.new("Contract Case", contract_id="CM-WS-2", source_kind="External record")
		frappe.db.commit()
		readable = {"CM-WS-1"}
		with mock.patch.object(audience, "workspace_audiences", return_value=["office"]), mock.patch.object(audience, "readable", side_effect=lambda user, case, at=None: [audience.Grant("office")] if case in readable else []):
			result = workspace.get_contract_workspace()
		self.assertEqual((result["total"], [r["case"] for r in result["rows"]]), (1, ["CM-WS-1"]))
