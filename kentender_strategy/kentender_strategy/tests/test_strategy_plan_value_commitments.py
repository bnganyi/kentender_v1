# Copyright (c) 2026, KenTender and contributors
"""STR-UI-07 Plan Value Commitments — list DTO, upsert, Active lock."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	OBJECTIVE_CODE,
	STRATEGY_PLAN_CODE,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_contracts import create_plan, list_plan_value_commitments
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles
from kentender_strategy.services.strategy_writes import upsert_plan_value_commitment


def _ensure_user(email: str, roles: list[str], procuring_entity: str | None = None) -> str:
	ensure_strategy_roles()
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		)
		user.insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	user.enabled = 1
	user.save(ignore_permissions=True)
	have = set(frappe.get_roles(email))
	for role in (
		"Strategy Viewer",
		"Strategy Officer",
		"Strategy Manager",
		"Strategy Reviewer",
		"Planning Authority",
	):
		if role in have and role not in roles:
			user.remove_roles(role)
	user.add_roles(*roles)
	if procuring_entity:
		frappe.defaults.set_user_default("Procuring Entity", procuring_entity, user=email)
	return email


def _delete_plan_cascade(plan_id: str | None):
	if not plan_id or not frappe.db.exists("Strategic Plan", plan_id):
		return
	for dt in (
		"Plan Value Commitment",
		"Performance Target",
		"Performance Indicator",
		"Strategic Outcome",
		"Strategy Sub Programme",
		"Strategy Programme",
		"Strategy Audit Event",
	):
		for name in frappe.get_all(dt, filters={"plan_version": plan_id}, pluck="name"):
			frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
	frappe.delete_doc("Strategic Plan", plan_id, force=True, ignore_permissions=True)


def _active_pvo(code: str) -> str:
	name = frappe.db.get_value(
		"Public Value Objective", {"objective_code": code, "status": "Active"}, "name"
	)
	if not name:
		name = frappe.db.get_value("Public Value Objective", {"objective_code": code}, "name")
	return name


class TestStrategyPlanValueCommitments(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()
		cls.pe = cls.seed["procuring_entity"]
		cls.plan_id = cls.seed["plan"]
		if cls.plan_id:
			status = frappe.db.get_value("Strategic Plan", cls.plan_id, "status")
			if status != "Active":
				frappe.db.set_value("Strategic Plan", cls.plan_id, "status", "Active")

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_active_moh_list_enriched_and_read_only(self):
		_ensure_user("str.officer.vc@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.vc@example.com")
		dto = list_plan_value_commitments(plan_code=STRATEGY_PLAN_CODE)
		self.assertIsInstance(dto, dict)
		self.assertEqual(dto["plan"]["code"], STRATEGY_PLAN_CODE)
		self.assertEqual(dto["plan"]["status"], "Active")
		self.assertFalse(dto["capabilities"]["editable"])
		codes = {r["objective"]["code"] for r in dto["rows"]}
		self.assertIn("PVO-EFT-01", codes)
		self.assertIn("PVO-ECO-01", codes)
		eft = next(r for r in dto["rows"] if r["objective"]["code"] == "PVO-EFT-01")
		self.assertTrue(eft["complete"])
		link_codes = {lnk.get("code") for lnk in eft["links"]}
		self.assertIn(OBJECTIVE_CODE, link_codes)
		self.assertTrue(any(lnk.get("name") for lnk in eft["links"]))
		self.assertGreaterEqual(dto["progress"]["total"], 2)
		self.assertEqual(dto["progress"]["complete"], dto["progress"]["total"])

	def test_officer_can_upsert_on_draft(self):
		_ensure_user("str.officer.vc.draft@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.vc.draft@example.com")
		code = f"STR-VC-{frappe.generate_hash(length=5).upper()}"
		created = create_plan(
			{
				"plan_code": code,
				"title": "VC Draft Plan",
				"plan_type": "Entity Strategic Plan",
				"procuring_entity": self.pe,
				"start_date": "2026-07-01",
				"end_date": "2030-06-30",
			}
		)
		plan_id = created["plan"]["id"]
		self.addCleanup(lambda: _delete_plan_cascade(plan_id))

		# Minimal structure so we can link an outcome
		from kentender_strategy.services.strategy_writes import upsert_structure_node

		prog = upsert_structure_node(
			{
				"type": "Programme",
				"plan_version": plan_id,
				"code": f"{code}-P",
				"title": "Prog",
				"responsible_function": "ICT",
			}
		)
		out = upsert_structure_node(
			{
				"type": "StrategicOutcome",
				"plan_version": plan_id,
				"programme": prog["id"],
				"code": f"{code}-O",
				"title": "Outcome",
				"description": "d",
				"responsible_function": "ICT",
			}
		)
		pvo = _active_pvo("PVO-LOC-01")
		self.assertTrue(pvo)
		res = upsert_plan_value_commitment(
			{
				"plan_version": plan_id,
				"public_value_objective_version": pvo,
				"rationale": "Local capability for this plan",
				"consideration_level": "recommended",
				"responsible_owner": "Director, Digital Health",
				"status": "Draft",
				"links": [{"link_type": "Strategic Outcome", "linked_outcome": out["id"]}],
			}
		)
		self.assertTrue(res.get("id"))
		dto = list_plan_value_commitments(plan_version=plan_id)
		self.assertTrue(dto["capabilities"]["editable"])
		self.assertEqual(dto["progress"]["total"], 1)
		self.assertEqual(dto["progress"]["complete"], 1)
		row = dto["rows"][0]
		self.assertEqual(row["objective"]["code"], "PVO-LOC-01")
		self.assertTrue(row["complete"])
		self.assertEqual(row["links"][0]["code"], f"{code}-O")

	def test_active_plan_blocks_upsert(self):
		_ensure_user("str.officer.vc.lock@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.vc.lock@example.com")
		pvo = _active_pvo("PVO-SUS-01")
		with self.assertRaises(frappe.ValidationError):
			upsert_plan_value_commitment(
				{
					"plan_version": self.plan_id,
					"public_value_objective_version": pvo,
					"rationale": "Should fail",
					"consideration_level": "Required consideration",
					"responsible_owner": "Owner",
					"links": [],
				}
			)

	def test_viewer_cannot_upsert(self):
		_ensure_user("str.viewer.vc@example.com", ["Strategy Viewer"], self.pe)
		frappe.set_user("str.viewer.vc@example.com")
		pvo = _active_pvo("PVO-SUS-01")
		with self.assertRaises(frappe.PermissionError):
			upsert_plan_value_commitment(
				{
					"plan_version": self.plan_id,
					"public_value_objective_version": pvo,
					"rationale": "Nope",
					"consideration_level": "Available",
					"responsible_owner": "X",
					"links": [{"link_type": "Strategic Outcome", "linked_outcome": "x"}],
				}
			)

	def test_incomplete_without_links(self):
		_ensure_user("str.manager.vc@example.com", ["Strategy Manager"], self.pe)
		frappe.set_user("Administrator")
		code = f"STR-VCI-{frappe.generate_hash(length=5).upper()}"
		created = create_plan(
			{
				"plan_code": code,
				"title": "VC Incomplete",
				"plan_type": "Entity Strategic Plan",
				"procuring_entity": self.pe,
				"start_date": "2026-07-01",
				"end_date": "2030-06-30",
			}
		)
		plan_id = created["plan"]["id"]
		self.addCleanup(lambda: _delete_plan_cascade(plan_id))
		pvo = _active_pvo("PVO-SUS-02")
		doc = frappe.get_doc(
			{
				"doctype": "Plan Value Commitment",
				"plan_version": plan_id,
				"public_value_objective_version": pvo,
				"rationale": "Needs a link",
				"consideration_level": "Required consideration",
				"responsible_owner": "Owner",
				"status": "Draft",
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.set_user("str.manager.vc@example.com")
		dto = list_plan_value_commitments(plan_version=plan_id)
		row = dto["rows"][0]
		self.assertFalse(row["complete"])
		self.assertEqual(dto["progress"]["complete"], 0)
		self.assertEqual(dto["progress"]["total"], 1)
