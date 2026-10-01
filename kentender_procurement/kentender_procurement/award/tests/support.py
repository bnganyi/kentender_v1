# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Award test base (AWD-CHG-001 v0.4 plan OD-B, tracker rules 10–11).

Every Award service test starts from a signed Evaluation report delivered by
the synthetic sources — no tender, bid, opening or evaluation is built, so a
case exists in well under a second. Per test only this module's namespace of
Award rows, the synthetic state and the fault switches are cleared. Writes
persist on this bench (`bench run-tests` has no rollback), so every test
cleans up after itself; nothing touches the canonical rows."""

from __future__ import annotations

import itertools
import unittest
from typing import Any

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.award.seeds import clear
from kentender_procurement.award.services import profile, records, simulation
from kentender_procurement.award.test_services import sources as syn

NS = "AWD_TEST"
HOP = "charles.mutiso@moh.example.test"
AO = "amina.hassan@moh.example.test"
MARY = "mary.wanjiku@afyadigital.example"
DAVID = "david.ouma@afyadigital.example"
DANIEL = "daniel.otieno@moh.example.test"
NAOMI = "naomi.chebet@moh.example.test"
REF = "TND-AWT-2100-033"
CASE = "AWD-AWT-2100-033"
T0 = "2027-06-16 14:07:01"
_keys = itertools.count(1)


def reset() -> None:
	clear.wipe(namespace=NS)
	syn.clear()
	simulation.reset_controls()
	frappe.flags.kt_awd_fixture_namespace = None
	frappe.flags.kt_awd_clock = None
	frappe.db.commit()


class AwardCase(IntegrationTestCase):
	"""One synthetic Award world per test, in milliseconds."""

	world = "033"
	reference = REF

	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		unittest.addModuleCleanup(reset)

	def setUp(self) -> None:
		frappe.set_user("Administrator")
		reset()
		frappe.flags.kt_awd_fixture_namespace = NS
		profile.install_test_profile(contracting_owner=HOP, technical_operator=DANIEL)
		self.at("2027-06-16 14:07:01")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		reset()

	# -- helpers ----------------------------------------------------------------
	def at(self, instant: str) -> None:
		frappe.flags.kt_awd_clock = instant

	def key(self, prefix: str = "t") -> str:
		return f"awd-test-{prefix}-{next(_keys)}-{frappe.generate_hash(length=6)}"

	def deliver(self, world: str | None = None, **kwargs) -> dict[str, Any]:
		world = world or self.world
		reference = kwargs.pop("reference", None) or self.reference.replace("-033", f"-{world}")
		return syn.deliver(world, reference=reference, **kwargs)

	def case(self, name: str = CASE):
		return frappe.get_doc(records.CASE, name)

	def version(self, name: str = CASE) -> int:
		return int(frappe.db.get_value(records.CASE, name, "record_version"))

	def run_as(self, user: str, fn, **kwargs) -> dict[str, Any]:
		frappe.set_user(user)
		try:
			return fn(user=user, idempotency_key=kwargs.pop("idempotency_key", None) or self.key(fn.__name__), **kwargs)
		finally:
			frappe.set_user("Administrator")

	def signed_opinion(self, name: str = CASE, *, conclusion: str = "Recommend award",
			reason: str = "The signed report identifies Afya Digital Supplies Limited as the lowest evaluated responsive tenderer. No unresolved issue prevents the proposed award.") -> dict[str, Any]:
		from kentender_procurement.award.services import opinion

		self.at("2027-06-17 09:00:00")
		self.run_as(HOP, opinion.save, award=name, conclusion=conclusion, reason=reason, expected_version=self.version(name))
		self.at("2027-06-17 09:10:00")
		return self.run_as(HOP, opinion.sign, award=name, expected_version=self.version(name))

	def awarded(self, name: str = CASE) -> dict[str, Any]:
		from kentender_procurement.award.services import decision

		self.signed_opinion(name)
		self.at("2027-06-17 10:00:00")
		return self.run_as(AO, decision.record, award=name, outcome="Award",
			reason="I accept the recommendation in the signed evaluation report and professional opinion.", expected_version=self.version(name))
