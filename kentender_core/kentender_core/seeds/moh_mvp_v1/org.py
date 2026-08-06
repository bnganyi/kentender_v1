# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PE + State Department + Directorate graph for MOH_MVP_V1."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds._common import ensure_procuring_entity
from kentender_core.seeds.moh_mvp_v1 import constants as C


def _upsert_department(
	*,
	code: str,
	name: str,
	entity: str,
	kind: str,
	parent_name: str | None = None,
) -> str:
	existing = frappe.db.get_value("Procuring Department", {"department_code": code}, "name")
	values = {
		"department_name": name,
		"procuring_entity": entity,
		"department_code": code,
		"department_kind": kind,
		"parent_department": parent_name,
	}
	if existing:
		frappe.db.set_value("Procuring Department", existing, values, update_modified=False)
		return existing
	# Prefer match by name+entity for pre-code rows
	by_name = frappe.db.get_value(
		"Procuring Department",
		{"department_name": name, "procuring_entity": entity},
		"name",
	)
	if by_name:
		frappe.db.set_value("Procuring Department", by_name, values, update_modified=False)
		return by_name
	doc = frappe.get_doc({"doctype": "Procuring Department", **values})
	doc.insert(ignore_permissions=True)
	return doc.name


def upsert_org() -> dict[str, Any]:
	pe_moh = ensure_procuring_entity(C.PE_MOH, C.PE_MOH_NAME)
	pe_moe = ensure_procuring_entity(C.PE_MOE, C.PE_MOE_NAME)
	sdms = _upsert_department(
		code=C.SD_MEDICAL, name=C.SD_MEDICAL_NAME, entity=pe_moh, kind="State Department"
	)
	sdph = _upsert_department(
		code=C.SD_PUBLIC, name=C.SD_PUBLIC_NAME, entity=pe_moh, kind="State Department"
	)
	dhp = _upsert_department(
		code=C.DIR_DHP,
		name=C.DIR_DHP_NAME,
		entity=pe_moh,
		kind="Directorate",
		parent_name=sdms,
	)
	hrmd = _upsert_department(
		code=C.DIR_HRMD,
		name=C.DIR_HRMD_NAME,
		entity=pe_moh,
		kind="Directorate",
		parent_name=sdph,
	)
	return {
		"pe_moh": pe_moh,
		"pe_moe": pe_moe,
		"sdms": sdms,
		"sdphps": sdph,
		"dir_dhp": dhp,
		"dir_hrmd": hrmd,
	}
