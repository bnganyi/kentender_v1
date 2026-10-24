# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 plan D17, D18, D20 (tracker CM8-314): the synthetic Award package has the keys Award freezes and nothing else; the synthetic source handoff has one
verifiable reference for each of the twelve required sources and says which the real owners do not yet supply; and the test base wipes only its own rows."""

from __future__ import annotations

import re
from pathlib import Path

import frappe

from kentender_contracts.tests import synthetic
from kentender_core.services import contract_source_contract as seam
from kentender_contracts.tests.support import NAMESPACE, ContractCase

GAP = Path(frappe.get_app_path("kentender_contracts")).resolve().parents[1] / "docs/mvp-1-r1/21_contract_management/reconciliation/package_gap.md"


class TestSyntheticSources(ContractCase):
	def test_the_synthetic_award_package_has_exactly_the_keys_award_freezes(self):
		line = next(line for line in GAP.read_text().splitlines() if line.startswith("The keys of the dictionary `_content`"))
		body = line.split("freezes into", 1)[1].split(":", 1)[1]
		braces = re.findall(r"`([a-z_]+)`\s*\{([^{}]*)\}", body)  # `name` {nested, keys}
		top_level = set(re.findall(r"`([a-z_]+)(?:\[\])?`", re.sub(r"\{[^{}]*\}", "", body)))
		package = synthetic.award_package()
		self.assertEqual(set(package), top_level)
		for name, nested in braces:
			simple = {k.strip() for k in nested.split(",") if re.fullmatch(r"[a-z_]+", k.strip())}
			if name in ("report", "opinion", "decision", "response"):
				self.assertEqual(set(package[name]), simple, name)
		self.assertEqual((package["contract_terms"]["quantity"], package["decision"]["evaluated_amount"], package["decision"]["currency"]), (10, 1_000_000, "KES"))

	def through(self, provider):
		"""Ask through the published seam, as Contract Management does."""
		frappe.flags.kt_contract_source_providers = [provider]
		self.addCleanup(lambda: setattr(frappe.flags, "kt_contract_source_providers", None))

	def test_the_handoff_has_one_reference_for_each_of_the_twelve_sources_with_a_digest_that_recomputes(self):
		rows = synthetic.source_handoff()
		self.assertEqual([r["source"] for r in rows], [f"S{n}" for n in range(1, 13)])
		self.through(synthetic.Provider())
		for row in rows:
			self.assertTrue(seam.verify(row["reference"]), row["source"])
			self.assertEqual(seam.fetch(row["reference"])["digest"], row["sha256"])
			self.assertEqual(row["provider"], "synthetic")
			self.assertEqual(row["size"], len(seam.fetch(row["reference"])["content"]))
		self.assertEqual(len({r["reference"] for r in rows}), 12)

	def test_a_source_whose_bytes_changed_fails_verification_and_an_unknown_reference_is_none(self):
		self.through(synthetic.Provider(tamper="S5"))
		self.assertFalse(seam.verify("S5-" + synthetic.CASE))
		self.assertTrue(seam.verify("S4-" + synthetic.CASE))
		self.assertIsNone(seam.fetch("S99-nothing"))

	def test_the_provider_is_registered_on_the_core_hook_and_answers_only_on_a_simulation_site(self):
		from kentender_contracts.services import simulation

		self.assertIn("kentender_contracts.simulation.sources.service", frappe.get_hooks(seam.HOOK))
		flags = {f: frappe.conf.get(f) for f in simulation.FLAGS}
		try:
			frappe.conf.kt_cm_simulation_environment = 1
			self.assertTrue(seam.verify("S3-" + synthetic.CASE))
			for f in simulation.FLAGS:
				frappe.conf[f] = 0
			frappe.flags.kt_contract_source_providers = None
			self.assertFalse(seam.verify("S3-" + synthetic.CASE), "outside a simulation environment no source is invented")
		finally:
			for f, v in flags.items():
				frappe.conf[f] = v

	def test_the_real_handoff_gaps_are_recorded_so_green_synthetic_never_means_accepted(self):
		self.assertEqual(synthetic.missing_from_real_handoff(), ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"])
		text = GAP.read_text()
		for number, (_, _, status) in synthetic.SOURCES.items():
			row = next(line for line in text.splitlines() if line.startswith(f"| {number} |"))
			self.assertIn(status, row, f"{number} is {status} in the gap document")


class TestContractCaseBase(ContractCase):
	def test_a_case_is_created_in_the_test_namespace(self):
		case = self.new_case("CM-SUPPORT-1")
		self.assertEqual(frappe.db.get_value("Contract Case", case.name, "fixture_namespace"), NAMESPACE)

	def test_only_the_test_namespace_is_wiped_after_each_test(self):
		self.new_case("CM-SUPPORT-2")
		self.assertEqual(frappe.db.count("Contract Case", {"fixture_namespace": NAMESPACE}), 1)

	def test_the_previous_test_left_nothing_behind(self):
		self.assertEqual(frappe.db.count("Contract Case", {"fixture_namespace": NAMESPACE}), 0)


class TestNativeWorldIsBuiltOncePerClass(ContractCase):
	native = True

	def test_the_native_world_exists_for_every_test_and_is_not_mocked(self):
		from kentender_contracts.tests import native_world as world

		self.assertTrue(frappe.db.exists("Supplier", world.SUPPLIER))
		self.assertTrue(frappe.db.exists("Item", world.ITEM_FA))

	def test_the_same_world_serves_a_second_test(self):
		from kentender_contracts.tests import native_world as world

		self.assertEqual(frappe.db.count("Supplier", {"name": world.SUPPLIER}), 1)
