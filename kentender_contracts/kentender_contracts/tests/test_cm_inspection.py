# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 5.5, 5.6, boards D05, D05-M, D19, D06 (plan Phase 6; tracker CM8-603, CM8-604; CM-AC-07, 08, 09, 67): inspection from the frozen criteria, with the units that are ready going on while
the ones still waiting for a reading wait.

A unit with no reading is Needs review, so one inspected serial never stands for a delivery, and there is no sampling rule of our own. A technical certificate confirms the units that have a reading and
names the ones that do not; those can be read again, and a second certificate confirms them; an acceptance report accepts only the units a signed certificate covers."""

from __future__ import annotations

import frappe

from kentender_contracts.boards import router
from kentender_contracts.services import delivery, errors, position, records, work
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class TestInspection(ContractCase):
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
		self.p = self.people
		self.t = tw.Thread(self.p, tag="INS")
		self.case = self.t.active()
		self.t.appointed()
		self.units = tw.fresh_serials(4)
		self.arrival = self.t.arrive(self.units)["arrival"]

	def mine(self, *who):
		users = {self.p[w] for w in who}
		return {(x["command"].split(":")[0], x["holder"], x["state"], x["title"]) for x in work.live(self.case) if x["holder"] in users}

	def certify(self, who="peter"):
		return delivery.sign_technical_certificate(self.case, arrival=self.arrival, expected_version=self.t.version(), idempotency_key=self.t.key("cert"), actor=self.p[who])

	def reread(self, units, **kw):
		return delivery.record_inspection(self.case, arrival=self.arrival, expected_version=self.t.version(), idempotency_key=self.t.key("reread"), actor=self.p["peter"], observations=tw.readings(units, **kw))

	# -- a unit with no reading ------------------------------------------------------------------------------------------------------
	def test_a_unit_with_no_reading_is_needs_review_and_one_serial_never_stands_for_the_delivery(self):
		self.t.inspect(self.arrival, self.units, blank=(self.units[1],))
		found = records.loads(delivery.current_inspection(self.case, self.arrival).findings_json)
		self.assertEqual({u: f["result"] for u, f in found["units"].items()}, {self.units[0]: "Meets", self.units[1]: "Needs review", self.units[2]: "Meets", self.units[3]: "Meets"})
		only_one = delivery.record_inspection(self.case, arrival=self.arrival, expected_version=self.t.version(), idempotency_key=self.t.key("one"), actor=self.p["peter"], observations=tw.readings(self.units[:1]))
		found = records.loads(delivery.current_inspection(self.case, self.arrival).findings_json)
		self.assertEqual(found["summary"], {"Meets": 1, "Does not meet": 0, "Needs review": 3}, "reading one unit does not cover the other three")

	def test_a_sample_is_refused_where_the_approved_requirements_authorise_none(self):
		exc = refusal(delivery.record_inspection, self.case, arrival=self.arrival, expected_version=self.t.version(), idempotency_key=self.t.key("sample"), actor=self.p["peter"],
			observations=tw.readings(self.units[:1]), coverage="authorised sample")
		self.assertEqual(exc.code, "CM_INCOMPLETE")
		self.assertIn("every unit is read", exc.detail["reason"])

	# -- partial confirmation --------------------------------------------------------------------------------------------------------
	def test_the_units_with_a_reading_are_confirmed_and_the_rest_wait_for_theirs(self):
		self.t.inspect(self.arrival, self.units, blank=(self.units[1], self.units[3]))
		live = self.mine("peter", "julia", "brian")
		self.assertIn(("SignTechnicalCertificate", self.p["peter"], "actionable", "Sign the technical certificate."), live, "the ready units go on")
		self.assertTrue([1 for c, _h, s, title in live if c == "RecordInspectionObservations" and s == "actionable" and title == "The inspection evidence needs review."], "the inspectors are asked for the missing readings")
		cert = frappe.get_doc("Contract Certificate", self.certify()["certificate"])
		content = records.loads(cert.content_json)
		self.assertEqual((sorted(content["covered"]), sorted(content["not_covered"])), (sorted([self.units[0], self.units[2]]), sorted([self.units[1], self.units[3]])))
		self.assertEqual(delivery.certified_units(self.case, 1), {self.units[0], self.units[2]})

	def test_the_confirmed_units_cannot_be_read_again_and_the_rest_can_and_get_their_own_certificate(self):
		self.t.inspect(self.arrival, self.units, blank=(self.units[1],))
		self.certify()
		self.assertEqual(refusal(self.reread, [self.units[0]]).code, "CM_RECONCILE", "a unit already confirmed is not quietly re-read")
		self.reread([self.units[1]])
		found = records.loads(delivery.current_inspection(self.case, self.arrival).findings_json)
		self.assertEqual({u: f["result"] for u, f in found["units"].items()}[self.units[0]], "Meets", "the confirmed units keep the readings they were confirmed on")
		second = frappe.get_doc("Contract Certificate", self.certify()["certificate"])
		self.assertEqual(records.loads(second.content_json)["covered"], [self.units[1]])
		self.assertEqual(delivery.certified_units(self.case, 1), set(self.units))
		self.assertEqual(len(delivery.signed_certificates(self.case, 1)), 2)
		self.assertTrue(self.certify().get("already"), "signing the same confirmation again changes nothing")

	def test_an_acceptance_report_accepts_only_the_units_a_signed_certificate_covers(self):
		self.t.inspect(self.arrival, self.units, blank=(self.units[1],))
		self.certify()
		out = delivery.prepare_acceptance_report(self.case, arrivals=[self.arrival], expected_version=self.t.version(), idempotency_key=self.t.key("prepare"), actor=self.p["julia"])
		line = records.loads(frappe.get_doc("Contract Acceptance", out["acceptance"]).lines_json)[0]
		self.assertEqual((sorted(line["units"]["accepted"]), line["units"]["deferred"]), (sorted([self.units[0], self.units[2], self.units[3]]), [self.units[1]]))
		self.assertEqual(line["accepted"] + line["rejected"] + line["deferred"], line["arrived"])

	def test_a_unit_that_meets_but_is_not_yet_confirmed_is_deferred_not_accepted(self):
		self.t.inspect(self.arrival, self.units, blank=(self.units[1],))
		self.certify()
		self.reread([self.units[1]])  # read now, so it meets, but its confirmation is not signed yet
		out = delivery.prepare_acceptance_report(self.case, arrivals=[self.arrival], expected_version=self.t.version(), idempotency_key=self.t.key("prepare"), actor=self.p["julia"])
		line = records.loads(frappe.get_doc("Contract Acceptance", out["acceptance"]).lines_json)[0]
		self.assertEqual((self.units[1] in line["units"]["accepted"], line["units"]["deferred"], line["reasons"][self.units[1]]), (False, [self.units[1]], "Not yet confirmed technically."))

	def test_the_deferred_unit_is_accepted_by_a_later_report_once_it_is_read_and_confirmed(self):
		self.t.inspect(self.arrival, self.units, blank=(self.units[1],))
		self.certify()
		first = delivery.prepare_acceptance_report(self.case, arrivals=[self.arrival], expected_version=self.t.version(), idempotency_key=self.t.key("prepare"), actor=self.p["julia"])
		for who in ("julia", "peter", "brian"):
			delivery.sign_acceptance_report(self.case, acceptance=first["acceptance"], expected_version=self.t.version(), idempotency_key=self.t.key("sign"), actor=self.p[who])
		self.reread([self.units[1]])
		self.certify()
		second = delivery.prepare_acceptance_report(self.case, arrivals=[self.arrival], expected_version=self.t.version(), idempotency_key=self.t.key("prepare2"), actor=self.p["julia"])
		line = records.loads(frappe.get_doc("Contract Acceptance", second["acceptance"]).lines_json)[0]
		self.assertEqual((line["units"]["accepted"], line["accepted"] + line["rejected"] + line["deferred"]), ([self.units[1]], 1), "only the newly confirmed unit is covered; prior decisions are not repeated")

	# -- the screens -----------------------------------------------------------------------------------------------------------------
	def test_the_blocked_inspection_screen_and_the_certificate_that_names_what_is_missing(self):
		self.t.inspect(self.arrival, self.units, blank=(self.units[2],))
		inspector = tw.capture(router.board_for(self.case, self.p["julia"]))
		self.assertEqual((inspector["id"], inspector["next"]["k"], inspector["p"]), ("D05-M", "blk", ""))
		self.assertEqual(sorted(inspector["next"]["fixes"]), ["Record observations", "View all observations"])
		self.assertEqual({"dialog"}, {inspector["actions"][f]["do"] for f in ("Record observations", "View all observations")})
		cert = router.board_for(self.case, self.p["peter"], tab="Deliveries")
		self.assertEqual(cert["id"], "D19", "the certifier confirms the units that have a reading first")
		facts = {r[0]: r[1] for r in cert["regions"][0]["b"][0]["items"]}
		self.assertEqual((facts["Inspected"], facts["Conforms"], facts["Missing evidence"]), ("4", "3", "1"))
