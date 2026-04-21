"""Phase L — Wave 0 smoke foundation (deterministic backend checks).

Run:
  bench --site kentender.midas.com run-tests --app kentender_core --module kentender_core.tests.test_wave0_smoke
"""

import importlib
import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.audit_event_service import log_audit_event
from kentender_core.services.business_id_service import generate_business_id
from kentender_core.services.workflow_guard_service import run_workflow_guard

KENTENDER_APPS = (
	"kentender_core",
	"kentender_strategy",
	"kentender_budget",
	"kentender_procurement",
	"kentender_suppliers",
	"kentender_governance",
	"kentender_compliance",
	"kentender_stores",
	"kentender_assets",
	"kentender_integrations",
	"kentender_transparency",
)

_SMOKE_PREFIX = "KT-SMOKE"
_SMOKE_ENTITY = "SMOKE"
_SMOKE_YEAR = 2035
_PE_CODE = "KT-SMOKE-PE-001"


class TestWave0Smoke(IntegrationTestCase):
	doctype = None

	def test_all_kentender_apps_installed(self):
		installed = set(frappe.get_installed_apps())
		for app in KENTENDER_APPS:
			self.assertIn(app, installed, f"Expected {app} to be installed")

	def test_all_kentender_hooks_import(self):
		for app in KENTENDER_APPS:
			with self.subTest(app=app):
				importlib.import_module(f"{app}.hooks")

	def test_smoke_generate_business_id(self):
		frappe.db.delete(
			"Business ID Counter",
			{"prefix": _SMOKE_PREFIX, "entity": _SMOKE_ENTITY, "year": _SMOKE_YEAR},
		)
		frappe.db.commit()

		first = generate_business_id(_SMOKE_PREFIX, _SMOKE_ENTITY, _SMOKE_YEAR)
		self.assertEqual(first, f"{_SMOKE_PREFIX}-{_SMOKE_ENTITY}-{_SMOKE_YEAR}-0001")

		frappe.db.delete(
			"Business ID Counter",
			{"prefix": _SMOKE_PREFIX, "entity": _SMOKE_ENTITY, "year": _SMOKE_YEAR},
		)
		frappe.db.commit()

	def test_smoke_log_audit_event(self):
		name = log_audit_event(
			event_type="ken.smoke.wave0",
			entity="SMOKE",
			document_type="Procuring Entity",
			document_name="SMOKE-PE",
			action="smoke",
			performed_by="Administrator",
			metadata={"wave": 0},
		)
		self.assertTrue(frappe.db.exists("Audit Event", name))
		row = frappe.get_doc("Audit Event", name)
		self.assertEqual(row.event_type, "ken.smoke.wave0")
		meta = row.metadata if isinstance(row.metadata, dict) else json.loads(row.metadata)
		self.assertEqual(meta.get("wave"), 0)
		frappe.delete_doc("Audit Event", name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def test_smoke_procuring_entity_exception_workflow_guard(self):
		if frappe.db.exists("Procuring Entity", _PE_CODE):
			frappe.delete_doc("Procuring Entity", _PE_CODE, force=1)

		pe = frappe.get_doc(
			{
				"doctype": "Procuring Entity",
				"entity_code": _PE_CODE,
				"entity_name": "Wave 0 smoke Procuring Entity",
			}
		)
		pe.insert()

		ok, msg = run_workflow_guard("smoke.test", pe)
		self.assertTrue(ok)
		self.assertEqual(msg, "")

		ex = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"reference_doctype": "Procuring Entity",
				"reference_name": pe.name,
				"reason": "Wave 0 smoke",
				"status": "Draft",
			}
		)
		ex.insert()
		self.assertTrue(frappe.db.exists("Exception Record", ex.name))

		frappe.delete_doc("Exception Record", ex.name, force=1)
		frappe.delete_doc("Procuring Entity", pe.name, force=1)
		frappe.db.commit()
