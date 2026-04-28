from __future__ import annotations

from pathlib import Path
import unittest

import yaml


PACKAGE_ROOT = (
	Path(__file__).resolve().parents[2]
	/ "fixtures"
	/ "std_engine"
	/ "works_building_rev_apr_2022"
)


class TestSTDSeedPopulation0203(unittest.TestCase):
	def test_seed_files_are_no_longer_placeholder_scaffolds(self):
		for path in PACKAGE_ROOT.rglob("*.yaml"):
			if path.name == "00_manifest.yaml":
				continue
			text = path.read_text(encoding="utf-8")
			self.assertNotIn("Placeholder Scaffold", text, msg=str(path))

	def test_core_seed_files_have_structured_records(self):
		files = {
			"01_source_documents.yaml": "source_documents",
			"02_template_family.yaml": "template_families",
			"03_template_version.yaml": "template_versions",
			"04_applicability_profiles.yaml": "applicability_profiles",
			"05_parts.yaml": "parts",
			"06_sections.yaml": "sections",
			"11_boq/11a_boq_definition.yaml": "boq_definition",
			"15_readiness_rules.yaml": "readiness_rules",
			"16_seed_instance_fixture.yaml": "seed_instance_fixture",
		}
		for rel, top_key in files.items():
			data = yaml.safe_load((PACKAGE_ROOT / rel).read_text(encoding="utf-8"))
			self.assertIn(top_key, data, msg=rel)

	def test_legal_text_seed_files_mark_pending_extraction(self):
		files = [
			"07_clauses/07a_invitation_to_tender.yaml",
			"09_forms/09a_tendering_forms.yaml",
			"09_forms/09e_contract_forms.yaml",
		]
		for rel in files:
			text = (PACKAGE_ROOT / rel).read_text(encoding="utf-8")
			self.assertIn("text_verbatim: null", text, msg=rel)
			self.assertIn("extraction_status: Pending Human-Reviewed Extraction", text, msg=rel)

