# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 19.4 and 19.5 (plan Phase 4, gate CM-G04, tracker CM8-402; CM-AC-65 started): the generated agreement keeps the issued Form No. 4 exactly and fills only its declared insertions, and
each certificate and decision output carries the specification's required statement word for word. Conformance here means what is checked: the **text** the specification fixes. The layout, the frozen header and
the evidence manifest of each output are not yet conformance-tested (recorded in the tracker); nothing here claims a renderer conformance result for a production template."""

from __future__ import annotations

import re
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_contracts.boards import statements
from kentender_contracts.services import source_package
from kentender_contracts.simulation import sources

SPEC = Path(frappe.get_app_path("kentender_contracts")).resolve().parents[1] / "docs/mvp-1-r1/21_contract_management/KenTender_CM-CHG-001_Contract_Management_v0_8.md"
INSERTION = re.compile(r'<span data-insertion="([a-z_]+)">.*?</span>', re.S)
VALUES = {"agreement_date": "2 July 2027", "entity_name": "Ministry of Health", "entity_address": "Afya House, Nairobi", "supplier_name": "Afya Digital Supplies Limited", "goods": "10 laptops",
	"amount": "KES 1,000,000, tax included", "documents": "Form No. 4, Price schedule", "entity_signatory": "Amina Hassan, Accounting Officer", "supplier_signatory": "Mary Wanjiku, Authorised signatory"}


def spec_statement(first_cell: str) -> str:
	"""The quoted statement in the row of the section 19.5 table whose first cell starts with `first_cell`."""
	text = SPEC.read_text()
	table = text[text.index("### 19.5 Certificate and decision outputs"):text.index("**Amendment execution output.**")]
	for line in table.splitlines():
		if line.startswith("| " + first_cell):
			match = re.search(r"“([^”]+)”", line)
			if match:
				return match.group(1)
	raise AssertionError(f"no quoted statement in the section 19.5 row for {first_cell}")


class TestCertificateStatements(IntegrationTestCase):
	def test_every_required_statement_is_the_specifications_own_words(self):
		for output, (template, placeholders) in statements.OUTPUTS.items():
			written = template
			for name, text in placeholders.items():
				written = written.replace("{" + name + "}", text)
			quoted = spec_statement({"technical certificate": "Technical quality/quantity certificate", "acceptance report": "Inspection and acceptance report", "invoice certification": "Procurement invoice certification", "final acceptance": "Final-acceptance record",
				"completion certificate": "Noncomplex completion certificate", "close-out decision": "AO close-out decision"}[output])
			self.assertEqual(" ".join(written.split()), " ".join(quoted.split()), output)

	def test_the_templates_carry_only_the_placeholders_the_specification_writes(self):
		for output, (template, placeholders) in statements.OUTPUTS.items():
			self.assertEqual(set(re.findall(r"\{(\w+)\}", template)), set(placeholders), output)


class TestAgreementRendering(IntegrationTestCase):
	def form(self) -> str:
		return sources._content("S7", sources.CASE).decode()

	def test_only_the_declared_insertions_change_and_the_issued_text_is_kept_exactly(self):
		form = self.form()
		rendered, missing = source_package.render(form, VALUES)
		self.assertEqual(missing, [])
		bare = lambda text: INSERTION.sub(lambda m: f"<<{m.group(1)}>>", text)
		self.assertEqual(bare(rendered), bare(form), "everything outside the insertions is the issued Form No. 4, byte for byte")
		for key, value in VALUES.items():
			self.assertIn(f'<span data-insertion="{key}">{value}</span>', rendered)

	def test_an_empty_insertion_is_reported_and_left_unfilled_never_guessed(self):
		rendered, missing = source_package.render(self.form(), {**VALUES, "entity_signatory": ""})
		self.assertEqual(missing, ["entity_signatory"])
		self.assertIn("{{entity_signatory}}", rendered)

	def test_a_value_is_escaped_and_cannot_add_text_to_the_agreement(self):
		rendered, _ = source_package.render(self.form(), {**VALUES, "goods": "<script>x</script> 10 laptops"})
		self.assertNotIn("<script>", rendered)
		self.assertIn("&lt;script&gt;", rendered)

	def test_the_digest_follows_the_content_and_nothing_else(self):
		from kentender_contracts.services import records

		one, _ = source_package.render(self.form(), VALUES)
		same, _ = source_package.render(self.form(), dict(reversed(list(VALUES.items()))))
		other, _ = source_package.render(self.form(), {**VALUES, "amount": "KES 1,000,001, tax included"})
		self.assertEqual(records.digest(one), records.digest(same))
		self.assertNotEqual(records.digest(one), records.digest(other))
