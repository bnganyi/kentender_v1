# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 server-generated business references (§4).

Formats follow the §14 fixtures exactly:
	DPP-{PE}-{OU}-{FYstart}-{NNN}      departmental plan root
	DPPE-{PE}-{OU}-{FYstart}-{NNN}     departmental entry (stable across copies)
	DPPS-…-V{n} / DPPT-…-V{n} / DPPV-…-V{n}   submission / validation task / decision
	PLN-{PE}-{FYstart}-{NNN}           annual plan root
	PPI-{PE}-{FYstart}-{NNN}           plan item (stable across successor copies)
	PSA-{PE}-{FYstart}-{item NNN}-{NNN}  source allocation (stable)
	FNT-/FND-{PE}-{FYstart}-{item NNN}-{NNN}   finance task / decision
	AOT-/SAT-/AOD-/APP-…-V{n}          governance tasks / decisions
	PUB-{PE}-{FYstart}-{plan NNN}-A{n} publication attempt

Sequence scans take a MariaDB advisory lock (NDS pattern) so two concurrent
creates cannot mint the same number.
"""

from __future__ import annotations

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_planning.errors import fail


def pe_code(procuring_entity: str) -> str:
	return cstr(procuring_entity).removeprefix("PE-") or cstr(procuring_entity)


def ou_code(organisation_unit: str, procuring_entity: str) -> str:
	code = cstr(organisation_unit)
	return code.removeprefix(f"OU-{pe_code(procuring_entity)}-").removeprefix("OU-") or code


def fy_start(financial_year: str) -> str:
	year = cstr(
		frappe.db.get_value("Financial Year", financial_year, "start_year") or ""
	)
	if not year:
		fail("PLN_NO_CONTEXT", "The Financial Year has no configured start year.")
	return year


def _next(doctype: str, field: str, prefix: str, *, width: int = 3) -> str:
	lock = f"pln:ref:{prefix}"[:64]
	if not frappe.db.sql("select get_lock(%s, 10)", lock)[0][0]:
		fail("PLN_STALE_WRITE", "Reference generation is busy. Try again.")
	rows = frappe.get_all(
		doctype, filters={field: ["like", f"{prefix}%"]}, pluck=field, limit_page_length=0
	)
	seq = (
		max(
			[
				int(ref[len(prefix):])
				for ref in rows
				if cstr(ref)[len(prefix):].isdigit()
			]
			or [0]
		)
		+ 1
	)
	return f"{prefix}{seq:0{width}d}"


def dpp_reference(procuring_entity: str, organisation_unit: str, financial_year: str) -> str:
	prefix = (
		f"DPP-{pe_code(procuring_entity)}-{ou_code(organisation_unit, procuring_entity)}"
		f"-{fy_start(financial_year)}-"
	)
	return _next("Departmental Plan", "dpp_reference", prefix)


def entry_id(dpp_reference_value: str) -> str:
	prefix = "DPPE-" + cstr(dpp_reference_value).removeprefix("DPP-").rsplit("-", 1)[0] + "-"
	return _next("Departmental Plan Entry", "entry_id", prefix)


def submission_reference(dpp_reference_value: str, version_number: int) -> str:
	return f"DPPS-{cstr(dpp_reference_value).removeprefix('DPP-')}-V{int(version_number)}"


def validation_task_reference(dpp_reference_value: str, version_number: int) -> str:
	return f"DPPT-{cstr(dpp_reference_value).removeprefix('DPP-')}-V{int(version_number)}"


def validation_decision_reference(dpp_reference_value: str, version_number: int) -> str:
	return f"DPPV-{cstr(dpp_reference_value).removeprefix('DPP-')}-V{int(version_number)}"


def plan_reference(procuring_entity: str, financial_year: str) -> str:
	prefix = f"PLN-{pe_code(procuring_entity)}-{fy_start(financial_year)}-"
	return _next("Annual Plan", "plan_reference", prefix)


def plan_item_id(procuring_entity: str, financial_year: str) -> str:
	prefix = f"PPI-{pe_code(procuring_entity)}-{fy_start(financial_year)}-"
	return _next("Annual Plan Item", "plan_item_id", prefix)


def allocation_id(plan_item_id_value: str) -> str:
	prefix = "PSA-" + cstr(plan_item_id_value).removeprefix("PPI-") + "-"
	return _next("Plan Source Allocation", "allocation_id", prefix)


def finance_task_reference(plan_item_id_value: str) -> str:
	prefix = "FNT-" + cstr(plan_item_id_value).removeprefix("PPI-") + "-"
	return _next("Plan Finance Task", "task_reference", prefix)


def finance_decision_reference(finance_task_reference_value: str) -> str:
	return "FND-" + cstr(finance_task_reference_value).removeprefix("FNT-")


def governance_task_reference(stage: str, version_reference: str) -> str:
	prefix = "AOT-" if stage == "Accounting Officer adoption" else "SAT-"
	return prefix + cstr(version_reference).removeprefix("PLN-")


def governance_decision_reference(stage: str, version_reference: str) -> str:
	prefix = "AOD-" if stage == "Accounting Officer adoption" else "APP-"
	return prefix + cstr(version_reference).removeprefix("PLN-")


def publication_reference(version_reference: str, attempt_number: int) -> str:
	"""Keyed by the Version, not the Plan: `attempt_number` counts attempts
	for one Version's own publication and resets for its successor, so the
	reference must carry the Version reference too, or a first attempt at
	V2 collides with V1's own first attempt (both otherwise 'attempt 1')."""
	return f"PUB-{cstr(version_reference).removeprefix('PLN-')}-A{int(attempt_number)}"
