# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Destructive: strategy seed + test users + MOH/MOE departments and entities (Part G)."""

from __future__ import annotations

import frappe

from kentender_core.seeds import constants as C
from kentender_core.seeds.reset_strategy_seed import run as reset_strategy


def run(dry_run: bool = False):
	frappe.only_for(("System Manager", "Administrator"))
	if dry_run:
		return {"strategy_preview": reset_strategy(dry_run=True), "dry_run": True}

	reset_strategy(dry_run=False)

	emails = [e[0] for e in C.SEED_USERS]
	for email in emails:
		if frappe.db.exists("User", email):
			frappe.db.delete("User Permission", {"user": email})
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)

	for ent in (C.ENTITY_MOH, C.ENTITY_MOE):
		if not frappe.db.exists("Procuring Entity", ent):
			continue
		depts = frappe.get_all("Procuring Department", filters={"procuring_entity": ent}, pluck="name")
		for d in depts:
			frappe.delete_doc("Procuring Department", d, force=True, ignore_permissions=True)
		frappe.delete_doc("Procuring Entity", ent, force=True, ignore_permissions=True)

	frappe.db.commit()
	return {"removed_users": emails, "entities_removed": [C.ENTITY_MOH, C.ENTITY_MOE]}
