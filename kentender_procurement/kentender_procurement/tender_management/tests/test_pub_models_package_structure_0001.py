# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0001 — ``tender_publication`` package scaffold and imports.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_pub_models_package_structure_0001
"""

from __future__ import annotations

import importlib

from frappe.tests import IntegrationTestCase

_PKG = "kentender_procurement.tender_management.tender_publication"
_SUBPACKAGES = (
	"readiness",
	"approval",
	"snapshot",
	"publication",
	"evidence",
	"authorization",
	"audit",
	"api",
	"seeds",
)
_STUB_MODULES = (
	"readiness.schema",
	"readiness.validator",
	"readiness.publication_readiness",
	"readiness.readiness_finding",
	"approval.approval_review_package",
	"approval.approval_decision",
	"approval.return_to_preparation",
	"snapshot.configuration_snapshot",
	"snapshot.tender_publication_snapshot",
	"publication.precondition",
	"publication.transaction",
	"publication.lock_service",
	"evidence.evidence_package",
	"authorization.publication_authorization",
	"audit.codes",
	"audit.post_publication_denial",
	"audit.publication_audit",
	"api.handlers",
)


class TestPubModelsPackageStructure0001(IntegrationTestCase):
	def test_pub_0001_import_package_and_subpackages(self) -> None:
		pkg = importlib.import_module(_PKG)
		self.assertTrue(pkg.__doc__ and "PUB-0001" in pkg.__doc__)

		for name in _SUBPACKAGES:
			with self.subTest(subpackage=name):
				importlib.import_module(f"{_PKG}.{name}")

		for rel in _STUB_MODULES:
			with self.subTest(stub_module=rel):
				importlib.import_module(f"{_PKG}.{rel}")
