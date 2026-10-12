# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Who may take each Award command (owner decision D2, 6 Oct 2026; AWD-CHG-001
v0.5 §6; AUD-AWD-001, AUD-AWD-011, AUD-AWD-015).

Only the Head of Procurement Function (HOP) prepares and signs the professional
opinion, handles correspondence and restrictions; only the Accounting Officer
(AO) records the award decision. Nobody else acts, whatever Frappe roles they
hold. Authority is the effective responsibility assignment, rechecked at every
command with its effective dates; the person who prepared/signed the opinion
does not record the decision and the decider does not prepare the opinion
(default for open question Q3).

Run:
  bench --site kentender-test.local run-tests --app kentender_procurement \\
    --module kentender_procurement.award.tests.test_awd_role_matrix
"""

from __future__ import annotations

import unittest

import frappe
from frappe.utils import add_days, now_datetime

from kentender_core.services import responsibility_administration as administration
from kentender_core.services.command_write_guard import purge_doc
from kentender_core.services.business_role_registry import REGISTRY
from kentender_procurement.award.services import corrections, decision, explanation, opinion, people, records, recovery, restrictions, state
from kentender_procurement.award.services.errors import AwardError
from kentender_procurement.award.tests.support import AO, CASE, DANIEL, HOP, NAOMI, NS, AwardCase

PREFIX = "awdmatrix."
DOMAIN = "@example.test"
FORMER_HOP = f"{PREFIX}formerhop{DOMAIN}"

HOP_COMMANDS = {
	"SaveProfessionalOpinion": (opinion.save, {"conclusion": "Recommend award", "reason": "x"}),
	"SignProfessionalOpinion": (opinion.sign, {}),
	"ReturnEvaluationReport": (opinion.return_report, {"reason": "x"}),
	"RecordExternalAwardRestriction": (restrictions.record_external, {"basis": "Reported challenge", "source": "x", "received_at": "2027-06-17 09:00:00", "reason": "x"}),
	"RecordAwardIssueDisposition": (restrictions.disposition, {"issue": "none", "outcome": "Further action required", "reason": "x", "evidence": "x", "next_action": "x"}),
	"SaveAwardExplanation": (explanation.save, {"request": "none", "reply": "x"}),
	"SendAwardExplanation": (explanation.send, {"request": "none", "reply": "x"}),
	"RetryNoticeDelivery": (recovery.correct_contact, {"notice": "none"}),
}
AO_COMMANDS = {
	"RecordAwardDecision": (decision.record, {"outcome": "No award", "reason": "x", "next_action": "x"}),
	"RecordAwardCorrectionDecision": (corrections.record, {"outcome": "Decline reconsideration", "reason": "x"}),
}
OTHER_ROLES = sorted(set(REGISTRY) - {people.HEAD_OF_PROCUREMENT, people.ACCOUNTING_OFFICER, people.AUDITOR, people.TECHNICAL_OPERATOR})


def _user_for(role: str) -> str:
	return f"{PREFIX}{role.lower().replace(' ', '')}{DOMAIN}"


def _remove_extras() -> None:
	frappe.set_user("Administrator")
	users = [u for u in frappe.get_all("User", filters={"name": ("like", f"{PREFIX}%")}, pluck="name")]
	for name in frappe.get_all("User Responsibility Assignment", filters={"user": ("like", f"{PREFIX}%")}, pluck="name"):
		purge_doc("User Responsibility Assignment", name)
	for user in users:
		frappe.delete_doc("User", user, force=1, ignore_permissions=True)
	frappe.db.commit()


def _make_user(email: str) -> str:
	if not frappe.db.exists("User", email):
		frappe.get_doc({"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True).add_roles("Desk User")
	return email


def _grant(user: str, role: str, **kwargs) -> str:
	unit = ""
	if REGISTRY[role].requires_organisation_unit:
		unit = frappe.get_all("Organisation Unit", pluck="name", limit=1)[0]
	return administration.grant(user=_make_user(user), business_role=role, organisation_unit=unit, actor="Administrator", **kwargs)["assignment"]


class TestAwardRoleMatrix(AwardCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		_remove_extras()
		cls.addClassCleanup(_remove_extras)

	def setUp(self):
		super().setUp()
		self.deliver()

	def refused(self, user: str, fn, **kwargs):
		"""The command is answered as a refusal or as a missing record, and changes nothing."""
		before = self.version()
		with self.assertRaises((AwardError, frappe.DoesNotExistError)) as ctx:
			self.run_as(user, fn, award=CASE, **kwargs)
		self.assertEqual(self.version(), before, f"{user} changed the case through {fn.__module__}.{fn.__name__}")
		if isinstance(ctx.exception, AwardError):
			self.assertEqual(ctx.exception.code, "AWD_AUTHORITY_REQUIRED")
		return ctx.exception

	# -- the role x command refusal matrix -----------------------------------------------
	def test_every_command_refuses_every_non_permitted_role(self):
		users = {role: _user_for(role) for role in OTHER_ROLES}
		for role, user in users.items():
			_grant(user, role)
		users["no responsibility"] = _make_user(f"{PREFIX}nobody{DOMAIN}")
		users["evaluation committee member"] = "grace.wambui@moh.example.test"  # signs the evaluation report; holds no Award responsibility
		users["Administrator"] = "Administrator"
		users["Auditor"] = NAOMI
		users["Technical Operator"] = DANIEL
		for label, user in users.items():
			for command, (fn, extra) in {**HOP_COMMANDS, **AO_COMMANDS}.items():
				with self.subTest(role=label, command=command):
					self.refused(user, fn, **extra)

	def test_hop_may_not_take_ao_commands_and_ao_may_not_take_hop_commands(self):
		for command, (fn, extra) in AO_COMMANDS.items():
			with self.subTest(user="HOP", command=command):
				self.assertEqual(self.refused(HOP, fn, **extra).code, "AWD_AUTHORITY_REQUIRED")
		for command, (fn, extra) in HOP_COMMANDS.items():
			with self.subTest(user="AO", command=command):
				self.assertEqual(self.refused(AO, fn, **extra).code, "AWD_AUTHORITY_REQUIRED")

	def test_a_frappe_role_alone_gives_no_award_authority(self):
		user = _make_user(f"{PREFIX}roleonly{DOMAIN}")
		frappe.get_doc("User", user).add_roles("System Manager", "Accounting Officer", "Head of Procurement Function")
		for command, (fn, extra) in {**HOP_COMMANDS, **AO_COMMANDS}.items():
			with self.subTest(command=command):
				self.refused(user, fn, **extra)

	def test_the_technical_operator_may_only_retry_an_operation(self):
		self.assertTrue(self.run_as(DANIEL, recovery.retry_operation, award=CASE)["ok"])
		for command, (fn, extra) in {**HOP_COMMANDS, **AO_COMMANDS}.items():
			with self.subTest(command=command):
				self.refused(DANIEL, fn, **extra)

	# -- effective dates ------------------------------------------------------------------
	def test_an_ended_or_not_yet_started_assignment_gives_no_authority(self):
		now = now_datetime()
		cases = {
			"ended HOP": (people.HEAD_OF_PROCUREMENT, add_days(now, -40), add_days(now, -10), HOP_COMMANDS),
			"scheduled HOP": (people.HEAD_OF_PROCUREMENT, add_days(now, 10), add_days(now, 40), HOP_COMMANDS),
			"ended AO": (people.ACCOUNTING_OFFICER, add_days(now, -40), add_days(now, -10), AO_COMMANDS),
			"scheduled AO": (people.ACCOUNTING_OFFICER, add_days(now, 10), add_days(now, 40), AO_COMMANDS),
		}
		for n, (label, (role, start, end, commands)) in enumerate(cases.items()):
			user = _user_for(f"{label}{n}")
			_grant(user, role, effective_from=str(start), effective_to=str(end))
			for command, (fn, extra) in commands.items():
				with self.subTest(case=label, command=command):
					self.refused(user, fn, **extra)

	def test_retry_operation_rechecks_the_technical_operator_effective_dates(self):
		user = _make_user(f"{PREFIX}expiredtech{DOMAIN}")
		now = now_datetime()
		_grant(user, people.TECHNICAL_OPERATOR, effective_from=str(add_days(now, -40)), effective_to=str(add_days(now, -10)))
		# the stored status is still Enabled; only the dates have passed
		self.assertTrue(frappe.db.exists("User Responsibility Assignment", {"user": user, "business_role": people.TECHNICAL_OPERATOR, "status": "Enabled"}))
		self.assertNotIn(user, people.technical_operators())
		self.assertFalse(people.is_technical_operator(user))
		before = self.version()
		with self.assertRaises(frappe.DoesNotExistError):
			self.run_as(user, recovery.retry_operation, award=CASE)
		self.assertEqual(self.version(), before)
		self.assertIn(DANIEL, people.technical_operators())

	# -- segregation of duties (open question Q3, default) -----------------------------------
	def take_offices(self, user: str, *roles: str) -> None:
		"""One person holds these (exclusive) offices for this test; the sitting holders are restored after."""
		for role in roles:
			sitting = frappe.get_all("User Responsibility Assignment", filters={"business_role": role, "status": "Enabled"}, pluck="name")
			for name in sitting:
				frappe.db.set_value("User Responsibility Assignment", name, "status", "Revoked", update_modified=False)
			self.addCleanup(lambda names=sitting: [frappe.db.set_value("User Responsibility Assignment", n, "status", "Enabled", update_modified=False) for n in names])
			_grant(user, role)

	def test_the_person_who_signed_the_opinion_cannot_record_the_decision(self):
		both = _make_user(f"{PREFIX}both{DOMAIN}")
		self.take_offices(both, people.HEAD_OF_PROCUREMENT, people.ACCOUNTING_OFFICER)
		self.at("2027-06-17 09:00:00")
		self.run_as(both, opinion.save, award=CASE, conclusion="Recommend award", reason="The signed report supports the recommendation.", expected_version=self.version())
		self.at("2027-06-17 09:10:00")
		signed = self.run_as(both, opinion.sign, award=CASE, expected_version=self.version())
		self.assertTrue(signed.get("signed"), signed)
		self.assertEqual(frappe.db.get_value(state.OPINION, {"award_case": CASE}, "signed_by"), both)
		self.at("2027-06-17 10:00:00")
		before = self.version()
		with self.assertRaises(AwardError) as ctx:
			self.run_as(both, decision.record, award=CASE, outcome="Award", reason="I accept it.", expected_version=before)
		self.assertEqual((ctx.exception.code, ctx.exception.detail["reason"]), ("AWD_AUTHORITY_REQUIRED", "segregation_of_duties"))
		self.assertEqual(self.version(), before)
		with self.assertRaises(AwardError) as ctx:
			self.run_as(both, corrections.record, award=CASE, outcome="Decline reconsideration", reason="x", expected_version=before)
		self.assertEqual(ctx.exception.detail.get("reason"), "segregation_of_duties")
		self.assertFalse(reads_actions(both)["decide"])

	def test_an_accounting_officer_who_did_not_prepare_the_opinion_decides_normally(self):
		self.signed_opinion()
		self.at("2027-06-17 10:00:00")
		self.assertTrue(self.run_as(AO, decision.record, award=CASE, outcome="Award", reason="I accept it.", expected_version=self.version())["ok"])

	def test_the_person_who_recorded_the_decision_cannot_prepare_or_sign_the_opinion(self):
		self.signed_opinion()  # Charles (the sitting HOP) prepared and signed it
		both = _make_user(f"{PREFIX}both2{DOMAIN}")
		self.take_offices(both, people.HEAD_OF_PROCUREMENT, people.ACCOUNTING_OFFICER)
		self.at("2027-06-17 10:00:00")
		self.run_as(both, decision.record, award=CASE, outcome="Return for correction", reason="Explain the unresolved funding concern.", expected_version=self.version())
		before = self.version()
		for fn, extra in ((opinion.save, {"conclusion": "Recommend award", "reason": "x"}), (opinion.sign, {})):
			with self.assertRaises(AwardError) as ctx:
				self.run_as(both, fn, award=CASE, expected_version=before, **extra)
			self.assertEqual(ctx.exception.detail.get("reason"), "segregation_of_duties")
		self.assertEqual(self.version(), before)
		self.assertFalse(reads_actions(both)["save_opinion"])


def reads_actions(user: str) -> dict:
	from kentender_procurement.award.services import reads

	return reads.record(award=CASE, user=user)["actions"]


class TestReplacedHeadOfProcurement(AwardCase):
	"""AUD-AWD-011: the Head of Procurement who received the report is no longer the holder."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.addClassCleanup(_remove_extras)

	def test_the_current_hop_can_return_a_report_the_replaced_hop_received(self):
		self.deliver(overrides={"recipient": FORMER_HOP})
		self.assertFalse(people.holds(FORMER_HOP, people.HEAD_OF_PROCUREMENT))
		out = self.run_as(HOP, opinion.return_report, award=CASE, reason="The service-location finding needs the committee's correction.", expected_version=self.version())
		self.assertTrue(out["ok"])
		doc = self.case()
		self.assertEqual((state.cycle(doc).awaiting_report, state.report(doc.current_report).state), (1, "Returned"))
		from kentender_procurement.award.test_services import sources as syn

		delivery = next(v for v in syn._state()["deliveries"].values() if v["tender_reference"] == "TND-AWT-2100-033")
		self.assertIn("who succeeded", delivery["return_comment"])  # Evaluation's record names the successor

	def test_someone_who_never_held_the_responsibility_still_cannot_return_it(self):
		self.deliver(overrides={"recipient": FORMER_HOP})
		stranger = _make_user(f"{PREFIX}stranger{DOMAIN}")
		with self.assertRaises(frappe.DoesNotExistError):
			self.run_as(stranger, opinion.return_report, award=CASE, reason="x")




if __name__ == "__main__":  # pragma: no cover
	unittest.main()
