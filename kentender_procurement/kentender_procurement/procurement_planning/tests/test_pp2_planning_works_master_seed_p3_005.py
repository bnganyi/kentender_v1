# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-005 — PP2 WORKS master planning seed upstream validation tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.demand_intake.seeds.works_master_demand_seed import upsert_works_master_demand
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
	validate_procurement_planning_works_master_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	BUDGET_LINE_CODE,
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	JOURNEY_CODE,
	PKG_CODE,
	PLAN_CODE,
	STD_VERSION_CODE,
	TENDER_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.upstream import (
	validate_upstream_for_checkpoint,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"
_STD_POC_CODE = "KE-PPRA-WORKS-BLDG-2022-04-POC"


def _bootstrap_upstream(*, with_tender: bool = True) -> None:
	ensure_currency_kes()
	ensure_procuring_entity(_PE_CODE, _PE_NAME)
	assert upsert_works_master_strategy_hierarchy().get("ok")
	assert upsert_works_master_budget().get("ok")
	assert upsert_works_master_demand().get("ok")
	assert upsert_works_master_journey().get("ok")
	from kentender_procurement.tender_management.seeds.works_master_std_seed import (
		upsert_works_master_std,
	)

	assert upsert_works_master_std().get("ok")
	if with_tender:
		from kentender_procurement.tender_management.seeds.works_master_tender_seed import (
			upsert_works_master_tender,
		)

		if not frappe.db.exists("TM2 Tender", TENDER_CODE):
			from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
				run_load,
			)

			run_load(checkpoint="RELEASED_TO_TENDER", force_reset=True)
			upsert_works_master_tender()


def _demand_doc_name() -> str | None:
	return frappe.db.get_value("Demand", {"demand_id": DEMAND_CODE}, "name")


def _restore_master_demand() -> None:
	"""Recreate demand when line items were removed (upsert alone is idempotent skip)."""
	demand_name = _demand_doc_name()
	if demand_name:
		item_count = frappe.db.count(
			"Demand Item",
			{"parent": demand_name, "parenttype": "Demand"},
		)
		if not item_count:
			frappe.delete_doc("Demand", demand_name, force=True, ignore_permissions=True)
			frappe.db.commit()
	upsert_works_master_demand()
	frappe.db.commit()


def _tender_linked_to_package() -> bool:
	if not frappe.db.exists("TM2 Tender", TENDER_CODE):
		return False
	if not frappe.db.exists("Procurement Package", PKG_CODE):
		return False
	row = frappe.db.get_value(
		"TM2 Tender",
		TENDER_CODE,
		["procurement_package", "procurement_package_code", "source_package_code"],
		as_dict=True,
	)
	if not row:
		return False
	candidates = {PKG_CODE}
	for field in ("procurement_package", "procurement_package_code", "source_package_code"):
		value = str(row.get(field) or "").strip()
		if value in candidates:
			return True
	return False


def _purge_orphan_master_tender_artifacts() -> None:
	"""Remove TM2 child rows left when tests delete the canonical tender."""
	if frappe.db.exists("TM2 Tender", TENDER_CODE):
		return
	for doctype, field in (
		("TM2 Tender Access Rule", "tm2_tender"),
		("TM2 Tender Access Rule", "tender_code"),
		("TM2 Tender Timeline", "tm2_tender"),
		("TM2 Tender Timeline", "tender_code"),
	):
		for name in frappe.get_all(doctype, filters={field: TENDER_CODE}, pluck="name"):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
	frappe.db.commit()


def _delete_unlinked_master_tender() -> None:
	if not frappe.db.exists("TM2 Tender", TENDER_CODE):
		_purge_orphan_master_tender_artifacts()
		return
	if _tender_linked_to_package():
		return
	frappe.delete_doc("TM2 Tender", TENDER_CODE, force=True, ignore_permissions=True)
	_purge_orphan_master_tender_artifacts()
	frappe.db.commit()


def _insert_stub_tm2_tender() -> None:
	"""Minimal TM2 Tender row for upstream validation when full TM seed path fails."""
	if frappe.db.exists("TM2 Tender", TENDER_CODE):
		return
	fields: dict[str, object] = {
		"doctype": "TM2 Tender",
		"tender_code": TENDER_CODE,
		"tender_title": "District Hospital Renovation Works",
		"status": "Published",
		"is_active": 1,
	}
	if frappe.db.exists("Procurement Package", PKG_CODE):
		fields["procurement_package"] = PKG_CODE
		fields["procurement_package_code"] = PKG_CODE
		fields["source_package_code"] = PKG_CODE
	doc = frappe.get_doc(fields)
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()


def _heal_master_planning_site(*, through: str = "RELEASED_TO_TENDER") -> None:
	"""Rebuild master planning seed after destructive P3-005 tests."""
	from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
		run_load,
	)

	checkpoints = ("INCLUDED_IN_PLAN", "PACKAGE_DRAFT", "READY_FOR_RELEASE", "RELEASED_TO_TENDER", "CONSUMED_BY_TENDER")
	for checkpoint in checkpoints:
		run_load(checkpoint=checkpoint, force_reset=False)
		if checkpoint == through:
			break

	if through == "CONSUMED_BY_TENDER":
		_restore_master_tender(require_linked=True)
		run_load(checkpoint="CONSUMED_BY_TENDER", force_reset=False)


def _restore_master_tender(*, require_linked: bool = False) -> None:
	"""Restore canonical TM2 tender; remove stub rows that break release/consumption seeds."""
	_delete_unlinked_master_tender()
	_purge_orphan_master_tender_artifacts()
	from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
		run_load,
	)
	from kentender_procurement.tender_management.services.create_tender_from_package import (
		active_tm2_tender_name_for_package,
	)

	if not frappe.db.exists("Procurement Package", PKG_CODE):
		run_load(checkpoint="RELEASED_TO_TENDER", force_reset=False)

	if frappe.db.exists("TM2 Tender", TENDER_CODE) and _tender_linked_to_package():
		return

	pkg_name = frappe.db.get_value("Procurement Package", PKG_CODE, "name") or PKG_CODE
	existing_tm2 = active_tm2_tender_name_for_package(pkg_name)
	if existing_tm2 and existing_tm2 != TENDER_CODE:
		from kentender_procurement.tender_management.seeds.works_master_tender_seed import (
			upsert_works_master_tender,
		)

		try:
			upsert_works_master_tender()
		except Exception:
			pass
		if frappe.db.exists("TM2 Tender", TENDER_CODE) and _tender_linked_to_package():
			return

	if not frappe.db.exists("TM2 Tender", TENDER_CODE):
		_insert_stub_tm2_tender()

	from kentender_procurement.tender_management.seeds.works_master_tender_seed import (
		upsert_works_master_tender,
	)

	try:
		upsert_works_master_tender()
	except Exception:
		if not require_linked:
			if not frappe.db.exists("TM2 Tender", TENDER_CODE):
				_insert_stub_tm2_tender()
			return
		raise

	if require_linked and not _tender_linked_to_package():
		_insert_stub_tm2_tender()


def _ensure_master_tender_for_upstream() -> None:
	if _tender_linked_to_package():
		return
	_restore_master_tender()


class TestPP2PlanningWorksMasterSeedUpstreamP3005(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Plan"):
			cls._skip = True
			return
		cls._skip = False
		_bootstrap_upstream(with_tender=False)

	def setUp(self):
		super().setUp()
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		clear_master_planning_seed()
		_restore_master_demand()

	def tearDown(self):
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		clear_master_planning_seed()
		upsert_works_master_budget()
		_restore_master_demand()
		upsert_works_master_journey()
		from kentender_procurement.tender_management.seeds.works_master_std_seed import (
			upsert_works_master_std,
		)

		upsert_works_master_std()

	@classmethod
	def tearDownClass(cls):
		if getattr(cls, "_skip", True):
			return super().tearDownClass()
		frappe.set_user("Administrator")
		try:
			_heal_master_planning_site(through="RELEASED_TO_TENDER")
			_restore_master_tender(require_linked=False)
		except Exception:
			pass
		return super().tearDownClass()

	def test_001_upstream_success_at_approved_demand_ready(self):
		"""SEED-TEST-P3-005-001: APPROVED_DEMAND_READY upstream links without STD/TND."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = validate_upstream_for_checkpoint("APPROVED_DEMAND_READY")
		self.assertTrue(out.get("ok"), out)
		links = out.get("links") or {}
		self.assertEqual(links.get("demand"), DEMAND_CODE)
		self.assertEqual(links.get("demand_item"), DEMAND_ITEM_CODE)
		self.assertEqual(links.get("budget_line"), BUDGET_LINE_CODE)
		self.assertEqual(links.get("journey"), JOURNEY_CODE)
		self.assertNotIn("std_version", links)
		self.assertNotIn("tender", links)

	def test_002_upstream_success_at_consumed_by_tender(self):
		"""SEED-TEST-P3-005-002: CONSUMED_BY_TENDER upstream includes STD and tender links."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		_ensure_master_tender_for_upstream()
		out = validate_upstream_for_checkpoint("CONSUMED_BY_TENDER")
		self.assertTrue(out.get("ok"), out)
		links = out.get("links") or {}
		self.assertEqual(links.get("demand_item"), DEMAND_ITEM_CODE)
		self.assertEqual(links.get("std_version"), STD_VERSION_CODE)
		self.assertEqual(links.get("tender"), TENDER_CODE)

	def test_003_missing_demand_blocks_loader(self):
		"""SEED-TEST-P3-005-003: Missing demand returns MISSING_DEMAND and no plan."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		demand_name = _demand_doc_name()
		try:
			if demand_name:
				frappe.delete_doc("Demand", demand_name, force=True, ignore_permissions=True)
				frappe.db.commit()

			out = seed_procurement_planning_works_master(checkpoint="INCLUDED_IN_PLAN")
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("error_code"), "MISSING_DEMAND")
			self.assertFalse(frappe.db.exists("Procurement Plan", PLAN_CODE))
		finally:
			_restore_master_demand()

	def test_004_demand_not_approved_blocks_loader(self):
		"""SEED-TEST-P3-005-004: Unapproved demand returns DEMAND_NOT_APPROVED."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		demand_name = _demand_doc_name()
		self.assertIsNotNone(demand_name)
		original_status = frappe.db.get_value("Demand", demand_name, "status")
		try:
			frappe.db.set_value("Demand", demand_name, "status", "Draft", update_modified=False)
			frappe.db.commit()

			out = seed_procurement_planning_works_master(checkpoint="INCLUDED_IN_PLAN")
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("error_code"), "DEMAND_NOT_APPROVED")
			self.assertFalse(frappe.db.exists("Procurement Plan", PLAN_CODE))
		finally:
			frappe.db.set_value(
				"Demand", demand_name, "status", original_status or "Approved", update_modified=False
			)
			frappe.db.commit()

	def test_005_missing_budget_line_blocks_loader(self):
		"""SEED-TEST-P3-005-005: Missing budget line returns MISSING_BUDGET_LINE."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		budget_name = frappe.db.get_value("Budget Line", {"budget_line_code": BUDGET_LINE_CODE}, "name")
		try:
			if budget_name:
				frappe.db.set_value(
					"Budget Line",
					budget_name,
					"budget_line_code",
					"BUD-P3-005-HIDDEN",
					update_modified=False,
				)
				frappe.db.commit()

			out = seed_procurement_planning_works_master(checkpoint="INCLUDED_IN_PLAN")
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("error_code"), "MISSING_BUDGET_LINE")
			self.assertFalse(frappe.db.exists("Procurement Plan", PLAN_CODE))
		finally:
			if budget_name:
				frappe.db.set_value(
					"Budget Line",
					budget_name,
					"budget_line_code",
					BUDGET_LINE_CODE,
					update_modified=False,
				)
			upsert_works_master_budget()
			frappe.db.commit()

	def test_006_missing_journey_blocks_loader(self):
		"""SEED-TEST-P3-005-006: Missing journey returns MISSING_JOURNEY."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		try:
			if frappe.db.exists("Procurement Journey", JOURNEY_CODE):
				frappe.delete_doc("Procurement Journey", JOURNEY_CODE, force=True, ignore_permissions=True)
				frappe.db.commit()

			out = seed_procurement_planning_works_master(checkpoint="INCLUDED_IN_PLAN")
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("error_code"), "MISSING_JOURNEY")
			self.assertFalse(frappe.db.exists("Procurement Plan", PLAN_CODE))
		finally:
			upsert_works_master_journey()
			frappe.db.commit()

	def test_007_missing_demand_item_blocks_loader(self):
		"""SEED-TEST-P3-005-007: Demand without line items returns MISSING_DEMAND_ITEM."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		demand_name = _demand_doc_name()
		self.assertIsNotNone(demand_name)
		rows = frappe.get_all(
			"Demand Item",
			filters={"parent": demand_name, "parenttype": "Demand"},
			pluck="name",
		)
		try:
			for row_name in rows:
				frappe.delete_doc("Demand Item", row_name, force=True, ignore_permissions=True)
			frappe.db.commit()

			out = validate_upstream_for_checkpoint("APPROVED_DEMAND_READY")
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("error_code"), "MISSING_DEMAND_ITEM")

			loader_out = seed_procurement_planning_works_master(checkpoint="INCLUDED_IN_PLAN")
			self.assertFalse(loader_out.get("ok"))
			self.assertEqual(loader_out.get("error_code"), "MISSING_DEMAND_ITEM")
			self.assertFalse(frappe.db.exists("Procurement Plan", PLAN_CODE))
		finally:
			_restore_master_demand()

	def test_008_missing_std_version_at_ready_for_release(self):
		"""SEED-TEST-P3-005-008: READY_FOR_RELEASE without STD refs returns MISSING_STD_VERSION."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		_restore_master_demand()
		journey_std_ref = frappe.db.get_value(
			"Procurement Journey", JOURNEY_CODE, "std_template_version_ref"
		)
		saved_std_codes: dict[str, str] = {}
		for code in (STD_VERSION_CODE, _STD_POC_CODE):
			for std_name in frappe.get_all(
				"STD Template", filters={"template_code": code}, pluck="name"
			):
				saved_std_codes[std_name] = code
		try:
			frappe.db.set_value(
				"Procurement Journey",
				JOURNEY_CODE,
				"std_template_version_ref",
				"",
				update_modified=False,
			)
			for std_name in saved_std_codes:
				frappe.db.set_value(
					"STD Template",
					std_name,
					"template_code",
					f"{std_name}-P3-005-HIDDEN",
					update_modified=False,
				)
			frappe.db.commit()

			out = validate_upstream_for_checkpoint("READY_FOR_RELEASE")
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("error_code"), "MISSING_STD_VERSION")

			loader_out = seed_procurement_planning_works_master(checkpoint="READY_FOR_RELEASE")
			self.assertFalse(loader_out.get("ok"))
			self.assertEqual(loader_out.get("error_code"), "MISSING_STD_VERSION")
		finally:
			frappe.db.set_value(
				"Procurement Journey",
				JOURNEY_CODE,
				"std_template_version_ref",
				journey_std_ref or STD_VERSION_CODE,
				update_modified=False,
			)
			for std_name, code in saved_std_codes.items():
				frappe.db.set_value(
					"STD Template", std_name, "template_code", code, update_modified=False
				)
			from kentender_procurement.tender_management.seeds.works_master_std_seed import (
				upsert_works_master_std,
			)

			upsert_works_master_std()
			frappe.db.commit()

	def test_009_missing_tender_at_consumed_by_tender(self):
		"""SEED-TEST-P3-005-009: CONSUMED_BY_TENDER without TND returns MISSING_TENDER."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		_ensure_master_tender_for_upstream()
		hidden_tender_code = "TND-P3-005-HIDDEN"
		try:
			if frappe.db.exists("TM2 Tender", TENDER_CODE):
				frappe.rename_doc("TM2 Tender", TENDER_CODE, hidden_tender_code, force=True)
				frappe.db.set_value(
					"TM2 Tender",
					hidden_tender_code,
					"tender_code",
					hidden_tender_code,
					update_modified=False,
				)
				frappe.db.commit()

			out = validate_upstream_for_checkpoint("CONSUMED_BY_TENDER")
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("error_code"), "MISSING_TENDER")

			loader_out = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
			self.assertFalse(loader_out.get("ok"))
			self.assertEqual(loader_out.get("error_code"), "MISSING_TENDER")
		finally:
			if frappe.db.exists("TM2 Tender", hidden_tender_code):
				frappe.rename_doc("TM2 Tender", hidden_tender_code, TENDER_CODE, force=True)
				frappe.db.set_value(
					"TM2 Tender",
					TENDER_CODE,
					"tender_code",
					TENDER_CODE,
					update_modified=False,
				)
				frappe.db.commit()
			_restore_master_tender()

	def test_010_validator_fail_fast_on_missing_upstream(self):
		"""SEED-TEST-P3-005-010: Validator aborts before VAL checks when upstream missing."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		demand_name = _demand_doc_name()
		try:
			if demand_name:
				frappe.delete_doc("Demand", demand_name, force=True, ignore_permissions=True)
				frappe.db.commit()

			out = validate_procurement_planning_works_master_seed(checkpoint="CONSUMED_BY_TENDER")
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("error_code"), "MISSING_DEMAND")
			self.assertEqual(out.get("checks"), [])
			self.assertEqual(out.get("passed"), 0)
			self.assertEqual(out.get("failed"), 0)
		finally:
			_restore_master_demand()
