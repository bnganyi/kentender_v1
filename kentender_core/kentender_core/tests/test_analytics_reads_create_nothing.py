"""ANL-CHG-001 v0.8 §16, tracker rule 5 — a read creates nothing, through the real endpoint and the real owner providers.

Every tab is read as several real people on whatever the test site holds. The row counts of the tables a stray write would
touch (preferences, versions, comments, logs, the audit trail, and every module's decision rows) are the same before and after.
The owners' own provider tests prove the same per owner; this is the whole-page check (ANL8-0115).

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_analytics_reads_create_nothing
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.api import analytics as api
from kentender_core.services import analytics_workspace as aw

PEOPLE = ["Administrator", "charles.mutiso@moh.example.test", "amina.hassan@moh.example.test", "peter.kimani@moh.example.test",
	"daniel.otieno@moh.example.test", "nadia.kamau@moh.example.test", "Guest"]
WATCHED = ["DefaultValue", "Version", "Comment", "Error Log", "Activity Log", "Audit Event", "Departmental Need Decision",
	"Departmental Plan Validation Decision", "Requisition Decision", "Requisition Version", "Funding Reservation", "Tender Cancellation",
	"Award Decision", "Notification Log", "ToDo", "Event Sync Log"]


def _counts() -> dict[str, int]:
	return {dt: frappe.db.count(dt) for dt in WATCHED if frappe.db.exists("DocType", dt)}


class TestReadsCreateNothing(IntegrationTestCase):
	def test_every_tab_as_every_person_changes_no_table(self):
		before = _counts()
		self.assertGreaterEqual(len(before), 8, "the watched tables must exist")
		try:
			for person in PEOPLE:
				if person not in ("Administrator", "Guest") and not frappe.db.exists("User", person):
					continue
				frappe.set_user(person)
				for tab in aw.TABS:
					out = api.get_procurement_analytics(tab=tab)
					self.assertIn(out["verdict"], ("ok", "no_area", "denied"), f"{person} {tab}")
					api.get_procurement_analytics(tab=tab, search="x")
				fy = (api.get_procurement_analytics()["filters"]["fy_options"] or [{}])[0].get("id")
				if fy:
					api.get_procurement_analytics(fy=fy)
				api.get_analytics_access()
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(_counts(), before)

	def test_a_read_leaves_no_working_context_preference(self):
		frappe.set_user("Administrator")
		before = frappe.db.count("DefaultValue", {"defkey": ["like", "kt_%"]})
		api.get_procurement_analytics(tab="needs", fy="2027-2028" if frappe.db.exists("Fiscal Year", "2027-2028") else "")
		self.assertEqual(frappe.db.count("DefaultValue", {"defkey": ["like", "kt_%"]}), before)
