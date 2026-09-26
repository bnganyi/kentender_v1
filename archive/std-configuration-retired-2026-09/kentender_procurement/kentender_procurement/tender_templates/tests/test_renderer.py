# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-TPL-001 v0.5 §15 item 11 / TPR-CHG-001 v0.6 §18 layer 4 — render
tests: exact reproduction of both Ministry of Health fixture outputs, the
Invitation/issued-Tender boundary (TPR-AC-035), the five reservation renders
(TPR-AC-041), the internal-only absence (TPR-AC-044, SMOKE-20), strict
failure on a missing key, and the convenience PDF (TPR-AC-039)."""

from __future__ import annotations

import copy
import json

from frappe.tests import IntegrationTestCase
from jinja2 import UndefinedError

from kentender_procurement.tender_templates import checks, loader, renderer


def _fixture() -> dict:
	return json.loads(loader.read_text("fixtures/moh_input.json"))


class TestExactReproduction(IntegrationTestCase):
	def test_the_invitation_renders_exactly_the_fixture(self):
		self.assertEqual(renderer.render_invitation(_fixture()), loader.read_text("fixtures/moh_invitation_expected.html"))

	def test_the_issued_tender_renders_exactly_the_fixture(self):
		self.assertEqual(renderer.render_issued_tender(_fixture()), loader.read_text("fixtures/moh_expected.html"))

	def test_render_both_is_clean_and_digests_are_separate(self):
		out = renderer.render_both(_fixture())
		self.assertEqual(out["problems"], [])
		self.assertNotEqual(out["invitation_digest"], out["issued_tender_digest"])
		self.assertTrue(checks.invitation_absent_from_issued_tender(out["issued_tender_html"]))

	def test_every_stable_id_is_published_exactly_once_in_section_v(self):
		html = renderer.render_issued_tender(_fixture())
		section_v = html.split("Section V - Schedule of Requirements</h2>", 1)[1].split("Section VI - General Conditions of Contract</h2>", 1)[0]
		for i in range(1, 12):
			self.assertEqual(section_v.count(f"TECH-{i:03d}"), 1, f"TECH-{i:03d}")
		for i in range(1, 6):
			self.assertEqual(section_v.count(f"ACC-{i:03d}"), 1, f"ACC-{i:03d}")
		self.assertIn("RQI-001, RQI-002", section_v)
		self.assertIn(">250<", section_v)


class TestReservationRendering(IntegrationTestCase):
	def test_none_renders_no_clause(self):
		html = renderer.render_issued_tender(_fixture())
		self.assertNotIn("Reserved procurement under regulation 149", html)
		self.assertIn("Tendering is open to all qualified and interested Tenderers.", renderer.render_invitation(_fixture()))

	def test_each_supported_category_renders_one_fixed_clause(self):
		for category in ("Youth", "Women", "Persons with disabilities", "Other disadvantaged group"):
			ctx = _fixture()
			ctx["reservation"]["category"] = category
			html = renderer.render_issued_tender(ctx)
			self.assertEqual(html.count("Reserved procurement under regulation 149"), 1, category)
			self.assertIn(f"in the category <strong>{category}</strong>", html)
			invitation = renderer.render_invitation(ctx)
			self.assertIn("reserved under regulation 149", invitation)
			self.assertEqual(renderer.render_both(ctx)["problems"], [], category)


class TestInternalOnlyAbsence(IntegrationTestCase):
	def test_strategic_objective_and_plan_horizon_never_reach_either_output(self):
		ctx = _fixture()
		ctx["_internal"] = {
			"strategic_objective_path": "Digital health systems › Health policy, standards and regulation › Digital health governance",
			"plan_horizon": "Single year", "multi_year_justification": "A multi-year justification that must never render",
		}
		out = renderer.render_both(ctx)
		self.assertEqual(out["problems"], [])
		for html in (out["invitation_html"], out["issued_tender_html"]):
			self.assertEqual(checks.internal_only_leaks(html, ctx), [])
			self.assertNotIn("Digital health governance", html)

	def test_an_internal_key_passed_at_top_level_is_stripped_before_the_template(self):
		ctx = _fixture()
		ctx["_strategic_objective"] = "must not be visible"
		self.assertNotIn("must not be visible", renderer.render_issued_tender(ctx))


class TestStrictness(IntegrationTestCase):
	def test_a_missing_key_fails_the_render(self):
		ctx = copy.deepcopy(_fixture())
		del ctx["tender"]["reference"]
		with self.assertRaises(UndefinedError):
			renderer.render_invitation(ctx)

	def test_unresolved_authoring_content_is_detected(self):
		self.assertTrue(checks.unresolved_content("<p>[insert the date]</p>"))
		self.assertTrue(checks.unresolved_content("<p>{{ tender.title }}</p>"))
		self.assertEqual(checks.unresolved_content("<p>Clean.</p>"), [])


class TestConveniencePdf(IntegrationTestCase):
	def test_the_pdf_is_produced_from_the_same_html(self):
		html = renderer.render_invitation(_fixture())
		pdf = renderer.to_pdf(html)
		self.assertTrue(pdf.startswith(b"%PDF"))
		self.assertGreater(len(pdf), 5_000)
