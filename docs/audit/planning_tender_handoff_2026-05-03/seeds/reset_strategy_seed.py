# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Remove seeded Strategic Plans (by spec titles) and all hierarchy rows. See plan Part G."""

from __future__ import annotations

import frappe

from kentender_core.seeds import constants as C


def run(dry_run: bool = False):
	frappe.only_for(("System Manager", "Administrator"))
	titles = (C.PLAN_BASIC_NAME, C.PLAN_EXTENDED_NAME)
	plans = frappe.get_all(
		"Strategic Plan",
		filters={"strategic_plan_name": ("in", titles), "procuring_entity": C.ENTITY_MOH},
		pluck="name",
	)
	if not plans:
		return {"deleted_plans": [], "dry_run": dry_run}
	if dry_run:
		return {"would_delete_plans": plans, "dry_run": True}
	for pn in plans:
		frappe.db.delete("Strategy Target", {"strategic_plan": pn})
		frappe.db.delete("Strategy Objective", {"strategic_plan": pn})
		frappe.db.delete("Strategy Program", {"strategic_plan": pn})
		frappe.delete_doc("Strategic Plan", pn, force=True, ignore_permissions=True)
	frappe.db.commit()
	return {"deleted_plans": plans, "dry_run": False}
