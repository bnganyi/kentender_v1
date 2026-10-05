# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ANL-CHG-001 v0.8 §4, §4A.2, §7.1 — the Departmental Needs feed to Analytics (`departmental_needs/services/analytics_provider.py`).

One shared world, built once in `setUpClass`: seven Needs under this module's own fixture namespace in Digital Health and
Human Resources Management and Development, one in every countable disposition plus a Draft and a Withdrawn one, with decision
rows at fixed instants (the provider reads rows, so they are inserted directly, as the Home provider test does), and three
test-only users granted a responsibility under the same namespace. The real seeded actors (Amina Hassan, Charles Mutiso, Naomi
Chebet, Mercy Kilonzo, Daniel Otieno, Brian Wafula) are read as themselves. Everything the class made is removed and counted.

Run:
  flock /tmp/kt-test-site.lock bench --site kentender-test.local run-tests --app kentender_procurement \\
    --module kentender_procurement.departmental_needs.tests.test_analytics_provider
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime

from kentender_core.services import analytics_contract as ac
from kentender_core.services import responsibility_administration as administration
from kentender_procurement.departmental_needs.constants import REASON_REQUIRED_ACTIONS
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import AUTHOR, DEPARTMENTAL_AUTHOR, upsert_departmental_needs, _granted_units
from kentender_procurement.departmental_needs.services import analytics_provider as provider

NS = "KT_TEST_NDSANL"
AO = "amina.hassan@moh.example.test"
HOPF = "charles.mutiso@moh.example.test"
AUDITOR = "naomi.chebet@moh.example.test"
PLANNER = "mercy.kilonzo@moh.example.test"
TECHNICAL_OPERATOR = "daniel.otieno@moh.example.test"
OFFICER = "brian.wafula@moh.example.test"  # a Procurement Officer: no Needs responsibility
AUTHOR_DH = "ndsa.author@example.test"  # Departmental Author, Digital Health; owns every fixture Need
HOD_DH = "ndsa.hod@example.test"  # Head of User Department, Digital Health
OTHER_AUTHOR_DH = "ndsa.other@example.test"  # Departmental Author, Digital Health, but owns nothing
USERS = (AUTHOR_DH, HOD_DH, OTHER_AUTHOR_DH)
PREFIX = "NDS-ANLT-"
REASON = "The fixture requirement needs a correction before it can be decided."

ACCEPTED_1 = datetime(2026, 11, 24, 11, 0)
ACCEPTED_2 = datetime(2026, 11, 24, 14, 0)
LATER_ACCEPTANCE = datetime(2026, 11, 24, 15, 0)  # a second "Accept for planning" row: only the first counts
SUCCESSOR_ACCEPTED = datetime(2026, 11, 20, 9, 0)  # an "Accept successor" row, dated even before the first acceptance: it is never one

TABLES = ("Departmental Need", "Departmental Need Revision", "Departmental Need Decision", "Departmental Need Review Task", "Need Withdrawal Request", "Departmental Need Event")


def _counts() -> dict[str, int]:
	counts = {doctype: frappe.db.count(doctype) for doctype in TABLES}
	counts["DefaultValue"] = frappe.db.count("DefaultValue")  # the working-context preference lives here
	counts["Notification Log"] = frappe.db.count("Notification Log")
	counts["assignments"] = frappe.db.count("User Responsibility Assignment")
	return counts


class TestNeedsAnalytics(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		upsert_departmental_needs()
		units = _granted_units(AUTHOR, DEPARTMENTAL_AUTHOR)
		cls.dh = units["Digital Health"]
		cls.hrmd = units["Human Resources Management and Development"]
		cls.remove_world(check=False)  # whatever a crashed earlier run left
		cls.before = _counts()
		cls.addClassCleanup(cls.remove_world)
		cls.build_users()
		cls.needs = cls.build_needs()
		frappe.db.commit()
		cls.at = now_datetime()

	# ----- the world -----

	@classmethod
	def build_users(cls) -> None:
		for email in USERS:
			frappe.get_doc({"doctype": "User", "email": email, "first_name": "NDSA " + email.split("@")[0], "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True).add_roles("Desk User")
		administration.grant(user=AUTHOR_DH, business_role="Departmental Author", organisation_unit=cls.dh, fixture_namespace=NS, actor="Administrator")
		administration.grant(user=OTHER_AUTHOR_DH, business_role="Departmental Author", organisation_unit=cls.dh, fixture_namespace=NS, actor="Administrator")
		administration.grant(user=HOD_DH, business_role="Head of User Department", organisation_unit=cls.dh, fixture_namespace=NS, actor="Administrator")

	@classmethod
	def make_need(cls, number: int, *, state: str, unit: str, title: str, revision_status: str, decisions: list[tuple[str, datetime]] = (), successor_title: str = "") -> str:
		reference = f"{PREFIX}{number:04d}"
		need = frappe.get_doc({
			"doctype": "Departmental Need", "need_reference": reference, "organisation_unit": unit, "financial_year": "2027-2028",
			"current_state": state, "record_version": 1, "fixture_namespace": NS,
		}).insert(ignore_permissions=True)
		revisions = [(1, revision_status, title)] + ([(2, "Draft", successor_title)] if successor_title else [])
		names = []
		for number_, status, text in revisions:
			names.append(frappe.get_doc({
				"doctype": "Departmental Need Revision", "need_revision_id": f"{reference}-V{number_}", "departmental_need": need.name, "revision_number": number_,
				"revision_status": status, "title": text, "description": "Procure and implement the analytics fixture requirement.",
				"expected_operational_result": "The department can operate the tested capability.", "indicative_quantity": 1, "unit": "Each",
				"required_by_date": "2027-12-31", "fixture_namespace": NS,
			}).insert(ignore_permissions=True).name)
		accepted = names[0] if revision_status == "Accepted" else None
		frappe.db.set_value("Departmental Need", need.name, {"owner": AUTHOR_DH, "current_revision": names[-1], "current_accepted_revision": accepted}, update_modified=False)
		for index, (action, at) in enumerate(decisions):
			frappe.get_doc({
				"doctype": "Departmental Need Decision", "decision_id": f"NDD-ANLT-{number}-{index}", "departmental_need": need.name, "need_revision": names[0],
				"action": action, "actor": "Administrator", "occurred_at": at, "prior_state": "Submitted", "result_state": state,
				"idempotency_key": f"ndsa-{number}-{index}", "fixture_namespace": NS,
				"reason": REASON if action in REASON_REQUIRED_ACTIONS else "",
			}).insert(ignore_permissions=True)
		return need.name

	@classmethod
	def build_needs(cls) -> dict[str, str]:
		make = cls.make_need
		return {
			# accepted with a successor under way: the baseline title is shown, the flag is raised, "Accept successor" is not a first acceptance
			"accepted_dh": make(1, state="Accepted for planning", unit=cls.dh, title="Clinic equipment", revision_status="Accepted", successor_title="Clinic equipment, enlarged draft",
				decisions=[("Accept for planning", ACCEPTED_1), ("Accept successor", SUCCESSOR_ACCEPTED)]),
			# two "Accept for planning" rows: the earliest is the first acceptance
			"accepted_hrmd": make(2, state="Accepted for planning", unit=cls.hrmd, title="Office furniture", revision_status="Accepted",
				decisions=[("Accept for planning", LATER_ACCEPTANCE), ("Accept for planning", ACCEPTED_2)]),
			"submitted_dh": make(3, state="Submitted", unit=cls.dh, title="Ward laptops", revision_status="Submitted", decisions=[("Submit", datetime(2026, 11, 20, 9, 0))]),
			"returned_hrmd": make(4, state="Returned", unit=cls.hrmd, title="Training room", revision_status="Returned", decisions=[("Return for correction", datetime(2026, 11, 21, 9, 0))]),
			"declined_dh": make(5, state="Not taken forward", unit=cls.dh, title="Staff vehicles", revision_status="Not taken forward", decisions=[("Do not take forward", datetime(2026, 11, 22, 9, 0))]),
			"draft_dh": make(6, state="Draft", unit=cls.dh, title="Unsent draft needs", revision_status="Draft"),
			"withdrawn_dh": make(7, state="Withdrawn", unit=cls.dh, title="Withdrawn requirement", revision_status="Withdrawn", decisions=[("Withdraw", datetime(2026, 11, 23, 9, 0))]),
		}

	@classmethod
	def remove_world(cls, check: bool = True) -> None:
		frappe.set_user("Administrator")
		for name in frappe.get_all("User Responsibility Assignment", filters={"fixture_namespace": NS}, pluck="name"):
			if frappe.db.get_value("User Responsibility Assignment", name, "status") == "Enabled":
				administration.revoke(name, reason="Revoked inside the Needs Analytics test.", actor="Administrator")
			frappe.delete_doc("User Responsibility Assignment", name, force=1, ignore_permissions=True)
		for doctype in ("Departmental Need Decision", "Departmental Need Revision", "Departmental Need"):
			frappe.db.delete(doctype, {"fixture_namespace": NS})
		for email in USERS:
			for name in frappe.get_all("Contact Email", filters={"email_id": email}, pluck="parent"):
				frappe.delete_doc("Contact", name, force=1, ignore_permissions=True)
			if frappe.db.exists("User", email):
				frappe.delete_doc("User", email, force=1, ignore_permissions=True)
			frappe.db.delete("DefaultValue", {"parent": email})
		frappe.db.commit()
		if check and getattr(cls, "before", None):
			after = _counts()
			if after != cls.before:
				raise AssertionError(f"Needs Analytics test rows left behind: before {cls.before}, after {after}")

	def setUp(self):
		super().setUp()
		self.addCleanup(frappe.set_user, "Administrator")

	# ----- helpers -----

	def read(self, user: str) -> list[dict[str, Any]]:
		"""Every Need record the actor gets, as the actor, then only this world's (the seeded Needs are not under test here)."""
		result = provider.facts(user=user, kind=ac.NEEDS, at=self.at)
		for record in result["records"]:
			ac.validate(record)
		return [record for record in result["records"] if record["reference"].startswith(PREFIX)]

	def refs(self, user: str) -> set[str]:
		return {record["reference"] for record in self.read(user)}

	def ref(self, key: str) -> str:
		return f"{PREFIX}{list(self.needs).index(key) + 1:04d}"

	def refs_of(self, *keys: str) -> set[str]:
		return {self.ref(key) for key in keys}

	COUNTABLE = ("accepted_dh", "accepted_hrmd", "submitted_dh", "returned_hrmd", "declined_dh")

	# ----- the facts for a known world -----

	def test_one_record_per_countable_need_with_its_owner_disposition_and_route(self):
		records = {record["reference"]: record for record in self.read("Administrator")}
		self.assertEqual(set(records), self.refs_of(*self.COUNTABLE))
		accepted = records[self.ref("accepted_dh")]
		self.assertEqual(
			(accepted["kind"], accepted["id"], accepted["state"], accepted["state_key"], accepted["fiscal_year"], accepted["org_units"], accepted["route"]),
			("needs", self.needs["accepted_dh"], "Accepted for planning", "accepted", "2027-2028", [self.dh], ["departmental-needs", self.ref("accepted_dh")]),
		)
		self.assertEqual({r["reference"]: r["state_key"] for r in records.values()}, {
			self.ref("accepted_dh"): "accepted", self.ref("accepted_hrmd"): "accepted", self.ref("submitted_dh"): "submitted",
			self.ref("returned_hrmd"): "returned", self.ref("declined_dh"): "not_taken_forward",
		})
		self.assertEqual(records[self.ref("returned_hrmd")]["org_units"], [self.hrmd])

	def test_acceptance_is_the_first_accept_for_planning_decision_and_nothing_else(self):
		records = {record["reference"]: record for record in self.read("Administrator")}
		self.assertEqual(records[self.ref("accepted_dh")]["accepted_at"], ACCEPTED_1)  # the "Accept successor" row dated earlier is not it
		self.assertEqual(records[self.ref("accepted_hrmd")]["accepted_at"], ACCEPTED_2)  # two accept rows: the earlier one
		for key in ("submitted_dh", "returned_hrmd", "declined_dh"):
			self.assertIsNone(records[self.ref(key)]["accepted_at"], key)

	def test_a_successor_in_preparation_raises_the_flag_and_never_discloses_the_draft_title(self):
		records = {record["reference"]: record for record in self.read("Administrator")}
		self.assertTrue(records[self.ref("accepted_dh")]["pending_successor"])
		self.assertEqual(records[self.ref("accepted_dh")]["title"], "Clinic equipment")  # the accepted baseline, not "…, enlarged draft"
		for key in ("accepted_hrmd", "submitted_dh", "returned_hrmd", "declined_dh"):
			self.assertFalse(records[self.ref(key)]["pending_successor"], key)
		self.assertEqual(records[self.ref("returned_hrmd")]["title"], "Training room")

	def test_the_seeded_accepted_needs_carry_the_instant_their_decision_row_records(self):
		for record in provider.facts(user="Administrator", kind=ac.NEEDS, at=self.at)["records"]:
			if record["reference"].startswith(PREFIX) or record["state_key"] != "accepted":
				continue
			rows = frappe.get_all("Departmental Need Decision", filters={"departmental_need": record["id"], "action": "Accept for planning"}, pluck="occurred_at")
			self.assertEqual(record["accepted_at"], min(rows) if rows else None, record["reference"])

	# ----- a read changes nothing -----

	def test_a_read_creates_and_persists_nothing_not_even_a_working_context_preference(self):
		before = _counts()
		for user in ("Administrator", AUTHOR_DH, HOD_DH, AO, HOPF, AUDITOR, PLANNER, OFFICER):
			provider.applies(user=user, at=self.at)
			provider.facts(user=user, kind=ac.NEEDS, at=self.at)
		frappe.db.commit()
		self.assertEqual(_counts(), before)

	def test_another_kind_or_a_guest_is_refused_not_answered_with_zero(self):
		with self.assertRaises(ValueError):
			provider.facts(user="Administrator", kind=ac.TENDERS, at=self.at)
		self.assertEqual(provider.applies(user="Guest", at=self.at), set())
		self.assertEqual(provider.facts(user="Guest", kind=ac.NEEDS, at=self.at)["records"], [])

	# ----- personas -----

	def test_a_departmental_author_sees_only_the_needs_they_own_in_their_own_unit(self):
		self.assertEqual(provider.applies(user=AUTHOR_DH, at=self.at), {ac.NEEDS})
		# the Digital Health ones, without the Draft and the Withdrawn one; the HRMD Needs they own are outside their unit
		self.assertEqual(self.refs(AUTHOR_DH), self.refs_of("accepted_dh", "submitted_dh", "declined_dh"))

	def test_an_author_of_the_unit_who_owns_nothing_sees_nothing(self):
		self.assertEqual(provider.applies(user=OTHER_AUTHOR_DH, at=self.at), {ac.NEEDS})
		self.assertEqual(self.refs(OTHER_AUTHOR_DH), set())

	def test_a_head_of_department_sees_only_their_own_department(self):
		self.assertEqual(provider.applies(user=HOD_DH, at=self.at), {ac.NEEDS})
		seen = self.read(HOD_DH)
		self.assertEqual({r["reference"] for r in seen}, self.refs_of("accepted_dh", "submitted_dh", "declined_dh"))
		self.assertEqual({unit for r in seen for unit in r["org_units"]}, {self.dh})

	def test_the_planner_keeps_the_module_reading_scope_accepted_needs_only(self):
		self.assertEqual(provider.applies(user=PLANNER, at=self.at), {ac.NEEDS})
		self.assertEqual(self.refs(PLANNER), self.refs_of("accepted_dh", "accepted_hrmd"))

	def test_the_offices_and_technical_readers_get_the_site_wide_aggregate_without_drafts_or_withdrawn(self):
		everything = self.refs_of(*self.COUNTABLE)
		for user in (HOPF, AO, AUDITOR, "Administrator", TECHNICAL_OPERATOR):
			self.assertEqual(provider.applies(user=user, at=self.at), {ac.NEEDS}, user)
			self.assertEqual(self.refs(user), everything, user)  # includes the Returned Need the module's own office read still masks
			self.assertTrue(self.refs(user).isdisjoint(self.refs_of("draft_dh", "withdrawn_dh")), user)

	def test_an_unrelated_role_gets_nothing(self):
		self.assertEqual(provider.applies(user=OFFICER, at=self.at), set())
		self.assertEqual(provider.facts(user=OFFICER, kind=ac.NEEDS, at=self.at)["records"], [])

	def test_a_revoked_scope_sees_nothing_on_the_next_read(self):
		self.assertEqual(self.refs(HOD_DH), self.refs_of("accepted_dh", "submitted_dh", "declined_dh"))
		assignment = frappe.db.get_value("User Responsibility Assignment", {"user": HOD_DH, "fixture_namespace": NS, "status": "Enabled"}, "name")
		administration.revoke(assignment, reason="Revoked inside the Needs Analytics test.", actor="Administrator")
		self.addCleanup(lambda: administration.grant(user=HOD_DH, business_role="Head of User Department", organisation_unit=self.dh, fixture_namespace=NS, actor="Administrator"))
		frappe.db.commit()
		self.assertEqual(provider.applies(user=HOD_DH, at=self.at), set())
		self.assertEqual(provider.facts(user=HOD_DH, kind=ac.NEEDS, at=self.at)["records"], [])
