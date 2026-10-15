# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 5.4, board D04 (plan Phase 6; tracker CM8-602; CM-AC-06, 08, 10, 49): goods that arrive are recorded once, whatever they are, and what the contract does not expect is an attributable
exception, never an acceptance.

Arrival creates custody and inspection work only (no native receipt, so no usable stock). Surplus, unexpected, premature and ambiguously referenced goods are recorded with who and when, held apart,
reviewed by HOP and never accepted; the same units under the same reference are a duplicate; a replacement names the rejected units it replaces and consumes the original entitlement."""

from __future__ import annotations

import frappe

from kentender_contracts.services import delivery, errors, formation, position, records, work
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class TestArrivalExceptions(ContractCase):
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
		self.t = tw.Thread(self.p, tag="ARX")

	def active(self):
		self.case = self.t.active()
		self.t.appointed()
		return self.case

	def arrive(self, items, *, reference="", who="grace", at="2027-07-12 10:00:00"):
		return delivery.record_arrival(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("arrive"), actor=self.p[who], received_at=at, destination="Afya House store", items=items, supplier_reference=reference)

	def row(self, number=1):
		return frappe.get_doc("Contract Arrival", {"contract_case": self.case, "arrival_no": number})

	def exceptions(self, number=1):
		return records.loads(self.row(number).exceptions_json, [])

	def mine(self, *who):
		users = {self.p[w] for w in who}
		return {(x["command"].split(":")[0], x["holder"], x["state"]) for x in work.live(self.case) if x["holder"] in users}

	# -- arrival is custody, not stock -----------------------------------------------------------------------------------------------
	def test_arrival_creates_custody_and_inspection_work_and_no_native_receipt(self):
		self.active()
		units = tw.fresh_serials(3)
		receipts = frappe.db.count("Purchase Receipt", {"cm_operation_identity": ["like", f"{self.case}|%"]})
		out = self.t.arrive(units)
		self.assertEqual(frappe.db.count("Purchase Receipt", {"cm_operation_identity": ["like", f"{self.case}|%"]}), receipts, "arrival makes no receipt, so no usable stock")
		self.assertEqual({u["status"] for u in position.position(self.case)["units"].values()}, {"Awaiting decision"})
		self.assertIn(("RecordInspectionObservations", self.p["julia"], "actionable"), self.mine("julia"))
		self.assertEqual(self.exceptions(), [])
		self.assertEqual((self.row().receiver, self.row().recorded_at is not None), (self.p["grace"], True), "attributable: who recorded it, and when")

	# -- surplus ---------------------------------------------------------------------------------------------------------------------
	def test_surplus_goods_are_recorded_held_apart_and_never_inspected_or_accepted(self):
		self.active()
		first = tw.fresh_serials(8)
		self.t.arrive(first)
		second = tw.fresh_serials(4)
		out = self.arrive([{"line_id": "L1", "quantity": 4, "units": second}], at="2027-07-13 10:00:00")
		found = self.exceptions(2)
		self.assertEqual([(e["kind"], e["quantity"], e["units"]) for e in found], [("Excess", 2, second[2:])], "the two beyond the entitlement are the surplus")
		units = position.position(self.case)["units"]
		self.assertEqual([units[u]["status"] for u in second], ["Awaiting decision", "Awaiting decision", "Excess", "Excess"])
		self.assertEqual(position.position(self.case)["lines"]["L1"]["excess_held"], 2)
		self.assertIn(("ResolveDeliveryException", self.p["charles"], "actionable"), self.mine("charles"))
		# the inspector reads only what can be accepted
		delivery.record_inspection(self.case, arrival=out["arrival"], expected_version=self.t.version(), idempotency_key=self.t.key("inspect"), actor=self.p["peter"], observations=tw.readings(second[:2]))
		stored = records.loads(delivery.current_inspection(self.case, out["arrival"]).findings_json)
		self.assertEqual(sorted(stored["units"]), sorted(second[:2]))
		self.assertEqual(refusal(delivery.record_inspection, self.case, arrival=out["arrival"], expected_version=self.t.version(), idempotency_key=self.t.key("surplus"), actor=self.p["peter"],
			observations=tw.readings(second[2:])).code, "CM_INPUT")
		# the surplus can be collected by the supplier, with evidence, like a rejected unit
		done = delivery.record_custody_return(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("collect"), actor=self.p["grace"], units=second[2:], evidence="Collection note C-1")
		self.assertEqual(sorted(done["returned"]), sorted(second[2:]))

	def test_goods_no_line_names_are_an_unexpected_exception_with_no_inspection(self):
		self.active()
		out = self.arrive([{"description": "Docking station", "quantity": 2, "units": ["DOCK-1", "DOCK-2"]}])
		self.assertEqual([(e["kind"], e["item"], e["quantity"]) for e in self.exceptions()], [("Unexpected", "Docking station", 2)])
		self.assertFalse([1 for c, _h, _s in self.mine("julia", "peter", "brian") if c == "RecordInspectionObservations"], "nothing here to inspect")
		self.assertIn(("ResolveDeliveryException", self.p["charles"], "actionable"), self.mine("charles"))
		self.assertEqual(position.position(self.case)["accepted"], 0)
		self.assertEqual(refusal(self.arrive, [{"quantity": 2}]).code, "CM_INPUT", "unexpected goods are described")

	# -- premature -------------------------------------------------------------------------------------------------------------------
	def test_goods_that_arrive_before_the_agreement_is_in_force_are_recorded_and_inspected_only_once_it_is(self):
		out = tw.receive(self.p, contract_id="CM-TEST-ARX-P")
		self.case = self.t.case = out["contract"]
		saved = formation.save_particulars(self.case, expected_version=out["record_version"], idempotency_key=self.t.key("p"), actor=self.p["brian"], values=tw.package_particulars(self.p))
		formation.request_signatures(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("send"), actor=self.p["charles"])
		early = self.arrive([{"line_id": "L1", "quantity": 2, "units": tw.fresh_serials(2)}])
		self.assertEqual([e["kind"] for e in self.exceptions()], ["Premature"])
		self.assertEqual(frappe.db.get_value("Contract Case", self.case, "lifecycle"), "Awaiting signatures")
		self.assertFalse([1 for c, _h, _s in self.mine("julia", "charles") if c == "RecordInspectionObservations"], "no inspection while the agreement is not in force")
		formation.sign_contract(self.case, party="Supplier", expected_version=self.t.version(), idempotency_key=self.t.key("s1"), actor=self.p["mary"])
		formation.sign_contract(self.case, party="Entity", expected_version=self.t.version(), idempotency_key=self.t.key("s2"), actor=self.p["amina"])
		self.assertIn(("RecordInspectionObservations", self.p["charles"], "actionable"), self.mine("charles"), "once Active the goods are open to inspection (inspectors are not yet appointed)")
		self.assertEqual(frappe.db.count("Contract Event", {"contract_case": self.case, "event_type": "Premature delivery released"}), 1)

	# -- ambiguity and duplicates ----------------------------------------------------------------------------------------------------
	def test_the_same_reference_for_other_units_is_ambiguous_and_for_the_same_goods_a_duplicate(self):
		self.active()
		first = tw.fresh_serials(2)
		self.arrive([{"line_id": "L1", "quantity": 2, "units": first}], reference="DN-100")
		again = refusal(self.arrive, [{"line_id": "L1", "quantity": 2, "units": first}], reference="dn-100")
		self.assertEqual(again.code, "CM_DUPLICATE")
		other = self.arrive([{"line_id": "L1", "quantity": 2, "units": tw.fresh_serials(2)}], reference="DN-100", at="2027-07-13 10:00:00")
		self.assertEqual([(e["kind"], e["earlier"]) for e in self.exceptions(2)], [("Ambiguous", "DEL-001")])
		self.assertTrue(frappe.db.exists("Contract Arrival", other["arrival"]))
		blank = self.arrive([{"line_id": "L1", "quantity": 1}], reference="DN-200", at="2027-07-14 10:00:00")
		self.assertEqual(refusal(self.arrive, [{"line_id": "L1", "quantity": 1}], reference="DN-200").code, "CM_DUPLICATE", "the same note, the same quantity, no units: the same delivery")

	def test_hop_records_what_became_of_an_exception_once_and_only_hop(self):
		self.active()
		out = self.arrive([{"description": "Docking station", "quantity": 1, "units": ["DOCK-9"]}])
		for who in ("julia", "grace", "mary"):
			self.assertEqual(refusal(delivery.resolve_exception, self.case, arrival=out["arrival"], disposition="To be collected by the supplier", reason="Told the supplier.", expected_version=self.t.version(),
				idempotency_key=self.t.key("res"), actor=self.p[who]).code, "CM_AUTHORITY", who)
		self.assertEqual(set(refusal(delivery.resolve_exception, self.case, arrival=out["arrival"], disposition="Maybe", reason="", expected_version=self.t.version(), idempotency_key=self.t.key("res"),
			actor=self.p["charles"]).fields), {"disposition", "reason"})
		delivery.resolve_exception(self.case, arrival=out["arrival"], disposition="To be collected by the supplier", reason="Told the supplier.", expected_version=self.t.version(), idempotency_key=self.t.key("res"), actor=self.p["charles"])
		self.assertFalse([1 for c, _h, _s in self.mine("charles") if c == "ResolveDeliveryException"])
		normal = self.arrive([{"line_id": "L1", "quantity": 1, "units": tw.fresh_serials(1)}], at="2027-07-13 10:00:00")
		self.assertEqual(refusal(delivery.resolve_exception, self.case, arrival=normal["arrival"], disposition="Separate delivery", reason="x", expected_version=self.t.version(), idempotency_key=self.t.key("res2"),
			actor=self.p["charles"]).code, "CM_CHANGED")

	# -- replacement -----------------------------------------------------------------------------------------------------------------
	def test_a_replacement_names_the_rejected_unit_it_replaces_and_consumes_the_original_entitlement(self):
		self.active()
		units = tw.fresh_serials(2)
		out = self.t.arrive(units)
		self.t.inspect(out["arrival"], units, bad=(units[1],))
		self.t.accept(out["arrival"])
		self.assertEqual(position.position(self.case)["lines"]["L1"]["remaining"], 9)
		delivery.record_custody_return(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("collect"), actor=self.p["grace"], units=[units[1]], evidence="Collection note C-2")
		fresh = tw.fresh_serials(1)
		self.assertEqual(refusal(self.arrive, [{"line_id": "L1", "quantity": 1, "units": fresh, "replaces": [units[0]]}]).code, "CM_INPUT", "an accepted unit is not replaced here")
		self.arrive([{"line_id": "L1", "quantity": 1, "units": fresh, "replaces": [units[1]]}], at="2027-07-15 10:00:00")
		unit = position.position(self.case)["units"][fresh[0]]
		self.assertEqual((unit["status"], unit["replaces"]), ("Awaiting decision", units[1]), "linked to the unit it replaces")
		self.assertEqual(self.exceptions(2), [], "a replacement is not surplus: the original entitlement is still open")
		again = tw.fresh_serials(1)
		self.assertEqual(refusal(self.arrive, [{"line_id": "L1", "quantity": 1, "units": again, "replaces": [units[1]]}]).code, "CM_INPUT", "one replacement for one rejected unit")

	# -- the screens -----------------------------------------------------------------------------------------------------------------
	def test_the_screens_show_the_exceptions_and_offer_each_person_their_own_step(self):
		from kentender_contracts.boards import router

		self.active()
		out = self.arrive([{"description": "Docking station", "quantity": 1, "units": ["DOCK-7"]}])
		hop = router.board_for(self.case, self.p["charles"], tab="Deliveries")
		self.assertEqual((hop["id"], hop["p"], hop["dialogs"]["resolve"]["command"], hop["dialogs"]["resolve"]["args"]), ("D04-S", "Record what became of it", "ResolveDeliveryException", {"arrival": out["arrival"]}))
		table = next(b for r in hop["regions"] if r["t"] == "Delivery exceptions" for b in r["b"])
		self.assertEqual(table["rows"], [["DEL-001", "Unexpected", "1 Docking station", "!Open"]])
		receiver = router.board_for(self.case, self.p["grace"], tab="Deliveries")
		self.assertIn("Record unexpected goods", receiver["actions"])
		self.assertEqual(receiver["dialogs"]["unexpected"]["command"], "RecordContractArrival")
		delivery.resolve_exception(self.case, arrival=out["arrival"], disposition="To be collected by the supplier", reason="Told the supplier.", expected_version=self.t.version(), idempotency_key=self.t.key("res"), actor=self.p["charles"])
		after = next(b for r in router.board_for(self.case, self.p["charles"], tab="Deliveries")["regions"] if r["t"] == "Delivery exceptions" for b in r["b"])
		self.assertEqual(after["rows"][0][3], "!To be collected by the supplier")
		# a replacement field is offered only where a rejected unit can be replaced
		plain = router.board_for(self.case, self.p["grace"], tab="Deliveries", subject=("record-delivery",))
		self.assertNotIn("replaces", [f["name"] for r in plain["regions"] for b in r["b"] for f in (b.get("items") or []) if isinstance(f, dict)])
		units = tw.fresh_serials(2)
		made = self.t.arrive(units)
		self.t.inspect(made["arrival"], units, bad=(units[1],))
		self.t.accept(made["arrival"])
		after = router.board_for(self.case, self.p["grace"], tab="Deliveries", subject=("record-delivery",))
		self.assertIn("replaces", [f["name"] for r in after["regions"] for b in r["b"] for f in (b.get("items") or []) if isinstance(f, dict)])
