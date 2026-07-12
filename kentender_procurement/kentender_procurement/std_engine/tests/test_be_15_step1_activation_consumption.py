# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-15 — Step 1 activation, consumption, render, and NSSF calibration contracts."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from unittest.mock import patch

from kentender_core.seeds.stable_platform_seed.constants import IT_PKG_CODE, IT_STD_VERSION_CODE
from kentender_procurement.std_engine.api.governance_api import get_activation_readiness
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID, NSSF_FIXTURE_CODE
from kentender_procurement.std_engine.fixtures.nssf_calibration_fixture_loader import (
	load_nssf_calibration_fixture,
)
from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter
from kentender_procurement.std_engine.package_import.draft_cleanup import (
	clear_draft_package_state,
	force_reset_package_state_for_tests,
)
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path_v1_1
from kentender_procurement.std_engine.services.activation_readiness_service import (
	evaluate_activation_readiness,
	sync_activation_flags,
)
from kentender_procurement.std_engine.services.activation_service import activate_version
from kentender_procurement.std_engine.services.legal_review_service import approve_all_pending
from kentender_procurement.std_engine.services.render_service import (
	compute_render_hash,
	probe_all_render_blocks,
	render_block_preview,
	render_section_preview,
)
from kentender_procurement.std_engine.services.tender_binding_service import (
	assert_std_template_bindable,
	assert_version_is_bindable,
	bind_consumer,
	bind_nssf_calibration_fixture,
)


class TestBe15Step1ActivationConsumption(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		force_reset_package_state_for_tests(CANONICAL_PACKAGE_ID, family_code="KE-PPRA-IT")
		CommitImporter(default_seed_zip_path_v1_1(), default_official_pdf_path()).run()
		frappe.set_user("Administrator")

	@classmethod
	def tearDownClass(cls) -> None:
		force_reset_package_state_for_tests(CANONICAL_PACKAGE_ID, family_code="KE-PPRA-IT")
		super().tearDownClass()

	def _ensure_draft_import(self) -> None:
		force_reset_package_state_for_tests(CANONICAL_PACKAGE_ID, family_code="KE-PPRA-IT")
		CommitImporter(default_seed_zip_path_v1_1(), default_official_pdf_path()).run()

	def _approve_ready(self) -> None:
		approve_all_pending(CANONICAL_PACKAGE_ID)
		sync_activation_flags(CANONICAL_PACKAGE_ID)

	def test_std_smoke_021_readiness_before_and_after_legal_approval(self) -> None:
		self._ensure_draft_import()
		before = evaluate_activation_readiness(CANONICAL_PACKAGE_ID)
		self.assertFalse(before.get("activationAllowed"))
		self.assertFalse(before.get("legalReviewComplete"))

		self._approve_ready()
		after = evaluate_activation_readiness(CANONICAL_PACKAGE_ID)
		self.assertTrue(after.get("legalReviewComplete"))
		self.assertTrue(after.get("activationAllowed"))

		api_payload = get_activation_readiness(CANONICAL_PACKAGE_ID)
		self.assertTrue(api_payload.get("ok"))
		self.assertTrue(api_payload.get("data", {}).get("activationAllowed"))

	def test_std_smoke_022_activate_promotes_to_active(self) -> None:
		self._approve_ready()
		result = activate_version(CANONICAL_PACKAGE_ID)
		self.assertTrue(result.get("ok"))
		self.assertEqual(
			frappe.db.get_value("STD Version", CANONICAL_PACKAGE_ID, "lifecycle_state"),
			"ACTIVE",
		)
		second = activate_version(CANONICAL_PACKAGE_ID)
		self.assertTrue(second.get("ok"))

	def test_std_smoke_023_active_package_rejects_draft_cleanup(self) -> None:
		self._approve_ready()
		activate_version(CANONICAL_PACKAGE_ID)
		with self.assertRaises(ValueError):
			clear_draft_package_state(CANONICAL_PACKAGE_ID, family_code="KE-PPRA-IT")

	def test_std_smoke_024_bind_to_active_succeeds(self) -> None:
		self._approve_ready()
		activate_version(CANONICAL_PACKAGE_ID)
		result = bind_consumer(
			CANONICAL_PACKAGE_ID,
			consumer_type="PROCUREMENT_PACKAGE",
			consumer_code=IT_PKG_CODE,
		)
		self.assertTrue(result.get("ok"))
		self.assertEqual(result.get("bindMode"), "ACTIVE")

	def test_std_smoke_025_test_mode_bind_requires_flag(self) -> None:
		self._ensure_draft_import()
		self._approve_ready()
		with patch(
			"kentender_procurement.std_engine.services.tender_binding_service._site_allows_test_binding",
			return_value=False,
		):
			with self.assertRaises(frappe.ValidationError):
				bind_consumer(
					CANONICAL_PACKAGE_ID,
					consumer_type="TEST_FIXTURE",
					consumer_code="TEST-UNREADY",
					simulate_active_for_test=False,
				)
		result = bind_consumer(
			CANONICAL_PACKAGE_ID,
			consumer_type="TEST_FIXTURE",
			consumer_code="TEST-READY",
			simulate_active_for_test=True,
		)
		self.assertEqual(result.get("bindMode"), "TEST_MODE")

	def test_std_smoke_026_render_itt_block_contains_verbatim_fragment(self) -> None:
		self._approve_ready()
		activate_version(CANONICAL_PACKAGE_ID)
		itt_section = frappe.db.get_value(
			"STD Section",
			{"package_id": CANONICAL_PACKAGE_ID, "section_key": ["like", "%.section.itt"]},
			"name",
		)
		self.assertTrue(itt_section)
		sample_clause = frappe.db.get_value(
			"STD Clause",
			{"package_id": CANONICAL_PACKAGE_ID, "section": itt_section},
			"clause_text",
		)
		self.assertTrue(sample_clause)
		preview = render_section_preview(CANONICAL_PACKAGE_ID, itt_section)
		self.assertIn("DRAFT PREVIEW", preview.get("html") or "")
		self.assertTrue(len(preview.get("html") or "") > len(sample_clause) // 2)

	def test_std_smoke_027_render_hash_is_deterministic(self) -> None:
		self._approve_ready()
		activate_version(CANONICAL_PACKAGE_ID)
		itt_section = frappe.db.get_value(
			"STD Section",
			{"package_id": CANONICAL_PACKAGE_ID, "section_key": ["like", "%.section.itt"]},
			"name",
		)
		first = render_section_preview(CANONICAL_PACKAGE_ID, itt_section)
		second = render_section_preview(CANONICAL_PACKAGE_ID, itt_section)
		self.assertEqual(first.get("renderHash"), second.get("renderHash"))
		self.assertEqual(first.get("renderHash"), compute_render_hash(first.get("html") or ""))

	def test_std_smoke_028_all_render_blocks_probe(self) -> None:
		self._approve_ready()
		activate_version(CANONICAL_PACKAGE_ID)
		probe = probe_all_render_blocks(CANONICAL_PACKAGE_ID)
		self.assertGreaterEqual(probe.get("total", 0), 17)
		self.assertEqual(probe.get("passed"), probe.get("total"))

	def test_cal_nssf_001_fixture_import_without_master_mutation(self) -> None:
		clause_count_before = frappe.db.count("STD Clause", {"package_id": CANONICAL_PACKAGE_ID})
		result = load_nssf_calibration_fixture(force_reload=True)
		self.assertTrue(result.get("ok"))
		clause_count_after = frappe.db.count("STD Clause", {"package_id": CANONICAL_PACKAGE_ID})
		self.assertEqual(clause_count_before, clause_count_after)
		self.assertTrue(frappe.db.exists("STD Usage Binding", f"FIXTURE-{NSSF_FIXTURE_CODE}"))

	def test_cal_nssf_002_golden_bind(self) -> None:
		self._approve_ready()
		activate_version(CANONICAL_PACKAGE_ID)
		load_nssf_calibration_fixture(force_reload=True)
		result = bind_nssf_calibration_fixture(CANONICAL_PACKAGE_ID)
		self.assertTrue(result.get("ok"))
		self.assertEqual(result.get("consumerCode"), NSSF_FIXTURE_CODE)
		self.assertEqual(result.get("bindMode"), "ACTIVE")
		meta = frappe.db.get_value(
			"STD Usage Binding",
			result.get("bindingKey"),
			"metadata_json",
		)
		self.assertIn(IT_STD_VERSION_CODE, meta or "")

	def test_cal_nssf_003_tds_values_validate_against_fixture(self) -> None:
		load_nssf_calibration_fixture(force_reload=True)
		meta_raw = frappe.db.get_value(
			"STD Usage Binding",
			f"FIXTURE-{NSSF_FIXTURE_CODE}",
			"metadata_json",
		)
		self.assertIn("TDS-04", meta_raw or "")
		self.assertIn("NSSFSPS/ICT/ERP/001/2025-2026", meta_raw or "")

	def test_cal_nssf_012_render_uses_official_locked_text(self) -> None:
		self._approve_ready()
		activate_version(CANONICAL_PACKAGE_ID)
		block = frappe.db.get_value(
			"STD Render Block",
			{"package_id": CANONICAL_PACKAGE_ID, "object_key": ["like", "%.render.itt"]},
			"render_block_key",
		)
		self.assertTrue(block)
		preview = render_block_preview(CANONICAL_PACKAGE_ID, block)
		self.assertNotIn("WARNING_LOCKED_ITT_TEXT_COMPRESSED", preview.get("html") or "")

	def test_cal_nssf_013_fixture_activation_blocked(self) -> None:
		with self.assertRaises(frappe.ValidationError):
			activate_version(NSSF_FIXTURE_CODE)

	def test_pkg_moh_it_std_bindable_helper(self) -> None:
		self._approve_ready()
		activate_version(CANONICAL_PACKAGE_ID)
		result = assert_std_template_bindable(IT_STD_VERSION_CODE)
		self.assertTrue(result.get("bindable"))

	def test_assert_version_is_bindable_after_activation(self) -> None:
		self._approve_ready()
		activate_version(CANONICAL_PACKAGE_ID)
		result = assert_version_is_bindable(CANONICAL_PACKAGE_ID)
		self.assertTrue(result.get("bindable"))
