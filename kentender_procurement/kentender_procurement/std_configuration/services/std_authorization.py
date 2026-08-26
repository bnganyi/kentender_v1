# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 §12 capability wiring.

STD Configuration is global config, not PE/OU-scoped (spec §14: "The global PE/FY
selector is not shown because STD packages are global configuration"). Strategy's
and CFG-CHG-002's precedent (`kentender_core.services.authorization_policy`,
`Operational Scope Assignment`) was tried first and found NOT to fit:
`Operational Scope Assignment.procuring_entity_id` is a mandatory Link field
platform-wide — the whole engine is built around PE-scoped grants, and no
existing module in this repo has a genuinely PE-less capability. Fabricating a
placeholder "global" Procuring Entity record to force-fit the PE-shaped engine
was rejected as dishonest scope modeling; modifying `Operational Scope
Assignment`'s schema to make the field optional is a `kentender_core`-owned,
cross-app, hard-to-reverse change well outside this module's boundary.

Instead: the base capability gate is plain Frappe Role membership (`STD
Configurator`/`STD Reviewer` — already wired into every Phase 1/2 doctype's own
permission block, so this doesn't introduce a second source of truth). Maker-
checker is a small bespoke check reusing the same submitted/decided history
`std_lifecycle.py` already records on `STD Cfg Review Task`/`STD Cfg Decision` —
not `authorization_policy`'s `_sod_blocked`, which requires a `ResourceContext`
this module has no honest way to construct.
"""

from __future__ import annotations

import frappe
from frappe import _

CAP_CONFIGURE = "std_configuration.package.configure"
CAP_REVIEW = "std_configuration.package.review"

ROLE_STD_CONFIGURATOR = "STD Configurator"
ROLE_STD_REVIEWER = "STD Reviewer"

STD_CONFIGURATION_ROLES = (ROLE_STD_CONFIGURATOR, ROLE_STD_REVIEWER)

# capability -> the Frappe Role that grants it. A plain 1:1 map today; kept as a
# map (not a hardcoded if/else) so a future capability can be added without
# touching every call site.
_CAPABILITY_ROLE: dict[str, str] = {
	CAP_CONFIGURE: ROLE_STD_CONFIGURATOR,
	CAP_REVIEW: ROLE_STD_REVIEWER,
}

# The one §12 maker-checker pair: a Draft's submitter (CAP_CONFIGURE) cannot also
# be its activator/returner (CAP_REVIEW) — spec §12: "The submitter cannot
# activate the same Draft."
_SOD_PAIR = (CAP_CONFIGURE, CAP_REVIEW)


def ensure_std_configuration_governance_roles() -> dict:
	"""Idempotent: create the 2 §12 Frappe Roles. No Capability Profile or
	Operational Scope Assignment records — see module docstring. Does not grant
	the role to a specific user; real actor assignment is Phase 5's seed
	contract, done the same way every other Frappe Role is granted (User's Roles
	table), not through the PE-scoped assignment mechanism."""
	created = {"roles": []}
	for role in STD_CONFIGURATION_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
				ignore_permissions=True
			)
			created["roles"].append(role)
	return created


def prior_actions_for_draft(draft_name: str) -> list[dict]:
	"""§12 maker-checker history for one Draft, reconstructed from the Review
	Task/Decision trail Phase 3 already records — no separate audit log needed:
	a submission is a CAP_CONFIGURE act, a Decision is a CAP_REVIEW act."""
	out = []
	for submitted_by in frappe.get_all(
		"STD Cfg Review Task", filters={"draft_id": draft_name}, pluck="submitted_by"
	):
		out.append({"user": submitted_by, "capability": CAP_CONFIGURE})
	task_names = frappe.get_all("STD Cfg Review Task", filters={"draft_id": draft_name}, pluck="name")
	if task_names:
		for decided_by in frappe.get_all(
			"STD Cfg Decision", filters={"review_task_id": ["in", task_names]}, pluck="decided_by"
		):
			out.append({"user": decided_by, "capability": CAP_REVIEW})
	return out


def _has_role(user: str, capability: str) -> bool:
	# §12 — "System Manager alone grants no STD business decision." Frappe's own
	# `get_roles()` returns every role in the system for "Administrator" (a
	# framework-level superuser bypass, confirmed live: 118/118 roles including
	# both of this module's own) — a plain role-membership check would silently
	# let Administrator through despite holding no real STD Configurator/Reviewer
	# assignment. Explicitly excluded here, matching Strategy's own §16.2
	# no-fallback rule for its equivalent lifecycle capabilities.
	if user == "Administrator":
		return False
	role = _CAPABILITY_ROLE.get(capability)
	return bool(role) and role in frappe.get_roles(user)


def _sod_blocked(user: str, capability: str, draft_name: str) -> bool:
	prior = {row["capability"] for row in prior_actions_for_draft(draft_name) if row["user"] == user}
	if not prior:
		return False
	first, second = _SOD_PAIR
	return (capability == first and second in prior) or (capability == second and first in prior)


def require_draft_capability(user: str, capability: str, draft, *, correlation_id: str = "") -> None:
	"""§12 — fail closed on a missing role (no System Manager/Administrator
	fallback) and on the maker-checker SoD pair. §13.3 error codes:
	`STD_CONTEXT_REQUIRED` (no effective assignment at all — the spec's own
	error table has no separate "wrong role for this specific action" code, so
	a Reviewer attempting a Configurator action also surfaces this one) and
	`STD_MAKER_CHECKER` (the SoD pairing specifically)."""
	from kentender_procurement.std_configuration.services.std_errors import (
		STD_CONTEXT_REQUIRED,
		STD_MAKER_CHECKER,
		std_throw,
	)

	draft_name = draft if isinstance(draft, str) else draft.name
	if not user or user == "Guest" or not _has_role(user, capability):
		std_throw(STD_CONTEXT_REQUIRED)
	if _sod_blocked(user, capability, draft_name):
		std_throw(STD_MAKER_CHECKER)


def has_draft_capability(user: str, capability: str, draft) -> bool:
	draft_name = draft if isinstance(draft, str) else draft.name
	return _has_role(user, capability) and not _sod_blocked(user, capability, draft_name)


def require_package_configure_capability(user: str, package_id: str) -> None:
	"""Bootstrap check for `create_draft`/`create_next_draft`: no Draft exists yet
	to run a maker-checker check against, so this is a plain role check.
	§13.3 `STD_CONTEXT_REQUIRED`."""
	from kentender_procurement.std_configuration.services.std_errors import (
		STD_CONTEXT_REQUIRED,
		std_throw,
	)

	if not user or user == "Guest" or not _has_role(user, CAP_CONFIGURE):
		std_throw(STD_CONTEXT_REQUIRED)
