# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 sections 5.3, 5.10, 19.3 CM-R-08 (plan Phase 5; tracker CM8-4xx security): a performance security the issued terms require holds the signing request until it is verified.

Synthetic sources, native ERPNext (proof level L1 for the sources). The hold names the one consequence it blocks and the person who clears it; a file is not a verification; a rejection keeps the
instrument and asks the supplier for a replacement; the supplier sees only its own side."""

from __future__ import annotations

import json
import os
from pathlib import Path

import frappe

from kentender_contracts.boards import router
from kentender_contracts.services import errors, formation, holds, security, work
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

CONTROLS = "Contract Test Environment Controls"
FIXTURES = Path(frappe.get_app_path("kentender_contracts")) / "public/js/contracts/fixtures"
CAPTURE = bool(os.environ.get("CM_CAPTURE_BOARDS"))
ENTITY = "Ministry of Health"
REQUIRED = 100_000.0  # 10% of the synthetic KES 1,000,000


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class TestSecurity(ContractCase):
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
		self.n = 0

	def capture(self, board: dict) -> dict:
		"""With `CM_CAPTURE_BOARDS=1` the board is written as a fixture for the structural fidelity gate (see test_cm_boards)."""
		if CAPTURE:
			FIXTURES.mkdir(parents=True, exist_ok=True)
			(FIXTURES / f"{board['id']}.json").write_text(json.dumps(board, indent=1, sort_keys=True, default=str) + "\n")
		return board

	def k(self):
		self.n += 1
		return f"sec-{self.id().rsplit('.', 1)[-1]}-{self.n}"

	def version(self, case):
		return frappe.db.get_value("Contract Case", case, "record_version")

	def prepared(self, security_required=True):
		out = tw.receive(self.p, security_required=security_required)
		saved = formation.save_particulars(out["contract"], expected_version=out["record_version"], idempotency_key=self.k(), actor=self.p["brian"], values=tw.package_particulars(self.p))
		return out["contract"]

	def record(self, case, *, who="charles", **o):
		values = {"issuer": "Test Bank", "beneficiary": ENTITY, "reference": "TEST-G-001", "amount": REQUIRED, "issued_on": "2027-07-01", "expires_on": "2028-08-31", **o}
		return security.record_security(case, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p[who], **values)

	def verify(self, case, row, *, who="charles", **o):
		values = {"confirmation_reference": "TEST-CONF-01", "received_on": "2027-07-02", "basis": "Issuer confirmation", **o}
		return security.verify_security(case, security=row, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p[who], **values)

	def mine(self, case):
		ours = set(self.p.values())
		return {(t["command"], t["holder"], t["state"]) for t in work.live(case) if t["holder"] in ours}

	# -- the requirement ----------------------------------------------------------------------------------------------------------
	def test_terms_that_require_no_security_hold_nothing_and_ask_for_nothing(self):
		case = self.prepared(security_required=False)
		self.assertEqual(holds.open_holds(case), [])
		self.assertFalse([c for c, _h, _s in self.mine(case) if "Security" in c])
		self.assertIn("do not require", str(refusal(security.record_security, case, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p["charles"], issuer="B", beneficiary=ENTITY,
			reference="X", amount=1, issued_on="2027-07-01", expires_on="2028-01-01").detail))

	def test_terms_that_require_one_ask_the_head_of_procurement_to_record_it_and_hold_the_signing_request(self):
		case = self.prepared()
		self.assertIn(("RecordContractSecurity", self.p["charles"], "actionable"), self.mine(case))
		found = holds.blocking(case, "new_signing_attempt")
		self.assertEqual([h.key for h in found], ["SECURITY_REQUIRED_NOT_VERIFIED"])
		self.assertEqual(found[0].owner, "Head of procurement function")
		self.assertEqual(holds.blocking(case, "pay"), [], "the hold blocks the one consequence that depends on the security")
		exc = refusal(formation.request_signatures, case, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p["charles"])
		self.assertEqual(exc.code, "CM_HOLD")
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Preparing")
		sign = next(t for t in work.live(case) if t["command"] == "RequestContractSignatures" and t["holder"] == self.p["charles"])
		self.assertEqual(sign["state"], "blocked", "the signing request is drawn blocked, with the hold as its reason")

	# -- recording ----------------------------------------------------------------------------------------------------------------
	def test_recording_names_each_field_to_correct_and_only_the_preparers_may_record(self):
		case = self.prepared()
		exc = refusal(security.record_security, case, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p["charles"], issuer="", beneficiary=ENTITY, reference="G", amount=0,
			issued_on="2027-07-01", expires_on="2027-06-01")
		self.assertEqual({k for k, v in exc.fields.items() if v}, {"issuer", "amount", "expires_on"})
		for who in ("julia", "mary", "grace"):
			self.assertEqual(refusal(security.record_security, case, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p[who], issuer="B", beneficiary=ENTITY, reference="G",
				amount=REQUIRED, issued_on="2027-07-01", expires_on="2028-01-01").code, "CM_AUTHORITY", who)
		self.assertEqual(frappe.db.count("Contract Security", {"contract_case": case}), 0)

	def test_a_recorded_instrument_asks_hop_to_check_it_and_tells_the_supplier_it_is_awaited(self):
		case = self.prepared()
		done = self.record(case)
		self.assertEqual(frappe.db.get_value("Contract Security", done["security"], "state"), "Recorded")
		live = self.mine(case)
		self.assertIn(("VerifyContractSecurity", self.p["charles"], "actionable"), live)
		self.assertNotIn(("RecordContractSecurity", self.p["charles"], "actionable"), live)
		self.assertIn(("VerifyContractSecurity:waiting:supplier", self.p["mary"], "waiting"), live)
		self.assertTrue(holds.blocking(case, "new_signing_attempt"), "recorded is not verified")

	def test_a_replay_with_the_same_key_records_once(self):
		case = self.prepared()
		key = self.k()
		args = dict(issuer="Test Bank", beneficiary=ENTITY, reference="TEST-G-001", amount=REQUIRED, issued_on="2027-07-01", expires_on="2028-08-31")
		first = security.record_security(case, expected_version=self.version(case), idempotency_key=key, actor=self.p["charles"], **args)
		again = security.record_security(case, expected_version=first["record_version"] - 1, idempotency_key=key, actor=self.p["charles"], **args)
		self.assertEqual(first["security"], again["security"])
		self.assertEqual(frappe.db.count("Contract Security", {"contract_case": case}), 1)

	# -- verifying ----------------------------------------------------------------------------------------------------------------
	def test_a_file_is_not_a_verification(self):
		case = self.prepared()
		row = self.record(case)["security"]
		exc = refusal(self.verify, case, row, confirmation_reference="", received_on="")
		self.assertEqual({k for k, v in exc.fields.items() if v}, {"confirmation_reference", "received_on"})
		self.assertEqual(frappe.db.get_value("Contract Security", row, "state"), "Recorded")

	def test_the_beneficiary_the_amount_and_the_expiry_are_checked_against_the_issued_terms(self):
		case = self.prepared()
		wrong_party = self.record(case, beneficiary="Some Other Ministry", reference="G-A")["security"]
		self.assertIn("not Ministry of Health", refusal(self.verify, case, wrong_party).fields["confirmation_reference"])
		short = self.record(case, amount=REQUIRED - 1, reference="G-B")["security"]
		self.assertIn("less than", refusal(self.verify, case, short).fields["confirmation_reference"])
		self.assertEqual(frappe.db.get_value("Contract Security", wrong_party, "state"), "Superseded", "a newer record supersedes an unverified one")
		lapsed = self.record(case, expires_on="2027-07-02", reference="G-C")["security"]
		self.assertIn("expired", refusal(self.verify, case, lapsed).fields["confirmation_reference"])
		self.assertTrue(holds.blocking(case, "new_signing_attempt"))

	def test_verifying_clears_the_hold_and_the_agreement_can_be_sent(self):
		case = self.prepared()
		row = self.record(case)["security"]
		done = self.verify(case, row)
		doc = frappe.get_doc("Contract Security", row)
		self.assertEqual((doc.state, doc.confirmation_reference, doc.verified_by), ("Verified", "TEST-CONF-01", self.p["charles"]))
		self.assertEqual(holds.blocking(case, "new_signing_attempt"), [])
		live = self.mine(case)
		self.assertFalse([1 for c, _h, _s in live if c.startswith("VerifyContractSecurity")], "the check and the supplier's waiting item are closed")
		sent = formation.request_signatures(case, expected_version=done["record_version"], idempotency_key=self.k(), actor=self.p["charles"])
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Awaiting signatures")
		self.assertTrue(sent["package"])

	def test_only_the_preparers_may_verify_and_a_verified_record_cannot_be_verified_again(self):
		case = self.prepared()
		row = self.record(case)["security"]
		for who in ("julia", "mary", "josphat"):
			self.assertEqual(refusal(self.verify, case, row, who=who).code, "CM_AUTHORITY", who)
		self.verify(case, row)
		self.assertEqual(refusal(self.verify, case, row).code, "CM_CHANGED")

	# -- rejecting ----------------------------------------------------------------------------------------------------------------
	def test_a_rejection_keeps_the_instrument_and_its_reason_and_asks_the_supplier_for_a_replacement(self):
		case = self.prepared()
		row = self.record(case)["security"]
		self.assertEqual({k for k, v in refusal(security.reject_security, case, security=row, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p["charles"], reason=" ").fields.items() if v}, {"reason"})
		security.reject_security(case, security=row, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p["charles"], reason="The issuer could not confirm this instrument.")
		doc = frappe.get_doc("Contract Security", row)
		self.assertEqual((doc.state, doc.rejection_reason), ("Rejected", "The issuer could not confirm this instrument."))
		live = self.mine(case)
		self.assertIn(("RecordContractSecurity", self.p["charles"], "actionable"), live)
		self.assertIn(("RecordContractSecurity:waiting:supplier", self.p["mary"], "waiting"), live)
		self.assertTrue(holds.blocking(case, "new_signing_attempt"))
		second = self.record(case, reference="TEST-G-002")
		self.assertEqual(frappe.db.get_value("Contract Security", row, "state"), "Rejected", "the rejected instrument stays as history")
		self.verify(case, second["security"])
		self.assertEqual(holds.blocking(case, "new_signing_attempt"), [])

	# -- the screens --------------------------------------------------------------------------------------------------------------
	def test_the_screens_of_the_security_branch_for_the_people_who_see_it(self):
		case = self.prepared()
		record = self.capture(router.board_for(case, self.p["charles"]))
		self.assertEqual((record["id"], record["p"], record["next"]["k"]), ("D25-R", "Save security", "turn"))
		self.assertEqual([r["t"] for r in record["regions"]], ["Security requirement", "Instrument"])
		self.assertEqual(record["regions"][0]["b"][0]["items"][1], ["Required under the issued terms", "KES 100,000"])
		row = self.record(case)["security"]
		verify = self.capture(router.board_for(case, self.p["charles"]))
		self.assertEqual((verify["id"], verify["p"], sorted(verify["dialogs"])), ("D25", "Verify security", ["reject", "verify"]))
		self.assertEqual(verify["regions"][0]["b"][0]["items"][2], ["Amount supplied", "KES 100,000"])
		supplier = router.board_for(case, self.p["mary"])
		self.assertNotIn(supplier["id"], ("D25", "D25-R"), "the supplier never sees HOP's check")
		security.reject_security(case, security=row, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p["charles"], reason="The issuer could not confirm this instrument.")
		rejected = self.capture(router.board_for(case, self.p["mary"]))
		self.assertEqual((rejected["id"], rejected["next"]["k"], rejected["back"]), ("D25-J", "wait", "Back to my contracts"))
		self.assertEqual(rejected["regions"][0]["b"][0]["items"][1], ["Reason", "The issuer could not confirm this instrument."])
