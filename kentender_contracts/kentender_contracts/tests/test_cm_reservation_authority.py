# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.13 proposal (follow-up FU-CM-59): Contract Management answers Budget's question "may this contract draw on this reservation?" from the contract's own frozen award.

The funding lineage in an effective agreement's terms is what Award's package named (source S9, hashed when it was gathered). A reservation the agreement does not name is not the contract's, whoever the
supplier is; a contract registered independently of a Tender names none and never draws on Budget; a name that is not one of our cases is not ours to answer."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_contracts.services import records
from kentender_contracts.services import reservation_authority as owner
from kentender_core.services import contract_reservation_authority as seam

NS = "CM_RESERVATION_AUTHORITY"


class TestContractManagementAnswersWhichReservationsAreTheContractsOwn(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.flags.kt_cm_fixture_namespace = NS
		self.addCleanup(self._wipe)

	def _wipe(self):
		frappe.flags.kt_cm_fixture_namespace = ""
		records.wipe(NS)
		frappe.db.commit()

	def _case(self, label: str, *, kind="KenTender award", versions=()):
		case = records.new("Contract Case", contract_id=f"CM-RA-{label}", source_kind=kind, fixture_namespace=NS)
		for number, (state, funding) in enumerate(versions, start=1):
			records.new("Contract Agreement Version", contract_case=case.name, version_no=number, state=state, terms_json=records.dumps({"funding": funding}), fixture_namespace=NS)
		return case.name

	def _awarded(self, *reservations):
		return {"allocations": [{"reservation": r, "amount": 100.0} for r in reservations]}

	def test_the_reservations_an_effective_agreement_names_are_the_contracts_own(self):
		case = self._case("A", versions=[("Effective", self._awarded("RSV-1", "RSV-2"))])
		self.assertIs(owner.Authority().authorises(contract=case, reservation="RSV-1"), True)
		self.assertIs(owner.Authority().authorises(contract=case, reservation="RSV-2"), True)

	def test_a_reservation_the_award_does_not_name_is_not_the_contracts_even_on_the_same_line(self):
		case = self._case("B", versions=[("Effective", self._awarded("RSV-1"))])
		self.assertIs(owner.Authority().authorises(contract=case, reservation="RSV-OTHER"), False)
		self.assertIs(owner.Authority().authorises(contract=case, reservation=""), False)

	def test_another_contracts_award_does_not_carry_over(self):
		mine = self._case("C1", versions=[("Effective", self._awarded("RSV-1"))])
		theirs = self._case("C2", versions=[("Effective", self._awarded("RSV-9"))])
		self.assertIs(owner.Authority().authorises(contract=mine, reservation="RSV-9"), False)
		self.assertIs(owner.Authority().authorises(contract=theirs, reservation="RSV-1"), False)

	def test_an_agreement_that_is_not_yet_effective_authorises_nothing(self):
		case = self._case("D", versions=[("Awaiting signatures", self._awarded("RSV-1"))])
		self.assertIs(owner.Authority().authorises(contract=case, reservation="RSV-1"), False)

	def test_a_contract_registered_independently_of_a_tender_never_draws_on_budget(self):
		case = self._case("E", kind="External record", versions=[("Effective", {"external": True})])
		self.assertIs(owner.Authority().authorises(contract=case, reservation="RSV-1"), False)

	def test_a_name_that_is_not_a_contract_case_is_not_ours_to_answer(self):
		self.assertIsNone(owner.Authority().authorises(contract="NOT-A-CASE", reservation="RSV-1"))
		self.assertIsNone(owner.Authority().authorises(contract="", reservation="RSV-1"))

	def test_the_owner_is_registered_on_the_core_seam(self):
		self.assertIn("kentender_contracts.services.reservation_authority.service", frappe.get_hooks(seam.HOOK))
		self.assertTrue(any(isinstance(provider, owner.Authority) for provider in seam.providers()))
		case = self._case("F", versions=[("Effective", self._awarded("RSV-1"))])
		self.assertIs(seam.authorises(case, "RSV-1"), True)
		self.assertIs(seam.authorises(case, "RSV-2"), False)
