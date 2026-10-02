# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A revealed bid shows a table answer (release 1.4) as a table with the published
column headings, and says whose business profile each row of answers is when the
published definition repeats a group per entity. A package without either renders
exactly as before."""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.bid_opening.services import package_renderer

DIRECTORS = [{"name": "Mary Wanjiku", "nationality": "Kenyan", "citizenship": "Kenyan", "shares": "60.00"}, {"name": "John Kamau", "nationality": "Kenyan", "citizenship": "Kenyan", "shares": "40.00"}]
LABELS = {
	"tasks": {"TASK-COMPANY": "Company"},
	"responses": {"R-STRUCTURE": "Business structure", "R-DIRECTORS": "Directors", "R-PORTS": "Ports"},
	"columns": {"R-DIRECTORS": [{"key": "name", "label": "Name"}, {"key": "nationality", "label": "Nationality"}, {"key": "citizenship", "label": "Citizenship"}, {"key": "shares", "label": "Shares owned (%)"}]},
	"entity_responses": ["R-STRUCTURE", "R-DIRECTORS"],
}


def body(**extra):
	return {
		"schema": package_renderer.SCHEMA, "tender": {"tender_reference": "TND-1"},
		"bid": {"tenderer_name": "Afya JV", "members": [{"organisation_id": "ORG-A", "legal_name": "Afya Digital Supplies Limited"}, {"organisation_id": "ORG-B", "legal_name": "Kisiwa Tech Limited"}]},
		"organisation_snapshot": {"facts": {"organisation": {"organisation_id": "ORG-A", "legal_name": "Afya Digital Supplies Limited"}}},
		"responses": [
			{"response_id": "R-STRUCTURE", "field_key": "business_structure", "task": "company", "member": "ORG-A", "value": "Registered company"},
			{"response_id": "R-DIRECTORS", "field_key": "directors", "task": "company", "member": "ORG-A", "value": DIRECTORS},
			{"response_id": "R-STRUCTURE", "field_key": "business_structure", "task": "company", "member": "ORG-B", "value": "Sole proprietor"},
			{"response_id": "R-PORTS", "field_key": "ports", "task": "company", "member": "", "value": [{"port_type": "USB-C", "count": 2}]},
		],
		"price": {"currency": "KES", "total": "1.00", "lines": []}, "evidence": [], "signatory": {}, **extra,
	}


def render(labels):
	return package_renderer.html_of(body(), envelope_id="ENV-1", receipt_reference="RCP-1", labels=labels)


class TestRowGroupRender(IntegrationTestCase):
	def test_a_table_answer_is_a_table_with_the_published_headings(self):
		html = render(LABELS)
		self.assertIn("<th>Shares owned (%)</th>", html)
		self.assertIn("<td>Mary Wanjiku</td><td>Kenyan</td><td>Kenyan</td><td>60.00</td>", html)
		self.assertNotIn("&quot;shares&quot;", html)  # no JSON

	def test_each_entitys_answers_name_the_entity(self):
		html = render(LABELS)
		self.assertIn("Business structure — Afya Digital Supplies Limited", html)
		self.assertIn("Business structure — Kisiwa Tech Limited", html)
		self.assertIn("Directors — Afya Digital Supplies Limited", html)

	def test_other_answers_render_as_before(self):
		html = render(LABELS)
		self.assertIn("<th>Ports</th>", html)  # not a per-entity answer: no suffix
		self.assertIn("{&quot;count&quot;: 2, &quot;port_type&quot;: &quot;USB-C&quot;}", html)  # a list of cells without columns keeps its JSON form

	def test_a_definition_without_tables_or_entities_renders_exactly_as_before(self):
		plain = {"tasks": LABELS["tasks"], "responses": LABELS["responses"]}
		html = render(plain)
		self.assertNotIn("—", html)
		self.assertIn("&quot;shares&quot;: &quot;60.00&quot;", html)
