# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 19.3 CM-R-01, 02, 03, 04, 17, 18 and section 19.4 "Coverage result" (plan Phase 5; tracker CM8-509): the facts behind the formation rules.

The pure checks are tested on their inputs; the wiring is tested on a received package, where every finding is returned together and holds only the sending of the agreement."""

from __future__ import annotations

import copy
import unittest

import frappe

from kentender_contracts.services import errors, formation, formation_rules as rules
from kentender_contracts.simulation import sources
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

NOW = "2027-07-02 09:00:00"
TERMS = {
	"total": 1_000_000, "parties": {"entity": {"entity_type": "Ministry"}, "supplier": {"organisation": "ORG-1"}}, "delivery": {"due": "2027-07-20"}, "warranty": {"months": 12},
	"payment": {"terms": "as issued"}, "security": {"required": False}, "advance": {"allowed": False},
	"signing_window": {"notification": {"id": "N1", "given_at": "2027-06-17 10:00:00"}, "signing_window": {"result": "Within window", "earliest_signing_at": "2027-07-02 09:00:00", "ends_on": "2027-07-14", "counting_basis": "x"}},
}


def keys(found):
	return [f["hold"] for f in found]


class TestRuleFacts(unittest.TestCase):
	def terms(self, **changes):
		out = copy.deepcopy(TERMS)
		out.update(changes)
		return out

	def test_an_agreement_with_a_different_supplier_from_the_award_is_held(self):
		package = {"decision": {"organisation": "ORG-2"}}
		self.assertEqual(keys(rules.tenderer(package, TERMS)), ["FORMATION_AUTHORITY"])
		self.assertEqual(rules.tenderer({"decision": {"organisation": "ORG-1"}}, TERMS), [])

	def test_the_signing_window_is_what_award_evidenced_and_is_never_worked_out_here(self):
		self.assertEqual(rules.window(TERMS, NOW), [])
		for drop in ("counting_basis", "result"):
			broken = self.terms()
			del broken["signing_window"]["signing_window"][drop]
			self.assertEqual(keys(rules.window(broken, NOW)), ["SIGNING_WINDOW_UNESTABLISHED"], drop)
		no_notice = self.terms(signing_window={"signing_window": TERMS["signing_window"]["signing_window"]})
		self.assertEqual(keys(rules.window(no_notice, NOW)), ["SIGNING_WINDOW_UNESTABLISHED"])
		self.assertIn("waiting period", rules.window(TERMS, "2027-07-01 09:00:00")[0]["reason"])
		self.assertIn("has ended", rules.window(TERMS, "2027-07-15 09:00:00")[0]["reason"])

	def test_the_attorney_general_clearance_is_needed_only_above_the_threshold_and_not_for_the_exempt(self):
		threshold = 5_000_000_000
		big = self.terms(total=threshold + 1)
		self.assertEqual(keys(rules.clearance(big, threshold)), ["AG_CLEARANCE_REQUIRED"])
		self.assertEqual(rules.clearance(self.terms(total=threshold), threshold), [], "the threshold is 'exceeding', not 'at'")
		self.assertEqual(rules.clearance(self.terms(total=threshold + 1, particulars={"ag_clearance": "AG/2027/1"}), threshold), [])
		for exempt in ("Parliament", "judiciary"):
			parties = {"entity": {"entity_type": exempt}, "supplier": {}}
			self.assertEqual(rules.clearance(self.terms(total=threshold + 1, parties=parties), threshold), [], exempt)
		self.assertEqual(rules.clearance(TERMS, threshold), [], "KES 1,000,000 never triggers it")

	def test_every_minimum_category_must_resolve_and_the_addenda_must_be_stated(self):
		full = {n: {"data": {"x": 1}} for n in ("S2", "S3", "S4", "S5", "S7", "S8")}
		self.assertEqual(rules.coverage(full, []), [], "an empty addenda list is explicit")
		self.assertEqual(keys(rules.coverage(full, None)), ["PACKAGE_INCOMPLETE"])
		short = {k: v for k, v in full.items() if k != "S5"}
		found = rules.coverage(short, [])
		self.assertEqual(found[0]["categories"], ["gcc", "scc"])

	def test_a_missing_commercial_term_names_the_exact_term(self):
		self.assertEqual(rules.terms_typed(TERMS), [])
		broken = self.terms(warranty={}, delivery={})
		self.assertEqual([f["term"] for f in rules.terms_typed(broken)], ["the delivery date", "the warranty period"])
		self.assertEqual({f["hold"] for f in rules.terms_typed(broken)}, {"TERM_MAPPING_MISSING"})

	def test_a_complex_contract_is_out_of_scope_and_an_unstated_classification_is_not_silently_complex(self):
		self.assertTrue(rules.in_scope("Goods"))
		self.assertTrue(rules.in_scope(""))
		self.assertFalse(rules.in_scope("Complex works"))
		self.assertEqual(rules.scope({"procurement_category": "Specialised"}), "Specialised")


class TestRulesOnAReceivedPackage(ContractCase):
	native = True

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.people = tw.build()
		cls.addClassCleanup(tw.teardown)

	def setUp(self):
		super().setUp()
		self.env = tw.Environment().__enter__()
		self.addCleanup(lambda: self.env.__exit__(None, None, None))
		self.p, self.n = self.people, 0

	def k(self):
		self.n += 1
		return f"rules-{self.id().rsplit('.', 1)[-1]}-{self.n}"

	def prepared(self):
		out = tw.receive(self.p)
		saved = formation.save_particulars(out["contract"], expected_version=out["record_version"], idempotency_key=self.k(), actor=self.p["brian"], values=tw.package_particulars(self.p))
		return out["contract"], saved

	def test_a_complex_contract_is_refused_on_receipt_and_acknowledged_by_nobody(self):
		package = sources.award_package()
		package["procurement_category"] = "Complex works"
		with self.assertRaises(errors.ContractError) as caught:
			formation.receive_award_package(package, handoff=sources.source_handoff(package["award_case"]), managing_unit=tw.unit(), idempotency_key=self.k(), actor="Administrator")
		self.assertEqual((caught.exception.code, caught.exception.detail["hold_key"]), ("CM_RULE", "OUT_OF_SCOPE_PRODUCT"))
		self.assertEqual(frappe.db.count("Contract Case", {"fixture_namespace": "CM_TEST"}), 0)

	def test_sending_before_the_waiting_period_ends_is_held_with_the_rule_and_its_holder(self):
		case, saved = self.prepared()
		frappe.flags.kt_cm_clock = "2027-07-01 09:00:00"
		with self.assertRaises(errors.ContractError) as caught:
			formation.request_signatures(case, expected_version=saved["record_version"], idempotency_key=self.k(), actor=self.p["charles"])
		reasons = caught.exception.reasons if hasattr(caught.exception, "reasons") else []
		self.assertEqual(caught.exception.code, "CM_HOLD")
		self.assertIn("SIGNING_WINDOW_UNESTABLISHED", str(caught.exception.detail) + str(reasons))
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Preparing")
		frappe.flags.kt_cm_clock = tw.CLOCK
		sent = formation.request_signatures(case, expected_version=frappe.db.get_value("Contract Case", case, "record_version"), idempotency_key=self.k(), actor=self.p["charles"])
		self.assertTrue(sent["package"], "once the period has ended the same agreement is sent")

	def test_the_window_closing_between_the_request_and_a_signature_stops_that_signature(self):
		case, saved = self.prepared()
		sent = formation.request_signatures(case, expected_version=saved["record_version"], idempotency_key=self.k(), actor=self.p["charles"])
		frappe.flags.kt_cm_clock = "2027-07-15 09:00:00"
		with self.assertRaises(errors.ContractError) as caught:
			formation.sign_contract(case, party="Supplier", expected_version=sent["record_version"], idempotency_key=self.k(), actor=self.p["mary"])
		self.assertEqual(caught.exception.code, "CM_HOLD")
		self.assertEqual(frappe.db.get_value("Contract Signature", {"contract_case": case, "party": "Supplier"}, "state"), "Requested")
