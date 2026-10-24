# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.16 BUD-BR-035/036, section 8.7 and BUD25-AC-002 (CM-AC-85, AWD-FUND-AC-003/005): an award that names several reservations is converted whole, only on the Award owner's verification.

Budget does not read Award, Requisition or Contract records. It asks the owner of the award's funding allocation through a core seam, compares the answer with what it holds on each reservation (plan source
allocation, drawdown line, Budget Line, source department, and the Requisition Version through the source-set hash), pins the verified revision, rechecks it under its locks, and then converts every
reservation or none. These tests use a realistic stand-in for the Award owner that builds its answer from the reservations as Budget holds them, so each guard can be broken one at a time."""

from __future__ import annotations

from pathlib import Path

import frappe

from kentender_budget.services import budget_check_reserve_contracts as check_reserve
from kentender_budget.services import budget_commitment_contracts as commit
from kentender_budget.services import contract_funding_provider as owner
from kentender_budget.services.budget_contracts import _line_position_exact
from kentender_budget.services.budget_service_principal import PRINCIPAL_CONTRACT, PRINCIPAL_REQUISITIONS, service_caller
from kentender_budget.tests.test_bud_chg_001_phase3_check_reserve import FUNDING_SOURCE, owner_ou
from kentender_budget.tests.test_bud_chg_001_v19_usability import _V19Base
from kentender_core.services import award_funding_verification as verification
from kentender_core.services import contract_funding_contract as seam
from kentender_core.services import contract_reservation_authority as authority

NOT_AUTHORISED = "BUDGET_RESERVATION_NOT_AUTHORISED"
DHI = "Digital health infrastructure programme"
HWD = "Digital health workforce development"
LINEAGE = {"award": "AWD-LIN-1", "decision": "AWD-LIN-1-DEC-01", "allocation_digest": "d" * 64, "package_digest": "p" * 64, "agreement_version": 1}


class _AwardOwner:
	"""A stand-in for Award that answers from the reservations Budget holds, so that a test can change one fact at a time. `revision` may be a list: each answer takes the next one."""

	def __init__(self, test, amounts: dict[str, str], *, source_set_hash=None):
		self.test, self.amounts = test, amounts
		self.status, self.mismatches, self.tamper, self.revisions, self.calls = verification.VERIFIED, [], {}, ["rev-1"], 0
		self.source_set_hash = source_set_hash

	def verify(self, *, lineage, contract, allocations, purpose):
		self.calls += 1
		revision = self.revisions[min(self.calls - 1, len(self.revisions) - 1)]
		if self.status != verification.VERIFIED:
			return verification.Verification(self.status, list(self.mismatches) or ["The award's funding allocation could not be verified."])
		rows = []
		for reservation, amount in self.amounts.items():
			doc = frappe.get_doc("Funding Reservation", reservation)
			rows.append({"reservation": reservation, "plan_source_allocation": doc.plan_source_allocation, "drawdown_line": doc.drawdown_line_id, "budget_line": doc.budget_line,
				"source_organisation_unit": doc.source_organisation_unit, "amount": amount, **self.tamper.get(reservation, {})})
		any_doc = frappe.get_doc("Funding Reservation", next(iter(self.amounts)))
		hash_ = self.source_set_hash if self.source_set_hash is not None else any_doc.source_set_hash
		return verification.Verification(verification.VERIFIED, [], {"schema": "AwardFundingAllocation.v1", "allocations": rows, "requisition": {"source_set_hash": hash_}}, revision)


class _AwardBase(_V19Base):
	def setUp(self):
		super().setUp()
		self.contract = f"CM-AWD-{self.suffix}-{frappe.generate_hash(length=5)}"
		self.caller = service_caller(PRINCIPAL_CONTRACT, reference=self.contract)
		self.fy, self.budget, self.v1 = self._active()
		self.dhi, self.hwd = self._line(self.v1, DHI), self._line(self.v1, HWD)
		self.first, self.second = self._reserve_both()
		self.owner = _AwardOwner(self, {self.first: "18560000.00", self.second: "27840000.00"})
		self.install()

	def install(self):
		"""The contract's agreement names both reservations (the interim answer from Contract Management) and the award's owner is the stand-in."""
		previous_authority, previous_verification = frappe.flags.get(authority.FLAG), frappe.flags.get(verification.FLAG)
		frappe.flags[authority.FLAG] = [authority.Static({self.contract: [self.first, self.second]})]
		frappe.flags[verification.FLAG] = [self.owner]
		self.addCleanup(lambda: frappe.flags.update({authority.FLAG: previous_authority, verification.FLAG: previous_verification}))

	def _reserve_both(self):
		"""One requisition authorisation, two drawdown lines: the two reservations share a source-set hash, as REQ's authorisation gives them."""
		self._as(self.finance_officer)
		tag = frappe.generate_hash(length=6)
		ref = f"REQ-{tag}"
		allocations = [{"budget_line": line, "source_organisation_unit": owner_ou(line) or self.ou_dhp, "amount": amount, "funding_source": FUNDING_SOURCE, "plan_source_allocation": f"PSA-{tag}-{n}"}
			for n, (line, amount) in enumerate(((self.dhi, 18_560_000), (self.hwd, 27_840_000)), start=1)]
		token = check_reserve.check_funding(plan_item=f"PPI-{tag}", plan_version=f"PLN-{tag}", finance_task=f"FNT-{tag}", source_set_hash=f"HASH-{tag}", allocations=allocations,
			correlation_id=frappe.generate_hash(length=12), caller=service_caller(PRINCIPAL_REQUISITIONS, reference=ref))
		result = check_reserve.reserve_funding(token=token["token"], finance_task=f"FNT-{tag}", source_set_hash=f"HASH-{tag}", idempotency_key=f"IDEM-{tag}", caller=service_caller(PRINCIPAL_REQUISITIONS, reference=ref))
		self.assertTrue(result["ok"])
		return result["reservations"][0]["reservation_id"], result["reservations"][1]["reservation_id"]

	def rows(self):
		return [{"reservation": self.first, "amount": "18560000.00"}, {"reservation": self.second, "amount": "27840000.00"}]

	def convert_set(self, *, key=None, rows=None, lineage="default", caller=None):
		self._as("Administrator")
		return commit.convert_award_allocation(rows or self.rows(), self.contract, key or f"set-{frappe.generate_hash(length=8)}", contract_event_id=f"{self.contract}:signed", contract_event_type="ContractEffective",
			lineage=LINEAGE if lineage == "default" else lineage, caller=caller or self.caller)

	def position(self, line):
		return {k: float(v) for k, v in _line_position_exact(line, commit._current_line_version(line)).items()}

	def commitments(self):
		return frappe.get_all("Procurement Commitment", filters={"contract": self.contract}, fields=["name", "reservation", "current_amount", "origin", "budget_line", "lineage_json", "status"], order_by="creation asc")

	def remaining(self, reservation):
		return float(frappe.db.get_value("Funding Reservation", reservation, "remaining_amount"))

	def assert_nothing_converted(self):
		self.assertEqual(self.commitments(), [])
		self.assertEqual((self.remaining(self.first), self.remaining(self.second)), (18_560_000.0, 27_840_000.0))

	def refused(self, **kwargs):
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			self.convert_set(**kwargs)
		titles = [m.get("title") for m in (frappe.local.message_log or []) if isinstance(m, dict)]
		self.assertIn(NOT_AUTHORISED, titles)
		self.assert_nothing_converted()


class TestTheWholeAllocationConvertsOrNothingDoes(_AwardBase):
	def test_both_reservations_convert_in_one_operation_and_the_lineage_is_retained(self):
		dhi_before, hwd_before = self.position(self.dhi), self.position(self.hwd)
		done = self.convert_set()
		self.assertEqual(sorted(float(c["current_amount"]) for c in done["commitments"]), [18_560_000.0, 27_840_000.0])
		rows = self.commitments()
		self.assertEqual({r.reservation: float(r.current_amount) for r in rows}, {self.first: 18_560_000.0, self.second: 27_840_000.0})
		self.assertTrue(all(r.origin == "Reservation conversion" and r.status == "Active" for r in rows))
		for row in rows:
			lineage = frappe.parse_json(row.lineage_json)
			self.assertEqual((lineage["award"], lineage["allocation_digest"], lineage["verified_revision"]), ("AWD-LIN-1", "d" * 64, "rev-1"), "the verified lineage is kept on the commitment")
		self.assertEqual((self.remaining(self.first), self.remaining(self.second)), (0.0, 0.0))
		# reserved falls and committed rises by the same amount on each line: Available does not move
		for line, before, amount in ((self.dhi, dhi_before, 18_560_000), (self.hwd, hwd_before, 27_840_000)):
			after = self.position(line)
			self.assertEqual((after["reserved"], after["committed"], after["available"]), (before["reserved"] - amount, before["committed"] + amount, before["available"]))
		events = frappe.get_all("Budget Audit Event", filters={"budget": self.budget, "event_type": "Contract commitment recorded"}, fields=["reason"])
		self.assertTrue(all("AWD-LIN-1" in e.reason for e in events), "the conversion event names the verified lineage")

	def test_an_identical_retry_returns_the_original_and_converts_nothing_twice(self):
		first = self.convert_set(key="set-once")
		again = self.convert_set(key="set-once")
		self.assertTrue(again.get("replayed"))
		self.assertEqual(len(self.commitments()), 2)
		self.assertEqual([c["commitment_id"] for c in first["commitments"]], [c["commitment_id"] for c in again["commitments"]])

	def test_the_provider_finds_the_whole_set_by_its_identity_so_a_retry_links_it_instead_of_converting_again(self):
		identity = f"CM-OP-{frappe.generate_hash(length=6)}"
		self._as("Administrator")
		done = owner.service().convert(identity=identity, contract=self.contract, allocations=[{"reservation": self.first, "amount": 18_560_000.0}, {"reservation": self.second, "amount": 27_840_000.0}],
			amount=46_400_000.0, lineage=LINEAGE)
		found = owner.service().lookup(identity=identity)
		self.assertEqual((found["reference"], found["amount"]), (done["reference"], 46_400_000.0))
		self.assertEqual(len(self.commitments()), 2)
		self.assertIsNone(owner.service().lookup(identity="CM-OP-NEVER"))

	def test_a_second_row_that_cannot_be_converted_rolls_the_whole_set_back_and_a_corrected_retry_works(self):
		rows = [{"reservation": self.first, "amount": "18560000.00"}, {"reservation": self.second, "amount": "27840000.01"}]  # one minor unit more than the second reservation holds
		self.owner.amounts[self.second] = "27840000.01"
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			self.convert_set(key="set-fail", rows=rows)
		titles = [m.get("title") for m in (frappe.local.message_log or []) if isinstance(m, dict)]
		self.assertIn("BUDGET_CONVERSION_EXCEEDS_REMAINDER", titles)
		self.assert_nothing_converted()
		self.owner.amounts[self.second] = "27840000.00"
		self.assertEqual(len(self.convert_set(key="set-fail")["commitments"]), 2, "the refused attempt left no claim on the key")

	def test_a_provider_conversion_that_does_not_add_up_converts_nothing(self):
		self._as("Administrator")
		with self.assertRaises(seam.Refused):
			owner.service().convert(identity="CM-OP-SUM", contract=self.contract, allocations=[{"reservation": self.first, "amount": 18_560_000.0}], amount=46_400_000.0, lineage=LINEAGE)
		self.assert_nothing_converted()

	def test_one_reservation_can_still_be_converted_on_its_own_and_is_verified_too(self):
		self._as("Administrator")
		done = commit.convert_reservation(self.first, self.contract, "18560000.00", f"one-{frappe.generate_hash(length=6)}", contract_event_id="e1", contract_event_type="ContractEffective", lineage=LINEAGE, caller=self.caller)
		self.assertEqual(done["commitment"]["current_amount"], 18_560_000)
		self.assertEqual(frappe.parse_json(self.commitments()[0].lineage_json)["award"], "AWD-LIN-1")
		self.owner.status = verification.NOT_VERIFIED
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			commit.convert_reservation(self.second, self.contract, "27840000.00", f"one-{frappe.generate_hash(length=6)}", contract_event_id="e1", contract_event_type="ContractEffective", lineage=LINEAGE, caller=self.caller)
		self.assertEqual(len(self.commitments()), 1)


class TestEveryGuardOfTheVerificationMatters(_AwardBase):
	"""One test per guard: removing any one of them makes exactly its test fail."""

	def test_an_award_that_is_not_verified_converts_nothing(self):
		self.owner.status, self.owner.mismatches = verification.NOT_VERIFIED, ["The funding sources changed after the allocation was retained."]
		self.refused()

	def test_an_owner_that_cannot_answer_is_a_refusal_not_a_pass(self):
		self.owner.status = verification.UNAVAILABLE
		self.refused()

	def test_no_owner_installed_is_a_refusal(self):
		with verification.installed():
			self.refused()

	def test_a_failing_owner_is_unavailable_never_a_pass(self):
		class Broken:
			def verify(self, **kwargs):
				raise RuntimeError("the award owner is down")

		with verification.installed(Broken()):
			self.refused()

	def test_a_different_plan_source_allocation_is_refused(self):
		self.owner.tamper[self.first] = {"plan_source_allocation": "PSA-SOMEONE-ELSE"}
		self.refused()

	def test_a_different_drawdown_line_is_refused(self):
		self.owner.tamper[self.second] = {"drawdown_line": "DL-SOMEONE-ELSE"}
		self.refused()

	def test_a_different_budget_line_is_refused(self):
		self.owner.tamper[self.first] = {"budget_line": self.hwd}
		self.refused()

	def test_a_different_source_department_is_refused(self):
		self.owner.tamper[self.second] = {"source_organisation_unit": "OU-SOMEONE-ELSE"}
		self.refused()

	def test_a_different_requisition_version_through_the_source_set_hash_is_refused(self):
		self.owner.source_set_hash = "HASH-OF-ANOTHER-VERSION"
		self.refused()

	def test_a_reservation_the_award_does_not_name_is_refused_even_on_the_same_line(self):
		stranger = self._reserve(self.dhi, 1_000_000, ref=f"REQ-STRANGER-{frappe.generate_hash(length=4)}")
		self._as("Administrator")
		rows = [{"reservation": self.first, "amount": "18560000.00"}, {"reservation": stranger, "amount": "1000000.00"}]
		frappe.flags[authority.FLAG] = [authority.Static({self.contract: [self.first, self.second, stranger]})]  # the agreement may name it; the award's owner does not
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			self.convert_set(rows=rows)
		self.assertEqual(self.commitments(), [])

	def test_a_set_that_is_not_the_whole_allocation_is_refused_as_a_set(self):
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			self.convert_set(rows=[{"reservation": self.first, "amount": "18560000.00"}])
		self.assert_nothing_converted()

	def test_the_interim_answer_of_the_contract_is_still_required_as_well(self):
		frappe.flags[authority.FLAG] = [authority.Static({self.contract: [self.first]})]  # the agreement names only the first
		self.refused()

	def test_the_verified_revision_is_pinned_and_rechecked_under_the_locks(self):
		self.owner.revisions = ["rev-1", "rev-2"]  # the award's allocation changed between the first read and the lock
		self.refused()
		self.assertEqual(self.owner.calls, 2)

	def test_a_stable_revision_is_read_twice_and_passes(self):
		self.owner.revisions = ["rev-1"]
		self.convert_set()
		self.assertEqual(self.owner.calls, 2, "once before the locks and once under them")

	def test_the_wrong_amount_for_a_reservation_is_refused_even_if_the_owner_said_yes(self):
		self.owner.amounts[self.second] = "27840000.01"  # the owner's allocation says one minor unit more than the conversion asks
		self.refused()

	def test_another_contracts_service_cannot_convert_this_contracts_set(self):
		with self.assertRaises(frappe.PermissionError):
			self.convert_set(caller=service_caller(PRINCIPAL_CONTRACT, reference="CM-SOMEONE-ELSE"))
		self.assert_nothing_converted()


class TestTheVerificationHelpersAreForTestsAndSeedsOnly(_AwardBase):
	def test_production_code_never_installs_a_verification_stand_in(self):
		root = Path(frappe.get_app_path("kentender_budget")).parents[1]
		offenders = []
		for path in sorted(p for app in root.glob("kentender_*") for p in app.rglob("*.py")):
			relative = str(path.relative_to(root))
			if any(part in relative for part in ("/tests/", "/seeds/", "/test_services/", "/simulation/")) or relative.startswith("kentender_core/kentender_core/services/award_funding_verification.py"):
				continue
			if relative.startswith("kentender_core/kentender_core/services/contract_reservation_authority.py"):
				continue
			text = path.read_text()
			if "kt_award_funding_verifications" in text or "award_funding_verification.permit_all" in text or "award_funding_verification.PermitAll" in text or "verified_for(" in text:
				offenders.append(relative)
		self.assertEqual(offenders, [])


class TestARepeatedCallReadsBackTheSameReference(_AwardBase):
	"""The funding owner answers a repeated conversion, lookup or closure with exactly what it answered the first time, in the same order (found on the canonical award, where a repeated closure came back
	with its two commitment codes the other way round)."""

	def test_conversion_lookup_and_closure_repeat_identically(self):
		from kentender_budget.services.contract_funding_provider import service

		provider = service()
		self._as("Administrator")
		identity = f"{self.contract}:convert"
		first = provider.convert(identity=identity, contract=self.contract, allocations=self.rows(), amount=46_400_000.0, lineage=LINEAGE)
		self.assertEqual(provider.convert(identity=identity, contract=self.contract, allocations=self.rows(), amount=46_400_000.0, lineage=LINEAGE), first)
		self.assertEqual(provider.lookup(identity=identity), first)
		args = dict(identity=f"{self.contract}:close", contract=self.contract, final_amount=46_400_000.0, event_id=f"{self.contract}:closed", event_type="ContractClosed", evidence=["RECON-1"])
		closed = provider.close(**args)
		for _ in range(3):
			self.assertEqual(provider.close(**args), closed)
		self.assertEqual(closed["reference"], ", ".join(sorted(closed["reference"].split(", "))))
