# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""seed_core_minimal — entities, departments, users, roles, KES (no Strategic Plans)."""

from __future__ import annotations

import frappe

from kentender_core.seeds import constants as C
from kentender_core.seeds._common import (
	ensure_currency_kes,
	ensure_department,
	ensure_procuring_entity,
	ensure_roles,
	upsert_seed_user,
)


def run():
	frappe.only_for(("System Manager", "Administrator"))
	out = _seed()
	frappe.db.commit()
	return out


def _seed():
	ensure_roles()
	ensure_currency_kes()
	moh = ensure_procuring_entity(C.ENTITY_MOH, "Ministry of Health")
	ensure_procuring_entity(C.ENTITY_MOE, "Ministry of Education")

	dept_map = {
		C.DEPT_CLIN: ensure_department(C.DEPT_CLIN, moh),
		C.DEPT_HR: ensure_department(C.DEPT_HR, moh),
		C.DEPT_FIN: ensure_department(C.DEPT_FIN, moh),
		C.DEPT_PROC: ensure_department(C.DEPT_PROC, moh),
	}

	users_done = []
	for email, full_name, biz, dept_label in C.SEED_USERS:
		dept_doc = dept_map.get(dept_label)
		upsert_seed_user(
			email,
			full_name,
			biz,
			entity_name=moh,
			department_docname=dept_doc,
		)
		users_done.append(email)

	return {
		"procuring_entities": [moh, C.ENTITY_MOE],
		"users": users_done,
	}
