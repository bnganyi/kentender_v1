# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0001 — ``works_completion`` package scaffold and imports.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_works_completion_package_structure_0001
"""

from __future__ import annotations

import importlib

from frappe.tests import IntegrationTestCase

_PKG = "kentender_procurement.tender_management.works_completion"
_SUBPACKAGES = (
	"api",
	"services",
	"validators",
	"repositories",
	"domain",
	"events",
	"seeds",
	"tests",
)
_SERVICE_MODULES = (
	"orchestrator",
	"context_validator",
	"completion_status",
)


class TestWorksCompletionPackageStructure0001(IntegrationTestCase):
	def test_works_comp_0001_import_package_and_subpackages(self) -> None:
		pkg = importlib.import_module(_PKG)
		self.assertTrue(pkg.__doc__ and "WORKS-COMP-0001" in pkg.__doc__)

		for name in _SUBPACKAGES:
			with self.subTest(subpackage=name):
				importlib.import_module(f"{_PKG}.{name}")

		for name in _SERVICE_MODULES:
			with self.subTest(service_module=name):
				importlib.import_module(f"{_PKG}.services.{name}")
