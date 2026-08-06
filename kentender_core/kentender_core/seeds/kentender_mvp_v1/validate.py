# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Contract v2.0 §9 verification report for KENTENDER_MVP_V1."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_core.services.org_scope_access import (
	can_access_owned_record,
	strategy_items_for_unit,
)


def _check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
	return {"name": name, "ok": bool(ok), "detail": detail}


def validate_kentender_mvp_v1() -> dict[str, Any]:
	checks: list[dict[str, Any]] = []

	# --- Identity / org ---
	for code, label in ((C.PE_MOH, "moh"), (C.PE_CGKIS, "cgkis")):
		checks.append(
			_check(
				f"org.pe.{label}",
				frappe.db.count("Procuring Entity", {"entity_code": code}) == 1,
			)
		)

	for code in (
		C.OU_SDMS,
		C.OU_DIR_DHP,
		C.OU_SDPHPS,
		C.OU_DIR_HRMD,
		C.OU_CGK_HEALTH,
	):
		row = frappe.db.get_value(
			"Organisation Unit",
			code,
			["procuring_entity", "parent_org_unit", "unit_type"],
			as_dict=True,
		)
		checks.append(_check(f"org.unit.{code}", bool(row)))
		if row and row.parent_org_unit:
			parent_pe = frappe.db.get_value(
				"Organisation Unit", row.parent_org_unit, "procuring_entity"
			)
			checks.append(
				_check(
					f"org.unit_parent_same_pe.{code}",
					parent_pe == row.procuring_entity,
					f"parent_pe={parent_pe} child_pe={row.procuring_entity}",
				)
			)

	# --- Strategy ---
	plan = frappe.db.get_value(
		"Strategic Plan",
		{"plan_code": C.PLAN_CODE, "version_number": 1},
		["name", "status", "fixture_namespace", "owner_org_unit"],
		as_dict=True,
	)
	checks.append(
		_check(
			"strategy.plan_active",
			bool(plan and plan.status == "Active"),
			f"status={getattr(plan, 'status', None)}",
		)
	)
	checks.append(
		_check(
			"strategy.plan_namespace",
			bool(plan and plan.fixture_namespace == C.FIXTURE_NS),
		)
	)
	checks.append(
		_check(
			"strategy.plan_entity_owned",
			bool(plan and not (plan.owner_org_unit or "").strip()),
		)
	)

	cgk_plan = frappe.db.get_value(
		"Strategic Plan",
		{"plan_code": C.CGK_PLAN_CODE, "version_number": 1},
		["name", "status", "owner_org_unit", "procuring_entity"],
		as_dict=True,
	)
	checks.append(
		_check(
			"strategy.cgk_plan_active",
			bool(cgk_plan and cgk_plan.status == "Active"),
		)
	)
	checks.append(
		_check(
			"strategy.cgk_owner_unit",
			bool(cgk_plan and cgk_plan.owner_org_unit == C.OU_CGK_HEALTH),
		)
	)

	for code in (
		C.PROG_DH,
		C.SUB_HIS,
		C.SUB_DHC,
		C.OUT_RELIABILITY,
		C.OUT_CAPABILITY,
		C.IND_AVAIL,
		C.IND_RESTORE,
		C.IND_SKILLS,
		C.TGT_AVAIL_2028,
		C.TGT_RESTORE_2028,
		C.TGT_AVAIL_2029,
		C.TGT_SKILLS_2029,
		C.TGT_SKILLS_2030,
		C.CGK_OUT_COLDCHAIN,
		C.CGK_IND_COLDCHAIN,
		C.CGK_TGT_COLDCHAIN,
	):
		exists = bool(
			frappe.db.exists("Strategy Programme", {"programme_code": code})
			or frappe.db.exists("Strategy Sub Programme", {"sub_programme_code": code})
			or frappe.db.exists("Strategic Outcome", {"outcome_code": code})
			or frappe.db.exists("Performance Indicator", {"indicator_code": code})
			or frappe.db.exists("Performance Target", {"target_code": code})
		)
		checks.append(_check(f"strategy.ref.{code}", exists))

	tgt_dhp = frappe.db.get_value(
		"Performance Target",
		{"target_code": C.TGT_AVAIL_2028},
		"owner_org_unit",
	)
	checks.append(_check("strategy.tgt_dhp_owner", tgt_dhp == C.OU_DIR_DHP))
	tgt_hrmd = frappe.db.get_value(
		"Performance Target",
		{"target_code": C.TGT_SKILLS_2029},
		"owner_org_unit",
	)
	checks.append(_check("strategy.tgt_hrmd_owner", tgt_hrmd == C.OU_DIR_HRMD))

	for pvc in (
		"MOH-PVC-EFT-01",
		"MOH-PVC-ECO-01",
		"MOH-PVC-LOC-01",
		"MOH-PVC-SUS-02",
		"CGK-PVC-EFT-01",
		"CGK-PVC-ECO-01",
		"CGK-PVC-SUS-01",
	):
		checks.append(
			_check(
				f"strategy.pvc.{pvc}",
				bool(frappe.db.exists("Plan Value Commitment", {"commitment_code": pvc})),
			)
		)

	sdms_items = strategy_items_for_unit(C.OU_SDMS)
	checks.append(
		_check(
			"strategy.scope.sdms_has_prog",
			any(r.get("strategy_item_code") == C.PROG_DH for r in sdms_items),
		)
	)
	cgk_items = strategy_items_for_unit(C.OU_CGK_HEALTH)
	checks.append(
		_check(
			"strategy.scope.cgk_has_coldchain",
			any(r.get("strategy_item_code") == C.CGK_OUT_COLDCHAIN for r in cgk_items),
		)
	)
	checks.append(
		_check(
			"strategy.scope.cgk_excludes_moh_prog",
			not any(r.get("strategy_item_code") == C.PROG_DH for r in cgk_items),
		)
	)

	# --- Budget ---
	bud = frappe.db.get_value(
		"Budget",
		{"generated_reference": C.BUD_ACTIVE},
		["name", "status", "external_approved_total"],
		as_dict=True,
	)
	checks.append(_check("budget.active_exists", bool(bud and bud.status == "Active")))

	lines = (
		frappe.get_all(
			"Budget Line",
			filters={"budget": bud.name} if bud else {"name": ["is", "not set"]},
			fields=[
				"generated_reference",
				"approved_amount",
				"amount_reserved",
				"amount_committed",
				"amount_actual",
				"owner_org_unit",
			],
		)
		if bud
		else []
	)
	by_code = {r.generated_reference: r for r in lines}
	dhi = by_code.get(C.BL_DHI_2027)
	hwd = by_code.get(C.BL_HWD_2027)
	approved = sum(flt(r.approved_amount) for r in lines)
	reserved = sum(flt(r.amount_reserved) for r in lines)
	committed = sum(flt(r.amount_committed) for r in lines)
	available = approved - reserved - committed
	checks.append(_check("budget.lines_total_560m", abs(approved - 560_000_000) < 0.01, str(approved)))
	checks.append(_check("budget.reserved_145m", abs(reserved - 145_000_000) < 0.01, str(reserved)))
	checks.append(_check("budget.committed_310m", abs(committed - 310_000_000) < 0.01, str(committed)))
	checks.append(_check("budget.available_105m", abs(available - 105_000_000) < 0.01, str(available)))
	checks.append(
		_check(
			"budget.dhi_actual_180m",
			bool(dhi and abs(flt(dhi.amount_actual) - 180_000_000) < 0.01),
		)
	)
	checks.append(_check("budget.dhi_owner_dhp", bool(dhi and dhi.owner_org_unit == C.OU_DIR_DHP)))
	checks.append(_check("budget.hwd_owner_hrmd", bool(hwd and hwd.owner_org_unit == C.OU_DIR_HRMD)))

	checks.append(
		_check(
			"budget.draft_exists",
			bool(frappe.db.exists("Budget", {"generated_reference": C.BUD_DRAFT, "status": "Draft"})),
		)
	)
	checks.append(
		_check(
			"budget.closed_exists",
			bool(frappe.db.exists("Budget", {"generated_reference": C.BUD_CLOSED, "status": "Closed"})),
		)
	)

	cgk_bud = frappe.db.get_value(
		"Budget",
		{"generated_reference": C.CGK_BUD_ACTIVE},
		["name", "status", "external_approved_total"],
		as_dict=True,
	)
	checks.append(
		_check("budget.cgk_active", bool(cgk_bud and cgk_bud.status == "Active"))
	)
	cgk_line = frappe.db.get_value(
		"Budget Line",
		{"generated_reference": C.CGK_BL_COLDCHAIN},
		["approved_amount", "amount_reserved", "amount_committed", "owner_org_unit", "primary_target_code"],
		as_dict=True,
	)
	checks.append(
		_check(
			"budget.cgk_24m_available",
			bool(
				cgk_line
				and abs(flt(cgk_line.approved_amount) - 24_000_000) < 0.01
				and flt(cgk_line.amount_reserved) == 0
				and flt(cgk_line.amount_committed) == 0
			),
		)
	)
	checks.append(
		_check(
			"budget.cgk_owner_and_target",
			bool(
				cgk_line
				and cgk_line.owner_org_unit == C.OU_CGK_HEALTH
				and cgk_line.primary_target_code == C.CGK_TGT_COLDCHAIN
			),
		)
	)

	rsv = frappe.db.get_value(
		"Funding Reservation",
		{"generated_reference": C.RSV_CODE},
		["original_amount", "remaining_reserved", "status"],
		as_dict=True,
	)
	checks.append(
		_check(
			"funding.reservation",
			bool(
				rsv
				and abs(flt(rsv.original_amount) - 455_000_000) < 0.01
				and abs(flt(rsv.remaining_reserved) - 145_000_000) < 0.01
			),
			str(rsv),
		)
	)
	com = frappe.db.get_value(
		"Procurement Commitment",
		{"generated_reference": C.COM_CODE},
		["current_amount", "actual_expenditure"],
		as_dict=True,
	)
	checks.append(
		_check(
			"funding.commitment",
			bool(com and abs(flt(com.current_amount) - 310_000_000) < 0.01),
			str(com),
		)
	)
	exp = frappe.db.get_value(
		"Expenditure Snapshot",
		{"generated_reference": C.EXP_CODE},
		["amount", "reconciliation_status"],
		as_dict=True,
	)
	checks.append(
		_check(
			"funding.expenditure_stale",
			bool(
				exp
				and exp.reconciliation_status == "Stale"
				and abs(flt(exp.amount) - 180_000_000) < 0.01
			),
			str(exp),
		)
	)

	for email in C.CANONICAL_USERS:
		checks.append(
			_check(
				f"user.enabled.{email}",
				bool(frappe.db.get_value("User", email, "enabled")),
			)
		)
		usa = frappe.db.count(
			"User Scope Assignment", {"user": email, "fixture_namespace": C.FIXTURE_NS}
		)
		checks.append(_check(f"user.scope.{email}", usa >= 1, str(usa)))

	# --- Ownership isolation (§9) ---
	pe_moh = frappe.db.get_value("Procuring Entity", {"entity_code": C.PE_MOH}, "name")
	pe_cgk = frappe.db.get_value("Procuring Entity", {"entity_code": C.PE_CGKIS}, "name")

	checks.append(
		_check(
			"isolation.medical_can_dhp_write",
			can_access_owned_record(
				procuring_entity=pe_moh,
				owner_org_unit=C.OU_DIR_DHP,
				user=C.USER_MEDICAL,
				require_write=True,
			),
		)
	)
	checks.append(
		_check(
			"isolation.medical_denied_hrmd_write",
			not can_access_owned_record(
				procuring_entity=pe_moh,
				owner_org_unit=C.OU_DIR_HRMD,
				user=C.USER_MEDICAL,
				require_write=True,
			),
		)
	)
	checks.append(
		_check(
			"isolation.public_can_hrmd_write",
			can_access_owned_record(
				procuring_entity=pe_moh,
				owner_org_unit=C.OU_DIR_HRMD,
				user=C.USER_PUBLIC,
				require_write=True,
			),
		)
	)
	checks.append(
		_check(
			"isolation.public_denied_dhp_write",
			not can_access_owned_record(
				procuring_entity=pe_moh,
				owner_org_unit=C.OU_DIR_DHP,
				user=C.USER_PUBLIC,
				require_write=True,
			),
		)
	)
	checks.append(
		_check(
			"isolation.reviewer_entity_wide",
			can_access_owned_record(
				procuring_entity=pe_moh,
				owner_org_unit=C.OU_DIR_HRMD,
				user=C.USER_STR_REVIEWER,
				require_write=False,
			)
			and can_access_owned_record(
				procuring_entity=pe_moh,
				owner_org_unit=C.OU_DIR_DHP,
				user=C.USER_STR_REVIEWER,
				require_write=False,
			),
		)
	)
	checks.append(
		_check(
			"isolation.kisumu_can_county_write",
			can_access_owned_record(
				procuring_entity=pe_cgk,
				owner_org_unit=C.OU_CGK_HEALTH,
				user=C.USER_KISUMU_OFFICER,
				require_write=True,
			),
		)
	)
	checks.append(
		_check(
			"isolation.kisumu_denied_moh",
			not can_access_owned_record(
				procuring_entity=pe_moh,
				owner_org_unit=C.OU_DIR_DHP,
				user=C.USER_KISUMU_OFFICER,
				require_write=False,
			),
		)
	)
	checks.append(
		_check(
			"isolation.moh_denied_kisumu",
			not can_access_owned_record(
				procuring_entity=pe_cgk,
				owner_org_unit=C.OU_CGK_HEALTH,
				user=C.USER_MEDICAL,
				require_write=False,
			),
		)
	)

	failed = [c for c in checks if not c["ok"]]
	ok = not failed
	report = {
		"ok": ok,
		"fixture_namespace": C.FIXTURE_NS,
		"passed": len(checks) - len(failed),
		"failed": len(failed),
		"checks": checks,
		"failures": failed,
	}
	lines_out = [
		f"{'PASS' if c['ok'] else 'FAIL'}: {c['name']}"
		+ (f" ({c['detail']})" if c["detail"] and not c["ok"] else "")
		for c in checks
	]
	report["summary"] = "\n".join(lines_out)
	return report
