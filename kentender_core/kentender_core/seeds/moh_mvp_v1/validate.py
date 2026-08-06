# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""§9 verification report for MOH_MVP_V1."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt

from kentender_core.seeds.moh_mvp_v1 import constants as C


def _check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
	return {"name": name, "ok": bool(ok), "detail": detail}


def validate_moh_mvp_v1() -> dict[str, Any]:
	checks: list[dict[str, Any]] = []

	plan = frappe.db.get_value(
		"Strategic Plan",
		{"plan_code": C.PLAN_CODE, "version_number": 1},
		["name", "status", "fixture_namespace"],
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
			getattr(plan, "fixture_namespace", None) or "",
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
	):
		exists = bool(
			frappe.db.exists("Strategy Programme", {"programme_code": code})
			or frappe.db.exists("Strategy Sub Programme", {"sub_programme_code": code})
			or frappe.db.exists("Strategic Outcome", {"outcome_code": code})
			or frappe.db.exists("Performance Indicator", {"indicator_code": code})
			or frappe.db.exists("Performance Target", {"target_code": code})
		)
		checks.append(_check(f"strategy.ref.{code}", exists))

	for pvc in (
		"MOH-PVC-EFT-01",
		"MOH-PVC-ECO-01",
		"MOH-PVC-LOC-01",
		"MOH-PVC-SUS-02",
	):
		checks.append(
			_check(
				f"strategy.pvc.{pvc}",
				bool(frappe.db.exists("Plan Value Commitment", {"commitment_code": pvc})),
			)
		)

	bud = frappe.db.get_value(
		"Budget",
		{"generated_reference": C.BUD_ACTIVE},
		["name", "status", "external_approved_total"],
		as_dict=True,
	)
	checks.append(_check("budget.active_exists", bool(bud and bud.status == "Active")))

	lines = frappe.get_all(
		"Budget Line",
		filters={"budget": bud.name} if bud else {"name": ["is", "not set"]},
		fields=[
			"generated_reference",
			"approved_amount",
			"amount_reserved",
			"amount_committed",
			"amount_actual",
			"owner_state_department",
		],
	) if bud else []
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
	checks.append(
		_check("budget.dhi_owner_sdms", bool(dhi and dhi.owner_state_department == C.SD_MEDICAL))
	)
	checks.append(
		_check("budget.hwd_owner_sdphps", bool(hwd and hwd.owner_state_department == C.SD_PUBLIC))
	)

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
			bool(exp and exp.reconciliation_status == "Stale" and abs(flt(exp.amount) - 180_000_000) < 0.01),
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

	# Org codes
	for code in (C.SD_MEDICAL, C.SD_PUBLIC, C.DIR_DHP, C.DIR_HRMD):
		checks.append(
			_check(
				f"org.{code}",
				bool(frappe.db.exists("Procuring Department", {"department_code": code})),
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
	# Human-readable lines for bench execute
	lines = [f"{'PASS' if c['ok'] else 'FAIL'}: {c['name']}" + (f" ({c['detail']})" if c['detail'] and not c['ok'] else "") for c in checks]
	report["summary"] = "\n".join(lines)
	return report
