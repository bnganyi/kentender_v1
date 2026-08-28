"""AUTH-ADR-001 — the explicit Role classification and capability-to-Role map.

Single source of truth for `authorization_policy.evaluate_capability()`'s
Role-based resolution (§5.2 of AUTH-ADR-001: classification "is part of the
role registry and test contract. It shall not be inferred from a display
label at runtime."). The full resolution history and rationale for every
entry here lives in docs/mvp-1-r1/00_common/AUTH-ADR-001-capability-mapping.md.

`plan.*` and `std_configuration.*` are deliberately absent — each is a
separate domain already enforced by its own native-Role mechanism
(`planning_permissions.py`, `std_authorization.py`); folding them in here
would recreate the dual-path conflict the mapping work found and resolved.
"""

from __future__ import annotations

import frappe

# Scope classifications (AUTH-ADR-001 §5.2):
# - "global_central": Role itself supplies scope; no User Permission required.
# - "pe_scoped": requires a User Permission on the exact Procuring Entity.
# - "pe_fy_scoped": requires a User Permission on the exact PE Fiscal Year
#   Context; falls back to Procuring Entity scope for resources that don't
#   yet carry a pe_fy_context_id (AUTH-ADR-001 §6.1's own PE-only allowance).
# - "pe_ou_scoped": requires Procuring Entity scope, plus Organisation Unit
#   scope when the resource carries one.
ROLE_CLASSIFICATIONS: dict[str, str] = {
	# Reference Data — CFG-CHG-002 v0.4 / AUTH-ADR-001 v1.1: one global Role,
	# not read through this capability-string map (see
	# reference_data_permissions.require_reference_data_manager) — registered
	# here only so its classification is documented in one place per §5.2.
	"Reference Data Manager": "global_central",
	# Downstream Accounting Officer (Procurement Planning's own approval Role —
	# distinct from the retired reference-data reuse of this same Role name).
	"Accounting Officer": "pe_fy_scoped",
	# Budget
	"Budget Viewer": "pe_scoped",
	"Budget Officer": "pe_scoped",
	"Budget Reviewer": "pe_scoped",
	"Budget Activation Authority": "pe_scoped",
	# Departmental Needs
	"Departmental Need Requester": "pe_ou_scoped",
	"Head of User Department": "pe_ou_scoped",
	"Procurement Planner": "pe_scoped",
	"Auditor": "pe_scoped",
	# Strategy — STR-CHG-001 v1.5 §7/§18.1: Strategy Reviewer retired outright;
	# Strategy Approval Authority renamed to Strategy Approver (same
	# responsibility, new name).
	"Strategy Author": "pe_scoped",
	"Strategy Approver": "pe_scoped",
	# Cross-cutting (new Roles this migration introduces)
	"KenTender Task Administrator": "pe_fy_scoped",
	"KenTender Support Analyst": "pe_scoped",
}

# Capability string -> exactly one required Frappe Role. Every entry here is
# either READY (already had a defensible Role) or RESOLVED (a real decision
# recorded in AUTH-ADR-001-capability-mapping.md §9) — none is a guess.
CAPABILITY_ROLE_MAP: dict[str, str] = {
	# Reference Data is deliberately absent (AUTH-AC-019): PE, Financial Year
	# and PE/FY Context maintenance require the Reference Data Manager Role
	# directly (reference_data_permissions.require_reference_data_manager),
	# not a reference_data.* capability string dispatched through this map.
	# Budget — RESOLVED (§9.3): .reserve retired to an internal service call,
	# .revision.apply retired outright, .approve remapped to Budget Activation
	# Authority per BUD-CHG-001 §7/§6.1.
	"budget.list": "Budget Viewer",
	"budget.view": "Budget Viewer",
	"budget.create": "Budget Officer",
	"budget.edit": "Budget Officer",
	"budget.submit": "Budget Officer",
	"budget.review": "Budget Reviewer",
	"budget.return": "Budget Reviewer",
	"budget.approve": "Budget Activation Authority",
	"budget.export": "Budget Activation Authority",
	# Departmental Needs — RESOLVED (§9.6): oversight_read moved off Budget
	# Officer onto Auditor; budget responsibility does not imply Needs
	# oversight authority.
	"departmental_needs.create": "Departmental Need Requester",
	"departmental_needs.edit_own": "Departmental Need Requester",
	"departmental_needs.submit": "Departmental Need Requester",
	"departmental_needs.view_own": "Departmental Need Requester",
	"departmental_needs.view_department": "Head of User Department",
	"departmental_needs.review": "Head of User Department",
	"departmental_needs.read_accepted_for_planning": "Procurement Planner",
	"departmental_needs.oversight_read": "Auditor",
	"procurement_planning.need_allocate": "Procurement Planner",
	# Strategy — READY (STR-CHG-001 v1.5: review capability retired)
	"strategy.plan_version.author": "Strategy Author",
	"strategy.plan_version.approve": "Strategy Approver",
	# Cross-cutting — RESOLVED (§9.2, §9.4)
	"authorization.task.reassign": "KenTender Task Administrator",
	"support.record.view": "KenTender Support Analyst",
}

# Roles this migration introduces or formalizes as real Frappe Roles for the
# first time (previously only a Capability Profile display name or a seed
# fixture username, never a registered Role — confirmed via the pre-cutover
# inventory). "Accounting Officer" and every other Role above already exists
# live and is not re-created here.
NEW_ROLES: tuple[str, ...] = (
	"Reference Data Manager",
	"Budget Activation Authority",
	"Finance Confirmation Officer",
	"KenTender Task Administrator",
	"KenTender Support Analyst",
)


def ensure_roles() -> None:
	"""Idempotently create every Role this migration introduces or formalizes."""
	for role in NEW_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)
