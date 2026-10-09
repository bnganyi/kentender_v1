"""A recorded fact beside the pack's figure style is one shared class, not a copy per module.

`.kt-meta-value` is the pack's figure style (heading face, 18px). A fact a board draws as plain text takes
`.is-plain`, defined once in the generated Industry stylesheet. Planning once carried its own scoped copy of the
rule and ten inline 14px overrides; this fails if a Planning screen or stylesheet sets a fact's size itself again."""

import re
from pathlib import Path

from frappe.tests.utils import FrappeTestCase

ROOT = Path(__file__).resolve().parents[3]
PLANNING_JS = ROOT / "kentender_procurement/kentender_procurement/public/js/procurement_planning"
PLANNING_CSS = ROOT / "kentender_procurement/kentender_procurement/public/css/procurement_planning_industry.css"
TOKENS = ROOT / "kentender_core/kentender_core/public/css/kt_industry_tokens.css"


class TestFactStyleIsShared(FrappeTestCase):
	def test_the_shared_stylesheet_defines_the_plain_fact(self):
		css = TOKENS.read_text(encoding="utf-8")
		rule = re.search(r"\.kt-industry \.kt-meta-value\.is-plain \{([^}]*)\}", css)
		self.assertTrue(rule, "the plain fact style must be in kt_industry_tokens.css")
		self.assertIn("font-size: 14px", rule.group(1))
		self.assertIn("font-weight: 400", rule.group(1))

	def test_planning_sets_no_fact_size_of_its_own(self):
		css = PLANNING_CSS.read_text(encoding="utf-8")
		for block in re.findall(r"([^{}]*\.kt-meta-value[^{}]*)\{([^}]*)\}", css):
			selector, body = block
			self.assertNotRegex(body, r"font-(size|family|weight)\s*:", f"{selector.strip()} resizes a fact; use is-plain")

	def test_no_planning_screen_resizes_a_fact_inline(self):
		offenders = []
		for path in sorted(PLANNING_JS.rglob("*.vue")):
			for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
				if re.search(r'kt-meta-value[^>]*style="[^"]*font-size', line):
					offenders.append(f"{path.name}:{number}")
		self.assertEqual(offenders, [])
