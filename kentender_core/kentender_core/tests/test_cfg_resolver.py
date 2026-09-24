"""CFG-CHG-002 v0.14 §4.10/§7.2 (CFG10-AC-033/034/043/045, CFG13-AC-002) —
ResolveProcurementConfiguration and ValidateProcurementConfigurationForDecision.

One result shape over every rule a consumer needs: an explicit status from
the closed §4.10 set, the exact selected version and its verification, the
typed payload, and a resolution hash over input and result so the owning
decision can prove, inside its own transaction, that nothing changed since
the check. Existing callers of the per-kind resolvers are unchanged
(FU-21 moves them onto this).

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_cfg_resolver
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import configuration_resolver as resolver
from kentender_core.services import regulatory_reference as register
from kentender_core.services.configuration_errors import ConfigurationError
from kentender_core.tests import v16_fixtures as fx

NS = "KT_TEST_CFG_RESOLVER"
PLAN = {"obligation_code": "AGPO-30", "measure_stage": "PlanningAllocation", "target_percent": 30}


class TestResolveProcurementConfiguration(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		fx.ensure_site_configured()
		register.purge_fixture_references(NS)
		ref = register.create_regulatory_reference(
			reference_key="KT-TEST-RESOLVER", reference_kind="Exclusive preference", display_name="KT Test Resolver", fixture_namespace=NS
		)
		cls.version = register.save_regulatory_reference_version(
			reference_set=ref["reference_set"],
			payload={"restriction_code": "KT-TEST", "category": "Works", "comparator": "LessThanOrEqual", "amount": 1_000_000_000, "currency": "KES"},
			effective_from="2097-07-01",
			effective_until="2098-06-30",
			applicability_basis="InvitationDate",
			fixture_namespace=NS,
		)["reference"]
		frappe.db.commit()
		cls.addClassCleanup(lambda: (register.purge_fixture_references(NS), frappe.db.commit()))

	def resolve(self, **kwargs):
		base = {"consumer": "kentender_procurement.planning", "action": "test", "rule": "Exclusive preference", "applicability_date": "2097-09-01"}
		return resolver.resolve_procurement_configuration(**{**base, **kwargs})

	def test_an_unverified_match_names_its_exact_version_and_is_not_usable(self):
		out = self.resolve()
		self.assertEqual(out["status"], "Unverified")
		self.assertEqual(out["selected"]["version"], self.version)
		self.assertEqual(out["selected"]["version_number"], 1)
		self.assertEqual(out["applicability"]["date"], "2097-09-01")
		self.assertEqual(out["payload"]["restriction_code"], "KT-TEST")
		self.assertTrue(out["resolution_hash"])

	def test_no_date_is_missing_basis_never_today(self):
		out = self.resolve(applicability_date="")
		self.assertEqual(out["status"], "MissingBasis")
		self.assertIsNone(out["selected"])

	def test_a_date_no_version_covers_is_missing(self):
		self.assertEqual(self.resolve(applicability_date="2090-01-01")["status"], "Missing")

	def test_an_absent_optional_price_index_is_not_published_not_missing(self):
		out = self.resolve(rule="Market price index", applicability_date="2090-01-01")
		self.assertEqual(out["status"], "NotPublished")

	def test_method_eligibility_and_schedules_resolve_through_the_same_shape(self):
		method = self.resolve(rule="Method eligibility", method="Open Tender", category="Goods", applicability_date="2090-01-01")
		self.assertEqual(method["status"], "Missing")
		schedule = self.resolve(rule="Procurement schedule", method="Open Tender", category="Goods", applicability_date="")
		self.assertEqual(schedule["status"], "MissingBasis")

	def test_an_unknown_rule_or_an_anonymous_consumer_is_refused(self):
		with self.assertRaises(ConfigurationError) as caught:
			self.resolve(rule="Not a rule")
		self.assertEqual(caught.exception.code, "CFG_SCHEMA_UNSUPPORTED")
		with self.assertRaises(ConfigurationError):
			self.resolve(consumer="")

	def test_the_hash_is_stable_for_the_same_input_and_result(self):
		self.assertEqual(self.resolve()["resolution_hash"], self.resolve()["resolution_hash"])
		self.assertNotEqual(self.resolve()["resolution_hash"], self.resolve(applicability_date="2098-01-01")["resolution_hash"])

	def test_a_decision_is_refused_when_the_configuration_changed_since_its_check(self):
		checked = self.resolve()
		same = resolver.validate_procurement_configuration_for_decision(
			expected_hash=checked["resolution_hash"],
			consumer="kentender_procurement.planning", action="test", rule="Exclusive preference", applicability_date="2097-09-01",
		)
		self.assertEqual(same["resolution_hash"], checked["resolution_hash"])
		frappe.db.set_value("Regulatory Reference", self.version, "verification_status", register.VERIFICATION_VERIFIED)
		try:
			with self.assertRaises(ConfigurationError) as caught:
				resolver.validate_procurement_configuration_for_decision(
					expected_hash=checked["resolution_hash"],
					consumer="kentender_procurement.planning", action="test", rule="Exclusive preference", applicability_date="2097-09-01",
				)
			self.assertEqual(caught.exception.code, "CFG_CONFIGURATION_CHANGED")
		finally:
			frappe.db.set_value("Regulatory Reference", self.version, "verification_status", register.VERIFICATION_PENDING)
			frappe.clear_document_cache("Regulatory Reference", self.version)
