"""An author's unsent Draft successor stays private (AUD-NDS-003).

NDS v1.16 §6.1 and OVS v0.6 §4.1: "unsent author Draft access remains
unchanged". An Accepted Need whose author is drafting an update is readable
by the Planner and by the AO/HOPF (as an observer); the Draft's content is not
theirs to read, only the accepted requirement is.
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.departmental_needs.seeds import profiles
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	AUTHOR,
	PLANNER,
	REVIEWER,
	upsert_departmental_needs,
)
from kentender_procurement.departmental_needs.services import lifecycle, workspace
from kentender_procurement.departmental_needs.tests import support
from kentender_procurement.departmental_needs.tests.test_ovs_needs_reads import AO, HOPF

ACCEPTED_NEED = "NDS-MOH-2027-0001"
PRIVATE_TITLE = "Private draft title nobody else may read"

CONTENT = {
	"description": "Laptop computers for deployment at priority health facilities.",
	"expected_operational_result": "Facilities can use the deployed digital health services.",
	"indicative_quantity": 10,
	"unit": "Each",
	"estimated_total_cost": 1000000,
	"required_by_date": "2027-12-31",
}


class TestUnsentSuccessorDraftStaysPrivate(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()
		support.ensure_transitional_reviewer_grant(cls)

	def key(self) -> str:
		return f"nds-unsent-{uuid4().hex}"

	def setUp(self):
		super().setUp()
		self.addCleanup(frappe.set_user, "Administrator")
		self.addCleanup(profiles.reset_profile, "successor")
		frappe.set_user(AUTHOR)
		version = frappe.db.get_value("Departmental Need", ACCEPTED_NEED, "record_version")
		opened = lifecycle.create_accepted_need_successor(
			need=ACCEPTED_NEED, expected_version=version, idempotency_key=self.key()
		)
		profiles._namespace("Departmental Need Revision", opened["successor_revision"], profiles.NS_SUCCESSOR)
		lifecycle.update_need(
			need=ACCEPTED_NEED,
			expected_version=opened["record_version"],
			idempotency_key=self.key(),
			title=PRIVATE_TITLE,
			**CONTENT,
		)
		frappe.set_user("Administrator")

	def test_the_planner_and_the_oversight_offices_do_not_receive_the_draft(self):
		"""AUD-NDS-003."""
		for user in (PLANNER, AO, HOPF):
			with self.subTest(user=user):
				record = workspace.get_need(need=ACCEPTED_NEED, user=user)
				self.assertNotEqual(record["current_revision"].get("title"), PRIVATE_TITLE)
				self.assertNotIn(PRIVATE_TITLE, str(record))
				listed = workspace.get_workspace(user=user)
				self.assertNotIn(PRIVATE_TITLE, str(listed["needs"]))

	def test_the_author_and_the_head_of_department_still_read_it(self):
		for user in (AUTHOR, REVIEWER):
			with self.subTest(user=user):
				record = workspace.get_need(need=ACCEPTED_NEED, user=user)
				self.assertEqual(record["current_revision"]["title"], PRIVATE_TITLE)
