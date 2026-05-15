# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0001 — ``security`` package scaffold and imports.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_sec_models_package_structure_0001
"""

from __future__ import annotations

import importlib

from frappe.tests import IntegrationTestCase

_PKG = "kentender_procurement.tender_management.security"
_SUBPACKAGES = (
	"permissions",
	"authorization",
	"action_availability",
	"audit",
	"evidence",
)
_STUB_MODULES = (
	"permissions.catalog",
	"permissions.seed_catalog",
	"permissions.role_matrix",
	"permissions.seed_role_matrix",
	"permissions.role_permission",
	"permissions.service",
	"authorization.denial_codes",
	"authorization.action_authorization_registry",
	"authorization.decision_engine",
	"authorization.object_scope",
	"authorization.state_authorization",
	"authorization.negative_permissions",
	"action_availability.service",
	"action_availability.catalog",
	"action_availability.api",
	"action_availability.access_denied_audit",
	"action_availability.guarded_service",
	"audit.event_catalog",
	"audit.metadata",
	"audit.event_service",
	"audit.denied_action",
	"evidence.export_authorization",
	"api",
)


class TestSecModelsPackageStructure0001(IntegrationTestCase):
	def test_sec_0001_import_package_and_subpackages(self) -> None:
		pkg = importlib.import_module(_PKG)
		self.assertTrue(pkg.__doc__ and "SEC-0001" in pkg.__doc__)

		for name in _SUBPACKAGES:
			with self.subTest(subpackage=name):
				importlib.import_module(f"{_PKG}.{name}")

		for rel in _STUB_MODULES:
			with self.subTest(stub_module=rel):
				importlib.import_module(f"{_PKG}.{rel}")
