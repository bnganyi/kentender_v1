# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DIA — ensure the four locked business Demand IDs for Procurement Planning F1 (6. Seed Data §6).

Idempotent: creates **DIA-MOH-2026-0011 / 0020 / 0030** if missing; ensures **DIA-MOH-2026-0004** exists
(from ``seed_dia_basic``) and normalises header **total_amount** to the locked spec. For **0020** and **0030**,
line item totals are kept small so finance approval can reserve on constrained UAT budget lines; the header
**total_amount** (used by C2 for package lines) is aligned to **1.2M** / **4M** after approval, same idea as
PP3 for **0011**.

**DIA-MOH-2026-0020** and **0030** sit outside the 0001…0009 clearable DIA range and are not removed
by ``clear_dia_seed_demands``.

Run::

	bench --site kentender.midas.com execute \\
	  kentender_procurement.demand_intake.seeds.seed_dia_planning_f1_prerequisites.run
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from kentender_core.seeds import constants as C
from kentender_procurement.demand_intake.seeds.dia_seed_common import (
	U_REQ,
	_fin_approve,
	_hod_approve,
	_insert_demand,
	_new_demand_dict,
	_submit,
	ensure_budget_line_prerequisites,
	ensure_core_prerequisites,
)

DEMAND_0004 = "DIA-MOH-2026-0004"
DEMAND_0011 = "DIA-MOH-2026-0011"
DEMAND_0020 = "DIA-MOH-2026-0020"
DEMAND_0030 = "DIA-MOH-2026-0030"

TARGET_0004 = 3_000_000.0
TARGET_0011 = 2_000_000.0
TARGET_0020 = 1_200_000.0
TARGET_0030 = 4_000_000.0


def _set_demand_reported_total(demand_name: str, target_total: float) -> None:
	frappe.db.set_value("Demand", demand_name, "total_amount", flt(target_total), update_modified=False)


def _ensure_0004() -> str:
	if not frappe.db.exists("Demand", {"demand_id": DEMAND_0004}):
		frappe.throw(
			_("Demand {0} is missing. Run kentender_procurement.demand_intake.seeds.seed_dia_basic.run first.").format(
				DEMAND_0004
			),
			title=_("DIA F1 prerequisite"),
		)
	name = frappe.db.get_value("Demand", {"demand_id": DEMAND_0004}, "name")
	_set_demand_reported_total(name, TARGET_0004)
	return name


def _ensure_0011() -> str:
	name = frappe.db.get_value("Demand", {"demand_id": DEMAND_0011}, "name")
	if name:
		_set_demand_reported_total(name, TARGET_0011)
		return name
	d = _insert_demand(
		_new_demand_dict(
			title="Ultrasound Units",
			demand_id=DEMAND_0011,
			requested_by=U_REQ,
			demand_type="Planned",
			bl_code="BL-MOH-2026-002",
			qty=2,
			unit_cost=5000.0,
		)
	)
	_submit(d.name)
	_hod_approve(d.name)
	_fin_approve(d.name)
	_set_demand_reported_total(d.name, TARGET_0011)
	return d.name


def _ensure_0020() -> str:
	name = frappe.db.get_value("Demand", {"demand_id": DEMAND_0020}, "name")
	if name:
		_set_demand_reported_total(name, TARGET_0020)
		return name
	# Small line totals for finance reservation (6. **Amount** 1.2M is the reported header used by planning).
	d = _insert_demand(
		_new_demand_dict(
			title="Laptops Procurement",
			demand_id=DEMAND_0020,
			requested_by=U_REQ,
			demand_type="Planned",
			bl_code="BL-MOH-2026-001",
			qty=1,
			unit_cost=1_000.0,
		)
	)
	_submit(d.name)
	_hod_approve(d.name)
	_fin_approve(d.name)
	_set_demand_reported_total(d.name, TARGET_0020)
	return d.name


def _ensure_0030() -> str:
	name = frappe.db.get_value("Demand", {"demand_id": DEMAND_0030}, "name")
	if name:
		_set_demand_reported_total(name, TARGET_0030)
		return name
	d = _insert_demand(
		_new_demand_dict(
			title="Emergency ICU Equipment",
			demand_id=DEMAND_0030,
			requested_by=U_REQ,
			demand_type="Emergency",
			bl_code="BL-MOH-2026-002",
			qty=1,
			unit_cost=1_000.0,
			impact_if_not_procured="Critical care treatment capacity is at risk without immediate equipment.",
			emergency_justification="F1 planning seed: verified emergency track for end-to-end testing.",
		)
	)
	_submit(d.name)
	_hod_approve(d.name)
	_fin_approve(d.name)
	_set_demand_reported_total(d.name, TARGET_0030)
	return d.name


def _ensure_core_if_needed() -> None:
	if frappe.db.exists("Procuring Entity", C.ENTITY_MOH) and frappe.db.exists("Currency", "KES"):
		return
	ensure_core_prerequisites()


def run() -> dict:
	"""Idempotent: ensure the four DIA business IDs for F1; return internal Demand names (by key)."""
	frappe.only_for(("System Manager", "Administrator"))
	_ensure_core_if_needed()
	ensure_budget_line_prerequisites()
	n4 = _ensure_0004()
	n11 = _ensure_0011()
	n20 = _ensure_0020()
	n30 = _ensure_0030()
	out = {
		"pack": "seed_dia_planning_f1_prerequisites",
		"DIA-MOH-2026-0004": n4,
		"DIA-MOH-2026-0011": n11,
		"DIA-MOH-2026-0020": n20,
		"DIA-MOH-2026-0030": n30,
		"demand_business_ids": [DEMAND_0004, DEMAND_0011, DEMAND_0020, DEMAND_0030],
	}
	frappe.db.commit()
	frappe.msgprint(_("DIA F1 planning prerequisites ensured for {0} business demand IDs.").format(4))
	return out
