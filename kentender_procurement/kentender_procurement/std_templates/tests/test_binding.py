# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-TPL-IMP-001 v1.0 §9 — the binding/publication lifecycle matrix and
the affected-Tender projection (STI10-AC-010/011/012/013; TPL10-AC-006/007/008;
owner rulings R3, R12; owner decision OD5 — the site switch)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_templates.compiler import compatibility
from kentender_procurement.std_templates.compiler.errors import STDTemplateError
from kentender_procurement.std_templates.services import binding, installer, lifecycle
from kentender_procurement.std_templates.tests import support


class BindingCase(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.release_ids: list[str] = []
		self.addCleanup(lambda: support.purge(self.release_ids))

	def install(self, switch: str = "Off", **kw):
		root, info = support.make_test_package(**kw)
		self.release_ids.append(info["release_id"])
		self.addCleanup(lambda: support.cleanup_tmp(info))
		installer.install_approved_std_release(str(root), installed_by="test", site_switch=switch)
		frappe.db.commit()
		return info["release_id"]

	def assertCode(self, code, fn):
		with self.assertRaises(STDTemplateError) as ctx:
			fn()
		self.assertEqual(ctx.exception.code, code, ctx.exception)


class TestMatrix(BindingCase):
	def test_switched_off_blocks_new_binding_but_never_strands_a_started_tender(self):
		release = self.install()
		self.assertCode("STD_RELEASE_NOT_AVAILABLE", lambda: binding.require(release, "new_binding"))
		for purpose in ("continue", "publication"):
			self.assertEqual(binding.require(release, purpose)["template_release_id"], release)

	def test_the_switch_turns_new_binding_on_and_off_and_is_audited(self):
		release = self.install(template_release="9.8-test")
		support.isolate_switch(self, keep=(release,))
		self.assertCode("STD_RELEASE_NOT_AVAILABLE", lambda: binding.available_release("IT-EQUIPMENT-OPEN-V1"))
		result = lifecycle.switch(release, "on", actor="test release owner")
		self.assertEqual((result["site_switch"], result["changed"]), ("On", True))
		self.assertEqual(binding.require(release, "new_binding")["site_switch"], "On")
		self.assertEqual(binding.available_release("IT-EQUIPMENT-OPEN-V1").name, release)
		self.assertFalse(lifecycle.switch(release, "On", actor="test release owner")["changed"])
		lifecycle.switch(release, "Off", actor="test release owner")
		self.assertCode("STD_RELEASE_NOT_AVAILABLE", lambda: binding.require(release, "new_binding"))
		actions = frappe.get_all("Audit Event", filters={"document_name": release, "action": ["like", "Switched %"]}, pluck="action", order_by="creation asc")
		self.assertEqual(actions, ["Switched On", "Switched Off"])
		self.assertEqual(frappe.db.get_value("Installed STD Release", release, "switched_by"), "test release owner")

	def test_switch_needs_a_state_and_an_actor_and_a_current_release(self):
		release = self.install(template_release="9.2-test")
		with self.assertRaises(frappe.ValidationError):
			lifecycle.switch(release, "Maybe", actor="test release owner")
		with self.assertRaises(frappe.ValidationError):
			lifecycle.switch(release, "On", actor="")
		lifecycle.supersede(release, release_owner="test release owner")
		self.assertCode("STD_RELEASE_NOT_AVAILABLE", lambda: lifecycle.switch(release, "On", actor="test release owner"))

	def test_available_binds_and_continues(self):
		release = self.install(switch="On", decision="APPROVE EXACT MANIFEST", pass_all_gates=True, template_release="9.7-test")
		support.isolate_switch(self, keep=(release,))
		facts = binding.require(release, "new_binding")
		self.assertEqual(facts["template_release_id"], release)
		self.assertEqual(facts["renderer_profile_id"], "BDS-GOODS-IT-V1")
		# TPR-CHG-001 v0.12 §4.1–4.2: a Tender binds the three rule digests too.
		doc = frappe.get_doc("Installed STD Release", release)
		for field in ("response_rules_digest", "downstream_rules_digest", "addendum_identity_rules_digest"):
			self.assertTrue(doc.get(field), field)
			self.assertEqual(facts[field], doc.get(field), field)
		self.assertEqual(binding.available_release("IT-EQUIPMENT-OPEN-V1").name, release)
		self.assertEqual(binding.require(release, "publication")["notice"], "")

	def test_superseded_blocks_new_binding_but_continues(self):
		release = self.install(template_release="9.6-test")
		lifecycle.supersede(release, release_owner="test release owner")
		self.assertCode("STD_RELEASE_NOT_AVAILABLE", lambda: binding.require(release, "new_binding"))
		cont = binding.require(release, "continue")
		self.assertIn("superseded", cont["notice"])
		self.assertEqual(frappe.db.get_value("Installed STD Release", release, "lifecycle_status"), "Superseded")

	def test_withdrawn_blocks_binding_and_publication_but_history_reads(self):
		release = self.install(template_release="9.5-test")
		result = lifecycle.withdraw(release, reason="Legal defect found in the reservation clause.", release_owner="test release owner")
		self.assertIn("affected", result)
		self.assertCode("STD_RELEASE_NOT_AVAILABLE", lambda: binding.require(release, "new_binding"))
		self.assertCode("STD_RELEASE_WITHDRAWN", lambda: binding.require(release, "continue"))
		self.assertCode("STD_RELEASE_WITHDRAWN", lambda: binding.require(release, "publication"))
		self.assertIn("withdrawn", binding.require(release, "read_published")["notice"])
		audit = frappe.get_all("Audit Event", filters={"document_name": release, "action": "Withdrawn"}, pluck="name")
		self.assertEqual(len(audit), 1)
		doc = frappe.get_doc("Installed STD Release", release)
		self.assertEqual((doc.withdrawn_by, doc.withdrawal_reason), ("test release owner", "Legal defect found in the reservation clause."))

	def test_withdrawal_needs_a_reason_and_never_touches_assets(self):
		release = self.install(template_release="9.4-test")
		assets_before = len(frappe.get_doc("Installed STD Release", release).assets)
		with self.assertRaises(frappe.ValidationError):
			lifecycle.withdraw(release, reason="", release_owner="test release owner")
		lifecycle.withdraw(release, reason="Safety defect in the renderer.", release_owner="test release owner")
		self.assertEqual(len(frappe.get_doc("Installed STD Release", release).assets), assets_before)

	def test_lifecycle_and_switch_fields_only_change_through_their_services(self):
		release = self.install()
		for field, value in (("lifecycle_status", "Withdrawn"), ("site_switch", "On")):
			with self.subTest(field=field):
				doc = frappe.get_doc("Installed STD Release", release)
				doc.set(field, value)
				with self.assertRaises(frappe.ValidationError):
					doc.save(ignore_permissions=True)
				frappe.db.rollback()


class TestCompatibility(BindingCase):
	def test_moh_facts_are_supported_and_usd_is_not(self):
		release = self.install()
		facts = compatibility.facts_from_projection(support.moh_projection())
		self.assertTrue(binding.check_compatibility(release, facts)["supported"])
		result = binding.check_compatibility(release, dict(facts, currency="USD"))
		self.assertFalse(result["supported"])
		self.assertEqual(result["first_failure"]["fact"], "currency")
