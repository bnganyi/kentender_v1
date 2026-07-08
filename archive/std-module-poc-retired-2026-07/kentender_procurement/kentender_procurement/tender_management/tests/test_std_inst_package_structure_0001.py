# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-0001 — ``std_instance`` package imports without circular dependency errors.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_inst_package_structure_0001
"""

from __future__ import annotations

import importlib

from frappe.tests import IntegrationTestCase

_PKG = "kentender_procurement.tender_management.std_instance"
_SUBMODULES = (
	"addendum",
	"attachment",
	"audit",
	"authorization",
	"binding",
	"boq",
	"downstream",
	"events",
	"generated_output",
	"instance",
	"jobs",
	"parameter",
	"publication_lock",
	"readiness",
	"snapshot",
	"state",
	"works_requirement",
)


class TestStdInstPackageStructure0001(IntegrationTestCase):
	def test_std_inst_0001_import_package_and_submodules(self) -> None:
		pkg = importlib.import_module(_PKG)
		self.assertTrue(pkg.__doc__ and "STDINST-0001" in pkg.__doc__)

		for name in _SUBMODULES:
			with self.subTest(submodule=name):
				importlib.import_module(f"{_PKG}.{name}")

		importlib.import_module("kentender_procurement.tender_management.api.std_instance")
