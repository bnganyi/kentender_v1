# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Desk wiring assertions for ITW-08..15 (engine hydration checked separately)."""

from __future__ import annotations

import ast
from pathlib import Path

from frappe.tests import UnitTestCase

APP_ROOT = Path(__file__).resolve().parents[2]
HOOKS_PATH = APP_ROOT / "hooks.py"

REQUIRED_PAGE_JS = {
	"it-tender-configuration-price-schedule": "public/js/it_wizard_price_schedule_page.js",
	"it-tender-configuration-evaluation-setup": "public/js/it_wizard_evaluation_setup_page.js",
	"it-tender-configuration-forms-and-evidence": "public/js/it_wizard_forms_and_evidence_page.js",
	"it-tender-configuration-scc": "public/js/it_wizard_scc_page.js",
	"it-tender-configuration-validation-report": "public/js/it_wizard_validation_report_page.js",
	"it-tender-configuration-review-and-approval": "public/js/it_wizard_review_and_approval_page.js",
	"it-tender-configuration-render-preview": "public/js/it_wizard_render_preview_page.js",
	"it-tender-configuration-publication-readiness": "public/js/it_wizard_publication_readiness_page.js",
}

REQUIRED_API_METHODS = (
	"get_price_schedule_api",
	"save_price_schedule_api",
	"get_evaluation_setup_api",
	"save_evaluation_setup_api",
	"get_forms_and_evidence_api",
	"save_forms_and_evidence_api",
	"get_scc_api",
	"save_scc_api",
	"get_validation_report_api",
	"save_validation_report_api",
	"get_review_and_approval_api",
	"save_review_and_approval_api",
	"get_render_preview_api",
	"save_render_preview_api",
	"get_publication_readiness_api",
	"save_publication_readiness_api",
)

REQUIRED_STEP_CODES = (
	("wizard_price_schedule_service.py", "PRICE_SCHEDULE"),
	("wizard_evaluation_setup_service.py", "EVALUATION_SETUP"),
	("wizard_forms_evidence_service.py", "FORMS_AND_EVIDENCE"),
	("wizard_scc_service.py", "SCC"),
	("wizard_validation_report_service.py", "VALIDATION_REPORT"),
	("wizard_review_service.py", "REVIEW_AND_APPROVAL"),
	("wizard_render_preview_service.py", "RENDER_PREVIEW"),
	("wizard_publication_readiness_service.py", "PUBLICATION_READINESS"),
)


def _load_page_js_map() -> dict[str, str]:
	tree = ast.parse(HOOKS_PATH.read_text(encoding="utf-8"))
	for node in tree.body:
		if isinstance(node, ast.Assign):
			for target in node.targets:
				if isinstance(target, ast.Name) and target.id == "page_js":
					return ast.literal_eval(node.value)
	raise AssertionError("page_js not found in hooks.py")


class TestItWizardDownstreamDeskWiring(UnitTestCase):
	def test_engine_registers_downstream_routes_and_loader(self) -> None:
		engine = (APP_ROOT / "public" / "js" / "it_wizard_engine.js").read_text(encoding="utf-8")
		downstream = (APP_ROOT / "public" / "js" / "it_wizard_downstream.js").read_text(encoding="utf-8")
		self.assertIn("register_downstream", engine)
		self.assertIn("PRICE_SCHEDULE", engine)
		self.assertIn("PUBLICATION_READINESS", engine)
		self.assertIn("it-tender-configuration-price-schedule", engine)
		self.assertIn("get_price_schedule_api", downstream)
		self.assertIn("get_publication_readiness_api", downstream)
		self.assertIn("it_wizard_downstream.js", (APP_ROOT / "hooks.py").read_text(encoding="utf-8"))

	def test_all_eight_downstream_pages_registered_in_page_js(self) -> None:
		page_js = _load_page_js_map()
		for route, asset in REQUIRED_PAGE_JS.items():
			self.assertIn(route, page_js)
			self.assertEqual(page_js[route], asset)
			self.assertNotIn("?", page_js[route], "page_js must not include ?v= cache bust")

	def test_page_js_and_css_assets_exist_on_disk(self) -> None:
		for route, rel in REQUIRED_PAGE_JS.items():
			js_path = APP_ROOT / rel
			self.assertTrue(js_path.is_file(), f"missing {js_path} for {route}")
			slug = route.removeprefix("it-tender-configuration-").replace("-", "_")
			css_path = APP_ROOT / "public" / "css" / f"it_wizard_{slug}_page.css"
			self.assertTrue(css_path.is_file(), f"missing {css_path}")
			page_dir = APP_ROOT / "kentender_procurement" / "page" / f"it_tender_configuration_{slug}"
			self.assertTrue((page_dir / f"it_tender_configuration_{slug}.json").is_file())

	def test_api_methods_and_step_codes_exported_for_engine_wiring(self) -> None:
		api_text = (APP_ROOT / "it_tender_wizard" / "api" / "instance_api.py").read_text(encoding="utf-8")
		for method in REQUIRED_API_METHODS:
			self.assertIn(f"def {method}(", api_text)

		services = APP_ROOT / "it_tender_wizard" / "services"
		for filename, step_code in REQUIRED_STEP_CODES:
			text = (services / filename).read_text(encoding="utf-8")
			self.assertIn(f'STEP_CODE = "{step_code}"', text)
			self.assertIn(f"def get_", text)
			self.assertIn(f"def save_", text)
