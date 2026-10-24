# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.13 proposal (follow-up FU-CM-59; owner decision 16 Oct 2026): a contract may consume only the reservations its own award names, within what each still holds.

Sharing a supplier or a Tender reference is not enough, and no answer from the owner of the contract's funding lineage is not a yes. Budget asks `contract_reservation_authority`
(Contract Management answers it from the contract's frozen award) and converts only on a clear yes. These tests use a fixed answer in its place; Contract Management's own answer is tested
in `kentender_contracts` (`test_cm_reservation_authority`).

The other money tests install an answer that permits everything, so the rule has to be tested here, with the narrow one."""

from __future__ import annotations

import ast
from pathlib import Path

import frappe

from kentender_budget.services import budget_commitment_contracts as commit
from kentender_budget.services import contract_funding_provider as owner
from kentender_budget.tests.test_budget_service_principal import _PrincipalBase, contract_caller
from kentender_core.services import contract_funding_contract as seam
from kentender_core.services import contract_reservation_authority as authority

NOT_AUTHORISED = "BUDGET_RESERVATION_NOT_AUTHORISED"


class TestAContractMayDrawOnlyOnItsAwardedReservations(_PrincipalBase):
	def _two_reservations(self, first=10_000_000, second=10_000_000):
		_budget, line = self._new_dhi_line()
		awarded = self._reserve(line, first, plan_item="TEST-PPI-SP-A")
		unrelated = self._reserve(line, second, reference="REQ-SP-OTHER", plan_item="TEST-PPI-SP-B")  # another requisition's hold on the same line
		self._as("Administrator")
		return awarded, unrelated

	def _convert(self, reservation, amount, *, key=None, contract=None):
		self._as("Administrator")
		return commit.convert_reservation(
			reservation, contract or self.contract, amount, key or self._key("conv"),
			contract_event_id=f"{self.contract}:signed", contract_event_type="ContractSigned", caller=contract_caller(contract or self.contract),
		)

	def _refused_as(self, reservation, amount, expected_title=NOT_AUTHORISED):
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			self._convert(reservation, amount)
		titles = [m.get("title") for m in (frappe.local.message_log or []) if isinstance(m, dict)]
		self.assertIn(expected_title, titles)

	def _untouched(self, reservation, remaining):
		self.assertEqual(frappe.db.count("Procurement Commitment", {"reservation": reservation}), 0)
		self.assertEqual(frappe.db.get_value("Funding Reservation", reservation, "remaining_amount"), remaining)

	def test_a_reservation_the_award_names_converts(self):
		awarded, _unrelated = self._two_reservations()
		with authority.installed(authority.Static({self.contract: [awarded]})):
			done = self._convert(awarded, 4_000_000)
		self.assertEqual(done["commitment"]["current_amount"], 4_000_000)
		self.assertEqual(done["reservation"]["remaining_amount"], 6_000_000)

	def test_a_reservation_the_award_does_not_name_is_refused_and_nothing_changes(self):
		"""The same contract, the same line, the same funding source, and a reservation it was never awarded: refused, not converted."""
		awarded, unrelated = self._two_reservations()
		with authority.installed(authority.Static({self.contract: [awarded]})):
			self._refused_as(unrelated, 4_000_000)
		self._untouched(unrelated, 10_000_000)
		self._untouched(awarded, 10_000_000)

	def test_the_award_of_another_contract_does_not_carry_over(self):
		awarded, unrelated = self._two_reservations()
		with authority.installed(authority.Static({self.contract: [awarded], f"{self.contract}-B": [unrelated]})):
			self._refused_as(unrelated, 1_000_000)
		self._untouched(unrelated, 10_000_000)

	def test_a_contract_no_owner_knows_is_refused(self):
		awarded, _unrelated = self._two_reservations()
		with authority.installed(authority.Static({})):
			self._refused_as(awarded, 1_000_000)
		self._untouched(awarded, 10_000_000)

	def test_no_owner_installed_at_all_is_a_refusal_never_a_yes(self):
		awarded, _unrelated = self._two_reservations()
		with authority.installed():
			frappe.local.message_log = []
			with self.assertRaises(frappe.ValidationError) as caught:
				self._convert(awarded, 1_000_000)
		self.assertIn("No funding owner confirms", str(caught.exception))
		self._untouched(awarded, 10_000_000)

	def test_an_awarded_reservation_is_still_bounded_by_what_it_holds(self):
		awarded, _unrelated = self._two_reservations(first=500_000)
		with authority.installed(authority.Static({self.contract: [awarded]})):
			self._refused_as(awarded, 600_000, expected_title="BUDGET_CONVERSION_EXCEEDS_REMAINDER")
		self._untouched(awarded, 500_000)

	def test_a_repeat_converts_once(self):
		awarded, _unrelated = self._two_reservations()
		key = self._key("conv")
		with authority.installed(authority.Static({self.contract: [awarded]})):
			first = self._convert(awarded, 3_000_000, key=key)
			replay = self._convert(awarded, 3_000_000, key=key)  # the same key and payload
			again = self._convert(awarded, 3_000_000)  # a new key, the same contract, reservation and amount
		self.assertTrue(replay.get("replayed"))
		self.assertEqual(replay["commitment"]["commitment_id"], first["commitment"]["commitment_id"])
		self.assertEqual(again["commitment"]["commitment_id"], first["commitment"]["commitment_id"])
		self.assertEqual(frappe.db.count("Procurement Commitment", {"reservation": awarded}), 1)
		self.assertEqual(frappe.db.get_value("Funding Reservation", awarded, "remaining_amount"), 7_000_000)


class TestSeveralReservationsThroughTheSeam(_PrincipalBase):
	"""A contract the award funds from more than one reservation: all of them convert, or none does."""

	def setUp(self):
		super().setUp()
		frappe.flags.kt_contract_funding_providers = [owner.Provider()]
		self.addCleanup(lambda: setattr(frappe.flags, "kt_contract_funding_providers", None))
		self.identity = f"{self.contract}|agreement 1|1|Funding conversion|effective"
		_budget, line = self._new_dhi_line()
		self.first = self._reserve(line, 10_000_000, plan_item="TEST-PPI-SP-1")
		self.second = self._reserve(line, 10_000_000, reference="REQ-SP-SECOND", plan_item="TEST-PPI-SP-2")
		self.stranger = self._reserve(line, 10_000_000, reference="REQ-SP-STRANGER", plan_item="TEST-PPI-SP-3")
		self._as("Administrator")

	def _allocations(self, *pairs):
		return [{"reservation": reservation, "amount": amount} for reservation, amount in pairs]

	def test_every_reservation_the_award_names_converts(self):
		with authority.installed(authority.Static({self.contract: [self.first, self.second]})):
			done = seam.convert(self.identity, contract=self.contract, allocations=self._allocations((self.first, 700_000), (self.second, 300_000)), amount=1_000_000)
		self.assertEqual(done["amount"], 1_000_000)
		self.assertEqual(sorted(frappe.get_all("Procurement Commitment", filters={"contract": self.contract}, pluck="current_amount")), [300_000, 700_000])

	def test_one_reservation_the_award_does_not_name_converts_nothing_at_all(self):
		with authority.installed(authority.Static({self.contract: [self.first, self.second]})):
			with self.assertRaises(seam.Refused) as caught:
				seam.convert(self.identity, contract=self.contract, allocations=self._allocations((self.first, 700_000), (self.stranger, 300_000)), amount=1_000_000)
		self.assertIn("not one of the reservations awarded", str(caught.exception))
		self.assertEqual(frappe.db.count("Procurement Commitment", {"contract": self.contract}), 0, "the award's own reservation was not converted either")
		self.assertEqual(frappe.db.get_value("Funding Reservation", self.first, "remaining_amount"), 10_000_000)
		self.assertEqual(frappe.db.get_value("Funding Reservation", self.stranger, "remaining_amount"), 10_000_000)

	def test_a_replay_of_the_whole_conversion_converts_nothing_more(self):
		with authority.installed(authority.Static({self.contract: [self.first, self.second]})):
			first = seam.convert(self.identity, contract=self.contract, allocations=self._allocations((self.first, 700_000), (self.second, 300_000)), amount=1_000_000)
			again = seam.convert(self.identity, contract=self.contract, allocations=self._allocations((self.first, 700_000), (self.second, 300_000)), amount=1_000_000)
		self.assertEqual(first, again)
		self.assertEqual(frappe.db.count("Procurement Commitment", {"contract": self.contract}), 2)
		self.assertEqual(frappe.db.get_value("Funding Reservation", self.first, "remaining_amount"), 9_300_000)


class TestTheAuthorityOverrideIsForSeedsAndTestsOnly(_PrincipalBase):
	def test_only_the_authority_module_seeds_and_tests_may_override_the_answer(self):
		"""A production file that installs its own answer, or reads the flag, could grant itself a yes. An import and syntax-tree scan: any use of the helpers or the flag outside the module, seeds and tests is found."""
		root = Path(frappe.get_app_path("kentender_budget")).parent.parent
		offenders = []
		for path in sorted(root.glob("kentender_*/**/*.py")):
			rel = str(path.relative_to(root))
			if "/tests/" in rel or "/seeds/" in rel or "/node_modules/" in rel or rel.endswith("contract_reservation_authority.py"):
				continue
			text = path.read_text(encoding="utf-8", errors="ignore")
			if "contract_reservation_authority" not in text and "kt_contract_reservation_authorities" not in text:
				continue
			for line in overrides_in(text):
				offenders.append((rel, line))
		self.assertEqual(offenders, [])

	def test_awarded_names_exactly_the_given_reservations_and_puts_the_previous_answer_back(self):
		before = frappe.flags.get(authority.FLAG)
		with authority.awarded("CTR-X", "RSV-1", "RSV-2"):
			self.assertIs(authority.authorises("CTR-X", "RSV-1"), True)
			self.assertIs(authority.authorises("CTR-X", "RSV-3"), False)
			self.assertIsNone(authority.authorises("CTR-Y", "RSV-1"))
		self.assertEqual(frappe.flags.get(authority.FLAG), before)

	def test_the_scan_finds_each_way_to_override(self):
		for label, source in {
			"permit_all": "from kentender_core.services import contract_reservation_authority as a\na.permit_all(self)\n",
			"installed": "from kentender_core.services import contract_reservation_authority as a\nwith a.installed(a.PermitAll()):\n    pass\n",
			"awarded": "from kentender_core.services.contract_reservation_authority import awarded\nawarded('C', 'R')\n",
			"flag": "import frappe\nfrappe.flags.kt_contract_reservation_authorities = []\n",
			"flag by name": "import frappe\nfrappe.flags['kt_contract_reservation_authorities'] = []\n",
			"flag constant": "import frappe\nfrom kentender_core.services import contract_reservation_authority as a\nfrappe.flags[a.FLAG] = []\n",
		}.items():
			with self.subTest(label):
				self.assertTrue(overrides_in(source), f"{label} was not found")
		self.assertEqual(overrides_in("from kentender_core.services import contract_reservation_authority as a\na.authorises('C', 'R')\n"), [])


def overrides_in(source: str) -> list[int]:
	"""Lines that set or install the contract reservation authority override: a call to one of the helpers, or a write to the flag."""
	tree = ast.parse(source)
	helpers = {"permit_all", "installed", "awarded", "Static", "PermitAll"}
	names, modules = set(), set()
	for node in ast.walk(tree):
		if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("contract_reservation_authority"):
			names |= {a.asname or a.name for a in node.names if a.name in helpers}
		elif isinstance(node, ast.ImportFrom):
			modules |= {a.asname or a.name for a in node.names if a.name == "contract_reservation_authority"}
		elif isinstance(node, ast.Import):
			modules |= {a.asname or a.name.split(".")[-1] for a in node.names if a.name.endswith("contract_reservation_authority")}
	found = []
	for node in ast.walk(tree):
		if isinstance(node, ast.Call):
			func = node.func
			if (isinstance(func, ast.Name) and func.id in names) or (isinstance(func, ast.Attribute) and func.attr in helpers and isinstance(func.value, ast.Name) and func.value.id in modules):
				found.append(node.lineno)
		elif isinstance(node, (ast.Assign, ast.AugAssign)):
			for target in node.targets if isinstance(node, ast.Assign) else [node.target]:
				if isinstance(target, ast.Attribute) and target.attr == "kt_contract_reservation_authorities":
					found.append(node.lineno)
				elif isinstance(target, ast.Subscript) and (
					(isinstance(target.slice, ast.Constant) and target.slice.value == "kt_contract_reservation_authorities")
					or (isinstance(target.slice, ast.Attribute) and target.slice.attr == "FLAG")
				):
					found.append(node.lineno)
	return found
