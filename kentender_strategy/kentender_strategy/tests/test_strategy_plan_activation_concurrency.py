# Copyright (c) 2026, KenTender and contributors
"""STR-FR-005 Active plan concurrency — domain evidence."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_contracts import create_plan
from kentender_strategy.services.strategy_domain_guards import PLAN_TYPE_ENTITY, PLAN_TYPE_PROGRAMME
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles
from kentender_strategy.services.strategy_transitions import transition_plan


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
	user.add_roles(*roles)
	if procuring_entity:
		frappe.defaults.set_user_default("Procuring Entity", procuring_entity, user=email)
	return email


def _force_status(plan_name: str, status: str) -> None:
	frappe.db.set_value("Strategic Plan", plan_name, "status", status, update_modified=False)


def _force_blank_scope(plan_name: str) -> None:
	"""Simulate a pre-normalization legacy row — bypasses the controller's own
	validate()-time scope_type/scope_id fill, which is otherwise unconditional
	for every Entity Strategic Plan on every save."""
	frappe.db.set_value(
		"Strategic Plan", plan_name, {"scope_type": None, "scope_id": None}, update_modified=False
	)


class TestStrategyPlanActivationConcurrency(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()
		cls.pe = cls.seed["procuring_entity"]
		cls.master = cls.seed["plan"]

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def _cleanup(self, plan_id: str | None):
		if plan_id and frappe.db.exists("Strategic Plan", plan_id):
			frappe.delete_doc("Strategic Plan", plan_id, force=True, ignore_permissions=True)

	def _create_approved(self, **over) -> str:
		_ensure_user("str.mgr.conc@example.com", ["Strategy Manager", "Planning Authority"], self.pe)
		frappe.set_user("str.mgr.conc@example.com")
		code = over.pop("plan_code", f"CONC-{frappe.generate_hash(length=6).upper()}")
		payload = {
			"plan_code": code,
			"title": over.pop("title", "Concurrency Fixture"),
			"plan_type": over.pop("plan_type", PLAN_TYPE_ENTITY),
			"procuring_entity": self.pe,
			"start_date": over.pop("start_date", "2026-07-01"),
			"end_date": over.pop("end_date", "2028-06-30"),
			"description": "STR-FR-005 fixture",
		}
		payload.update(over)
		created = create_plan(payload)
		self.assertTrue(created.get("ok"), created)
		plan_id = created["plan"]["id"]
		self.addCleanup(lambda: self._cleanup(plan_id))
		# Bypass readiness hierarchy for concurrency-focused Activate tests.
		_force_status(plan_id, "Approved")
		return plan_id

	def test_overlapping_active_esp_rejected(self):
		plan_id = self._create_approved(
			plan_code=f"ESP-OL-{frappe.generate_hash(length=4).upper()}",
			start_date="2027-01-01",
			end_date="2028-12-31",
		)
		frappe.set_user("str.mgr.conc@example.com")
		with self.assertRaises(frappe.ValidationError) as ctx:
			transition_plan(plan_id, "Activate")
		msg = str(ctx.exception).lower()
		self.assertTrue("overlapping" in msg or "entity strategic plan" in msg, msg)

	def test_legacy_blank_scope_esp_still_blocks_overlap(self):
		"""SCL-601 — an existing Active ESP row with blank scope_type/scope_id
		(simulating a record that predates the doctype's own scope-normalization
		save hook) must still be treated as occupying its period; a new
		overlapping ESP for the same entity cannot activate."""
		legacy = self._create_approved(
			plan_code=f"ESP-LEGACY-{frappe.generate_hash(length=4).upper()}",
			start_date="2040-01-01",
			end_date="2041-12-31",
		)
		frappe.set_user("str.mgr.conc@example.com")
		self.assertEqual(transition_plan(legacy, "Activate")["status"], "Active")
		frappe.set_user("Administrator")
		_force_blank_scope(legacy)
		self.assertFalse(frappe.db.get_value("Strategic Plan", legacy, "scope_type"))

		challenger = self._create_approved(
			plan_code=f"ESP-CHAL-{frappe.generate_hash(length=4).upper()}",
			start_date="2040-06-01",
			end_date="2042-06-30",
		)
		frappe.set_user("str.mgr.conc@example.com")
		with self.assertRaises(frappe.ValidationError) as ctx:
			transition_plan(challenger, "Activate")
		msg = str(ctx.exception).lower()
		self.assertTrue("overlaps" in msg or "entity strategic plan" in msg, msg)

	def test_subordinate_without_parent_rejected(self):
		# create_plan requires parent — build via ORM for this negative activate case
		doc = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"plan_code": f"PROG-NP-{frappe.generate_hash(length=4).upper()}",
				"version_number": 1,
				"title": "Programme without parent",
				"procuring_entity": self.pe,
				"plan_type": PLAN_TYPE_PROGRAMME,
				"scope_type": "Programme",
				"scope_id": "MOH-PROG-HR",
				"parent_plan": None,
				"status": "Approved",
				"start_date": "2026-07-01",
				"end_date": "2028-06-30",
			}
		).insert(ignore_permissions=True)
		self.addCleanup(lambda: self._cleanup(doc.name))
		_ensure_user("str.pa.conc@example.com", ["Planning Authority"], self.pe)
		frappe.set_user("str.pa.conc@example.com")
		with self.assertRaises(frappe.ValidationError) as ctx:
			transition_plan(doc.name, "Activate")
		self.assertIn("parent", str(ctx.exception).lower())

	def test_subordinate_with_parent_and_distinct_scope_allowed(self):
		scope_id = f"MOH-PROG-OK-{frappe.generate_hash(length=4).upper()}"
		plan_id = self._create_approved(
			plan_code=f"PROG-OK-{frappe.generate_hash(length=4).upper()}",
			plan_type=PLAN_TYPE_PROGRAMME,
			parent_plan=self.master,
			scope_type="Programme",
			scope_id=scope_id,
			start_date="2026-07-01",
			end_date="2028-06-30",
		)
		frappe.set_user("str.mgr.conc@example.com")
		out = transition_plan(plan_id, "Activate")
		self.assertEqual(out["status"], "Active")
		doc = frappe.get_doc("Strategic Plan", plan_id)
		self.assertEqual(doc.parent_plan, self.master)
		self.assertEqual(doc.scope_id, scope_id)

	def test_same_type_scope_overlap_rejected(self):
		first = self._create_approved(
			plan_code=f"PROG-A-{frappe.generate_hash(length=4).upper()}",
			plan_type=PLAN_TYPE_PROGRAMME,
			parent_plan=self.master,
			scope_type="Programme",
			scope_id="MOH-PROG-SCOPE-X",
			start_date="2026-07-01",
			end_date="2028-06-30",
		)
		frappe.set_user("str.mgr.conc@example.com")
		self.assertEqual(transition_plan(first, "Activate")["status"], "Active")

		second = self._create_approved(
			plan_code=f"PROG-B-{frappe.generate_hash(length=4).upper()}",
			plan_type=PLAN_TYPE_PROGRAMME,
			parent_plan=self.master,
			scope_type="Programme",
			scope_id="MOH-PROG-SCOPE-X",
			start_date="2027-01-01",
			end_date="2029-06-30",
		)
		with self.assertRaises(frappe.ValidationError) as ctx:
			transition_plan(second, "Activate")
		self.assertIn("overlapping", str(ctx.exception).lower())

	def test_same_plan_code_still_supersedes(self):
		# Successor of master ESP with non-conflicting path: clone Approved successor overlapping
		# same plan_code must supersede, not reject.
		src = frappe.get_doc("Strategic Plan", self.master)
		succ = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"plan_code": STRATEGY_PLAN_CODE,
				"version_number": int(src.version_number or 1) + 100,
				"title": src.title + " successor concurrency",
				"procuring_entity": self.pe,
				"plan_type": PLAN_TYPE_ENTITY,
				"scope_type": "Procuring Entity",
				"scope_id": self.pe,
				"status": "Approved",
				"start_date": src.start_date,
				"end_date": src.end_date,
				"supersedes_plan_version": src.name,
			}
		).insert(ignore_permissions=True)
		self.addCleanup(lambda: self._cleanup(succ.name))
		_ensure_user("str.pa.succ@example.com", ["Planning Authority"], self.pe)
		frappe.set_user("str.pa.succ@example.com")
		out = transition_plan(succ.name, "Activate")
		self.assertEqual(out["status"], "Active")
		self.assertEqual(frappe.db.get_value("Strategic Plan", self.master, "status"), "Superseded")
		# Restore master Active for other tests / seed consumers
		frappe.set_user("Administrator")
		frappe.db.set_value("Strategic Plan", succ.name, "status", "Superseded", update_modified=False)
		frappe.db.set_value("Strategic Plan", self.master, "status", "Active", update_modified=False)

	def test_create_programme_requires_parent(self):
		_ensure_user("str.off.conc@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.off.conc@example.com")
		missing = create_plan(
			{
				"plan_code": f"PROG-REQ-{frappe.generate_hash(length=4).upper()}",
				"title": "Needs parent",
				"plan_type": PLAN_TYPE_PROGRAMME,
				"procuring_entity": self.pe,
				"scope_type": "Programme",
				"scope_id": "MOH-PROG-HR",
				"start_date": "2026-07-01",
				"end_date": "2028-06-30",
			}
		)
		self.assertFalse(missing.get("ok"))
		self.assertIn("parent_plan", missing.get("errors") or {})

	def test_create_esp_auto_scope_no_parent(self):
		_ensure_user("str.off.esp@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.off.esp@example.com")
		created = create_plan(
			{
				"plan_code": f"ESP-NEW-{frappe.generate_hash(length=4).upper()}",
				"title": "ESP create scope",
				"plan_type": PLAN_TYPE_ENTITY,
				"procuring_entity": self.pe,
				"start_date": "2032-07-01",
				"end_date": "2034-06-30",
			}
		)
		self.assertTrue(created.get("ok"), created)
		plan = created["plan"]
		self.addCleanup(lambda: self._cleanup(plan["id"]))
		self.assertEqual(plan["scope_type"], "Procuring Entity")
		self.assertEqual(plan["scope_id"], self.pe)
		self.assertIsNone(plan.get("parent_plan"))
