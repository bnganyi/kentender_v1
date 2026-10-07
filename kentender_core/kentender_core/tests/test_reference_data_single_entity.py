"""AUD-XC-017 — one site, one Procuring Entity: the reference-data API cannot
create a second entity or open a PE/FY context for one (AUTH-ADR-001 §19,
CFG10-AC-003)."""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.api import reference_data_api as api
from kentender_core.services.reference_data_permissions import REFERENCE_DATA_MANAGER_ROLE


class TestReferenceDataSingleEntity(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.manager = f"cfg.single.{self.suffix}@test.local"
		frappe.get_doc(
			{"doctype": "User", "email": self.manager, "first_name": "single", "enabled": 1, "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		if not frappe.db.exists("Role", REFERENCE_DATA_MANAGER_ROLE):
			frappe.get_doc({"doctype": "Role", "role_name": REFERENCE_DATA_MANAGER_ROLE, "desk_access": 1}).insert(
				ignore_permissions=True
			)
		frappe.get_doc("User", self.manager).add_roles(REFERENCE_DATA_MANAGER_ROLE)
		self.pe_type = f"SINGLETYPE_{self.suffix}".upper()
		frappe.get_doc(
			{"doctype": "PE Type", "type_code": self.pe_type, "label": "Single Type", "status": "Active"}
		).insert(ignore_permissions=True)
		self.entity_code = f"PE-SINGLE-{self.suffix}".upper()

	def tearDown(self):
		frappe.set_user("Administrator")
		for doctype, filters in (
			("Procuring Entity Version", [["procuring_entity", "=", self.entity_code]]),
			("Procuring Entity", [["name", "=", self.entity_code]]),
			("PE Type", [["name", "like", f"%{self.suffix}%"]]),
		):
			for name in frappe.get_all(doctype, filters=filters, pluck="name"):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		if frappe.db.exists("User", self.manager):
			frappe.delete_doc("User", self.manager, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _configured_site_pe(self):
		return frappe.db.get_single_value("Site Procuring Entity", "pe_code")

	def test_a_role_holder_cannot_create_a_second_procuring_entity(self):
		if not self._configured_site_pe() and not frappe.db.count("Procuring Entity"):
			self.skipTest("site has no Procuring Entity; the bootstrap case is allowed")
		before = frappe.db.count("Procuring Entity")
		frappe.set_user(self.manager)
		with self.assertRaisesRegex(frappe.ValidationError, "one Procuring Entity"):
			api.create_or_revise_pe(
				payload={
					"entity_code": self.entity_code,
					"legal_name": "Second Entity",
					"display_name": "Second Entity",
					"pe_type_code": self.pe_type,
				}
			)
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.count("Procuring Entity"), before)

	def _rest_request(self):
		"""Make the call look like it arrived over HTTP (what `/api/resource` does), restored afterwards."""
		previous = getattr(frappe.local, "request", None)
		frappe.local.request = frappe._dict(method="POST", path="/api/resource/Procuring Entity", headers={})
		self.addCleanup(setattr, frappe.local, "request", previous)

	def _second_entity(self):
		return frappe.get_doc(
			{"doctype": "Procuring Entity", "entity_code": self.entity_code, "legal_name": "Second Entity", "entity_name": "Second Entity", "reporting_currency": "KES"}
		)

	def test_a_role_holder_cannot_create_a_second_procuring_entity_through_the_resource_api(self):
		"""RG-07 / AUD-XC-017: the rule lived only in the reference-data API; `POST /api/resource/Procuring Entity`
		went straight to the doctype, whose DocPerm let the role create."""
		if not self._configured_site_pe() and not frappe.db.count("Procuring Entity"):
			self.skipTest("site has no Procuring Entity; the bootstrap case is allowed")
		before = frappe.db.count("Procuring Entity")
		frappe.set_user(self.manager)
		self._rest_request()
		with self.assertRaises((frappe.PermissionError, frappe.ValidationError)):
			self._second_entity().insert()
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.count("Procuring Entity"), before)
		self.assertFalse(frappe.db.exists("Procuring Entity", self.entity_code))

	def test_the_single_entity_rule_holds_in_the_controller_for_a_request_made_by_administrator(self):
		if not self._configured_site_pe() and not frappe.db.count("Procuring Entity"):
			self.skipTest("site has no Procuring Entity; the bootstrap case is allowed")
		frappe.set_user("Administrator")
		self._rest_request()
		with self.assertRaisesRegex(frappe.ValidationError, "one Procuring Entity"):
			self._second_entity().insert()
		self.assertFalse(frappe.db.exists("Procuring Entity", self.entity_code))

	def test_no_business_or_technical_role_holds_create_on_the_doctype(self):
		roles = {p.role for p in frappe.get_meta("Procuring Entity").permissions if p.create}
		self.assertFalse(roles - {"Administrator"}, f"roles with create: {roles}")

	def test_a_role_holder_cannot_open_a_context_for_another_entity(self):
		site_pe = self._configured_site_pe()
		if not site_pe:
			self.skipTest("site is not configured")
		other = frappe.db.get_value("Procuring Entity", {"name": ("!=", site_pe)}, "name")
		if not other:
			self.skipTest("no non-site Procuring Entity row exists to probe with")
		frappe.set_user(self.manager)
		with self.assertRaisesRegex(frappe.ValidationError, "one Procuring Entity"):
			api.enable_pe_fy_context(other, "FY-NONE", "2100-01-01 00:00:00", "2100-12-31 00:00:00")


class TestOrganisationUnitCatalogueIsInternal(IntegrationTestCase):
	"""AUD-XC-029 — the unit catalogue is for internal (Desk) users, as the doctype's own DocPerm says."""

	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.addCleanup(self._purge)
		self.portal = f"cfg.portal.{self.suffix}@test.local"
		self.internal = f"cfg.internal.{self.suffix}@test.local"
		for email, utype in ((self.portal, "Website User"), (self.internal, "System User")):
			doc = frappe.get_doc(
				{"doctype": "User", "email": email, "first_name": "x", "enabled": 1, "send_welcome_email": 0, "user_type": utype}
			)
			if utype == "System User":
				doc.append("roles", {"role": "Desk User"})
			doc.insert(ignore_permissions=True)

	def _purge(self):
		frappe.set_user("Administrator")
		for email in (self.portal, self.internal):
			if frappe.db.exists("User", email):
				frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		frappe.db.commit()

	def test_portal_account_is_refused_internal_account_is_served(self):
		frappe.set_user(self.portal)
		with self.assertRaises(frappe.PermissionError):
			api.list_organisation_units()
		frappe.set_user(self.internal)
		self.assertIn("rows", api.list_organisation_units())
