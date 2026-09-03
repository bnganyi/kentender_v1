# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PE + Organisation Unit Types + Organisation Units for KENTENDER_MVP_V1."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds._common import ensure_procuring_entity
from kentender_core.seeds.kentender_mvp_v1 import constants as C


def _upsert_unit_type(type_ref: str, label: str) -> str:
	if frappe.db.exists("Organisation Unit Type", type_ref):
		frappe.db.set_value(
			"Organisation Unit Type",
			type_ref,
			{
				"display_label": label,
				"status": "Active",
				"fixture_namespace": C.FIXTURE_NS,
			},
			update_modified=False,
		)
		return type_ref
	doc = frappe.get_doc(
		{
			"doctype": "Organisation Unit Type",
			"type_reference": type_ref,
			"display_label": label,
			"status": "Active",
			"fixture_namespace": C.FIXTURE_NS,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _upsert_unit(
	*,
	code: str,
	name: str,
	pe: str,
	unit_type: str,
	parent: str | None = None,
) -> str:
	values = {
		"unit_code": code,
		"unit_name": name,
		"procuring_entity": pe,
		"unit_type": unit_type,
		"parent_organisation_unit": parent or "",
		"status": "Active",
		"fixture_namespace": C.FIXTURE_NS,
	}
	if frappe.db.exists("Organisation Unit", code):
		frappe.db.set_value("Organisation Unit", code, values, update_modified=False)
		return code
	doc = frappe.get_doc({"doctype": "Organisation Unit", **values})
	doc.insert(ignore_permissions=True)
	return doc.name


def upsert_org() -> dict[str, Any]:
	pe_moh = ensure_procuring_entity(
		C.PE_MOH, C.PE_MOH_NAME, entity_type="Ministry", short_name="MoH"
	)
	pe_cgk = ensure_procuring_entity(
		C.PE_CGKIS,
		C.PE_CGKIS_NAME,
		entity_type="County Government",
		short_name="Kisumu",
	)
	# Keep PE-MOE for unrelated platform seeds; not part of canonical v2 story.
	pe_moe = ensure_procuring_entity(C.PE_MOE, C.PE_MOE_NAME, entity_type="Ministry")

	out_sd = _upsert_unit_type(C.OUT_STATE_DEPT, "State Department")
	out_dir = _upsert_unit_type(C.OUT_DIRECTORATE, "Directorate")
	out_cd = _upsert_unit_type(C.OUT_COUNTY_DEPT, "County Department")

	sdms = _upsert_unit(code=C.OU_SDMS, name=C.OU_SDMS_NAME, pe=pe_moh, unit_type=out_sd)
	sdph = _upsert_unit(code=C.OU_SDPHPS, name=C.OU_SDPHPS_NAME, pe=pe_moh, unit_type=out_sd)
	dhp = _upsert_unit(
		code=C.OU_DIR_DHP, name=C.OU_DIR_DHP_NAME, pe=pe_moh, unit_type=out_dir, parent=sdms
	)
	hrmd = _upsert_unit(
		code=C.OU_DIR_HRMD,
		name=C.OU_DIR_HRMD_NAME,
		pe=pe_moh,
		unit_type=out_dir,
		parent=sdph,
	)
	cgk_health = _upsert_unit(
		code=C.OU_CGK_HEALTH,
		name=C.OU_CGK_HEALTH_NAME,
		pe=pe_cgk,
		unit_type=out_cd,
	)
	return {
		"pe_moh": pe_moh,
		"pe_cgkis": pe_cgk,
		"pe_moe": pe_moe,
		"types": {"state_dept": out_sd, "directorate": out_dir, "county_dept": out_cd},
		"units": {
			"sdms": sdms,
			"sdphps": sdph,
			"dir_dhp": dhp,
			"dir_hrmd": hrmd,
			"cgk_health": cgk_health,
		},
	}
