# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 server-generated business references (§4).

Formats follow the §14 fixtures exactly; the embedded entity code comes from
the site Procuring Entity (an opaque stable string, never a permission
dimension — §1.1):
	DPP-{PE}-{OU}-{FYstart}-{NNN}      departmental plan root
	DPPE-{PE}-{OU}-{FYstart}-{NNN}     departmental entry (stable across copies)
	DPPS-…-V{n} / DPPT-…-V{n} / DPPV-…-V{n}   submission / validation task / decision
	PLN-{PE}-{FYstart}-{NNN}           annual plan root
	PPI-{PE}-{FYstart}-{NNN}           plan item (stable across successor copies)
	PSA-{PE}-{FYstart}-{item NNN}-{NNN}  source allocation (stable)
	FNT-{PE}-{FYstart}-{plan NNN}[-{k}] / FND-…-V{n}   plan-level finance task / decision
	AOT-/SAT-/AOD-/APP-…-V{n}          governance tasks / decisions
	PUB-{PE}-{FYstart}-{plan NNN}-V{n}-A{n} publication attempt

Sequence scans take a MariaDB advisory lock (NDS pattern) so two concurrent
creates cannot mint the same number.
"""

from __future__ import annotations

import frappe
from frappe.utils import cstr, getdate

from kentender_procurement.procurement_planning.errors import fail


def pe_code() -> str:
	"""The site Procuring Entity's code without the `PE-` prefix (`MOH`)."""
	code = cstr(frappe.db.get_single_value("Site Procuring Entity", "pe_code"))
	if not code:
		fail("PLN_NO_CONTEXT", "This site has no Procuring Entity configured yet.")
	return code.removeprefix("PE-") or code


def ou_code(organisation_unit: str) -> str:
	"""A short unit mnemonic for references: the unit's own code without the
	`OU-{PE}-` prefix (`DHI` from `OU-MOH-DHI`); a generated code such as
	`OU-MOH-00421` keeps its number."""
	code = cstr(frappe.db.get_value("Organisation Unit", organisation_unit, "unit_code") or organisation_unit)
	return code.removeprefix(f"OU-{pe_code()}-").removeprefix(f"{pe_code()}-").removeprefix("OU-") or code


def fy_start(fiscal_year: str) -> str:
	start = frappe.db.get_value("Fiscal Year", fiscal_year, "year_start_date")
	if not start:
		fail("PLN_NO_CONTEXT", "The Fiscal Year is not configured.")
	return str(getdate(start).year)


def fy_period_label(fiscal_year: str) -> str:
	"""`2027/28` — the display period without an `FY` prefix (§4.7)."""
	year = int(fy_start(fiscal_year))
	return f"{year}/{str(year + 1)[-2:]}"


def fy_label(fiscal_year: str) -> str:
	return f"FY {fy_period_label(fiscal_year)}"


def _next(doctype: str, field: str, prefix: str, *, width: int = 3) -> str:
	lock = f"pln:ref:{prefix}"[:64]
	if not frappe.db.sql("select get_lock(%s, 10)", lock)[0][0]:
		fail("PLN_STALE_WRITE", "Reference generation is busy. Try again.")
	rows = frappe.get_all(doctype, filters={field: ["like", f"{prefix}%"]}, pluck=field, limit_page_length=0)
	seq = max([int(ref[len(prefix):]) for ref in rows if cstr(ref)[len(prefix):].isdigit()] or [0]) + 1
	return f"{prefix}{seq:0{width}d}"


def dpp_reference(organisation_unit: str, fiscal_year: str) -> str:
	prefix = f"DPP-{pe_code()}-{ou_code(organisation_unit)}-{fy_start(fiscal_year)}-"
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


def plan_reference(fiscal_year: str) -> str:
	prefix = f"PLN-{pe_code()}-{fy_start(fiscal_year)}-"
	return _next("Annual Plan", "plan_reference", prefix)


def plan_item_id(fiscal_year: str) -> str:
	prefix = f"PPI-{pe_code()}-{fy_start(fiscal_year)}-"
	return _next("Annual Plan Item", "plan_item_id", prefix)


def allocation_id(plan_item_id_value: str) -> str:
	prefix = "PSA-" + cstr(plan_item_id_value).removeprefix("PPI-") + "-"
	return _next("Plan Source Allocation", "allocation_id", prefix)


def finance_task_reference(plan_reference_value: str) -> str:
	"""One Finance task per Plan Version (§4.11): the first task of a Plan is
	`FNT-MOH-2027-001` (§14.6); later requests on the same Plan append a
	sequence (`FNT-MOH-2027-001-2`)."""
	base = "FNT-" + cstr(plan_reference_value).removeprefix("PLN-")
	if not frappe.db.exists("Plan Finance Task", base):
		return base
	return _next("Plan Finance Task", "task_reference", base + "-", width=1)


def finance_decision_reference(finance_task_reference_value: str, version_number: int) -> str:
	return "FND-" + cstr(finance_task_reference_value).removeprefix("FNT-") + f"-V{int(version_number)}"


def governance_task_reference(stage: str, version_reference: str) -> str:
	prefix = "AOT-" if stage == "Accounting Officer adoption" else "SAT-"
	return prefix + cstr(version_reference).removeprefix("PLN-")


def governance_decision_reference(stage: str, version_reference: str) -> str:
	prefix = "AOD-" if stage == "Accounting Officer adoption" else "APP-"
	return prefix + cstr(version_reference).removeprefix("PLN-")


def publication_reference(version_reference: str, attempt_number: int) -> str:
	"""Keyed by the Version, not the Plan (v1.2 finding 21)."""
	return f"PUB-{cstr(version_reference).removeprefix('PLN-')}-A{int(attempt_number)}"
