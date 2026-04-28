# Copyright (c) 2026, KenTender and contributors

from __future__ import annotations

import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "std_engine" / "works_building_rev_apr_2022"
REQUIRED_FILES = [
	"00_manifest.yaml",
	"01_source_documents.yaml",
	"02_template_family.yaml",
	"03_template_version.yaml",
	"04_applicability_profiles.yaml",
	"05_parts.yaml",
	"06_sections.yaml",
	"07_clauses/07a_invitation_to_tender.yaml",
	"07_clauses/07b_section_i_itt.yaml",
	"07_clauses/07c_section_ii_tds.yaml",
	"07_clauses/07d_section_iii_evaluation.yaml",
	"07_clauses/07e_section_iv_forms_index.yaml",
	"07_clauses/07f_section_v_boq.yaml",
	"07_clauses/07g_section_vi_specifications.yaml",
	"07_clauses/07h_section_vii_drawings.yaml",
	"07_clauses/07i_section_viii_gcc.yaml",
	"07_clauses/07j_section_ix_scc.yaml",
	"07_clauses/07k_section_x_contract_forms.yaml",
	"08_parameters/08a_tender_identity.yaml",
	"08_parameters/08b_tds_parameters.yaml",
	"08_parameters/08c_scc_parameters.yaml",
	"08_parameters/08d_evaluation_parameters.yaml",
	"08_parameters/08e_boq_parameters.yaml",
	"08_parameters/08f_parameter_dependencies.yaml",
	"09_forms/09a_tendering_forms.yaml",
	"09_forms/09b_qualification_forms.yaml",
	"09_forms/09c_security_forms.yaml",
	"09_forms/09d_other_tender_forms.yaml",
	"09_forms/09e_contract_forms.yaml",
	"10_works_requirements.yaml",
	"11_boq/11a_boq_definition.yaml",
	"11_boq/11b_bills.yaml",
	"11_boq/11c_item_schema.yaml",
	"11_boq/11d_dayworks.yaml",
	"11_boq/11e_provisional_sums_and_summary.yaml",
	"12_evaluation_rules.yaml",
	"13_contract_carry_forward.yaml",
	"14_extraction_mappings/14a_bundle_mappings.yaml",
	"14_extraction_mappings/14b_dsm_mappings.yaml",
	"14_extraction_mappings/14c_dom_mappings.yaml",
	"14_extraction_mappings/14d_dem_mappings.yaml",
	"14_extraction_mappings/14e_dcm_mappings.yaml",
	"15_readiness_rules.yaml",
	"16_seed_instance_fixture.yaml",
	"17_generated_output_expectations.yaml",
	"18_addendum_fixture.yaml",
	"19_smoke_expected_results.yaml",
]
REQUIRED_MANIFEST_ENTRIES = [
	"01_source_documents.yaml",
	"02_template_family.yaml",
	"03_template_version.yaml",
	"04_applicability_profiles.yaml",
	"05_parts.yaml",
	"06_sections.yaml",
	"07_clauses",
	"08_parameters",
	"09_forms",
	"10_works_requirements.yaml",
	"11_boq",
	"12_evaluation_rules.yaml",
	"13_contract_carry_forward.yaml",
	"14_extraction_mappings",
	"15_readiness_rules.yaml",
	"16_seed_instance_fixture.yaml",
	"17_generated_output_expectations.yaml",
	"18_addendum_fixture.yaml",
	"19_smoke_expected_results.yaml",
]


class TestSTDSeedPackageStructure(unittest.TestCase):
	def test_seed_package_root_exists(self):
		self.assertTrue(PACKAGE_ROOT.exists())
		self.assertTrue(PACKAGE_ROOT.is_dir())

	def test_all_required_files_exist(self):
		missing = [rel for rel in REQUIRED_FILES if not (PACKAGE_ROOT / rel).exists()]
		self.assertEqual([], missing)

	def test_manifest_references_all_required_files(self):
		manifest_text = (PACKAGE_ROOT / "00_manifest.yaml").read_text(encoding="utf-8")
		for entry in REQUIRED_MANIFEST_ENTRIES:
			self.assertIn(f"  - {entry}", manifest_text)

