"""The access state is one component kept as a copy in every app, because a Vue component cannot cross a bundle boundary
(AGENTS.md section 6.6). Copies are only safe while they are identical, so this fails the moment one drifts."""

from pathlib import Path

from frappe.tests.utils import FrappeTestCase

ROOT = Path(__file__).resolve().parents[3]
COPIES = (
	"kentender_core/kentender_core/public/js/access_shared/AccessDenied.vue",
	"kentender_strategy/kentender_strategy/public/js/strategy_shared/components/AccessDenied.vue",
	"kentender_budget/kentender_budget/public/js/budget_shared/components/AccessDenied.vue",
	"kentender_procurement/kentender_procurement/public/js/access_shared/AccessDenied.vue",
)


class TestAccessDeniedCopies(FrappeTestCase):
	def test_every_copy_is_identical(self):
		texts = {path: (ROOT / path).read_text(encoding="utf-8") for path in COPIES}
		reference = texts[COPIES[0]]
		drifted = [path for path, text in texts.items() if text != reference]
		self.assertEqual(drifted, [], "AccessDenied.vue differs from the core copy; change all four together")

	def test_the_state_uses_the_packs_access_classes(self):
		text = (ROOT / COPIES[0]).read_text(encoding="utf-8")
		for needle in ("kt-empty kt-access", "kt-spot is-neutral", 'role="alert"'):
			self.assertIn(needle, text)
