# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Contract Management test base (plan D18; tracker CM8-314).

`ContractCase` gives a test class: the `CM_TEST` fixture namespace, a per-test wipe of only that namespace's Contract Management rows (Python tests have no
rollback on this bench), and -- when `native = True` -- the ERPNext world of `native_world.py` built **once per class** and removed at its end (MariaDB test
site only). Native documents are never mocked in a test that claims native behaviour; synthetic sources (`synthetic.py`) are for development progress and
never prove package acceptance. Run on `kentender-test.local`, one module at a time, never while a Playwright process is active (`make cm-preflight`)."""

from __future__ import annotations

import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_contracts.services import records
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import synthetic

NAMESPACE = "CM_TEST"


class ContractCase(IntegrationTestCase):
	native = False  # set True on a class that needs the ERPNext world

	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		if cls.native:
			if frappe.db.db_type != "mariadb":
				raise unittest.SkipTest("native tests run on the MariaDB test site")
			world.build()
			cls.addClassCleanup(cls._remove_world)

	@staticmethod
	def _remove_world() -> None:
		failed = world.teardown()
		if failed:
			print("native world: could not remove", failed)

	def setUp(self) -> None:
		super().setUp()
		frappe.flags.kt_cm_fixture_namespace = NAMESPACE
		self.addCleanup(self._wipe)

	def _wipe(self) -> None:
		frappe.flags.kt_cm_fixture_namespace = ""
		records.wipe(NAMESPACE)
		frappe.db.commit()

	def new_case(self, contract_id: str = "CM-TEST-1", **values):
		"""A Contract Case in the test namespace, committed."""
		doc = records.new("Contract Case", contract_id=contract_id, source_kind=values.pop("source_kind", "External record"), **values)
		frappe.db.commit()
		return doc

	@staticmethod
	def award_package() -> dict:
		return synthetic.award_package()

	@staticmethod
	def source_provider(**kw) -> synthetic.Provider:
		return synthetic.Provider(**kw)
