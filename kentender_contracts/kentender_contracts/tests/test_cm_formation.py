# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 sections 5.2, 5.3, 5.14, 7 (plan Phase 4; tracker CM8-401 to CM8-405): from a received Award package to an agreement in force, on real ERPNext, the real
core signing facade with the Contract Management simulation provider, and the synthetic sources and funding owner (proof level L1 for the sources; L2 for the native order and the
signing facade). Mutation checks are recorded in the tracker."""

from __future__ import annotations

import frappe

from kentender_contracts.services import errors, formation, holds, records, simulation, work
from kentender_contracts.simulation import sources
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


class TestFormation(ContractCase):
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
		frappe.flags.pop("kt_cm_funding_fault", None)
		self.p = self.people
		self.key = 0

	def mine(self, case):
		"""The live obligations held by the people of this test (the test site has other modules' people too)."""
		ours = set(self.p.values())
		return {(t["holder"], t["state"]) for t in work.live(case) if t["holder"] in ours}

	def k(self):
		self.key += 1
		return f"k-{self.id().rsplit('.', 1)[-1]}-{self.key}"

	def prepared(self):
		out = tw.receive(self.p)
		case = out["contract"]
		saved = formation.save_particulars(case, expected_version=out["record_version"], idempotency_key=self.k(), actor=self.p["brian"], values=tw.package_particulars(self.p))
		return case, saved

	def sent(self):
		case, saved = self.prepared()
		sent = formation.request_signatures(case, expected_version=saved["record_version"], idempotency_key=self.k(), actor=self.p["charles"])
		return case, sent

	def test_receiving_the_package_makes_one_case_and_one_prepare_task_and_a_retry_returns_them(self):
		first = tw.receive(self.p)
		again = formation.receive_award_package(sources.award_package(), handoff=sources.source_handoff(), managing_unit=tw.unit(), idempotency_key="another-key", actor="Administrator")
		self.assertEqual((first["lifecycle"], first["intake"]), ("Preparing", "created"))
		self.assertEqual((again["contract"], again["intake"]), (first["contract"], "existing"))
		self.assertEqual(frappe.db.count("Contract Case", {"fixture_namespace": "CM_TEST"}), 1)
		live = work.live(first["contract"])
		self.assertEqual([(t["command"], t["holder"], t["state"]) for t in live if t["holder"] == self.p["charles"]], [("RequestContractSignatures", self.p["charles"], "actionable")])
		self.assertEqual({t["command"] for t in live}, {"RequestContractSignatures"})

	def test_an_incomplete_package_is_refused_and_acknowledged_by_nobody(self):
		package = sources.award_package()
		package["decision"]["outcome"] = "No award"
		exc = refusal(formation.receive_award_package, package, handoff=sources.source_handoff(), managing_unit=tw.unit(), idempotency_key=self.k(), actor="Administrator")
		self.assertEqual(exc.code, "CM_SOURCE")
		self.assertEqual(frappe.db.count("Contract Case", {"fixture_namespace": "CM_TEST"}), 0)

	def test_particulars_generate_the_agreement_from_the_verified_sources_and_say_what_is_missing(self):
		out = tw.receive(self.p)
		blank = formation.save_particulars(out["contract"], expected_version=out["record_version"], idempotency_key=self.k(), actor=self.p["brian"], values={})
		self.assertEqual(blank["missing"], ["agreement_date", "entity_signatory", "item_mapping", "native_supplier"])
		agreement = frappe.get_doc("Contract Agreement Version", blank["agreement"])
		self.assertEqual((agreement.state, agreement.version_no, float(agreement.amount)), ("Draft", 1, 1_000_000.0))
		self.assertIn("{{agreement_date}}", agreement.rendered_html)
		self.assertIn("covenant and precedence text", agreement.rendered_html, "the issued Form No. 4 text is kept")
		full = formation.save_particulars(out["contract"], expected_version=blank["record_version"], idempotency_key=self.k(), actor=self.p["brian"], values=tw.package_particulars(self.p))
		self.assertEqual(full["missing"], [])
		html = frappe.db.get_value("Contract Agreement Version", full["agreement"], "rendered_html")
		for fragment in ("2 July 2027", "Ministry of Health", "Afya Digital Supplies Limited", "10 Laptop computer", "KES 1,000,000, tax included", "Amina Hassan, Accounting Officer", "Mary Wanjiku, Authorised signatory"):
			self.assertIn(fragment, html)
		self.assertEqual(frappe.db.count("Contract Agreement Version", {"contract_case": out["contract"]}), 1, "saving again refreshes the draft, it does not make another version")

	def test_only_a_person_whose_responsibility_covers_the_work_may_prepare(self):
		out = tw.receive(self.p)
		for who in ("julia", "mary", "grace"):
			exc = refusal(formation.save_particulars, out["contract"], expected_version=out["record_version"], idempotency_key=self.k(), actor=self.p[who], values={})
			self.assertEqual(exc.code, "CM_AUTHORITY", who)
		self.assertEqual(formation.save_particulars(out["contract"], expected_version=out["record_version"], idempotency_key=self.k(), actor=self.p["charles"], values={})["ok"], True)

	def test_a_stale_version_is_a_conflict_and_a_bad_form_value_names_its_field(self):
		out = tw.receive(self.p)
		self.assertEqual(refusal(formation.save_particulars, out["contract"], expected_version=out["record_version"] + 5, idempotency_key=self.k(), actor=self.p["brian"], values={}).code, "CM_CHANGED")
		exc = refusal(formation.save_particulars, out["contract"], expected_version=out["record_version"], idempotency_key=self.k(), actor=self.p["brian"], values={"agreement_date": "not a date", "entity_signatory": self.p["julia"]})
		self.assertEqual(set(exc.fields), {"agreement_date", "entity_signatory"})

	def test_sending_for_signature_needs_every_particular_and_freezes_one_version_with_its_package(self):
		out = tw.receive(self.p)
		exc = refusal(formation.request_signatures, out["contract"], expected_version=out["record_version"], idempotency_key=self.k(), actor=self.p["charles"])
		self.assertIn("No agreement", str(exc.detail) + str(exc))  # nothing prepared yet
		case, sent = self.sent()
		agreement = frappe.get_doc("Contract Agreement Version", sent["agreement"])
		self.assertEqual((agreement.state, frappe.db.get_value("Contract Case", case, "lifecycle")), ("Awaiting signatures", "Awaiting signatures"))
		package = frappe.get_doc("Contract Source Package", sent["package"])
		manifest = records.loads(package.manifest_json)
		self.assertEqual([e["source"] for e in manifest["entries"]], [f"S{n}" for n in range(1, 13)])
		self.assertEqual(package.package_digest, manifest["package_digest"])
		slots = frappe.get_all("Contract Signature", filters={"contract_case": case}, fields=["party", "state", "sequence", "signer"], order_by="sequence")
		self.assertEqual([(s.party, s.state, s.signer) for s in slots], [("Supplier", "Requested", self.p["mary"]), ("Entity", "Waiting", self.p["amina"])])
		self.assertEqual(self.mine(case), {(self.p["mary"], "actionable"), (self.p["charles"], "waiting")})

	def test_a_changed_source_after_the_award_stops_the_agreement(self):
		case, saved = self.prepared()
		frappe.flags.kt_contract_source_providers = [sources.Provider(tamper="S5")]
		exc = refusal(formation.request_signatures, case, expected_version=saved["record_version"], idempotency_key=self.k(), actor=self.p["charles"])
		self.assertEqual(exc.code, "CM_SOURCE")
		self.assertEqual([f["source"] for f in exc.detail["failed"]], ["S5"])
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Preparing")

	def test_the_supplier_signs_first_and_the_entity_second_and_the_second_proof_makes_the_agreement_active(self):
		case, sent = self.sent()
		early = refusal(formation.sign_contract, case, party="Entity", expected_version=sent["record_version"], idempotency_key=self.k(), actor=self.p["amina"])
		self.assertEqual(early.code, "CM_CHANGED")
		stranger = refusal(formation.sign_contract, case, party="Supplier", expected_version=sent["record_version"], idempotency_key=self.k(), actor=self.p["david"])
		self.assertEqual(stranger.code, "CM_SEGREGATION", "a representative is not a signatory")
		first = formation.sign_contract(case, party="Supplier", expected_version=sent["record_version"], idempotency_key=self.k(), actor=self.p["mary"])
		self.assertEqual((first["state"], first["lifecycle"]), ("Signed", "Awaiting signatures"))
		self.assertEqual(self.mine(case), {(self.p["amina"], "actionable"), (self.p["charles"], "waiting"), (self.p["mary"], "waiting")})
		second = formation.sign_contract(case, party="Entity", expected_version=first["record_version"], idempotency_key=self.k(), actor=self.p["amina"])
		self.assertEqual((second["lifecycle"], second["effective"]), ("Active", True))
		proofs = frappe.get_all("Contract Signature", filters={"contract_case": case}, pluck="proof_reference")
		self.assertTrue(all(p.startswith("CMSIM-") for p in proofs) and len(set(proofs)) == 2)
		agreement = formation.current_agreement(case)
		self.assertEqual(agreement.state, "Effective")
		order = formation.native_order(case)
		self.assertTrue(order)
		po = frappe.get_doc("Purchase Order", order)
		self.assertEqual((po.docstatus, po.supplier, [(i.item_code, i.qty, i.rate) for i in po.items]), (1, world.SUPPLIER, [(world.ITEM_FA, 10, 100000)]))
		self.assertEqual(frappe.db.get_value("Contract Operation Intent", {"contract_case": case, "operation_kind": "Funding conversion"}, "state"), "Succeeded")
		self.assertEqual(holds.open_holds(case), [])

	def test_the_same_key_signs_once_and_a_second_click_with_a_new_key_does_not_sign_again(self):
		case, sent = self.sent()
		key = self.k()
		first = formation.sign_contract(case, party="Supplier", expected_version=sent["record_version"], idempotency_key=key, actor=self.p["mary"])
		replay = formation.sign_contract(case, party="Supplier", expected_version=sent["record_version"], idempotency_key=key, actor=self.p["mary"])
		self.assertEqual(first["signature"], replay["signature"])
		again = formation.sign_contract(case, party="Supplier", expected_version=first["record_version"], idempotency_key=self.k(), actor=self.p["mary"])
		self.assertTrue(again.get("already"))
		self.assertEqual(frappe.db.count("Contract Simulated Signature", {"fixture_namespace": "CM_TEST"}), 1)

	def test_an_unavailable_signing_service_saves_the_work_and_a_retry_signs_the_same_attempt(self):
		case, sent = self.sent()
		frappe.db.set_single_value(CONTROLS, "signing_outcome", "Unavailable")
		exc = refusal(formation.sign_contract, case, party="Supplier", expected_version=sent["record_version"], idempotency_key=self.k(), actor=self.p["mary"])
		self.assertEqual(exc.code, "CM_SIGNING")
		self.assertEqual(frappe.db.get_value("Contract Signature", {"contract_case": case, "party": "Supplier"}, "state"), "Failed")
		self.assertEqual(frappe.db.count("Contract Simulated Signature", {"fixture_namespace": "CM_TEST"}), 0)
		self.assertIn((self.p["daniel"], "actionable"), self.mine(case))
		frappe.db.set_single_value(CONTROLS, "signing_outcome", "")
		done = formation.sign_contract(case, party="Supplier", expected_version=frappe.db.get_value("Contract Case", case, "record_version"), idempotency_key=self.k(), actor=self.p["mary"])
		self.assertEqual(done["state"], "Signed")
		self.assertEqual(frappe.db.count("Contract Simulated Signature", {"fixture_namespace": "CM_TEST"}), 1)
		self.assertEqual(frappe.db.count("Contract Operation Intent", {"contract_case": case, "operation_kind": "Signing attempt"}), 1, "the same attempt, not a new one")

	def test_a_lost_reply_stays_pending_and_the_retry_finds_the_signature_instead_of_signing_twice(self):
		case, sent = self.sent()
		frappe.db.set_single_value(CONTROLS, "signing_outcome", "Indeterminate")
		exc = refusal(formation.sign_contract, case, party="Supplier", expected_version=sent["record_version"], idempotency_key=self.k(), actor=self.p["mary"])
		self.assertEqual((exc.code, exc.detail["pending"]), ("CM_SIGNING", True))
		self.assertEqual(frappe.db.get_value("Contract Signature", {"contract_case": case, "party": "Supplier"}, "state"), "Pending")
		self.assertTrue(holds.blocking(case, "new_signing_attempt"), "an uncertain signature holds a new attempt")
		frappe.db.set_single_value(CONTROLS, "signing_outcome", "")
		done = formation.sign_contract(case, party="Supplier", expected_version=frappe.db.get_value("Contract Case", case, "record_version"), idempotency_key=self.k(), actor=self.p["mary"])
		self.assertEqual(done["state"], "Signed")
		self.assertEqual(frappe.db.count("Contract Simulated Signature", {"fixture_namespace": "CM_TEST"}), 1)
		self.assertEqual(holds.open_holds(case), [])

	def test_a_funding_failure_leaves_the_contract_signed_and_restoring_it_never_asks_for_a_signature(self):
		case, sent = self.sent()
		first = formation.sign_contract(case, party="Supplier", expected_version=sent["record_version"], idempotency_key=self.k(), actor=self.p["mary"])
		frappe.flags.kt_cm_funding_fault = "fail"
		second = formation.sign_contract(case, party="Entity", expected_version=first["record_version"], idempotency_key=self.k(), actor=self.p["amina"])
		self.assertEqual(second["lifecycle"], "Active")
		self.assertTrue(formation.native_order(case), "the order does not wait for the funding")
		keys = {h.key.split(":")[0] for h in holds.open_holds(case)}
		self.assertEqual(keys, {"operation"})
		self.assertIn((self.p["daniel"], "actionable"), self.mine(case))
		before = frappe.db.count("Contract Signature", {"contract_case": case, "state": "Signed"})
		frappe.flags.pop("kt_cm_funding_fault")
		restored = formation.restore_operations(case, actor=self.p["daniel"])
		self.assertEqual({o["kind"]: o["state"] for o in restored["operations"]}, {"Purchase order": "Succeeded", "Funding conversion": "Succeeded"})
		self.assertEqual(holds.open_holds(case), [])
		self.assertEqual(frappe.db.count("Contract Signature", {"contract_case": case, "state": "Signed"}), before)
		self.assertEqual(frappe.db.count("Purchase Order", {"supplier": world.SUPPLIER, "docstatus": 1}), 1, "one order, however often it is restored")
		self.assertEqual(refusal(formation.restore_operations, case, actor=self.p["julia"]).code, "CM_AUTHORITY")

	def test_a_rule_that_is_not_verified_stops_sending_on_a_site_that_is_not_a_simulation(self):
		case, saved = self.prepared()
		for flag in simulation.FLAGS:
			frappe.conf[flag] = 0
		frappe.flags.kt_contract_source_providers = [sources.Provider()]  # the synthetic provider answers only on a simulation site; the sources themselves are not what this test is about
		frappe.db.set_value("Contract Case", case, "legal_profile", "KE-PPADA-2015")
		exc = refusal(formation.request_signatures, case, expected_version=saved["record_version"], idempotency_key=self.k(), actor=self.p["charles"])
		self.assertEqual(exc.code, "CM_RULE")
		self.assertIn("CM_HOLD", {r["code"] for r in exc.reasons}, "the unanswered legal question about production execution is reported with it")
