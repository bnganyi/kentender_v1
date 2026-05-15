# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0001 — ``derived_models`` package scaffold and imports.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_models_package_structure_0001
"""

from __future__ import annotations

import importlib

from frappe.tests import IntegrationTestCase

_PKG = "kentender_procurement.tender_management.derived_models"
_SUBPACKAGES = (
	"common",
	"bundle",
	"dsm",
	"dom",
	"dem",
	"dcm",
	"consumption",
	"addendum",
	"api",
	"events",
	"seeds",
	"tests",
)
_STUB_MODULES = (
	"common.metadata",
	"common.source_trace",
	"common.versioning",
	"bundle.schema",
	"bundle.generator",
	"bundle.validator",
	"dsm.schema",
	"dsm.generator",
	"dsm.validator",
	"dom.schema",
	"dom.generator",
	"dom.validator",
	"dem.schema",
	"dem.generator",
	"dem.validator",
	"dcm.schema",
	"dcm.generator",
	"dcm.validator",
	"consumption.output_consumption",
	"addendum.derived_model_impact",
)


class TestDerivedModelsPackageStructure0001(IntegrationTestCase):
	def test_derived_0001_import_package_and_subpackages(self) -> None:
		pkg = importlib.import_module(_PKG)
		self.assertTrue(pkg.__doc__ and "DERIVED-0001" in pkg.__doc__)

		for name in _SUBPACKAGES:
			with self.subTest(subpackage=name):
				importlib.import_module(f"{_PKG}.{name}")

		for rel in _STUB_MODULES:
			with self.subTest(stub_module=rel):
				importlib.import_module(f"{_PKG}.{rel}")
