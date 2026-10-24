# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 5.13, boards D12, D21, D21-H (plan Phase 5; tracker CM8-508; CM-AC-25 to 28): a contract signed before KenTender.

Registered once under a stable key, saved while incomplete and revised as findings come (a revision voids every confirmation); Finance confirms the opening position against the native records it
is linked to; the head of procurement starts management. Nothing is signed again, nothing historical is reposted, and the opening position is a starting offset that new activity can never exceed."""

from __future__ import annotations

from kentender_contracts.simulation.timeline import D  # noqa: F401
import json
import os
from pathlib import Path

import frappe

from kentender_contracts.boards import router
from kentender_contracts.services import errors, existing, formation, opening, position, records, work
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase
from kentender_contracts.native import adapter

CONTROLS = "Contract Test Environment Controls"
FIXTURES = Path(frappe.get_app_path("kentender_contracts")) / "public/js/contracts/fixtures"
CAPTURE = bool(os.environ.get("CM_CAPTURE_BOARDS"))


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class TestExistingContract(ContractCase):
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
		self.native = None

	def capture(self, board: dict, name: str = "") -> dict:
		if CAPTURE:
			FIXTURES.mkdir(parents=True, exist_ok=True)
			(FIXTURES / f"{name or board['id']}.json").write_text(json.dumps(board, indent=1, sort_keys=True, default=str) + "\n")
		return board

	def k(self):
		self.n += 1
		return f"ext-{self.id().rsplit('.', 1)[-1]}-{self.n}"

	def version(self, case):
		return frappe.db.get_value("Contract Case", case, "record_version")

	def linked(self):
		"""A real receipt of four units and the invoice for them, as the opening position links them."""
		if self.native is None:
			receipt = world.fixed_asset_receipt(f"EXT{self.n}", 4)
			invoice = adapter.invoice_receipt(receipt, world.identity(f"invoice ext {self.n}", "Native invoice"), bill_no=f"EXT-INV-{self.n}", qty=4)
			frappe.db.commit()
			self.native = (receipt, invoice)
		return self.native

	def values(self, **o):
		receipt, invoice = self.linked()
		v = {"source": "External records", "reference": "MOH/ICT/2027/EXT-01", "supplier_country": tw.REGISTRATION[0], "supplier_registration": tw.REGISTRATION[1],
			"agreement_file": tw.evidence_file(self.p["brian"], "ext-agreement"), "amendments": "None", "signed_on": D("2027-07-02"), "effective_on": D("2027-07-02"), "cutover": D("2027-08-03 00:00:00"),
			"original_value": 1_000_000, "current_value": 1_000_000, "items": "Laptop computer | 10 | Each | 100000 | Included | 4 | 2 | 4", "delivery_due": D("2027-07-20"), "payment_days": 30,
			"warranty_months": 12, "acceptance": "RAM | >= | 16 | GB\nStorage | >= | 512 | GB\nStarts successfully | = | Yes | ", "security_required": "No", "advance_allowed": "No", "restrictions": "None",
			"clauses": "Agreement EXT-01 §§2-8", "owner": self.p["julia"], "managing_unit": tw.unit(), "entity_signatory": self.p["amina"], "native_supplier": world.SUPPLIER, "asset_location": world.LOCATION,
			"item_mapping": {"L1": world.ITEM_FA}, "prior_activity": "Some", "opening_invoiced": 400_000, "opening_credits": 0, "opening_cash_paid": 0, "opening_outstanding": 400_000, "opening_advance": 0,
			"units_in_custody": "CM-EXT-009\nCM-EXT-010", "link_purchase_receipt": receipt, "link_purchase_invoice": invoice, **o}
		return v

	def register(self, who="brian", **o):
		return existing.register_existing_contract(idempotency_key=self.k(), actor=self.p[who], values=self.values(**o))

	def mine(self, case):
		ours = set(self.p.values())
		return {(t["command"], t["holder"], t["state"]) for t in work.live(case) if t["holder"] in ours}

	def confirm(self, case, who="beatrice"):
		return existing.confirm_opening_position(case, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p[who])

	def start(self, case, who="charles"):
		return existing.start_management(case, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p[who])

	# -- registering -------------------------------------------------------------------------------------------------------------------
	def test_a_complete_registration_makes_one_draft_case_with_the_terms_in_the_same_shape_as_any_agreement(self):
		out = self.register()
		self.assertEqual((out["intake"], out["missing"]), ("created", []))
		case = frappe.get_doc("Contract Case", out["open"])
		self.assertEqual((case.source_kind, case.lifecycle, case.supplier_name, case.origin_key, case.intake_revision), ("External record", "Preparing", "Afya Digital Supplies Limited", "external records|moh/ict/2027/ext-01", 1))
		agreement = frappe.get_doc("Contract Agreement Version", {"contract_case": case.name})
		terms = records.loads(agreement.terms_json)
		self.assertEqual((agreement.state, terms["total"], terms["lines"][0]["quantity"], terms["warranty"]["months"], terms["payment"]["days"], [c["name"] for c in terms["criteria"]]),
			("Draft", 1_000_000, 10, 12, 30, ["RAM", "Storage", "Starts successfully"]))
		self.assertEqual(terms["parties"]["supplier"]["user"], self.p["mary"])
		self.assertEqual(terms["origin"]["evidence"], "Recorded from external source", "never presented as verified by an e-procurement system")
		self.assertEqual(frappe.db.count("Contract Signature", {"contract_case": case.name}), 0, "nobody is asked to sign")
		live = self.mine(case.name)
		self.assertIn(("ConfirmOpeningPosition", self.p["beatrice"], "actionable"), live)
		self.assertIn(("StartContractManagement:waiting:finance", self.p["charles"], "waiting"), live)

	def test_saving_while_incomplete_is_allowed_and_names_what_is_missing(self):
		out = existing.register_existing_contract(idempotency_key=self.k(), actor=self.p["brian"], values={"source": "External records", "reference": "EXT-PARTIAL", "supplier_country": tw.REGISTRATION[0],
			"supplier_registration": tw.REGISTRATION[1]})
		self.assertIn("agreement_file", out["missing"])
		self.assertIn("items", out["missing"])
		self.assertIn(("ReviseContractIntake", self.p["brian"], "actionable"), self.mine(out["open"]))
		self.assertEqual(refusal(self.start, out["open"]).code, "CM_HOLD", "starting names what is still missing")

	def test_the_key_prevents_a_second_case_for_the_same_contract(self):
		first = self.register()
		exc = refusal(self.register, reference="  moh/ict/2027/EXT-01 ")
		self.assertEqual((exc.code, exc.detail["contract"]), ("CM_DUPLICATE", first["open"]))
		self.assertEqual(frappe.db.count("Contract Case", {"origin_key": "external records|moh/ict/2027/ext-01"}), 1)
		self.assertEqual(self.register(source="eGP", egp_tender_reference="T", egp_contract_reference="C")["intake"], "created", "another origin system is another key")

	def test_only_a_preparer_may_register_and_a_value_given_wrongly_names_its_field(self):
		for who in ("julia", "mary", "grace", "beatrice"):
			self.assertEqual(refusal(self.register, who=who).code, "CM_AUTHORITY", who)
		exc = refusal(self.register, current_value=900_000, delivery_due="soon", payment_days="x", supplier_registration="NOPE")
		self.assertEqual(set(exc.fields), {"current_value", "delivery_due", "payment_days", "supplier_registration"})
		self.assertIn("items come to 1,000,000.00, not 900,000.00", exc.fields["current_value"])
		self.assertEqual(frappe.db.count("Contract Case", {"fixture_namespace": "CM_TEST"}), 0)

	def test_the_opening_position_cannot_contradict_the_contract(self):
		exc = refusal(self.register, items="Laptop computer | 10 | Each | 100000 | Included | 9 | 2 | 4")
		self.assertIn("more than the quantity", exc.fields["items"])
		exc = refusal(self.register, items="Laptop computer | 10 | Each | 100000 | Included | 4 | 2 | 5")
		self.assertIn("more units are invoiced", exc.fields["items"])
		self.assertIn("not 300,000.00", refusal(self.register, opening_outstanding=300_000).fields["opening_outstanding"])
		self.assertIn("quantities at the contract rate", refusal(self.register, opening_invoiced=450_000, opening_outstanding=450_000).fields["opening_invoiced"])

	def test_unknown_figures_stay_unknown_and_none_means_zero_with_confirmation(self):
		out = self.register(items="Laptop computer | 10 | Each | 100000 | Included | 4 | | 4")
		self.assertIn("opening", out["missing"])
		none = self.register(reference="EXT-NONE", prior_activity="None", items="Laptop computer | 10 | Each | 100000 | Included", units_in_custody="")
		self.assertEqual(none["missing"], [])
		case = none["open"]
		self.assertEqual(stored_opening(case)["invoiced"], 0.0)
		live = self.mine(case)
		self.assertIn(("StartContractManagement", self.p["charles"], "actionable"), live)
		self.assertFalse([1 for c, _h, _s in live if c == "ConfirmOpeningPosition"], "Finance confirms only when there was prior activity")

	# -- revising ----------------------------------------------------------------------------------------------------------------------
	def test_a_revision_voids_every_confirmation_and_keeps_the_earlier_digest(self):
		case = self.register()["open"]
		self.confirm(case)
		first = stored_intake(case)
		self.assertEqual(first["confirmations"]["finance"]["revision"], 1)
		revised = existing.revise_intake(case, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p["brian"], values={"payment_days": 45})
		intake = stored_intake(case)
		self.assertEqual((intake["revision"], intake["confirmations"], intake["history"][0]["digest"]), (2, {}, first["digest"]))
		self.assertIn(("ConfirmOpeningPosition", self.p["beatrice"], "actionable"), self.mine(case))
		self.assertEqual(refusal(self.start, case).code, "CM_HOLD", "the confirmation was of revision 1")
		self.assertEqual(refusal(existing.revise_intake, case, expected_version=self.version(case) + 3, idempotency_key=self.k(), actor=self.p["brian"], values={}).code, "CM_CHANGED")

	# -- Finance confirms ---------------------------------------------------------------------------------------------------------------
	def test_finance_confirms_only_when_the_source_and_the_linked_records_agree(self):
		case = self.register(opening_cash_paid=300_000, opening_outstanding=100_000)["open"]
		exc = refusal(self.confirm, case)
		self.assertEqual(exc.code, "CM_RECONCILE")
		self.assertEqual(exc.detail["differing"], ["Cash paid", "Outstanding"])
		self.assertEqual(refusal(self.confirm, case, who="charles").code, "CM_AUTHORITY", "the head of procurement does not confirm money")
		fine = self.register(reference="EXT-OK")["open"]
		self.confirm(fine)
		self.assertEqual(stored_intake(fine)["confirmations"]["finance"]["by"], self.p["beatrice"])
		self.assertIn(("StartContractManagement", self.p["charles"], "actionable"), self.mine(fine))

	# -- starting ----------------------------------------------------------------------------------------------------------------------
	def test_starting_activates_the_agreement_at_its_actual_date_and_creates_only_outstanding_work(self):
		case = self.register()["open"]
		self.confirm(case)
		self.assertEqual(refusal(self.start, case, who="beatrice").code, "CM_AUTHORITY")
		done = self.start(case)
		doc = frappe.get_doc("Contract Case", case)
		agreement = formation.current_agreement(case)
		self.assertEqual((doc.lifecycle, str(doc.operative_date), agreement.state, str(agreement.effective_at)[:10]), ("Active", D("2027-07-02"), "Effective", D("2027-07-02")))
		self.assertEqual(frappe.db.count("Contract Signature", {"contract_case": case}), 0, "nobody was asked to sign")
		self.assertEqual(frappe.db.count("Contract Simulated Signature", {"fixture_namespace": "CM_TEST"}), 0)
		live = self.mine(case)
		self.assertIn(("RecommendContractInspectors", self.p["charles"], "actionable"), live)
		self.assertIn(("RecordInspectionObservations", self.p["charles"], "actionable"), live, "the two units in custody are to be inspected")
		self.assertFalse([1 for c, _h, _s in live if c in ("SignContractVersion", "RequestContractSignatures", "ConfirmOpeningPosition")])
		arrival = frappe.get_doc("Contract Arrival", {"contract_case": case})
		self.assertEqual((arrival.delivery_reference, records.loads(arrival.items_json)[0]["units"]), ("Opening position", ["CM-EXT-009", "CM-EXT-010"]))
		order = formation.native_order(case)
		self.assertTrue(order and frappe.db.get_value("Purchase Order", order, "supplier") == world.SUPPLIER, "no order was linked, so the same route as any agreement made one")
		self.assertEqual(refusal(self.start, case).code, "CM_CHANGED", "activated once")

	def test_the_opening_position_is_a_starting_offset_new_activity_cannot_exceed(self):
		case = self.register()["open"]
		self.confirm(case)
		self.start(case)
		line = position.position(case)["lines"]["L1"]
		self.assertEqual((line["ordered"], line["accepted"], line["arrived"], line["in_custody"], line["pending_decision"], line["remaining"]), (10, 4, 6, 2, 2, 6))
		self.assertEqual((opening.invoiced(case), opening.line(case, "L1")["invoiced_quantity"]), (400_000.0, 4))
		from kentender_contracts.services import payment

		matched = payment.match_claim(case, [{"line_id": "L1", "quantity": 1}])
		self.assertEqual(matched["rows"][0]["eligible_quantity"], 0, "the four accepted units were all invoiced already")
		self.assertEqual((matched["previous_claims"], matched["remaining_contractual"]), (400_000.0, 600_000.0))

	def test_a_restriction_or_an_unverified_required_security_stops_the_start(self):
		restricted = self.register(reference="EXT-R", restrictions="Court order of 1 July 2027")["open"]
		self.confirm(restricted)
		exc = refusal(self.start, restricted)
		self.assertEqual(exc.code, "CM_HOLD")
		secured = self.register(reference="EXT-S", security_required="Yes")["open"]
		self.confirm(secured)
		self.assertIn("SECURITY_REQUIRED_NOT_VERIFIED", str(refusal(self.start, secured).detail) + str(refusal(self.start, secured).reasons if hasattr(errors.ContractError, "reasons") else ""))
		self.assertEqual(frappe.db.get_value("Contract Case", secured, "lifecycle"), "Preparing")

	# -- the screens -------------------------------------------------------------------------------------------------------------------
	def test_the_screens(self):
		board = self.capture(router.board_for("register", self.p["brian"]))
		self.assertEqual((board["id"], board["title"], board["p"], board["case"]), ("D12", "Register existing contract", "Save and review", ""))
		self.assertEqual(refusal(router.board_for, "register", self.p["julia"]).detail["denied"], True)
		case = self.register()["open"]
		self.assertEqual(router.board_for(case, self.p["beatrice"])["id"], "D21")
		review = self.capture(router.board_for(case, self.p["beatrice"]))
		self.assertEqual((review["p"], [r[0] for r in review["regions"][0]["b"][0]["rows"]]), ("Confirm opening position", ["Accepted units", "In custody", "Invoiced", "Cash paid", "Outstanding", "Advance"]))
		self.confirm(case)
		start = self.capture(router.board_for(case, self.p["charles"]))
		self.assertEqual((start["id"], start["p"]), ("D21-H", "Start management"))
		draft = router.board_for(case, self.p["brian"], tab="Agreement")
		self.assertEqual(draft["id"], "D12")
		table = next(b for r in draft["regions"] for b in r["b"] if b["k"] == "table")
		self.assertEqual((table["rows"][0][0], table["rows"][0][1], len(table["rows"])), ("~Laptop computer", "#10", 4), "the saved line, then blank rows to add more")
		egp = self.register(source="eGP", reference="EXT-EGP", egp_tender_reference="TDR-1", egp_contract_reference="CON-1")["open"]
		self.capture(router.board_for(egp, self.p["brian"], tab="Agreement"), "D12-G")
		self.assertIn("Linked receipt", [f["l"] for r in draft["regions"] for b in r["b"] for f in (b.get("items") or []) if isinstance(f, dict) and "l" in f])
		listing = __import__("kentender_contracts.boards.listing", fromlist=["workspace"]).workspace(self.p["charles"], view="All contracts")["board"]
		self.assertEqual(listing["headP"], "Register existing contract")
		self.assertEqual(__import__("kentender_contracts.boards.listing", fromlist=["workspace"]).workspace(self.p["mary"])["board"]["headP"], "")


def stored_intake(case: str) -> dict:
	return existing.stored(case)["intake"]


def stored_opening(case: str) -> dict:
	return stored_intake(case)["opening"]


class TestIntakeValues(ContractCase):
	"""The command layer turns the item table's cells into the items the service reads."""

	def test_the_cells_become_item_lines_and_an_empty_row_is_not_an_item(self):
		from kentender_contracts.api import commands

		out = commands._intake_values({"row.1.description": "Laptop", "row.1.quantity": "10", "row.1.uom": "Each", "row.1.rate": "100000", "row.1.tax": "Included|Included", "row.1.accepted": "4",
			"row.2.description": "", "row.2.quantity": "", "row.2.tax": "Included|Included", "row.3.description": "Dock", "row.3.quantity": "2", "row.3.uom": "Each", "row.3.rate": "5000", "row.3.tax": "Excluded|Excluded", "source": "eGP|eGP"})
		self.assertEqual(out["items"], "Laptop | 10 | Each | 100000 | Included | 4 |  | \nDock | 2 | Each | 5000 | Excluded |  |  | ")
		self.assertEqual(out["source"], "eGP")
		self.assertFalse([k for k in out if k.startswith("row.")])
