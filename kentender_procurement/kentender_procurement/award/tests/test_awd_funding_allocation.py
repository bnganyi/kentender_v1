# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AWD-CHG-001 v0.7 section 7.1 / AWD-FUND-AC-001 to -004: the award's price is traced to the reservations that fund it, retained with the decision, and verified for Budget.

The synthetic source world serves one source by default and several on request (`allocation` in `award/test_services/sources.py`). The arithmetic is proven without a database in `test_funding_split`;
here the allocation is built from the owners' inputs, refused when it cannot be traced, retained with the committed decision, superseded by a corrected one, and verified for the funding owner."""

from __future__ import annotations

from kentender_core.seeds.calendar import fiscal as F  # noqa: F401
from kentender_procurement.award.test_services.timeline import W  # noqa: F401

import frappe

from kentender_core.services.award_funding_verification import NOT_VERIFIED, UNAVAILABLE, VERIFIED
from kentender_procurement.award.services import checks, decision, funding_allocation as allocation, funding_verification as verification, records
from kentender_procurement.award.services.errors import AwardError
from kentender_procurement.award.test_services import sources as syn
from kentender_procurement.award.tests.support import AO, CASE, AwardCase

TENDER = "SYN-TND-AWT-2100-033"
REASON = "I accept the recommendation in the signed evaluation report and professional opinion."
TWO = {"sources": [{"drawdown_line": "DL-HRMD", "reservation": "RSV-HRMD", "quantity": "100", "unit": "OU-HRMD"}, {"drawdown_line": "DL-DHI", "reservation": "RSV-DHI", "quantity": "150", "unit": "OU-DHI"}],
	"unit_price": "185600", "budget_line": "BL-HWD"}


class _Allocated(AwardCase):
	def setUp(self):
		super().setUp()
		self.deliver()
		self.signed_opinion()
		self.at(W("2027-06-17 10:00:00"))

	def award(self):
		return self.run_as(AO, decision.record, award=CASE, outcome="Award", reason=REASON, expected_version=self.version())

	def held(self):
		return allocation.current(self.case())

	def lineage(self, **overrides):
		return {"award": CASE, "allocation_digest": self.held().digest, **overrides}

	def verify(self, allocations, **lineage):
		return verification.service().verify(lineage=self.lineage(**lineage), contract="CM-X", allocations=allocations, purpose="convert")


class TestThePriceIsTracedToItsSources(_Allocated):
	def test_a_positive_decision_retains_the_allocation_of_its_own_decision(self):
		self.award()
		held = self.held()
		self.assertEqual((held.status, held.decision, held.supported_total), (allocation.CURRENT, self.case().current_decision, "46400000.00"))
		payload = allocation.payload_of(held)
		self.assertEqual(payload["schema"], allocation.SCHEMA)
		self.assertEqual([(a["reservation"], a["amount"]) for a in payload["allocations"]], [("SYN-RSV", "46400000.00")])

	def test_two_sources_split_by_quantity_and_both_reservations_are_named(self):
		syn.set_fact(TENDER, allocation=TWO)
		self.award()
		payload = allocation.payload_of(self.held())
		self.assertEqual([(a["reservation"], a["quantity"], a["amount"]) for a in payload["allocations"]], [("RSV-DHI", "150", "27840000.00"), ("RSV-HRMD", "100", "18560000.00")])
		self.assertEqual(sum(float(a["amount"]) for a in payload["allocations"]), 46400000.0)
		self.assertTrue(all(a["budget_line"] == "BL-HWD" for a in payload["allocations"]), "both sources may share one Budget Line")

	def test_the_digest_is_the_same_before_and_after_the_decision_when_the_sources_are_unchanged(self):
		syn.set_fact(TENDER, allocation=TWO)
		before = allocation.compute(self.case())["digest"]
		self.award()
		self.assertEqual(self.held().digest, before)

	def test_the_retained_allocation_cannot_be_changed(self):
		self.award()
		held = frappe.get_doc(allocation.ALLOCATION, self.held().name)
		held.supported_total = "1.00"
		held.flags.kt_awd_command = True
		with self.assertRaises(frappe.ValidationError):
			held.save(ignore_permissions=True)


class TestAnUntraceablePriceBlocksAPositiveDecision(_Allocated):
	def refused(self):
		with self.assertRaises(AwardError) as ctx:
			self.award()
		self.assertEqual(self.case().decision_status, "No decision recorded")
		self.assertIsNone(self.held())
		return ctx.exception

	def test_shares_that_do_not_add_up_to_the_awarded_price_hold_the_award(self):
		syn.set_fact(TENDER, allocation={**TWO, "unit_price": "100"})  # the priced lines now come to 25,000, not what was awarded
		error = self.refused()
		self.assertEqual((error.code, error.detail["check"]), ("AWD_ON_HOLD", "funding_allocation"))

	def test_a_requisition_that_is_no_longer_authorised_holds_the_award(self):
		syn.set_fact(TENDER, requisition_revoked=True)
		error = self.refused()
		self.assertEqual((error.code, error.detail["check"]), ("AWD_ON_HOLD", "funding_allocation"))
		self.assertIn("no longer authorised", error.detail["reason"])

	def test_an_owner_that_cannot_answer_is_unavailable_never_a_pass(self):
		syn.set_fact(TENDER, allocation_down=True)
		error = self.refused()
		self.assertEqual((error.code, error.detail["check"]), ("AWD_STATUS_UNAVAILABLE", "funding_allocation"))

	def test_no_award_does_not_need_an_allocation(self):
		syn.set_fact(TENDER, allocation_down=True)
		out = self.run_as(AO, decision.record, award=CASE, outcome="No award", reason="The sources could not be traced.", next_action="Ask Procurement to resolve the sources", expected_version=self.version())
		self.assertTrue(out["ok"])
		self.assertIsNone(self.held())


class TestACorrectedSourceGivesANewVersionBesideTheOld(_Allocated):
	def setUp(self):
		super().setUp()
		syn.set_fact(TENDER, allocation=TWO)
		self.award()

	def test_the_standing_is_current_until_the_sources_move(self):
		self.assertEqual(allocation.standing(self.case())["state"], "Current")
		self.assertEqual(checks.funding_stop(self.case()), "")

	def test_a_source_that_moved_makes_the_retained_allocation_changed_and_holds_progress(self):
		syn.set_fact(TENDER, allocation={**TWO, "sources": [{**TWO["sources"][0], "quantity": "60"}, {**TWO["sources"][1], "quantity": "190"}]})
		standing = allocation.standing(self.case())
		self.assertEqual(standing["state"], "Changed")
		self.assertEqual(checks.funding_stop(self.case()), "allocation")

	def test_retaining_a_corrected_allocation_supersedes_the_old_one_and_never_overwrites_it(self):
		old = self.held()
		syn.set_fact(TENDER, allocation={**TWO, "sources": [{**TWO["sources"][0], "quantity": "60"}, {**TWO["sources"][1], "quantity": "190"}]})
		decision_doc = frappe.get_doc("Award Decision", self.case().current_decision)
		new = allocation.retain(self.case(), decision_doc)
		old.reload()
		self.assertEqual((old.status, old.superseded_by, new.status, new.version), (allocation.SUPERSEDED, new.name, allocation.CURRENT, old.version + 1))
		self.assertNotEqual(old.digest, new.digest)
		self.assertEqual([a["amount"] for a in allocation.payload_of(old)["allocations"]], ["27840000.00", "18560000.00"], "the earlier allocation is exactly what it was")

	def test_the_same_sources_retain_the_same_allocation_once(self):
		before = frappe.db.count(allocation.ALLOCATION, {"award_case": CASE})
		decision_doc = frappe.get_doc("Award Decision", self.case().current_decision)
		self.assertEqual(allocation.retain(self.case(), decision_doc).name, self.held().name)
		self.assertEqual(frappe.db.count(allocation.ALLOCATION, {"award_case": CASE}), before)


class TestAwardAnswersBudgetsQuestion(_Allocated):
	"""VerifyAwardFundingLineage: computed now, not read back from an earlier answer. One test per guard, so that removing any guard fails one of them."""

	def setUp(self):
		super().setUp()
		syn.set_fact(TENDER, allocation=TWO)
		self.award()

	def both(self):
		return [{"reservation": "RSV-HRMD", "amount": "18560000.00"}, {"reservation": "RSV-DHI", "amount": "27840000.00"}]

	def test_the_exact_allocation_is_verified_with_its_whole_payload_and_revision(self):
		answer = self.verify(self.both())
		self.assertEqual(answer.status, VERIFIED)
		self.assertEqual(answer.revision, self.held().digest)
		self.assertEqual(sorted(a["reservation"] for a in answer.allocation["allocations"]), ["RSV-DHI", "RSV-HRMD"], "the whole set comes back, so the caller can check completeness")

	def test_one_reservation_of_the_set_is_verified_on_its_own(self):
		self.assertEqual(self.verify([self.both()[0]]).status, VERIFIED)

	def test_a_conversion_that_names_no_award_or_allocation_is_not_verified(self):
		self.assertEqual(verification.service().verify(lineage={}, contract="CM-X", allocations=self.both(), purpose="convert").status, NOT_VERIFIED)
		self.assertEqual(self.verify(self.both(), allocation_digest="").status, NOT_VERIFIED)

	def test_an_unknown_award_or_allocation_is_not_verified(self):
		self.assertEqual(self.verify(self.both(), award="AWD-NOPE").status, NOT_VERIFIED)
		self.assertEqual(self.verify(self.both(), allocation_digest="0" * 64).status, NOT_VERIFIED)

	def test_a_reservation_the_award_does_not_name_is_not_verified(self):
		answer = self.verify([{"reservation": "RSV-OTHER", "amount": "1.00"}])
		self.assertEqual(answer.status, NOT_VERIFIED)
		self.assertIn("RSV-OTHER", " ".join(answer.mismatches))

	def test_the_wrong_amount_is_not_verified(self):
		self.assertEqual(self.verify([{"reservation": "RSV-HRMD", "amount": "18560000.01"}]).status, NOT_VERIFIED)

	def test_a_reservation_named_twice_is_not_verified(self):
		self.assertEqual(self.verify([self.both()[0], self.both()[0]]).status, NOT_VERIFIED)

	def test_a_decision_other_than_the_one_in_force_is_not_verified(self):
		self.assertEqual(self.verify(self.both(), decision="Award-Decision-Of-Another-Case").status, NOT_VERIFIED)

	def test_a_superseded_allocation_is_not_verified(self):
		held = self.held()
		syn.set_fact(TENDER, allocation={**TWO, "sources": [{**TWO["sources"][0], "quantity": "60"}, {**TWO["sources"][1], "quantity": "190"}]})
		allocation.retain(self.case(), frappe.get_doc("Award Decision", self.case().current_decision))
		answer = verification.service().verify(lineage={"award": CASE, "allocation_digest": held.digest}, contract="CM-X", allocations=self.both(), purpose="convert")
		self.assertEqual(answer.status, NOT_VERIFIED)
		self.assertIn("superseded", " ".join(answer.mismatches))

	def test_sources_that_moved_since_the_allocation_was_retained_are_not_verified(self):
		syn.set_fact(TENDER, allocation={**TWO, "sources": [{**TWO["sources"][0], "quantity": "60"}, {**TWO["sources"][1], "quantity": "190"}]})
		answer = self.verify(self.both())
		self.assertEqual(answer.status, NOT_VERIFIED)
		self.assertIn("changed", " ".join(answer.mismatches))

	def test_a_revoked_requisition_is_not_verified(self):
		syn.set_fact(TENDER, requisition_revoked=True)
		self.assertEqual(self.verify(self.both()).status, NOT_VERIFIED)

	def test_an_owner_that_cannot_answer_is_unavailable_not_negative(self):
		syn.set_fact(TENDER, allocation_down=True)
		self.assertEqual(self.verify(self.both()).status, UNAVAILABLE)

	def test_a_cancelled_award_is_not_verified(self):
		records.bump(self.case(), cancelled=1)
		self.assertEqual(self.verify(self.both()).status, NOT_VERIFIED)

	def test_a_holding_issue_stops_the_conversion_as_it_stops_a_notice(self):
		from kentender_procurement.award.services import issues

		issues.open_issue(self.case(), source_event="test-hold", issue_type="Review/order", title="A review has been filed.")
		answer = self.verify(self.both())
		self.assertEqual(answer.status, NOT_VERIFIED)
		self.assertIn("holds this award", " ".join(answer.mismatches))
