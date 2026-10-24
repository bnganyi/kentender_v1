# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 5.4 to 5.6 and boards D31, D31-A (plan Phase 6; tracker CM8-605; CM-AC-06, 10, 49): a related service is performed and evidenced, never received.

The package here is the goods-plus-service one: ten laptops at KES 100,000 and one training session at KES 50,000. The service has its own requirement, deadline and evidence; goods criteria do not apply to it
and its criteria do not apply to the laptops; accepting it creates no receipt, no stock and no asset; and the entitlement it creates is claimed once."""

from __future__ import annotations

from kentender_contracts.simulation.timeline import D, short_date  # noqa: F401
import json

import frappe

from kentender_contracts.boards import router
from kentender_contracts.services import delivery, errors, payment, position, records, work
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


def flat(value) -> str:
	return json.dumps(value, ensure_ascii=False)


def service_readings(unit, attendance="10", checklist="10"):
	return [{"unit": unit, "criterion_id": "C4", "value": attendance}, {"unit": unit, "criterion_id": "C5", "value": checklist}]


class TestRelatedServices(ContractCase):
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
		self.t = tw.Thread(self.p, tag="SVC", services=True)
		self.case = self.t.active()
		self.t.appointed()
		self.terms = records.loads(frappe.db.get_value("Contract Agreement Version", {"contract_case": self.case, "state": "Effective"}, "terms_json"))

	def perform(self, reference="TRAIN-01", quantity=1):
		return delivery.record_arrival(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("perform"), actor=self.p["grace"], received_at=D("2027-07-26 14:00:00"), destination="Afya House training room",
			items=[{"line_id": "L2", "quantity": quantity, "units": [reference] if reference else []}])

	def read(self, arrival, unit, **kw):
		return delivery.record_inspection(self.case, arrival=arrival, expected_version=self.t.version(), idempotency_key=self.t.key("read"), actor=self.p["peter"], observations=service_readings(unit, **kw))

	def certify(self, arrival):
		return delivery.sign_technical_certificate(self.case, arrival=arrival, expected_version=self.t.version(), idempotency_key=self.t.key("cert"), actor=self.p["peter"])

	def report(self, *arrivals):
		return delivery.prepare_acceptance_report(self.case, arrivals=list(arrivals), expected_version=self.t.version(), idempotency_key=self.t.key("prepare"), actor=self.p["julia"])["acceptance"]

	def sign_all(self, report):
		out = {}
		for who in ("julia", "peter", "brian"):
			out = delivery.sign_acceptance_report(self.case, acceptance=report, expected_version=self.t.version(), idempotency_key=self.t.key(f"sign-{who}"), actor=self.p[who])
		return out

	def serviced(self, **kw):
		arrival = self.perform()["arrival"]
		self.read(arrival, "TRAIN-01", **kw)
		return arrival

	# -- the package ------------------------------------------------------------------------------------------------------------------
	def test_the_package_carries_the_service_with_its_requirement_deadline_and_evidence(self):
		lines = {l["line_id"]: l for l in self.terms["lines"]}
		self.assertEqual((lines["L2"]["kind"], lines["L2"]["quantity"], lines["L2"]["rate"], self.terms["total"]), ("service", 1, 50000, 1050000))
		self.assertEqual(self.terms["services"][0], {"line_id": "L2", "requirement": "Train ten named users to start and operate the supplied laptops", "deadline": D("2027-07-27"), "evidence_required": "Attendance and completed practical checklist"})
		self.assertEqual({l["line_id"] for l in self.terms["lines"] if l.get("kind") == "service"}, {"L2"})
		self.assertEqual(delivery.service_lines(self.terms), {"L2"})

	def test_goods_criteria_do_not_apply_to_the_service_and_the_service_criteria_do_not_apply_to_the_laptops(self):
		self.assertEqual([c["id"] for c in delivery.criteria_for(self.terms, "L2")], ["C4", "C5"])
		self.assertEqual([c["id"] for c in delivery.criteria_for(self.terms, "L1")], ["C1", "C2", "C3"])
		unscoped = [{"id": "G1", "name": "Sealed", "comparator": "=", "value": "Yes", "unit": ""}]
		self.assertEqual([c["id"] for c in delivery.criteria_for({"lines": self.terms["lines"], "criteria": unscoped}, "L1")], ["G1"], "a criterion naming no line applies to the goods")
		self.assertEqual(delivery.criteria_for({"lines": self.terms["lines"], "criteria": unscoped}, "L2"), [], "and never to a service")

	def test_a_unit_no_criterion_applies_to_is_needs_review_never_silently_meets(self):
		found = delivery.findings([{"id": "C1", "name": "RAM", "comparator": ">=", "value": 16, "unit": "GB", "line_id": "L1"}], ["TRAIN-01"], [], {"TRAIN-01": "L2"}, {"L2"})
		self.assertEqual(found["units"]["TRAIN-01"]["result"], "Needs review")

	# -- performing the service -----------------------------------------------------------------------------------------------------
	def test_a_performed_service_is_recorded_with_its_reference_and_the_inspectors_are_asked_for_the_evidence(self):
		out = self.perform()
		arrival = frappe.get_doc("Contract Arrival", out["arrival"])
		item = records.loads(arrival.items_json)[0]
		self.assertEqual((item["line_id"], item["units"], item["unidentified"]), ("L2", ["TRAIN-01"], 0))
		live = {(x["command"].split(":")[0], x["title"]) for x in work.live(self.case) if x["holder"] == self.p["peter"]}
		self.assertIn(("RecordInspectionObservations", "Record the training evidence."), live)

	def test_a_service_with_no_reference_is_given_one_so_its_evidence_has_something_to_attach_to(self):
		out = self.perform(reference="")
		item = records.loads(frappe.get_doc("Contract Arrival", out["arrival"]).items_json)[0]
		self.assertEqual((item["units"], item["unidentified"]), (["SVC-001-L2-1"], 0))

	def test_a_service_is_recorded_on_its_own_not_with_goods(self):
		exc = refusal(delivery.record_arrival, self.case, expected_version=self.t.version(), idempotency_key=self.t.key("mixed"), actor=self.p["grace"], received_at=D("2027-07-12 10:00:00"), destination="Afya House store",
			items=[{"line_id": "L1", "quantity": 1, "units": tw.fresh_serials(1)}, {"line_id": "L2", "quantity": 1, "units": ["TRAIN-01"]}])
		self.assertIn("on its own", exc.fields["items"])

	# -- the evidence -----------------------------------------------------------------------------------------------------------------
	def test_the_evidence_is_judged_against_the_services_own_requirements(self):
		arrival = self.serviced()
		found = records.loads(delivery.current_inspection(self.case, arrival).findings_json)
		self.assertEqual((found["units"]["TRAIN-01"]["result"], sorted(found["units"]["TRAIN-01"]["criteria"])), ("Meets", ["C4", "C5"]))

	def test_short_attendance_does_not_meet(self):
		arrival = self.serviced(attendance="7")
		found = records.loads(delivery.current_inspection(self.case, arrival).findings_json)["units"]["TRAIN-01"]
		self.assertEqual((found["result"], found["criteria"]["C4"]["reason"]), ("Does not meet", "Attendance is 7, below the requirement."))

	def test_a_missing_checklist_is_needs_review(self):
		arrival = self.perform()["arrival"]
		self.read(arrival, "TRAIN-01", checklist="")
		self.assertEqual(records.loads(delivery.current_inspection(self.case, arrival).findings_json)["units"]["TRAIN-01"]["result"], "Needs review")

	# -- accepting it creates no stock and no asset, and the entitlement is claimed once ---------------------------------------
	def test_accepting_the_service_posts_no_receipt_and_creates_no_stock_or_asset_unit(self):
		arrival = self.serviced()
		self.certify(arrival)
		report = self.report(arrival)
		before = frappe.db.count("Asset", {"purchase_receipt": ["is", "set"]})
		out = self.sign_all(report)
		self.assertTrue(out["effective"])
		doc = frappe.get_doc("Contract Acceptance", report)
		self.assertEqual((doc.state, doc.posting_intent), ("Effective", None), "nothing to post for a service")
		self.assertEqual(delivery.posted_receipts(self.case), [])
		self.assertEqual(frappe.db.count("Asset", {"purchase_receipt": ["is", "set"]}), before)
		self.assertEqual(position.position(self.case)["lines"]["L2"]["accepted"], 1)

	def test_the_entitlement_is_the_services_price_and_it_is_claimed_once(self):
		arrival = self.serviced()
		self.certify(arrival)
		self.sign_all(self.report(arrival))
		first = payment.submit_invoice(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("c1"), actor=self.p["david"], claim_reference="SVC-INV-1", invoice_date=frappe.utils.today(), lines=[{"line_id": "L2", "quantity": 1}])
		self.assertEqual((frappe.db.get_value("Contract Invoice", first["invoice"], "state"), frappe.db.get_value("Contract Invoice", first["invoice"], "claimed_amount")), ("Submitted", 50000))
		again = payment.submit_invoice(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("c2"), actor=self.p["david"], claim_reference="SVC-INV-2", invoice_date=frappe.utils.today(), lines=[{"line_id": "L2", "quantity": 1}])
		self.assertEqual(frappe.db.get_value("Contract Invoice", again["invoice"], "state"), "Held", "the same training is not paid twice")

	def test_the_services_claim_is_invoiced_natively_from_the_order_because_there_is_no_receipt(self):
		arrival = self.serviced()
		self.certify(arrival)
		self.sign_all(self.report(arrival))
		out = payment.submit_invoice(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("c1"), actor=self.p["david"], claim_reference="SVC-INV-1", invoice_date=frappe.utils.today(), lines=[{"line_id": "L2", "quantity": 1}])
		row = frappe.get_doc("Contract Invoice", out["invoice"])
		self.assertTrue(row.native_invoice)
		doc = frappe.get_doc("Purchase Invoice", row.native_invoice)
		self.assertEqual((doc.docstatus, doc.grand_total, [(i.item_code, i.qty) for i in doc.items], bool(doc.items[0].purchase_receipt)), (0, 50000, [("CM-TEST-SERVICE", 1)], False))

	def test_goods_and_a_service_accepted_together_receive_only_the_goods(self):
		units = tw.fresh_serials(3)
		goods = self.t.arrive(units)["arrival"]
		self.t.inspect(goods, units)
		service = self.serviced()
		self.certify(goods)
		self.certify(service)
		self.sign_all(self.report(goods, service))
		receipt = frappe.get_doc("Purchase Receipt", delivery.posted_receipts(self.case)[0])
		self.assertEqual([(r.item_code, r.qty) for r in receipt.items], [("CM-TEST-LAPTOP-FA", 3)], "the training is not a receipt line")
		claim = payment.submit_invoice(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("svc"), actor=self.p["david"], claim_reference="SVC-INV-9", invoice_date=frappe.utils.today(), lines=[{"line_id": "L2", "quantity": 1}])
		stored = records.loads(frappe.db.get_value("Contract Invoice", claim["invoice"], "lines_json"))
		self.assertEqual((frappe.db.get_value("Contract Invoice", claim["invoice"], "state"), stored[0]["receipt"]), ("Submitted", ""), "a service claim is never tied to the laptops' receipt")

	# -- the boards -------------------------------------------------------------------------------------------------------------------
	def test_the_certifier_sees_the_service_board_and_the_signers_the_service_report_board(self):
		arrival = self.perform()["arrival"]
		board = tw.capture(router.board_for(self.case, self.p["peter"]))
		self.assertEqual((board["id"], board["title"], board["p"]), ("D31", "Review training completion", "Save observations"))
		text = flat(board["regions"])
		for needle in ("1 training session · KES 50,000", "Train ten named users to start and operate the supplied laptops", short_date("2027-07-27"), "Attendance and completed practical checklist", "TRAIN-01", "Observed attendance"):
			self.assertIn(needle, text)
		self.read(arrival, "TRAIN-01")
		self.certify(arrival)
		self.report(arrival)
		signing = tw.capture(router.board_for(self.case, self.p["julia"]))
		self.assertEqual((signing["id"], signing["p"]), ("D31-A", "Sign report"))
		text = flat(signing["regions"])
		self.assertIn("Invoice entitlement for the service is KES 50,000, once. No stock or asset unit is created for a training service.", text)
		self.assertIn("Technical member", text)
