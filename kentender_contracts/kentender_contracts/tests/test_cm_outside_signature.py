# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 sections 5.3, 7, 19.4, boards D26, D26-E, D26-H (plan Phase 5; tracker CM8-505): signing outside the system, as evidence that HOP confirms.

Where the issued terms permit it, a party may sign a copy outside Contract Management. The tests prove the method is checked, the person is the one the agreement names, the copy is the person's own
checked upload, nothing is signed until HOP confirms, the confirmation is never an electronic proof, and a copy that no longer binds the version in force blocks it."""

from __future__ import annotations

import json
import os
from pathlib import Path

import frappe

from kentender_contracts.boards import router
from kentender_contracts.services import errors, formation, holds, outside_signature as outside, records, work
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

CONTROLS = "Contract Test Environment Controls"
FIXTURES = Path(frappe.get_app_path("kentender_contracts")) / "public/js/contracts/fixtures"
CAPTURE = bool(os.environ.get("CM_CAPTURE_BOARDS"))


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class TestOutsideSignature(ContractCase):
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
		self.p, self.n = self.people, 0

	def capture(self, board: dict) -> dict:
		if CAPTURE:
			FIXTURES.mkdir(parents=True, exist_ok=True)
			(FIXTURES / f"{board['id']}.json").write_text(json.dumps(board, indent=1, sort_keys=True, default=str) + "\n")
		return board

	def k(self):
		self.n += 1
		return f"out-{self.id().rsplit('.', 1)[-1]}-{self.n}"

	def version(self, case):
		return frappe.db.get_value("Contract Case", case, "record_version")

	def sent(self, outside_signing=True):
		out = tw.receive(self.p, outside_signing=outside_signing)
		saved = formation.save_particulars(out["contract"], expected_version=out["record_version"], idempotency_key=self.k(), actor=self.p["brian"], values=tw.package_particulars(self.p))
		formation.request_signatures(out["contract"], expected_version=saved["record_version"], idempotency_key=self.k(), actor=self.p["charles"])
		return out["contract"]

	def record(self, case, party, *, who="charles", signer=None, **o):
		signer = signer or ("mary" if party == "Supplier" else "amina")
		values = {"signed_by": tw.PEOPLE[signer][0], "capacity": "Authorised signatory" if party == "Supplier" else "Accounting Officer", "signed_on": "2027-07-02", "notes": "",
			"copy": tw.evidence_file(self.p[who], f"{party.lower()}-{self.n}"), **o}
		return outside.record_outside_signature(case, party=party, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p[who], **values)

	def confirm(self, case, who="charles"):
		return outside.confirm_outside_signature(case, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p[who])

	def slot(self, case, party):
		return frappe.get_doc("Contract Signature", {"contract_case": case, "party": party})

	def mine(self, case):
		ours = set(self.p.values())
		return {(t["command"], t["holder"], t["state"]) for t in work.live(case) if t["holder"] in ours}

	# -- the method and the person --------------------------------------------------------------------------------------------------
	def test_the_method_must_be_permitted_by_the_issued_terms(self):
		case = self.sent(outside_signing=False)
		exc = refusal(self.record, case, "Supplier")
		self.assertEqual((exc.code, exc.detail["hold_key"]), ("CM_RULE", "EXECUTION_METHOD_UNSUPPORTED"))
		self.assertEqual(self.slot(case, "Supplier").state, "Requested")

	def test_only_a_preparer_may_record_and_the_person_must_be_the_one_the_agreement_names(self):
		case = self.sent()
		for who in ("julia", "mary", "grace"):
			self.assertEqual(refusal(self.record, case, "Supplier", who=who).code, "CM_AUTHORITY", who)
		exc = refusal(self.record, case, "Supplier", signed_by="Amina Hassan")
		self.assertIn("This signature is for Mary Wanjiku", exc.fields["signed_by"])
		self.assertEqual(refusal(self.record, case, "Supplier", capacity=" ").fields["capacity"], "Enter the capacity.")
		self.assertIn("future", refusal(self.record, case, "Supplier", signed_on="2027-07-09").fields["signed_on"])
		self.assertIn("not out for signature", refusal(self.record, case, "Supplier", signed_on="2027-06-01").fields["signed_on"])
		self.assertEqual(self.slot(case, "Supplier").state, "Requested")

	def test_the_copy_is_the_persons_own_checked_upload(self):
		case = self.sent()
		self.assertEqual(refusal(self.record, case, "Supplier", copy="").fields["copy"], "Attach the file.")
		self.assertIn("could not be found", refusal(self.record, case, "Supplier", copy="no-such-file").fields["copy"])
		someone_elses = tw.evidence_file(self.p["julia"], "julias")
		self.assertIn("just uploaded", refusal(self.record, case, "Supplier", copy=someone_elses).fields["copy"])
		word = frappe.get_doc({"doctype": "File", "file_name": "cm-test-notes.docx", "is_private": 1, "content": b"PK\x03\x04 word"}).insert(ignore_permissions=True)
		frappe.db.set_value("File", word.name, "owner", self.p["charles"])
		self.assertIn("not permitted", refusal(self.record, case, "Supplier", copy=word.name).fields["copy"])

	# -- evidence is not a signature ------------------------------------------------------------------------------------------------
	def test_recording_makes_evidence_not_a_signature_and_asks_for_the_other_partys_copy(self):
		case = self.sent()
		self.record(case, "Supplier")
		slot = self.slot(case, "Supplier")
		self.assertEqual((slot.state, slot.method, slot.proof_reference or ""), ("Evidence recorded", "Outside signature", ""))
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Awaiting signatures")
		live = self.mine(case)
		self.assertIn(("RecordOutsideContractSignature", self.p["charles"], "actionable"), live)
		self.assertNotIn(("ConfirmOutsideSignatureEvidence", self.p["charles"], "actionable"), live)
		self.assertEqual(refusal(formation.sign_contract, case, party="Supplier", expected_version=self.version(case), idempotency_key=self.k(), actor=self.p["mary"]).code, "CM_CHANGED")
		self.assertEqual(refusal(self.confirm, case).code, "CM_CHANGED", "the entity's copy is not recorded yet")

	def test_both_copies_recorded_then_confirmed_make_both_signatures_and_the_agreement_effective(self):
		case = self.sent()
		self.record(case, "Supplier")
		self.record(case, "Entity")
		self.assertIn(("ConfirmOutsideSignatureEvidence", self.p["charles"], "actionable"), self.mine(case))
		done = self.confirm(case)
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Active")
		for party in ("Supplier", "Entity"):
			slot = self.slot(case, party)
			self.assertEqual((slot.state, slot.method), ("Signed", "Outside signature"))
			self.assertTrue(slot.proof_reference.startswith("OUTSIDE-") and slot.proof_reference[8:] == slot.copy_digest[:16])
		self.assertEqual(frappe.db.count("Contract Simulated Signature", {"fixture_namespace": "CM_TEST"}), 0, "no electronic signature was made or pretended")
		self.assertEqual(formation.current_agreement(case).state, "Effective")
		self.assertTrue(formation.native_order(case), "the order and the funding follow, as they do for an electronic signature")
		live = self.mine(case)
		self.assertFalse([1 for c, _h, _s in live if "Outside" in c or c.startswith("SignContractVersion")], "every signing task is closed")
		self.assertEqual(refusal(self.confirm, case).code, "CM_CHANGED")
		self.assertEqual(holds.open_holds(case), [])

	def test_a_copy_that_no_longer_binds_the_version_in_force_blocks_confirmation(self):
		case = self.sent()
		self.record(case, "Supplier")
		self.record(case, "Entity")
		slot = self.slot(case, "Entity")
		held = outside.evidence_of(slot)
		records.update(slot, evidence_json=records.dumps({**held, "agreement_digest": "0" * 64}))
		frappe.db.commit()
		exc = refusal(self.confirm, case)
		self.assertEqual(exc.code, "CM_SOURCE")
		self.assertIn("do not match agreement 1", exc.detail["reason"])
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Awaiting signatures")
		board = self.capture(router.board_for(case, self.p["charles"]))
		self.assertEqual((board["id"], board["next"]["k"], board["p"]), ("D26-H", "blk", ""))

	def test_authority_is_rechecked_when_the_copy_is_recorded_and_when_it_is_confirmed(self):
		case = self.sent()
		rows = frappe.get_all("User Responsibility Assignment", filters={"user": self.p["amina"], "business_role": "Entity contract signing", "status": "Enabled"}, pluck="name")
		self.assertTrue(rows)
		for name in rows:
			frappe.db.set_value("User Responsibility Assignment", name, "status", "Disabled")
		frappe.db.commit()
		try:
			self.assertEqual(refusal(self.record, case, "Entity").code, "CM_AUTHORITY", "recording")
		finally:
			for name in rows:
				frappe.db.set_value("User Responsibility Assignment", name, "status", "Enabled")
			frappe.db.commit()
		self.record(case, "Supplier")
		self.record(case, "Entity")
		for name in rows:
			frappe.db.set_value("User Responsibility Assignment", name, "status", "Disabled")
		frappe.db.commit()
		try:
			self.assertEqual(refusal(self.confirm, case).code, "CM_AUTHORITY", "confirming")
			self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Awaiting signatures")
		finally:
			for name in rows:
				frappe.db.set_value("User Responsibility Assignment", name, "status", "Enabled")
			frappe.db.commit()

	def test_the_window_closing_before_confirmation_stops_it(self):
		case = self.sent()
		self.record(case, "Supplier")
		self.record(case, "Entity")
		frappe.flags.kt_cm_clock = "2027-07-15 09:00:00"
		self.assertEqual(refusal(self.confirm, case).code, "CM_HOLD")
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Awaiting signatures")

	def test_recording_again_before_confirmation_replaces_the_evidence_and_keeps_the_earlier(self):
		case = self.sent()
		self.record(case, "Supplier")
		self.record(case, "Supplier")
		held = outside.evidence_of(self.slot(case, "Supplier"))
		self.assertEqual(set(held["replaces"]), {"file", "digest", "recorded_by", "recorded_at"})
		self.assertEqual(frappe.db.count("Contract Event", {"contract_case": case, "event_type": "Outside signature recorded"}), 2)

	# -- the screens ---------------------------------------------------------------------------------------------------------------
	def test_the_screens(self):
		case = self.sent()
		agreement_tab = router.board_for(case, self.p["charles"], tab="Agreement")
		self.assertIn("Record an outside signature", agreement_tab["actions"])
		route = agreement_tab["actions"]["Record an outside signature"]["route"]
		self.assertEqual(route[1:], ["agreement", "outside", "supplier"], "the route is /<contract>/agreement/outside/supplier")
		form = router.board_for(case, self.p["charles"], tab="Agreement", subject=("outside", "supplier"))
		self.assertEqual((form["id"], form["p"], form["next"]["k"], form["next"]["h"]), ("D26", "Save signature evidence", "turn", "Record the supplier's signed agreement."))
		self.assertEqual([f["name"] for f in form["regions"][0]["b"][0]["items"]], ["party", "signed_by", "capacity", "signed_on", "copy", "notes"])
		self.assertEqual(form["regions"][0]["b"][0]["items"][1]["v"], "Mary Wanjiku")
		self.assertNotIn("Record an outside signature", router.board_for(case, self.p["mary"], tab="Agreement")["actions"], "the supplier is not offered HOP's recording")
		self.record(case, "Supplier")
		self.record(case, "Entity")
		check = router.board_for(case, self.p["charles"])
		self.assertEqual((check["id"], check["p"], check["next"]["k"]), ("D26-E", "Confirm signature evidence", "turn"))
		table = check["regions"][0]["b"][0]
		self.assertEqual([r[0] for r in table["rows"]], ["Supplier", "Procuring entity"])
		self.assertTrue(all(r[4].startswith("@Signed agreement 1 — ") for r in table["rows"]))
		self.assertEqual(next(a for k, a in check["actions"].items() if k.endswith("— supplier"))["do"], "download")
		self.capture(form)
		self.capture(check)
