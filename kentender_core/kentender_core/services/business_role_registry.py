"""AUTH-ADR-001 v1.6 §4.4 — the code-owned business-role registry.

Administrators assign registered responsibilities; they do not define new
roles, scope types or capability strings in production. Every entry here is
taken from the owning module's approved document — this file records the
role's *scope classification*, never invents a role, a business action or an
approval stage.

Exactly two scope types exist (§4.4): **Site-wide** and **Organisation
Unit**. One site is one Procuring Entity, so the former `Global` and
`Procuring Entity` classifications collapse into Site-wide; no other value is
representable.

The registry deliberately holds no capability strings and no command list:
"The registry does not enumerate commands. Each module names the business
role its commands require" (§4.4).

Notes on two properties:

- `exclusive_office` — the §4.7 mechanism (reject a second overlapping
  Active assignment for the same scope, returning the exact conflicting
  record) is implemented in the administration service, but no registered
  role declares it yet: the KT-STD-001 §8.3 canonical seed places two
  simultaneous Head of User Department holders in `OU-MOH-HRMD` (Peter's
  substantive assignment plus Grace's Cartesian-product fixture), which an
  exclusive office would refuse, and ADR §16 explicitly marks AUTH-DES-05's
  conflict as an artboard-only fixture. A module document that declares an
  exclusive office flips the flag here; nothing else changes (tracker D4).
- `sod_tags` — "stable categories consumed by domain segregation checks,
  never free-form capabilities" (§4.4). The live segregation rules are
  evaluated against the actual actions in one evidence chain; the tags only
  categorise, and grant nothing.

Deliberately omitted (KT-STD-001 §7 default-to-omit): `Requisition Preparer`
and `Head of Procurement Function` are illustrative in ADR §4.4 but no
approved, implemented module names them yet — each is registered in the
cutover slice of the document that owns it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import frappe

from kentender_core.services.responsibility_errors import fail

# §4.4 scope types. The literal strings are part of the service contract.
SCOPE_SITE = "Site-wide"
SCOPE_OU = "Organisation Unit"
SCOPE_TYPES: tuple[str, ...] = (SCOPE_SITE, SCOPE_OU)

# §4.4 `allowed_assignment_admin`. System Manager is the live administrative
# role; Administrator holds it implicitly through Frappe.
ASSIGNMENT_ADMIN: tuple[str, ...] = ("System Manager",)


@dataclass(frozen=True)
class BusinessRole:
	"""One registered responsibility, with the §4.4 properties in order."""

	business_role: str
	scope_type: str
	frappe_roles: tuple[str, ...]
	exclusive_office: bool = False
	allowed_assignment_admin: tuple[str, ...] = ASSIGNMENT_ADMIN
	sod_tags: tuple[str, ...] = field(default_factory=tuple)
	# Which approved document is the source of this role's name and actions.
	owning_document: str = ""

	@property
	def requires_organisation_unit(self) -> bool:
		"""§4.5 — required for OU-scoped roles, prohibited for Site-wide."""
		return self.scope_type == SCOPE_OU


def _entry(
	business_role: str,
	scope_type: str,
	owning_document: str,
	*,
	exclusive_office: bool = False,
	sod_tags: tuple[str, ...] = (),
	frappe_roles: tuple[str, ...] | None = None,
) -> BusinessRole:
	# §5.7 — the Frappe Role projection is the minimal framework access the
	# responsibility needs for Desk/DocType reach. Every registered
	# responsibility currently projects the identically-named Role, which is
	# what every module service already checks today.
	return BusinessRole(
		business_role=business_role,
		scope_type=scope_type,
		frappe_roles=frappe_roles if frappe_roles is not None else (business_role,),
		exclusive_office=exclusive_office,
		sod_tags=sod_tags,
		owning_document=owning_document,
	)


_ENTRIES: tuple[BusinessRole, ...] = (
	# --- Departmental Needs (NDS-CHG-001 v1.4) ---------------------------
	_entry(
		"Departmental Author",
		SCOPE_OU,
		"NDS-CHG-001 v1.4",
		sod_tags=("need_authoring", "departmental_plan_authoring"),
	),
	_entry(
		"Head of User Department",
		SCOPE_OU,
		"NDS-CHG-001 v1.4",
		sod_tags=("need_decision", "departmental_certification"),
	),
	_entry(
		"Procurement Planner",
		SCOPE_SITE,
		"NDS-CHG-001 v1.4 / PLN-CHG-001 v1.4 §6",
		sod_tags=("procurement_validation", "plan_preparation"),
	),
	# NDS registers "Auditor"; PLN registers "Planning Auditor". Both are
	# kept: §4.4 makes the module document the source of the exact role name,
	# so they are not merged into one label. ADR §4.4 permits an OU-scoped
	# Auditor "where an approved oversight scope is narrower than the site";
	# no approved document declares that narrowing yet, so Site-wide governs.
	_entry(
		"Auditor",
		SCOPE_SITE,
		"NDS-CHG-001 v1.4 / BUD-CHG-001 v1.3 §7",
		sod_tags=("oversight_read",),
	),
	# --- Procurement Planning (PLN-CHG-001 v1.4 §6) ----------------------
	# Budget Officer serves two approved documents: Budget authoring
	# (BUD-CHG-001 v1.3 §7) and the Planning Finance task (PLN §6). Which of
	# Budget Officer / Finance Confirmation Officer owns the Planning Finance
	# confirmation is an open conflict between those two documents; both are
	# registered and neither is quietly retired here.
	_entry(
		"Budget Officer",
		SCOPE_SITE,
		"BUD-CHG-001 v1.3 §7 / PLN-CHG-001 v1.4 §6",
		sod_tags=("budget_authoring", "finance_confirmation"),
	),
	_entry(
		"Accounting Officer",
		SCOPE_SITE,
		"PLN-CHG-001 v1.4 §6",
		sod_tags=("plan_adoption",),
	),
	# §6: "Exactly one route applies to the PE." The applicable capacity —
	# responsible Cabinet Secretary, County Executive Committee Member, Board
	# or similar governing body — is resolved from the site's own governed
	# entity type at decision time, not by a separate role per capacity.
	_entry(
		"Plan Statutory Approver",
		SCOPE_SITE,
		"PLN-CHG-001 v1.4 §6",
		sod_tags=("statutory_approval",),
	),
	_entry(
		"Planning Auditor",
		SCOPE_SITE,
		"PLN-CHG-001 v1.4 §6",
		sod_tags=("oversight_read",),
	),
	# --- Budget & Funding (BUD-CHG-001 v1.3 §7) --------------------------
	# There is no Budget Viewer role under v1.3 — read access is produced by
	# the registered permission hooks (DocPerm + kentender_scope_map) acting
	# on the actor's assignments, not a fourth business responsibility.
	_entry("Budget Approver", SCOPE_SITE, "BUD-CHG-001 v1.3 §7", sod_tags=("budget_approval",)),
	_entry(
		"Finance Confirmation Officer",
		SCOPE_SITE,
		"BUD-CHG-001 v1.3 §7",
		sod_tags=("finance_confirmation",),
	),
	# --- Strategy Alignment (STR-CHG-001 v1.5 §7) ------------------------
	# ADR v1.6 §20 binds Strategy Author and Approver to Site-wide scope; any
	# departmental narrowing stays a record-ownership check inside Strategy.
	_entry("Strategy Author", SCOPE_SITE, "STR-CHG-001 v1.5 §7", sod_tags=("strategy_authoring",)),
	_entry("Strategy Approver", SCOPE_SITE, "STR-CHG-001 v1.5 §7", sod_tags=("strategy_approval",)),
)

REGISTRY: dict[str, BusinessRole] = {entry.business_role: entry for entry in _ENTRIES}

# §4.4 — Administrator and System Manager are technical roles under §8. They
# are not business assignments and are deliberately absent from REGISTRY; a
# technical role never satisfies `require_registered`.
TECHNICAL_ROLES: frozenset[str] = frozenset({"Administrator", "System Manager"})


def is_registered(business_role: str) -> bool:
	return business_role in REGISTRY


def require_registered(business_role: str) -> BusinessRole:
	"""Return the registered responsibility, or fail with §10's config code."""
	entry = REGISTRY.get(business_role)
	if entry is None:
		fail(
			"AUTH_CONFIGURATION_INVALID",
			f"{business_role} is not a registered KenTender responsibility.",
		)
	return entry  # type: ignore[return-value]


def scope_type(business_role: str) -> str:
	return require_registered(business_role).scope_type


def roles_with_scope_type(wanted: str) -> tuple[str, ...]:
	return tuple(
		sorted(name for name, entry in REGISTRY.items() if entry.scope_type == wanted)
	)


def roles_with_sod_tag(tag: str) -> tuple[str, ...]:
	return tuple(sorted(name for name, entry in REGISTRY.items() if tag in entry.sod_tags))


def projected_frappe_roles(business_role: str) -> tuple[str, ...]:
	return require_registered(business_role).frappe_roles


def all_projected_frappe_roles() -> tuple[str, ...]:
	projected: set[str] = set()
	for entry in REGISTRY.values():
		projected.update(entry.frappe_roles)
	return tuple(sorted(projected))


def may_administer(business_role: str, roles: set[str]) -> bool:
	"""§9.2 — does this actor hold an administrative role allowed to grant it?"""
	entry = require_registered(business_role)
	return bool(set(entry.allowed_assignment_admin) & roles)


def ensure_roles() -> None:
	"""Idempotently create every projected Frappe Role (§5.7).

	Wired into `after_migrate` so the projection a grant depends on exists on
	every site without a seed run. Role provisioning was imperative and
	seed-only before this, which is how role names drifted between modules.
	"""
	for role in all_projected_frappe_roles():
		if not frappe.db.exists("Role", role):
			frappe.get_doc(
				{"doctype": "Role", "role_name": role, "desk_access": 1}
			).insert(ignore_permissions=True)
