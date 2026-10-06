# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 — the Requisitions feed to Home (`procurement_requisitions/services/home_provider.py`).

Class one shares one Planning/Requisitions world (built once; the provider only reads). Each test makes its own
requisition through the owner's real commands (send, certify) on the one active plan item and the module's own wipe removes
it afterwards; the rows of rarely used outcomes (authorised, withdrawn) are inserted as decisions. Class two builds a second
world for the one outcome that cannot be undone, a Planning correction (a hold on the plan item), and walks it in order.
The test clock is the §10B timeline (16-18 June 2027): the rows' instants are set on the records, as the Tenders test does.

Run:
  bench --site kentender-test.local run-tests --app kentender_procurement \\
    --module kentender_procurement.procurement_requisitions.tests.test_home_provider
"""

from __future__ import annotations

from datetime import datetime, timedelta

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import home_entries as he
from kentender_core.services import home_support, home_time
from kentender_core.services import home_workspace as hw
from kentender_core.services import responsibility_administration as administration
from kentender_procurement.procurement_planning.tests import fixtures as pln_fx
from kentender_procurement.procurement_requisitions.services import eligibility_gateway, lifecycle, my_work_provider
from kentender_procurement.procurement_requisitions.services import home_provider
from kentender_procurement.procurement_requisitions.services.home_provider import entries
from kentender_procurement.procurement_requisitions.tests import fixtures as fx

EXTRA = "reqt.home.extra@example.test"  # an unrelated internal user until a test grants it something
EXTRA_NS = "KT_TEST_REQHOME"
H12 = datetime(2027, 6, 18, 10, 0)
SPEC_PAGES = ("procurement-requisitions",)
SENT_AT, CERTIFIED_AT, AUTHORISED_AT = "2027-06-16 09:00:00", "2027-06-16 11:00:00", "2027-06-17 11:00:00"
HOD, AUTHOR, HOPF, PLANNER, AUDITOR, AO, OUTSIDER = fx.HOD, fx.AUTHOR, fx.HOPF, fx.PLANNER, fx.AUDITOR, fx.ACCOUNTING_OFFICER, fx.OUTSIDER
HOPF_2 = pln_fx.HYBRID_HOPF_AO  # a second Head of Procurement Function (also an Accounting Officer)


def _dt(text: str) -> datetime:
	return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")


def _remove_extra() -> None:
	frappe.set_user("Administrator")
	for name in frappe.get_all("User Responsibility Assignment", filters={"fixture_namespace": EXTRA_NS}, pluck="name"):
		frappe.delete_doc("User Responsibility Assignment", name, force=1, ignore_permissions=True)
	for name in frappe.get_all("Contact Email", filters={"email_id": EXTRA}, pluck="parent"):
		frappe.delete_doc("Contact", name, force=1, ignore_permissions=True)
	if frappe.db.exists("User", EXTRA):
		frappe.delete_doc("User", EXTRA, force=1, ignore_permissions=True)
	frappe.db.commit()


def _left_behind() -> dict[str, int]:
	"""What this module's tests may leave: test-world requisitions and their rows, and the extra user's responsibilities."""
	requisitions = fx.test_requisitions()
	versions = frappe.get_all("Requisition Version", filters={"requisition": ("in", requisitions or [""])}, pluck="name")
	return {
		"requisitions": len(requisitions),
		"versions": len(versions),
		"tasks": frappe.db.count("Requisition Task", {"requisition": ("in", requisitions or [""])}),
		"decisions": frappe.db.count("Requisition Decision", {"requisition_version": ("in", versions or [""])}),
		"journal": frappe.db.count("Requisition Command Journal", {"document_name": ("in", requisitions or [""])}),
		"assignments": frappe.db.count("User Responsibility Assignment", {"fixture_namespace": EXTRA_NS}),
		"extra_user": frappe.db.count("User", {"name": EXTRA}),
	}


def _remove_world() -> None:
	frappe.set_user("Administrator")
	fx.wipe_requisition_rows()
	_remove_extra()
	left = _left_behind()
	if any(left.values()):
		raise AssertionError(f"Requisitions Home test rows left behind: {left}")


class HomeCase(IntegrationTestCase):
	"""Helpers shared by both worlds."""

	@classmethod
	def build_world(cls):
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)
		cls.addClassCleanup(_remove_world)
		fx.wipe_requisition_rows()
		fx.wipe_planning_rows()
		pln_fx._user(EXTRA, "REQHOME Extra")
		_, cls.item_id = fx.active_item()
		frappe.db.commit()

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_requisition_rows()
		home_support.reset()
		self.addCleanup(fx.wipe_requisition_rows)
		self.addCleanup(self.release_grants)
		self.addCleanup(frappe.set_user, "Administrator")

	def release_grants(self):
		"""Whatever a test granted the extra user or Grace inside this module's namespace: revoked (so the Role projection follows) then removed."""
		frappe.set_user("Administrator")
		for name in frappe.get_all("User Responsibility Assignment", filters={"fixture_namespace": EXTRA_NS}, pluck="name"):
			if frappe.db.get_value("User Responsibility Assignment", name, "status") == "Enabled":
				administration.revoke(name, reason="Revoked inside the Home provider test.", actor="Administrator")
			frappe.delete_doc("User Responsibility Assignment", name, force=1, ignore_permissions=True)
		frappe.db.commit()

	def stamp_sent(self, requisition: str) -> None:
		frappe.set_user("Administrator")
		frappe.db.set_value("Requisition Command Journal", {"document_name": requisition, "command": "SendForDepartmentApproval"}, "occurred_at", _dt(SENT_AT), update_modified=False)
		frappe.db.set_value("Requisition Task", fx.open_task(requisition, "Head of User Department"), "creation", _dt(SENT_AT), update_modified=False)

	# ----- the owner's flows, then the §10B instants set on the records -----

	def sent(self) -> str:
		"""A complete draft sent for department approval by Grace (AUTHOR) at 16 June, 09:00."""
		requisition = fx.complete_draft(self.item_id)
		fx.send(requisition)
		self.stamp_sent(requisition)
		return requisition

	def certified(self, by: str = HOD) -> str:
		"""The same requisition certified to Procurement by `by` at 16 June, 11:00."""
		requisition = self.sent()
		fx.submit_as_hod(requisition, by)
		frappe.set_user("Administrator")
		self.stamp_decision(requisition, "Submit to Procurement", CERTIFIED_AT)
		frappe.db.set_value("Requisition Task", fx.open_task(requisition, "Head of Procurement Function"), "creation", _dt(CERTIFIED_AT), update_modified=False)
		return requisition

	def stamp_decision(self, requisition: str, decision: str, at: str) -> str:
		name = frappe.db.get_value("Requisition Decision", {"requisition_version": self.version(requisition), "decision": decision}, "name")
		frappe.db.set_value("Requisition Decision", name, "decided_at", _dt(at), update_modified=False)
		return name

	def version(self, requisition: str) -> str:
		return frappe.db.get_value("Procurement Requisition", requisition, "current_version")

	def add_decision(self, requisition: str, decision: str, *, actor: str, at: datetime) -> str:
		return frappe.get_doc({
			"doctype": "Requisition Decision", "requisition_version": self.version(requisition), "actor": actor, "decision": decision, "authority_snapshot": "{}",
			"decided_at": at, "command_idempotency_key": fx.key(),
		}).insert(ignore_permissions=True).name

	# ----- reads -----

	def region(self, user: str, region: str):
		home_support.reset()
		return entries(user=user, region=region)

	def mine(self, rows):
		roots = set(fx.test_requisitions())
		return [row for row in rows or [] if row["root"] in roots]

	def one(self, user: str, region: str, requisition: str, action_id: str = ""):
		rows = [row for row in self.region(user, region) or [] if row["root"] == requisition and (not action_id or row["action_id"] == action_id)]
		self.assertEqual(len(rows), 1, f"{user} {region} {requisition}: {rows}")
		return rows[0]

	def reference(self, requisition: str) -> str:
		return frappe.db.get_value("Procurement Requisition", requisition, "requisition_reference")

	def title(self, requisition: str) -> str:
		return frappe.db.get_value("Requisition Version", self.version(requisition), "requirement_title")

	def name(self, user: str) -> str:
		return frappe.db.get_value("User", user, "full_name")

	def home(self, user: str, at: datetime = H12):
		return hw.get_workspace(user, providers=[entries], at=at)

	def row(self, user: str, region: str, requisition: str, at: datetime = H12) -> dict:
		rows, cursor = [], None
		while True:
			page = hw.get_workspace(user, regions=[region], cursors={region: cursor} if cursor else None, providers=[entries], at=at)["regions"][region]
			rows += page["entries"]
			cursor = page["next_cursor"]
			if not cursor:
				break
		rows = [row for row in rows if row["reference"] == self.reference(requisition)]
		self.assertEqual(len(rows), 1, f"{user} {region}: {rows}")
		return rows[0]

	def holders(self, role: str, unit: str = "", *, besides: str = "") -> list[str]:
		"""Who holds `role` now, read independently of the provider: Site-wide rows have no unit (NULL or empty), unit-scoped rows
		sit on `unit`."""
		out: list[str] = []
		for row in frappe.get_all("User Responsibility Assignment", filters={"business_role": role, "status": "Enabled"}, fields=["user", "organisation_unit"], order_by="creation asc"):
			if (row.organisation_unit or "") == unit and row.user not in out and row.user != besides:
				out.append(row.user)
		return out

	def phrase(self, role: str, unit: str = "", *, besides: str = "") -> tuple[str, str]:
		"""(the holder as the display, as a sentence subject) the way the owner words it: names when two or fewer."""
		people = [self.name(user) for user in self.holders(role, unit, besides=besides)]
		if 0 < len(people) <= 2:
			return " or ".join(people), " or ".join(people)
		return role, f"{'an' if role[0] in 'AEIOU' else 'a'} {role}"


class TestRequisitionsHomeProvider(HomeCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.build_world()

	# ----- My work -----

	def test_the_head_of_procurement_functions_authorise_row_is_worded_by_the_spec(self):
		requisition = self.certified()
		task = fx.open_task(requisition, "Head of Procurement Function")
		row = self.one(HOPF, he.MY_WORK, requisition)
		self.assertEqual((row["title"], row["action"], row["reference"]), (self.title(requisition), "Authorise requisition", self.reference(requisition)))
		self.assertNotEqual(row["title"], row["reference"])  # the business title leads, the reference is secondary
		self.assertEqual((row["entered_at"], row["entered_verb"], row["action_id"]), (_dt(CERTIFIED_AT), "Received", task))
		self.assertEqual(row["destination"], {"route": ["procurement-requisitions", "procurement-task", task], "route_options": {}})
		self.assertEqual((row["blocked"], row["reason"], row["owner"], row["region"]), (False, "", "requisitions", he.MY_WORK))
		self.assertEqual(row["source_revision"], frappe.db.get_value("Requisition Task", task, "task_token"))
		# the second Head of Procurement Function holds it too (they did not certify it)
		self.assertEqual(self.one(HOPF_2, he.MY_WORK, requisition)["action_id"], task)

	def test_the_home_read_renders_the_spec_timing_for_the_authorise_row(self):
		requisition = self.certified()
		row = self.row(HOPF, "my_work", requisition)
		self.assertEqual((row["action"], row["timing"], row["module"]), ("Authorise requisition", "Received 2 days ago (16 June, 11:00)", "Requisitions"))
		self.assertEqual(row["title"], self.title(requisition))
		self.assertEqual(self.row(HOPF, "my_work", requisition, at=datetime(2027, 6, 17, 10, 0))["timing"], "Received yesterday (16 June, 11:00)")

	def test_the_departmental_approval_row_belongs_to_the_head_of_user_department(self):
		requisition = self.sent()
		task = fx.open_task(requisition, "Head of User Department")
		row = self.one(HOD, he.MY_WORK, requisition)
		self.assertEqual((row["title"], row["action"], row["reference"]), (self.title(requisition), "Review departmental requisition", self.reference(requisition)))
		self.assertEqual((row["entered_at"], row["entered_verb"], row["action_id"], row["blocked"]), (_dt(SENT_AT), "Received", task, False))
		self.assertEqual(row["destination"]["route"], ["procurement-requisitions", "department-task", task])
		for user in (AUTHOR, OUTSIDER, PLANNER, AUDITOR, AO):  # the sender, another unit's author, a planner, the auditor: no task
			self.assertEqual(self.mine(self.region(user, he.MY_WORK) or []), [], user)
		self.assertEqual(self.mine(self.region(HOPF, he.MY_WORK)) and self.one(HOPF, he.MY_WORK, requisition)["action_id"], task)  # Charles is also Head of the unit

	def test_the_authoriser_who_certified_the_requisition_is_not_offered_to_authorise_it(self):
		# Charles holds both responsibilities and certified it himself: the owner's command refuses him (REQ_SOD_BLOCKED)
		requisition = self.certified(by=HOPF)
		self.assertEqual(self.mine(self.region(HOPF, he.MY_WORK)), [])
		self.assertEqual(self.one(HOPF_2, he.MY_WORK, requisition)["action"], "Authorise requisition")
		with self.assertRaises(Exception):  # the command the row would have led to
			frappe.set_user(HOPF)
			from kentender_procurement.procurement_requisitions.services import authorise

			authorise.authorise_requisition(requisition=requisition, task=fx.open_task(requisition, "Head of Procurement Function"), expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())

	def test_an_author_who_prepared_the_version_as_an_author_is_not_offered_the_head_of_departments_decision(self):
		requisition = fx.complete_draft(self.item_id)  # Grace prepares it as a Departmental Author
		self.assertEqual(frappe.db.get_value("Requisition Version", self.version(requisition), "prepared_capacity"), "Departmental Author")
		fx.send(requisition)
		self.stamp_sent(requisition)
		administration.grant(user=AUTHOR, business_role="Head of User Department", organisation_unit=fx.ou_alpha(), fixture_namespace=EXTRA_NS, actor="Administrator")
		frappe.set_user("Administrator")
		self.assertEqual(self.mine(self.region(AUTHOR, he.MY_WORK)), [])  # the command refuses her (REQ_SOD_BLOCKED)
		self.assertEqual(self.one(HOD, he.MY_WORK, requisition)["action"], "Review departmental requisition")
		with self.assertRaises(Exception):
			frappe.set_user(AUTHOR)
			lifecycle.submit_requisition_to_procurement(requisition=requisition, task=fx.open_task(requisition, "Head of User Department"), expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		# she still waits for the other Heads of the unit
		wait = self.one(AUTHOR, he.WAITING, requisition)
		self.assertEqual(wait["since"], _dt(SENT_AT))

	def test_a_hold_on_the_plan_item_blocks_only_the_authorisation_row_with_the_owners_words(self):
		requisition = self.certified()
		held = {"hold": {"held": True, "unresolved_requests": []}}
		original = eligibility_gateway.get_requisition_eligible_plan_item
		eligibility_gateway.get_requisition_eligible_plan_item = lambda plan_item_id: held
		self.addCleanup(setattr, eligibility_gateway, "get_requisition_eligible_plan_item", original)
		row = self.one(HOPF_2, he.MY_WORK, requisition)
		self.assertEqual((row["blocked"], row["reason"], row["action"]), (True, "Authorisation is on hold while Planning reviews a correction request.", "Authorise requisition"))
		# the held row says why through the Home read
		self.assertTrue(self.row(HOPF_2, "my_work", requisition)["blocked"])

	# ----- Waiting -----

	def test_the_author_waits_for_the_head_of_user_department_after_sending(self):
		requisition = self.sent()
		wait = self.one(AUTHOR, he.WAITING, requisition)
		display, subject = self.phrase("Head of User Department", fx.ou_alpha(), besides=AUTHOR)
		self.assertEqual((wait["title"], wait["reference"], wait["since"], wait["due"]), (self.title(requisition), self.reference(requisition), _dt(SENT_AT), None))
		self.assertEqual(wait["action"], f"Waiting for {subject} to review the departmental requisition")
		self.assertEqual((wait["holder"], wait["action_id"]), (display, fx.open_task(requisition, "Head of User Department")))
		self.assertEqual(wait["destination"]["route"], ["procurement-requisitions", self.reference(requisition)])
		self.assertEqual(self.row(AUTHOR, "waiting", requisition)["timing"], "Waiting 2 days (since 16 June, 09:00)")
		# nobody else waits: the Head holds the task, the outsider sent nothing
		for user in (HOD, OUTSIDER, PLANNER, AUDITOR):
			self.assertEqual([r for r in self.region(user, he.WAITING) or [] if r["root"] == requisition], [], user)

	def test_the_head_of_user_department_waits_for_procurement_after_certifying(self):
		requisition = self.certified()
		wait = self.one(HOD, he.WAITING, requisition)
		display, subject = self.phrase("Head of Procurement Function", besides=HOD)
		self.assertEqual(wait["since"], _dt(CERTIFIED_AT))
		self.assertEqual(wait["action"], f"Waiting for {subject} to authorise the requisition")
		self.assertEqual((wait["holder"], wait["title"], wait["action_id"]), (display, self.title(requisition), fx.open_task(requisition, "Head of Procurement Function")))
		self.assertEqual(self.row(HOD, "waiting", requisition)["timing"], "Waiting 2 days (since 16 June, 11:00)")
		# Grace sent it, but it has left the Head of Department: her wait is over
		self.assertEqual([r for r in self.region(AUTHOR, he.WAITING) if r["root"] == requisition], [])
		# the Head of Procurement Function holds the task; the one who certified it did not hand anything to himself
		self.assertEqual([r for r in self.region(HOPF, he.WAITING) if r["root"] == requisition], [])

	def test_a_certifier_who_cannot_authorise_what_they_certified_waits_for_the_other_holders(self):
		requisition = self.certified(by=HOPF)
		wait = self.one(HOPF, he.WAITING, requisition)
		display, subject = self.phrase("Head of Procurement Function", besides=HOPF)
		self.assertNotIn(self.name(HOPF), wait["holder"])
		self.assertEqual((wait["holder"], wait["action"]), (display, f"Waiting for {subject} to authorise the requisition"))

	def test_the_holder_helper_matches_site_wide_rows_stored_without_a_unit(self):
		# the survey's warning: a unit column holding NULL is not matched by `= ""`; the helper must find the site-wide holders
		self.assertTrue({HOPF, HOPF_2} <= set(home_provider._holders("Head of Procurement Function")))
		self.assertTrue({HOD, HOPF} <= set(home_provider._holders("Head of User Department", fx.ou_alpha())))
		self.assertNotIn(OUTSIDER, home_provider._holders("Head of User Department", fx.ou_alpha()))
		self.assertEqual(set(home_provider._holders("Head of Procurement Function")), set(self.holders("Head of Procurement Function")))

	def test_a_returned_requisition_is_nobodys_wait(self):
		requisition = self.sent()
		task = fx.open_task(requisition, "Head of User Department")
		frappe.set_user(HOD)
		lifecycle.return_to_department_author(task=task, reason="Please state the delivery site precisely.", expected_record_version=frappe.db.get_value("Requisition Task", task, "record_version"), idempotency_key=fx.key())
		frappe.set_user("Administrator")
		self.assertEqual([r for r in self.region(AUTHOR, he.WAITING) if r["root"] == requisition], [])
		self.assertEqual([r for r in self.region(HOD, he.MY_WORK) if r["root"] == requisition], [])
		returned = [row for row in self.region(HOD, he.COMPLETED) if row["root"] == requisition]
		self.assertEqual([r["action"] for r in returned], ["Returned requisition for correction"])
		self.assertTrue(returned[0]["sentence"].startswith("You returned this requisition for correction on ") and "awaiting" not in returned[0]["sentence"])

	# ----- Records you oversee, Coming up -----

	def test_requisitions_supply_no_oversight_and_no_coming_up_in_v1(self):
		self.certified()
		for user in (HOD, HOPF, AUTHOR, PLANNER, AUDITOR, AO, OUTSIDER, EXTRA):
			self.assertIsNone(self.region(user, he.OVERSIGHT), user)
			self.assertIsNone(self.region(user, he.COMING_UP), user)

	# ----- Recently completed actions -----

	def test_grace_sending_names_who_department_approval_awaits(self):
		requisition = self.sent()
		row = self.one(AUTHOR, he.COMPLETED, requisition)
		display, _subject = self.phrase("Head of User Department", fx.ou_alpha(), besides=AUTHOR)
		self.assertEqual((row["title"], row["action"], row["reference"], row["completed_at"]), (self.title(requisition), "Sent requisition for department approval", self.reference(requisition), _dt(SENT_AT)))
		self.assertTrue(row["sentence"].startswith("You sent this requisition for department approval on 16 June 2027, 09:00 "), row["sentence"])
		self.assertEqual(row["sentence"].split(". ", 1)[1], f"It is awaiting department approval by {display}.")
		self.assertEqual(row["destination"]["route"], ["procurement-requisitions", self.reference(requisition)])
		self.assertEqual(self.row(AUTHOR, "completed", requisition)["action"], "Sent requisition for department approval")

	def test_the_head_of_departments_certification_names_who_authorisation_awaits(self):
		requisition = self.certified()
		decision = frappe.db.get_value("Requisition Decision", {"requisition_version": self.version(requisition), "decision": "Submit to Procurement"}, "name")
		row = self.one(HOD, he.COMPLETED, requisition, decision)
		display, _subject = self.phrase("Head of Procurement Function", besides=HOD)
		self.assertEqual((row["action"], row["completed_at"], row["title"]), ("Sent requisition to Procurement", _dt(CERTIFIED_AT), self.title(requisition)))
		self.assertTrue(row["sentence"].startswith("You sent this requisition to Procurement on 16 June 2027, 11:00 "), row["sentence"])
		self.assertEqual(row["sentence"].split(". ", 1)[1], f"It is awaiting authorisation by {display}.")
		# once the requisition has moved on, the clause is dropped (FU-HOME-24)
		frappe.db.set_value("Procurement Requisition", requisition, "current_state", "Authorised", update_modified=False)
		self.assertNotIn("awaiting", self.one(HOD, he.COMPLETED, requisition, decision)["sentence"])
		# Grace's sending has also left the Head of Department
		self.assertNotIn("awaiting", self.one(AUTHOR, he.COMPLETED, requisition)["sentence"])

	def test_charles_authorisation_reads_as_the_spec_does(self):
		requisition = self.certified()
		decision = self.add_decision(requisition, "Authorise requisition", actor=HOPF_2, at=_dt(AUTHORISED_AT))
		frappe.db.set_value("Procurement Requisition", requisition, "current_state", "Authorised", update_modified=False)
		row = self.one(HOPF_2, he.COMPLETED, requisition, decision)
		self.assertEqual((row["title"], row["action"], row["completed_at"]), (self.title(requisition), "Authorised requisition", _dt(AUTHORISED_AT)))
		self.assertTrue(row["sentence"].startswith("You authorised this requisition on 17 June 2027, 11:00 ") and row["sentence"].endswith("."), row["sentence"])
		self.assertNotIn("awaiting", row["sentence"])
		self.assertEqual(row["destination"]["route"], ["procurement-requisitions", self.reference(requisition)])
		self.assertEqual(self.row(HOPF_2, "completed", requisition)["action"], "Authorised requisition")

	def test_every_whitelisted_outcome_has_a_sentence_and_nothing_else_is_shown(self):
		requisition = self.certified()
		for decision in home_provider.COMPLETED:
			self.add_decision(requisition, decision, actor=HOPF_2, at=_dt(AUTHORISED_AT))
		other = self.add_decision(requisition, "Reopen for something else", actor=HOPF_2, at=_dt(AUTHORISED_AT))
		rows = [row for row in self.region(HOPF_2, he.COMPLETED) if row["root"] == requisition]
		self.assertEqual({row["action"] for row in rows}, {label for label, _did in home_provider.COMPLETED.values()})
		self.assertNotIn(other, [row["action_id"] for row in rows])
		for row in rows:
			self.assertTrue(row["sentence"].startswith("You ") and " on 17 June 2027, 11:00 " in row["sentence"], row["sentence"])

	def test_only_the_actors_own_decisions_inside_thirty_days_for_a_requisition_they_can_read(self):
		requisition = self.certified()
		old = self.add_decision(requisition, "Withdraw requisition", actor=HOPF_2, at=home_time.now() - timedelta(days=45))
		recent = self.add_decision(requisition, "Withdraw requisition", actor=HOPF_2, at=home_time.now() - timedelta(days=5))
		ids = [row["action_id"] for row in self.region(HOPF_2, he.COMPLETED)]
		self.assertIn(recent, ids)
		self.assertNotIn(old, ids)
		self.assertNotIn(recent, [row["action_id"] for row in self.region(HOPF, he.COMPLETED)])  # Charles did not take it
		# the core window drops one older than thirty days at the read instant
		keys = [row["key"].split("|")[-1] for row in hw.get_workspace(HOPF_2, regions=["completed"], providers=[entries], at=H12)["regions"]["completed"]["entries"]]
		self.assertNotIn(old, keys)

	def test_a_decision_with_no_task_is_still_read_for_the_actor(self):
		# the doctype's own permission hooks hide a decision with no task (Withdraw, Revoke, Planning correction) from everyone but a technical reader
		requisition = self.certified()
		decision = self.add_decision(requisition, "Withdraw requisition", actor=HOD, at=home_time.now())
		self.assertIsNone(frappe.db.get_value("Requisition Decision", decision, "task"))
		self.assertEqual(self.one(HOD, he.COMPLETED, requisition, decision)["action"], "Withdrew requisition")

	def test_an_actor_whose_scope_was_revoked_sees_nothing_of_the_requisition(self):
		# an extra Head of the unit certifies it, then loses the unit and keeps only another department's authorship
		requisition = self.sent()
		administration.grant(user=EXTRA, business_role="Head of User Department", organisation_unit=fx.ou_alpha(), fixture_namespace=EXTRA_NS, actor="Administrator")
		self.assertEqual(self.one(EXTRA, he.MY_WORK, requisition)["action"], "Review departmental requisition")
		fx.submit_as_hod(requisition, EXTRA)
		frappe.set_user("Administrator")
		self.assertEqual(len(self.mine(self.region(EXTRA, he.COMPLETED))), 1)
		self.assertEqual(len(self.mine(self.region(EXTRA, he.WAITING))), 1)
		self.release_grants()
		self.assertIsNone(self.region(EXTRA, he.COMPLETED))  # no responsibility: the region does not apply
		administration.grant(user=EXTRA, business_role="Departmental Author", organisation_unit=fx.ou_beta(), fixture_namespace=EXTRA_NS, actor="Administrator")
		self.assertEqual(self.region(EXTRA, he.COMPLETED), [])  # applies, but the unit is not theirs: nothing of this requisition
		self.assertEqual(self.region(EXTRA, he.WAITING), [])
		self.assertEqual(self.region(EXTRA, he.MY_WORK), [])
		revoked = self.home(EXTRA)
		self.assertFalse([row for region in revoked["regions"].values() for row in region["entries"] if row["reference"] == self.reference(requisition)])

	# ----- applicability, personas, technical readers -----

	def test_none_versus_empty_by_responsibility(self):
		self.certified()
		for region in (he.MY_WORK, he.WAITING, he.COMPLETED):
			for user in (HOD, HOPF, AUTHOR, PLANNER, AUDITOR, OUTSIDER):
				self.assertIsInstance(self.region(user, region), list, (user, region))
			for user in (EXTRA, AO):  # no Requisitions responsibility (the Accounting Officer's authorised-only read is not one)
				self.assertIsNone(self.region(user, region), (user, region))
		self.assertEqual(self.mine(self.region(AUDITOR, he.MY_WORK)), [])  # the Auditor holds no task
		self.assertEqual(self.mine(self.region(PLANNER, he.WAITING)), [])

	def test_the_technical_reader_and_an_unrelated_internal_user_get_nothing(self):
		self.certified()
		for region in he.REGIONS:
			self.assertIsNone(self.region("Administrator", region), region)
			self.assertIsNone(self.region("Guest", region), region)
			self.assertIsNone(self.region(EXTRA, region), region)
		view = self.home("Administrator")
		self.assertEqual((view["empty"], view["regions"]["my_work"]["entries"]), (True, []))
		nobody = self.home(EXTRA)
		self.assertEqual(nobody["state"], "ready")
		self.assertFalse(any(region["entries"] for region in nobody["regions"].values()))
		self.assertEqual({region["coverage"] for region in nobody["regions"].values()}, {hw.NOT_APPLICABLE})

	def test_the_provider_writes_nothing(self):
		requisition = self.certified()
		self.add_decision(requisition, "Withdraw requisition", actor=HOPF_2, at=home_time.now())
		frappe.db.commit()
		before = frappe.db.transaction_writes
		for user in (HOD, HOPF, HOPF_2, AUTHOR, PLANNER, AUDITOR, AO, OUTSIDER, EXTRA, "Administrator"):
			for region in he.REGIONS:
				self.region(user, region)
		self.home(HOPF)
		self.assertEqual(frappe.db.transaction_writes, before)

	def test_the_scan_runs_once_per_home_read(self):
		self.certified()
		calls = []
		original = my_work_provider.my_work_rows

		def counting(**kwargs):
			calls.append(kwargs["user"])
			return original(**kwargs)

		my_work_provider.my_work_rows = counting
		self.addCleanup(setattr, my_work_provider, "my_work_rows", original)
		self.home(HOPF_2)
		self.assertEqual(calls, [HOPF_2])

	# ----- destinations, tables -----

	def test_every_destination_opens_a_real_page_the_actor_may_open(self):
		for page in SPEC_PAGES:
			self.assertTrue(frappe.db.exists("Page", page), page)
		self.certified()
		seen = set()
		for user in (HOD, HOPF, HOPF_2, AUTHOR):
			for region in (he.MY_WORK, he.WAITING, he.COMPLETED):
				for row in self.mine(self.region(user, region)):
					seen.add(row["destination"]["route"][0])
					self.assertTrue(hw._page_permitted(row["destination"]["route"][0], user), (user, row["destination"]))
		self.assertEqual(seen, {"procurement-requisitions"})

	def test_the_owners_tables_cover_every_row_kind_and_decision(self):
		self.assertEqual(set(home_provider.ACTION), {home_provider.DEPARTMENT_APPROVAL, home_provider.PROCUREMENT_AUTHORISATION})
		self.assertEqual(home_provider.ACTION[home_provider.PROCUREMENT_AUTHORISATION], "Authorise requisition")
		for line in (home_provider.WAIT_DEPARTMENT, home_provider.WAIT_AUTHORISATION, home_provider.WAIT_PLANNING):
			self.assertTrue(line.startswith("Waiting for {who} to ") and "{" not in line.format(who="Someone"), line)
		options = frappe.get_meta("Requisition Decision").get_field("decision")
		self.assertEqual(options.fieldtype, "Data")  # decisions are free text, so the whitelist is the one place the vocabulary lives
		for label, did in home_provider.COMPLETED.values():
			self.assertTrue(label and did and "{" not in did, (label, did))


class TestRequisitionsHomeAfterAPlanningCorrection(HomeCase):
	"""One world, one walk in order: the requisition is certified, Planning's hold is placed on its plan item, then the
	requisition is stopped for a Planning correction (neither can be undone, so nothing else shares this world)."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.build_world()

	def test_the_hold_blocks_the_row_and_the_stop_turns_the_requester_into_a_waiter(self):
		requisition = fx.submitted(self.item_id)
		frappe.set_user("Administrator")
		self.assertFalse(self.one(HOPF_2, he.MY_WORK, requisition)["blocked"])
		# the owner's own contract opens a correction request and holds the plan item, leaving the requisition where it was
		root = frappe.get_doc("Procurement Requisition", requisition)
		frappe.set_user(HOPF)
		eligibility_gateway.receive_plan_item_correction_request(
			plan_item_id=root.plan_item_id, requisition_reference=root.requisition_reference, requisition_version=root.current_version,
			reason="The approved source allocation refers to the wrong Budget Line.", idempotency_key=fx.key(),
		)
		frappe.set_user("Administrator")
		frappe.db.commit()
		blocked = self.one(HOPF_2, he.MY_WORK, requisition)
		self.assertEqual((blocked["blocked"], blocked["reason"], blocked["action"]), (True, "Authorisation is on hold while Planning reviews a correction request.", "Authorise requisition"))
		self.assertTrue(self.row(HOPF_2, "my_work", requisition)["blocked"])
		self.assertEqual([r["blocked"] for r in self.region(HOD, he.WAITING) if r["root"] == requisition], [False])  # a wait is never blocked
		before = frappe.db.transaction_writes
		for region in he.REGIONS:
			self.region(HOPF_2, region)
			self.region(HOD, region)
		self.assertEqual(frappe.db.transaction_writes, before)

		# now the requisition is stopped for the correction by Charles
		frappe.set_user(HOPF)
		lifecycle.request_upstream_plan_correction(requisition=requisition, reason="The approved source allocation refers to the wrong Budget Line.", expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		frappe.set_user("Administrator")
		stopped_at = _dt("2027-06-17 15:00:00")
		decision = frappe.db.get_value("Requisition Decision", {"requisition_version": self.version(requisition), "decision": "Request Planning correction"}, "name")
		frappe.db.set_value("Requisition Decision", decision, "decided_at", stopped_at, update_modified=False)
		self.assertEqual(frappe.db.get_value("Procurement Requisition", requisition, "current_state"), "Upstream correction required")
		wait = self.one(HOPF, he.WAITING, requisition)
		display, subject = self.phrase("Procurement Planner", besides=HOPF)
		self.assertEqual((wait["since"], wait["holder"], wait["title"]), (stopped_at, display, self.title(requisition)))
		self.assertEqual(wait["action"], f"Waiting for {subject} to resolve the Planning correction request")
		self.assertEqual(wait["action_id"], f"{requisition}:planning-correction")
		self.assertEqual(self.row(HOPF, "waiting", requisition)["timing"], "Waiting 1 day (since 17 June, 15:00)")
		# the stopped requisition has no open task: nobody holds an item, and only the requester waits
		for user in (HOPF, HOPF_2, HOD, AUTHOR):
			self.assertEqual([r for r in self.region(user, he.MY_WORK) if r["root"] == requisition], [], user)
		for user in (HOD, HOPF_2, AUTHOR, PLANNER):
			self.assertEqual([r for r in self.region(user, he.WAITING) if r["root"] == requisition], [], user)
		row = self.one(HOPF, he.COMPLETED, requisition, decision)
		self.assertEqual(row["action"], "Requested Planning correction")
		self.assertTrue(row["sentence"].startswith("You asked Planning to correct the plan behind this requisition on 17 June 2027, 15:00 "), row["sentence"])
		self.assertNotIn("awaiting", row["sentence"])
		before = frappe.db.transaction_writes
		for user in (HOPF, HOD, PLANNER):
			for region in he.REGIONS:
				self.region(user, region)
		self.assertEqual(frappe.db.transaction_writes, before)
