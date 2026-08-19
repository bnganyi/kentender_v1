from pathlib import Path

from frappe.tests import UnitTestCase


ROOT = Path(__file__).resolve().parents[2]


class TestDepartmentalNeedsUIContract(UnitTestCase):
	def test_workspace_assets_and_canonical_route(self):
		js = (ROOT / "public/js/departmental_needs_page.js").read_text()
		css = (ROOT / "public/css/departmental_needs.css").read_text()
		self.assertIn('const PAGE = "departmental-needs"', js)
		self.assertIn("/desk/departmental-needs", js)
		self.assertNotIn("/app/departmental-needs", js)
		for copy in ("Capture and review departmental requirements for procurement planning.", "Awaiting departmental review", "Accepted for planning", "Planning usage"):
			self.assertIn(copy, js)
		self.assertIn("@media(max-width:599px)", css)
