"""PLN-CHG-001 v1.18 §5.5.1B / RI-040 — `upsert_notification_log`: one
evolving notice per correlation key, updated in place, resolved without
deletion.

Lives apart from `test_notification_service.py`, whose legacy
`FrappeTestCase` base trips this site's pre-existing Fiscal Year overlap
while creating framework test records (plan C18).

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_notification_upsert
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.notification_service import upsert_notification_log

KEY = "kt-test:upsert:item-1:invitation"


class TestUpsertNotificationLog(IntegrationTestCase):
	def tearDown(self):
		for name in frappe.get_all("Notification Log", filters={"email_header": ("like", KEY + "%")}, pluck="name"):
			frappe.delete_doc("Notification Log", name, force=True, ignore_permissions=True)

	def test_upsert_updates_the_same_notice_in_place(self):
		common = dict(
			for_user="Administrator", document_type="", document_name="", event_type="milestone",
			entity_scope="PE-MOH", route="/desk/procurement-planning", correlation_key=KEY,
		)
		first = upsert_notification_log(subject="Due in 7 days", message="Invitation due 1 May 2027.", **common)
		self.assertTrue(first)
		second = upsert_notification_log(subject="Scheduled date passed — actual not recorded", message="Invitation was due 1 May 2027.", **common)
		self.assertEqual(first, second)
		self.assertEqual(frappe.db.count("Notification Log", {"email_header": KEY}), 1)
		row = frappe.db.get_value("Notification Log", first, ["subject", "read"], as_dict=True)
		self.assertEqual(row.subject, "Scheduled date passed — actual not recorded")
		self.assertEqual(int(row.read), 0)
		resolved = upsert_notification_log(subject="Resolved", message="Actual recorded.", active=False, **common)
		self.assertEqual(resolved, first)
		self.assertEqual(int(frappe.db.get_value("Notification Log", first, "read")), 1)
		# Resolving a notice that never existed creates nothing.
		self.assertIsNone(upsert_notification_log(subject="x", message="y", active=False, **{**common, "correlation_key": KEY + ":never"}))
