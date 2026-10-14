# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 sections 5.4 to 5.6, 6.1, 6.2.1 (plan Phase 4; tracker CM8-406 to CM8-412): appointment and declarations, arrival, inspection against the frozen criteria, the
technical certificate, the acceptance report with every required signer, and the accepted-subset receipt on real ERPNext (units and assets), through the real signing facade. Mutation checks are
recorded in the tracker."""

from __future__ import annotations

from unittest import mock

import frappe

from kentender_contracts.native import adapter
from kentender_contracts.services import bindings, delivery, errors, formation, holds, position, records, work
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

CONTROLS = "Contract Test Environment Controls"


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class DeliveryCase(ContractCase):
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
		frappe.db.set_single_value(CONTROLS, "signing_outcome", "")
		self.p = self.people
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24])
		self.case = self.t.active()
		self.units = tw.fresh_serials(10)

	def v(self):
		return self.t.version()

	def k(self, step):
		return self.t.key(step)


class TestAppointment(DeliveryCase):
	def members(self, **kw):
		return [{"user": self.p["julia"], "capacity": "Chair"}, {"user": self.p["peter"], "certifier": True}, {"user": self.p["brian"]}]

	def test_a_recommendation_needs_a_chair_two_others_the_responsibility_and_a_technical_confirmer(self):
		for members, field in (
				(self.members()[:2], "members"), ([{"user": self.p["julia"], "capacity": "Chair"}, {"user": self.p["peter"]}, {"user": self.p["brian"]}], "members"),
				([{"user": self.p["julia"], "capacity": "Chair"}, {"user": self.p["peter"], "certifier": True}, {"user": self.p["grace"]}], "members")):
			exc = refusal(delivery.recommend_inspectors, self.case, expected_version=self.v(), idempotency_key=self.k("r"), actor=self.p["charles"], members=members)
			self.assertIn(field, exc.fields)

	def test_hop_recommends_the_accounting_officer_appoints_and_each_member_declares_before_acting(self):
		rec = delivery.recommend_inspectors(self.case, expected_version=self.v(), idempotency_key=self.k("r"), actor=self.p["charles"], members=self.members())
		self.assertEqual(refusal(delivery.recommend_inspectors, self.case, expected_version=self.v(), idempotency_key=self.k("r"), actor=self.p["julia"], members=self.members()).code, "CM_AUTHORITY")
		self.assertEqual(refusal(delivery.appoint_inspectors, self.case, appointment=rec["appointment"], expected_version=self.v(), idempotency_key=self.k("a"), actor=self.p["charles"]).code, "CM_AUTHORITY")
		delivery.appoint_inspectors(self.case, appointment=rec["appointment"], expected_version=self.v(), idempotency_key=self.k("a"), actor=self.p["amina"])
		state = delivery.appointment_state(self.case)
		self.assertEqual((state["ready"], sorted(state["missing"])), (False, sorted([self.p["julia"], self.p["peter"], self.p["brian"]])))
		exc = refusal(delivery.require_ready, self.case)
		self.assertEqual((exc.code, len(exc.detail["undeclared"])), ("CM_APPOINTMENT", 3))
		for who in ("julia", "peter", "brian"):
			delivery.declare_interest(self.case, expected_version=self.v(), idempotency_key=self.k("d"), actor=self.p[who])
		self.assertTrue(delivery.appointment_state(self.case)["ready"])
		self.assertEqual(refusal(delivery.declare_interest, self.case, expected_version=self.v(), idempotency_key=self.k("d"), actor=self.p["grace"]).code, "CM_AUTHORITY")

	def test_a_declared_conflict_suspends_that_member_and_asks_hop_for_a_replacement(self):
		rec = delivery.recommend_inspectors(self.case, expected_version=self.v(), idempotency_key=self.k("r"), actor=self.p["charles"], members=self.members())
		delivery.appoint_inspectors(self.case, appointment=rec["appointment"], expected_version=self.v(), idempotency_key=self.k("a"), actor=self.p["amina"])
		delivery.declare_interest(self.case, expected_version=self.v(), idempotency_key=self.k("d"), actor=self.p["brian"], conflict="My brother owns the supplier.")
		self.assertIsNone(bindings.inspector_act(self.case, self.p["brian"]), "a conflicted member cannot act")
		self.assertTrue(bindings.inspector_read(self.case, self.p["brian"]), "but the appointment still lets them read")
		self.assertIn(("RecommendContractInspectors", self.p["charles"]), {(t["command"], t["holder"]) for t in work.live(self.case)})
		self.assertEqual(delivery.appointment_state(self.case)["conflicts"], [self.p["brian"]])

	def test_a_returned_recommendation_keeps_its_reason_and_goes_back_to_hop(self):
		rec = delivery.recommend_inspectors(self.case, expected_version=self.v(), idempotency_key=self.k("r"), actor=self.p["charles"], members=self.members())
		self.assertIn("reason", refusal(delivery.return_appointment, self.case, appointment=rec["appointment"], expected_version=self.v(), idempotency_key=self.k("x"), actor=self.p["amina"], reason=" ").fields)
		delivery.return_appointment(self.case, appointment=rec["appointment"], expected_version=self.v(), idempotency_key=self.k("x"), actor=self.p["amina"], reason="Name a member from the user department.")
		self.assertEqual(frappe.db.get_value("Contract Appointment", rec["appointment"], ["state", "reason"]), ("Returned", "Name a member from the user department."))
		self.assertIsNone(bindings.effective_appointment(self.case))

	def test_a_later_appointment_applies_from_then_on_and_the_earlier_is_kept(self):
		self.t.appointed()
		first = bindings.effective_appointment(self.case)["appointment"]
		rec = delivery.recommend_inspectors(self.case, expected_version=self.v(), idempotency_key=self.k("r"), actor=self.p["charles"], members=self.members())
		delivery.appoint_inspectors(self.case, appointment=rec["appointment"], expected_version=self.v(), idempotency_key=self.k("a"), actor=self.p["amina"])
		self.assertEqual(frappe.db.get_value("Contract Appointment", first, "state"), "Replaced")
		self.assertNotEqual(bindings.effective_appointment(self.case)["appointment"], first)
		self.assertTrue(frappe.db.get_value("Contract Appointment", first, "effective_to"))


class TestArrivalAndInspection(DeliveryCase):
	def setUp(self):
		super().setUp()
		self.t.appointed()

	def test_only_the_receiver_records_an_arrival_and_it_makes_custody_and_inspection_work_not_a_receipt(self):
		before = frappe.db.count("Purchase Receipt", {"supplier": world.SUPPLIER})
		self.assertEqual(refusal(delivery.record_arrival, self.case, expected_version=self.v(), idempotency_key=self.k("a"), actor=self.p["julia"], received_at="2027-07-12 10:00:00",
			destination="Afya House store", items=[{"line_id": "L1", "quantity": 10, "units": self.units}]).code, "CM_AUTHORITY")
		out = self.t.arrive(self.units)
		self.assertEqual(frappe.db.count("Purchase Receipt", {"supplier": world.SUPPLIER}), before, "arrival creates no native receipt (section 5.4)")
		live = {(t["command"], t["holder"]) for t in work.live(self.case) if t["holder"] in self.p.values()}
		self.assertTrue({("RecordInspectionObservations", self.p[w]) for w in ("julia", "peter", "brian")} <= live)
		now = position.position(self.case)
		self.assertEqual((now["arrived"], now["accepted"], now["in_custody"], now["remaining"]), (10, 0, 10, 10))
		self.assertEqual(frappe.db.get_value("Contract Arrival", out["arrival"], ["arrival_no", "delivery_reference", "state"]), (1, "DEL-001", "Recorded"))

	def test_the_same_unit_cannot_arrive_twice_and_a_blank_arrival_names_its_fields(self):
		self.t.arrive(self.units[:5])
		self.assertEqual(refusal(self.t.arrive, self.units[4:7]).code, "CM_DUPLICATE")
		exc = refusal(delivery.record_arrival, self.case, expected_version=self.v(), idempotency_key=self.k("a"), actor=self.p["grace"], received_at="", destination="", items=[])
		self.assertEqual(set(exc.fields), {"items", "received_at", "destination"})

	def test_missing_serials_stay_unresolved_and_no_serial_is_invented(self):
		out = delivery.record_arrival(self.case, expected_version=self.v(), idempotency_key=self.k("a"), actor=self.p["grace"], received_at="2027-07-12 10:00:00", destination="Afya House store",
			items=[{"line_id": "L1", "quantity": 10, "units": self.units[:8]}])
		items = records.loads(frappe.db.get_value("Contract Arrival", out["arrival"], "items_json"))
		self.assertEqual((items[0]["quantity"], len(items[0]["units"]), items[0]["unidentified"]), (10, 8, 2))
		self.assertEqual(position.position(self.case)["lines"]["L1"]["unidentified"], 2)

	def test_inspection_needs_an_appointed_declared_inspector_and_gives_findings_against_the_frozen_criteria(self):
		arrival = self.t.arrive(self.units)["arrival"]
		stranger = refusal(delivery.record_inspection, self.case, arrival=arrival, expected_version=self.v(), idempotency_key=self.k("i"), actor=self.p["grace"], observations=tw.readings(self.units))
		self.assertEqual(stranger.code, "CM_AUTHORITY")
		out = self.t.inspect(arrival, self.units, bad=(self.units[8], self.units[9]), blank=(self.units[7],))
		self.assertEqual(out["findings"], {"Meets": 7, "Does not meet": 2, "Needs review": 1})
		found = records.loads(frappe.db.get_value("Contract Inspection", out["inspection"], "findings_json"))
		bad = found["units"][self.units[8]]["criteria"]["C1"]
		self.assertEqual((bad["result"], bad["requirement"], bad["observed"]), ("Does not meet", "Screen size >= 14 inch", "13.3"))
		self.assertEqual(found["units"][self.units[7]]["criteria"]["C1"]["result"], "Needs review", "a blank required reading is never a pass")

	def test_a_new_record_supersedes_the_earlier_one_and_keeps_it(self):
		arrival = self.t.arrive(self.units)["arrival"]
		first = self.t.inspect(arrival, self.units, bad=(self.units[9],))
		second = self.t.inspect(arrival, self.units)
		self.assertEqual((first["inspection_version"], second["inspection_version"]), (1, 2))
		self.assertEqual(frappe.db.get_value("Contract Inspection", first["inspection"], "state"), "Superseded")
		self.assertEqual(delivery.current_inspection(self.case, arrival).name, second["inspection"])
		self.assertIn("Does not meet", frappe.db.get_value("Contract Inspection", first["inspection"], "findings_json"), "the original finding stays visible")

	def test_a_conflicted_or_undeclared_inspector_cannot_record(self):
		arrival = self.t.arrive(self.units)["arrival"]
		frappe.db.set_value("Contract Appointment", bindings.effective_appointment(self.case)["appointment"], "members_json",
			records.dumps([{**m, "declared_at": None} if m["user"] == self.p["peter"] else m for m in bindings.effective_appointment(self.case)["members"]]))
		exc = refusal(self.t.inspect, arrival, self.units)
		self.assertIn(exc.code, ("CM_AUTHORITY", "CM_APPOINTMENT"))


class TestAcceptanceAndReceipt(DeliveryCase):
	def setUp(self):
		super().setUp()
		self.t.appointed()
		self.arrival = self.t.arrive(self.units)["arrival"]
		self.good, self.bad = self.units[:8], self.units[8:]
		self.t.inspect(self.arrival, self.units, bad=tuple(self.bad))

	def certify(self):
		return delivery.sign_technical_certificate(self.case, arrival=self.arrival, expected_version=self.v(), idempotency_key=self.k("c"), actor=self.p["peter"])

	def prepare(self, **kw):
		return delivery.prepare_acceptance_report(self.case, arrivals=[self.arrival], expected_version=self.v(), idempotency_key=self.k("p"), actor=self.p["julia"], **kw)

	def sign_all(self, acceptance, who=("julia", "peter", "brian")):
		out = None
		for person in who:
			out = delivery.sign_acceptance_report(self.case, acceptance=acceptance, expected_version=self.v(), idempotency_key=self.k("s"), actor=self.p[person])
		return out

	def test_only_the_technical_certifier_signs_the_technical_certificate_and_only_when_every_reading_is_in(self):
		self.assertEqual(refusal(delivery.sign_technical_certificate, self.case, arrival=self.arrival, expected_version=self.v(), idempotency_key=self.k("c"), actor=self.p["julia"]).code, "CM_AUTHORITY")
		self.t.inspect(self.arrival, self.units, blank=(self.units[0],))
		exc = refusal(self.certify)
		self.assertEqual((exc.code, exc.detail["units"]), ("CM_INCOMPLETE", [self.units[0]]))
		self.t.inspect(self.arrival, self.units, bad=tuple(self.bad))
		out = self.certify()
		self.assertEqual(out["state"], "Signed")
		cert = frappe.get_doc("Contract Certificate", out["certificate"])
		self.assertTrue(cert.proof_reference.startswith("CMSIM-"))
		self.assertEqual(cert.signer, self.p["peter"])
		self.assertTrue(self.certify().get("already"))
		self.assertEqual(frappe.db.count("Contract Simulated Signature", {"fixture_namespace": "CM_TEST", "signer": self.p["peter"]}), 1)
		self.assertEqual(refusal(self.t.inspect, self.arrival, self.units).code, "CM_RECONCILE", "a signed confirmation is not quietly re-inspected")

	def test_the_chair_prepares_one_report_whose_quantities_add_up_to_what_it_covers(self):
		exc = refusal(self.prepare)
		self.assertEqual(exc.code, "CM_INCOMPLETE")
		self.certify()
		self.assertEqual(refusal(delivery.prepare_acceptance_report, self.case, arrivals=[self.arrival], expected_version=self.v(), idempotency_key=self.k("p"), actor=self.p["peter"]).code, "CM_AUTHORITY")
		out = self.prepare()
		report = frappe.get_doc("Contract Acceptance", out["acceptance"])
		line = records.loads(report.lines_json)[0]
		self.assertEqual((line["accepted"], line["rejected"], line["deferred"], line["arrived"]), (8, 2, 0, 10))
		self.assertEqual((line["units"]["accepted"], line["units"]["rejected"]), (self.good, self.bad))
		self.assertEqual([s["user"] for s in records.loads(report.signers_json)], [self.p["julia"], self.p["peter"], self.p["brian"]])
		self.assertEqual(position.position(self.case)["accepted"], 0, "nothing is accepted until the last required signature")

	def test_a_unit_that_did_not_meet_cannot_be_accepted_and_a_met_unit_is_rejected_only_with_a_reason(self):
		self.certify()
		exc = refusal(self.prepare, overrides={self.bad[0]: {"disposition": "accepted"}})
		self.assertEqual(exc.code, "CM_INCOMPLETE")
		exc = refusal(self.prepare, overrides={self.good[0]: {"disposition": "rejected", "reason": ""}})
		self.assertIn("overrides", exc.fields)
		out = self.prepare(overrides={self.good[0]: {"disposition": "deferred", "reason": "Screen flicker to be re-checked."}})
		line = records.loads(frappe.db.get_value("Contract Acceptance", out["acceptance"], "lines_json"))[0]
		self.assertEqual((line["accepted"], line["rejected"], line["deferred"]), (7, 2, 1))

	def test_every_required_member_signs_the_same_report_and_the_last_proof_makes_one_decision_and_posts_the_accepted_units_once(self):
		self.certify()
		out = self.prepare()
		before_assets = frappe.db.count("Asset", {"item_code": world.ITEM_FA, "docstatus": ["<", 2]})
		first = delivery.sign_acceptance_report(self.case, acceptance=out["acceptance"], expected_version=self.v(), idempotency_key=self.k("s"), actor=self.p["julia"])
		self.assertFalse(first.get("effective"))
		self.assertEqual(frappe.db.get_value("Contract Acceptance", out["acceptance"], "state"), "Awaiting signatures")
		self.assertEqual(delivery.posted_receipts(self.case), [])
		self.sign_all(out["acceptance"], who=("peter", "brian"))
		report = frappe.get_doc("Contract Acceptance", out["acceptance"])
		self.assertEqual((report.state, bool(report.decision_at), bool(report.posting_intent)), ("Effective", True, True))
		receipts = delivery.posted_receipts(self.case)
		self.assertEqual(len(receipts), 1)
		receipt = frappe.get_doc("Purchase Receipt", receipts[0])
		self.assertEqual((receipt.docstatus, receipt.supplier, [(i.item_code, i.qty) for i in receipt.items]), (1, world.SUPPLIER, [(world.ITEM_FA, 8)]))
		assets = frappe.get_all("Asset", filters={"purchase_receipt": receipts[0], "docstatus": ["<", 2]}, pluck="cm_unit_reference")
		self.assertEqual(sorted(assets), self.good, "an asset for each accepted unit, named by its own reference; none for the rejected")
		self.assertEqual(frappe.db.count("Asset", {"item_code": world.ITEM_FA, "docstatus": ["<", 2]}) - before_assets, 8)
		now = position.position(self.case)
		self.assertEqual((now["accepted"], now["lines"]["L1"]["rejected"], now["in_custody"], now["remaining"]), (8, 2, 2, 2))
		self.assertEqual(holds.open_holds(self.case), [])
		again = delivery.post_accepted_receipt(self.case, acceptance=out["acceptance"], actor=self.p["julia"])
		self.assertEqual(again["reference"], receipts[0])
		self.assertEqual(len(delivery.posted_receipts(self.case)), 1)

	def test_the_receiver_cannot_sign_acceptance_of_the_arrival_they_recorded_and_a_stranger_cannot_sign(self):
		self.certify()
		out = self.prepare()
		self.assertEqual(refusal(delivery.sign_acceptance_report, self.case, acceptance=out["acceptance"], expected_version=self.v(), idempotency_key=self.k("s"), actor=self.p["grace"]).code, "CM_AUTHORITY")
		frappe.db.set_value("Contract Arrival", self.arrival, "receiver", self.p["brian"])
		exc = refusal(delivery.sign_acceptance_report, self.case, acceptance=out["acceptance"], expected_version=self.v(), idempotency_key=self.k("s"), actor=self.p["brian"])
		self.assertEqual((exc.code, exc.detail["separation"]), ("CM_SEGREGATION", "receiver_not_acceptance_signer"))

	def test_a_failed_posting_leaves_the_signed_acceptance_and_a_retry_posts_once_without_a_new_signature(self):
		self.certify()
		out = self.prepare()
		with mock.patch.object(adapter, "receive", side_effect=RuntimeError("stock service down")):
			self.sign_all(out["acceptance"])
		report = frappe.get_doc("Contract Acceptance", out["acceptance"])
		self.assertEqual(report.state, "Effective", "signed acceptance is retained (section 5.6)")
		self.assertEqual(frappe.db.get_value("Contract Operation Intent", report.posting_intent, "state"), "Uncertain")
		blocked = {h.key.split(":")[0] for h in holds.open_holds(self.case)}
		self.assertEqual(blocked, {"operation"})
		self.assertTrue(holds.blocking(self.case, "certify_invoice"))
		self.assertIn((self.p["daniel"], "actionable"), {(t["holder"], t["state"]) for t in work.live(self.case)})
		signatures_before = frappe.db.count("Contract Simulated Signature", {"fixture_namespace": "CM_TEST"})
		result = delivery.post_accepted_receipt(self.case, acceptance=out["acceptance"], actor=self.p["daniel"])
		self.assertIn(result["state"], ("Succeeded", "Reconciled"))
		self.assertEqual(len(delivery.posted_receipts(self.case)), 1)
		self.assertEqual(frappe.db.count("Contract Simulated Signature", {"fixture_namespace": "CM_TEST"}), signatures_before)
		self.assertEqual(holds.open_holds(self.case), [])

	def test_rejected_units_are_collected_by_the_supplier_and_only_rejected_units_can_be(self):
		self.certify()
		out = self.prepare()
		self.sign_all(out["acceptance"])
		self.assertEqual(refusal(delivery.record_custody_return, self.case, expected_version=self.v(), idempotency_key=self.k("x"), actor=self.p["grace"], units=[self.good[0]], evidence="Gate pass 1").code, "CM_QUANTITY")
		self.assertIn("evidence", refusal(delivery.record_custody_return, self.case, expected_version=self.v(), idempotency_key=self.k("x"), actor=self.p["grace"], units=self.bad, evidence="").fields)
		delivery.record_custody_return(self.case, expected_version=self.v(), idempotency_key=self.k("x"), actor=self.p["grace"], units=self.bad, evidence="Supplier gate pass GP-77")
		now = position.position(self.case)
		self.assertEqual((now["lines"]["L1"]["returned"], now["in_custody"], now["remaining"]), (2, 0, 2))
