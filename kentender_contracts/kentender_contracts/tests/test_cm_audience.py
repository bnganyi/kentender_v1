# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 §6.2 (tracker CM8-311; CM-AC-20, 43, 48 started): the eleven reader audiences are the specification's, each decided separately by AUTH's role-bound
resolver so one role's unit never broadens another; fields are the union of what the matching audiences allow; nothing is counted or paged before the authority filter;
a reader who may read is never denied for lacking a task or a command responsibility.

The AUTH answer is a controlled fake here so every audience and scope can be exercised; one test at the end uses a real assignment."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

import frappe
from frappe.tests import IntegrationTestCase

from kentender_contracts.services import audience, authority, errors, reads
from kentender_core.services import business_role_registry as registry
from kentender_core.services import responsibility_administration as administration
from kentender_core.services.command_write_guard import purge_doc

SPEC = Path(frappe.get_app_path("kentender_contracts")).resolve().parents[1] / "docs/mvp-1-r1/21_contract_management/KenTender_CM-CHG-001_Contract_Management_v0_8.md"
A, B = "OU-A", "OU-B"
FACTS = audience.Facts(case="CM-1", managing_unit=A, source_units=("OU-SRC",), supplier_organisation="ORG-1")


class Fake:
	"""A controlled AUTH: `holding` is a set of (role, unit) the user holds; `technical` makes the user a technical account."""

	def __init__(self, holding=(), technical=False):
		self.holding, self.is_technical = set(holding), technical

	def holds(self, user, role, unit="", *, at=None):
		return (role, unit) in self.holding

	def tech(self, user):
		return self.is_technical

	def __enter__(self):
		self.patches = [mock.patch.object(audience.people, "holds", side_effect=self.holds), mock.patch.object(audience.people, "technical", side_effect=self.tech)]
		for p in self.patches:
			p.start()
		return self

	def __exit__(self, *exc):
		for p in self.patches:
			p.stop()


def keys(found):
	return [g.audience for g in found]


class SupplierProvider:
	def __init__(self, assignments):
		self.assignments = assignments

	def active_assignments(self, *, user, at=None):
		return self.assignments.get(user, [])


class TestAudienceTable(IntegrationTestCase):
	def test_the_audiences_are_exactly_the_rows_of_the_specification_table(self):
		lines = SPEC.read_text().splitlines()
		start = next(i for i, line in enumerate(lines) if line.startswith("| Reader | Discoverability"))
		rows = []
		for line in lines[start + 2:]:
			if not line.startswith("|"):
				break
			rows.append(line.split("|")[1].strip())
		self.assertEqual([a.label for a in audience.AUDIENCES], rows)

	def test_the_field_set_policy_follows_the_specification(self):
		sets = {a.key: a.field_sets for a in audience.AUDIENCES}
		self.assertFalse(set().union(*sets.values()) - set(audience.FIELD_SETS))
		self.assertTrue(all("bank_full" not in s for s in sets.values()), "full banking is only for an independently reviewed oversight projection")
		self.assertEqual(sets["supplier"], {"core", "supplier_view"}, "the supplier sees nothing internal: no deliberation, allocation, accounts or banking")
		self.assertEqual({k for k, s in sets.items() if "finance_accounts" in s}, {"finance", "technical"})
		self.assertEqual({k for k, s in sets.items() if "deliberation" in s}, {"office"})
		for key in ("preparer", "coordinator", "receiver", "user_department", "appointee", "signatory"):
			self.assertNotIn("money_native", sets[key], f"{key} has no Finance editor or native payment projection")
		self.assertIn("money_summary", sets["receiver"])
		self.assertNotIn("money_summary", sets["appointee"])
		self.assertEqual(sets["signatory"] & {"terms", "delivery", "money_summary"}, set(), "an entity signatory reads the signature subject, not unrelated powers")


class TestResolver(IntegrationTestCase):
	def setUp(self):
		self.saved = (dict(authority.BINDINGS), dict(authority.READ_BINDINGS), frappe.flags.get("kt_supplier_account_provider"))
		authority.BINDINGS.clear()
		authority.READ_BINDINGS.clear()

	def tearDown(self):
		authority.BINDINGS.clear()
		authority.BINDINGS.update(self.saved[0])
		authority.READ_BINDINGS.clear()
		authority.READ_BINDINGS.update(self.saved[1])
		frappe.flags.kt_supplier_account_provider = self.saved[2]

	def test_the_office_reads_every_contract_without_a_task(self):
		with Fake({("Accounting Officer", "")}):
			self.assertEqual(keys(audience.grants("ao@x", FACTS)), ["office"])
			self.assertEqual(keys(audience.grants("ao@x", audience.Facts(case="CM-2"))), ["office"])

	def test_an_organisation_unit_responsibility_reads_only_at_the_managing_unit(self):
		with Fake({("Contract preparation", A)}):
			self.assertEqual(keys(audience.grants("p@x", FACTS)), ["preparer"])
			self.assertEqual(keys(audience.grants("p@x", audience.Facts(case="CM-2", managing_unit=B))), [])
			self.assertEqual(keys(audience.grants("p@x", audience.Facts(case="CM-3"))), [], "no managing unit, no unit-scoped read")

	def test_one_roles_unit_never_broadens_another_role(self):
		with Fake({("Contract preparation", A), ("Receiving", B)}):
			in_a, in_b = audience.grants("u@x", FACTS), audience.grants("u@x", audience.Facts(case="CM-2", managing_unit=B))
			self.assertEqual((keys(in_a), keys(in_b)), (["preparer"], ["receiver"]))
			self.assertNotEqual(audience.field_sets(in_a), audience.field_sets(in_b))
			self.assertNotIn("appointments", audience.field_sets(in_b))

	def test_the_head_of_user_department_reads_through_the_managing_unit_or_a_named_source_unit_only(self):
		with Fake({("Head of User Department", "OU-SRC")}):
			self.assertEqual(keys(audience.grants("h@x", FACTS)), ["user_department"])
			self.assertEqual(keys(audience.grants("h@x", audience.Facts(case="CM-2", managing_unit=B))), [])
		with Fake({("Departmental Author", A), ("Planner", A)}):
			self.assertEqual(keys(audience.grants("d@x", FACTS)), [], "Departmental Author, Planner or Evaluation membership alone grants no contract access")

	def test_an_appointee_needs_the_responsibility_and_the_exact_appointment_and_reads_while_a_declaration_is_pending(self):
		authority.binding("inspector")(lambda case, user, at: {"appointment": "APP-1"} if (case, user) == ("CM-1", "i@x") else None)
		with Fake({("Contract inspection", "")}):
			self.assertEqual(keys(audience.grants("i@x", FACTS)), ["appointee"])
			self.assertEqual(audience.grants("i@x", FACTS)[0].evidence["appointment"], "APP-1")
			self.assertEqual(keys(audience.grants("i@x", audience.Facts(case="CM-2"))), [], "another contract")
			self.assertEqual(keys(audience.grants("other@x", FACTS)), [], "someone else")
		with Fake():
			self.assertEqual(keys(audience.grants("i@x", FACTS)), [], "an appointment alone grants nothing")
		with Fake({("Contract inspection", "")}):
			authority.BINDINGS.clear()
			authority.binding("inspector", read=True)(lambda case, user, at: {"appointment": "APP-2", "declaration": "pending"})
			self.assertEqual(keys(audience.grants("i@x", FACTS)), ["appointee"], "a wider read provider admits a reader whose action is not yet effective")

	def test_an_entity_signatory_reads_the_signing_subject_with_responsibility_and_mandate(self):
		authority.binding("entity signatory")(lambda case, user, at: {"mandate": "M-1"})
		with Fake({("Entity contract signing", "")}):
			found = audience.grants("s@x", FACTS)
		self.assertEqual(keys(found), ["signatory"])
		self.assertIn("signing_subject", audience.field_sets(found))

	def test_a_supplier_reads_only_its_own_contract_through_its_active_organisation_binding(self):
		frappe.flags.kt_supplier_account_provider = SupplierProvider({
			"rep@s": [{"organisation_id": "ORG-1", "responsibility": "Supplier Representative", "active": True}],
			"old@s": [{"organisation_id": "ORG-1", "responsibility": "Authorised Signatory", "active": False}],
			"rival@s": [{"organisation_id": "ORG-2", "responsibility": "Supplier Representative", "active": True}],
		})
		with Fake():
			self.assertEqual(keys(audience.grants("rep@s", FACTS)), ["supplier"])
			self.assertEqual(keys(audience.grants("old@s", FACTS)), [], "an expired binding keeps no live access")
			self.assertEqual(keys(audience.grants("rival@s", FACTS)), [], "another supplier")
			self.assertEqual(keys(audience.grants("staff@x", FACTS)), [])
			self.assertEqual(audience.field_sets(audience.grants("rep@s", FACTS)), {"core", "supplier_view"})

	def test_a_technical_account_reads_as_the_technical_audience_only_and_holds_no_business_capacity(self):
		with Fake({("Accounting Officer", ""), ("Finance approval", "")}, technical=True):
			found = audience.grants("daniel@x", FACTS)
		self.assertEqual(keys(found), ["technical"])
		self.assertNotIn("deliberation", audience.field_sets(found))

	def test_a_user_in_several_audiences_sees_the_union(self):
		with Fake({("Contract preparation", A), ("Finance approval", "")}):
			found = audience.grants("u@x", FACTS)
		self.assertEqual(keys(found), ["preparer", "finance"])
		self.assertTrue({"finance_accounts", "appointments", "source_projection"} <= audience.field_sets(found))

	def test_no_user_and_the_guest_read_nothing_and_a_denial_is_stable(self):
		self.assertEqual(audience.grants("", FACTS), [])
		self.assertEqual(audience.grants("Guest", FACTS), [])
		with Fake(), mock.patch.object(audience, "facts_of", return_value=FACTS):
			with self.assertRaises(errors.ContractError) as caught:
				audience.require_read("nobody@x", "CM-1")
		self.assertEqual((caught.exception.code, caught.exception.detail["denied"]), ("CM_AUTHORITY", True))


class TestReadModels(IntegrationTestCase):
	FIELDS = {"name": "core", "agreement": "terms", "bank_account": "finance_accounts", "paid": "money_native", "comment": "deliberation"}
	VALUES = {"name": "CM-1", "agreement": "A", "bank_account": "0001", "paid": 5, "comment": "internal", "extra": "never listed"}

	def test_only_the_fields_the_readers_audiences_reach_are_in_the_answer(self):
		receiver = [audience.Grant("receiver", audience.BY_KEY["receiver"].field_sets)]
		self.assertEqual(reads.project(self.FIELDS, self.VALUES, receiver), {"name": "CM-1"})
		both = [audience.Grant("preparer", audience.BY_KEY["preparer"].field_sets), audience.Grant("finance", audience.BY_KEY["finance"].field_sets)]
		self.assertEqual(reads.project(self.FIELDS, self.VALUES, both), {"name": "CM-1", "agreement": "A", "bank_account": "0001", "paid": 5})
		self.assertEqual(reads.project(self.FIELDS, self.VALUES, []), {})
		with self.assertRaises(ValueError):
			reads.project({"x": "not a field set"}, {"x": 1}, both)

	def test_a_list_is_filtered_by_authority_before_it_is_counted_or_paged(self):
		def resolver(user, case, at=None):
			return [audience.Grant("preparer")] if case in ("C2", "C4", "C5") else []

		with mock.patch.object(audience, "readable", side_effect=resolver):
			first = reads.page("u@x", ["C1", "C2", "C3", "C4", "C5"], number=1, size=2)
			second = reads.page("u@x", ["C1", "C2", "C3", "C4", "C5"], number=2, size=2)
		self.assertEqual((first["total"], [r["case"] for r in first["rows"]]), (3, ["C2", "C4"]))
		self.assertEqual((second["total"], [r["case"] for r in second["rows"]]), (3, ["C5"]))
		self.assertEqual(first["rows"][0]["audiences"], ["preparer"])


class TestRealAssignment(IntegrationTestCase):
	USER = "cm.audience.test@test.example.test"

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.count("Organisation Unit"):
			raise unittest.SkipTest("this site has no organisation structure, so no responsibility can be assigned")
		registry.ensure_roles()
		if not frappe.db.exists("User", cls.USER):
			frappe.get_doc({"doctype": "User", "email": cls.USER, "first_name": "CM Audience", "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True).add_roles("Desk User")
		frappe.db.commit()
		cls.addClassCleanup(cls.cleanup)

	@classmethod
	def cleanup(cls):
		for name in frappe.get_all("User Responsibility Assignment", filters={"user": cls.USER}, pluck="name"):
			purge_doc("User Responsibility Assignment", name)
		if frappe.db.exists("User", cls.USER):
			frappe.delete_doc("User", cls.USER, force=True, ignore_permissions=True)
		frappe.db.commit()

	def test_a_real_contract_preparation_assignment_reads_at_its_unit_and_a_user_without_one_reads_nothing(self):
		unit = frappe.get_all("Organisation Unit", pluck="name", limit=1)[0]
		facts = audience.Facts(case="CM-1", managing_unit=unit)
		self.assertEqual(audience.grants(self.USER, facts), [])
		administration.grant(user=self.USER, business_role="Contract preparation", organisation_unit=unit, actor="Administrator")
		frappe.db.commit()
		self.assertEqual(keys(audience.grants(self.USER, facts)), ["preparer"])
		self.assertEqual(audience.grants(self.USER, audience.Facts(case="CM-2")), [], "the case names no managing unit, so a unit-scoped responsibility reads nothing")
