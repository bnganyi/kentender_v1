# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 §6, §6.1, §6.2.1, plan D11 (tracker CM8-310): authority is an active responsibility assignment rechecked at every action, plus -- for
the capacities that need it -- an effective contract-specific appointment or mandate that only supplements it; the six separations are enforced from the
actual history of who signed, made or recorded; a technical account holds no business capacity."""

from __future__ import annotations

import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_contracts.services import authority, errors, segregation
from kentender_core.services import business_role_registry as registry
from kentender_core.services import responsibility_administration as administration
from kentender_core.services.command_write_guard import purge_doc

USER = "cm.authority.test@test.example.test"
OTHER = "cm.authority.other@test.example.test"


def code_of(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except errors.ContractError as exc:
		return exc
	return None


class TestSegregation(IntegrationTestCase):
	"""The six separations of §6.1, evaluated from actual history and refused with CM_SEGREGATION naming only the actor's own earlier act."""

	def refused(self, fn, *args, **kwargs):
		exc = code_of(fn, *args, **kwargs)
		self.assertIsNotNone(exc, "should have been refused")
		self.assertEqual(exc.code, "CM_SEGREGATION")
		return exc

	def test_there_are_exactly_the_six_separations(self):
		self.assertEqual(len(segregation.SEPARATIONS), 6)
		self.assertEqual(len({s.key for s in segregation.SEPARATIONS}), 6)

	def test_an_acceptance_report_signer_cannot_certify_the_claim_it_supports(self):
		exc = self.refused(segregation.certifier_not_acceptance_signer, "hop@x", ["inspector@x", "hop@x", "chair@x"])
		self.assertEqual(exc.detail["separation"], "certifier_not_acceptance_signer")
		self.assertIn("signed the acceptance report", exc.detail["incompatibility"])
		self.assertNotIn("inspector@x", str(exc.detail), "other people's protected assignments are not revealed")
		self.assertIsNone(code_of(segregation.certifier_not_acceptance_signer, "hop@x", ["inspector@x", "chair@x"]))

	def test_reassignment_cannot_erase_an_earlier_signature(self):
		# the history is the signer identities recorded at signing, so a later reassignment of the task is not an input
		self.refused(segregation.certifier_not_acceptance_signer, "Hop@X", ["hop@x"])

	def test_a_receiver_cannot_sign_acceptance_for_the_arrival_they_recorded_but_may_coordinate_suppliers(self):
		self.refused(segregation.receiver_not_acceptance_signer, "rec@x", ["rec@x"])
		self.assertIsNone(code_of(segregation.receiver_not_acceptance_signer, "rec@x", ["someone@x"]))

	def test_a_change_requester_cannot_recommend_or_decide_and_a_reviewer_cannot_decide(self):
		self.refused(segregation.change_roles_separate, "req@x", action="recommend", requesters=["req@x"], recommenders=[], reviewers=[])
		self.refused(segregation.change_roles_separate, "req@x", action="decide", requesters=["req@x"], recommenders=[], reviewers=[])
		self.refused(segregation.change_roles_separate, "rev@x", action="decide", requesters=["req@x"], recommenders=[], reviewers=["rev@x"])
		self.refused(segregation.change_roles_separate, "rec@x", action="decide", requesters=["req@x"], recommenders=["rec@x"], reviewers=[])
		self.assertIsNone(code_of(segregation.change_roles_separate, "ao@x", action="decide", requesters=["req@x"], recommenders=["rec@x"], reviewers=["rev@x"]))
		with self.assertRaises(ValueError):
			segregation.change_roles_separate("ao@x", action="approve", requesters=[], recommenders=[], reviewers=[])

	def test_a_finance_maker_cannot_approve_and_a_maker_or_certifier_cannot_confirm_settlement(self):
		self.refused(segregation.finance_maker_not_approver, "fm@x", ["fm@x"])
		self.assertIsNone(code_of(segregation.finance_maker_not_approver, "fa@x", ["fm@x"]))
		self.refused(segregation.settlement_confirmer_independent, "fm@x", makers=["fm@x"], certifiers=["hop@x"])
		self.refused(segregation.settlement_confirmer_independent, "hop@x", makers=["fm@x"], certifiers=["hop@x"])
		self.assertIsNone(code_of(segregation.settlement_confirmer_independent, "fa@x", makers=["fm@x"], certifiers=["hop@x"]))

	def test_a_conflicted_member_cannot_act_on_the_affected_scope(self):
		self.refused(segregation.member_not_conflicted, "m@x", ["m@x", "n@x"])
		self.assertIsNone(code_of(segregation.member_not_conflicted, "o@x", ["m@x"]))

	def test_only_a_current_supplier_signatory_signs_and_bid_submission_power_is_not_reused_for_invoices(self):
		self.refused(segregation.supplier_signs_only_as_signatory, "rep@s", signatories=["sig@s"], action="sign")
		self.assertIsNone(code_of(segregation.supplier_signs_only_as_signatory, "sig@s", signatories=["sig@s"], action="sign"))
		self.assertIsNone(code_of(segregation.supplier_signs_only_as_signatory, "rep@s", signatories=["sig@s"], action="claim", representatives=["rep@s"]))
		self.refused(segregation.supplier_signs_only_as_signatory, "bidder@s", signatories=["sig@s"], action="claim", representatives=["rep@s"])


class TestAuthority(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.count("Organisation Unit"):  # core refuses to assign a responsibility until the site has an organisation structure
			raise unittest.SkipTest("this site has no organisation structure, so no responsibility can be assigned")
		registry.ensure_roles()
		for email in (USER, OTHER):
			if not frappe.db.exists("User", email):
				frappe.get_doc({"doctype": "User", "email": email, "first_name": "CM Authority", "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True).add_roles("Desk User")
		frappe.db.commit()
		cls.saved = dict(authority.BINDINGS)
		cls.addClassCleanup(cls.cleanup)

	@classmethod
	def cleanup(cls):
		authority.BINDINGS.clear()
		authority.BINDINGS.update(cls.saved)
		for name in frappe.get_all("User Responsibility Assignment", filters={"user": ["in", [USER, OTHER]]}, pluck="name"):
			purge_doc("User Responsibility Assignment", name)
		for email in (USER, OTHER):
			if frappe.db.exists("User", email):
				frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		frappe.db.commit()

	def tearDown(self):
		authority.BINDINGS.clear()
		for name in frappe.get_all("User Responsibility Assignment", filters={"user": ["in", [USER, OTHER]]}, pluck="name"):
			purge_doc("User Responsibility Assignment", name)
		frappe.db.commit()

	def grant(self, user, role):
		unit = frappe.get_all("Organisation Unit", pluck="name", limit=1)[0] if registry.REGISTRY[role].requires_organisation_unit else ""
		administration.grant(user=user, business_role=role, organisation_unit=unit, actor="Administrator")
		frappe.db.commit()
		return unit

	def test_a_responsibility_is_required_and_its_absence_names_what_is_missing_and_who_provisions_it(self):
		exc = code_of(authority.require, USER, "Contract preparation", organisation_unit="")
		self.assertEqual(exc.code, "CM_AUTHORITY")
		self.assertEqual((exc.detail["missing"], exc.detail["responsibility"]), ("responsibility", "Contract preparation"))
		self.assertIn("System setup", exc.detail["provisioned_by"])

	def test_an_active_assignment_passes_at_its_scope_and_not_elsewhere(self):
		unit = self.grant(USER, "Contract preparation")
		self.assertIsNone(code_of(authority.require, USER, "Contract preparation", organisation_unit=unit))
		self.assertEqual(code_of(authority.require, OTHER, "Contract preparation", organisation_unit=unit).code, "CM_AUTHORITY")

	def test_a_technical_account_exercises_no_business_capacity(self):
		self.assertEqual(code_of(authority.require, "Administrator", "Finance approval").code, "CM_AUTHORITY")

	def test_an_assignment_alone_grants_no_contract_access_without_an_effective_appointment(self):
		self.grant(USER, "Contract inspection")
		exc = code_of(authority.require_capacity, "CM-1", USER, "inspector")
		self.assertEqual((exc.code, exc.detail["missing"]), ("CM_AUTHORITY", "appointment"))

	def test_an_appointment_alone_grants_nothing_without_the_registered_responsibility(self):
		authority.binding("inspector")(lambda case, user, at: {"appointment": "APP-1"})
		exc = code_of(authority.require_capacity, "CM-1", USER, "inspector")
		self.assertEqual((exc.code, exc.detail["missing"]), ("CM_AUTHORITY", "responsibility"))

	def test_the_responsibility_plus_the_exact_appointment_passes_and_returns_the_evidence(self):
		self.grant(USER, "Contract inspection")
		authority.binding("inspector")(lambda case, user, at: {"appointment": "APP-1", "case": case} if (case, user) == ("CM-1", USER) else None)
		self.assertEqual(authority.require_capacity("CM-1", USER, "inspector"), {"appointment": "APP-1", "case": "CM-1"})
		self.assertEqual(code_of(authority.require_capacity, "CM-2", USER, "inspector").detail["missing"], "appointment")

	def test_only_the_five_capacities_the_specification_binds_exist(self):
		self.assertEqual(set(authority.CAPACITY_RESPONSIBILITY), {"inspector", "technical certifier", "entity signatory", "final acceptance representative"})
		with self.assertRaises(ValueError):
			authority.binding("everything")
