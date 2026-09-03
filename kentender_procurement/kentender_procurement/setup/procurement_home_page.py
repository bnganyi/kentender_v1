"""Procurement Home Desk page roles (`kt-procurement-home`).

`kt-procurement-home` is the Desk landing page for the whole KenTender
procurement suite — the "Home" entry in the module menu, and where a signed-in
user arrives. A role absent from its `roles` list is refused the page outright
with "Not permitted", **whatever** access that role holds elsewhere.

Until this module existed the list was hand-maintained inside
`page/kt_procurement_home/kt_procurement_home.json`, and it silently went stale
once per module rebuild: STR-CHG-001 v1.5, BUD-CHG-001 v1.2, CFG-CHG-002 and
NDS-CHG-001 v1.1 each renamed or introduced roles and none of them updated this
page. Observed 2026-08-29: **42 enabled users across 5 modules were locked out
of the application**, including every `Departmental Author` (the v1.1 rename of
`Departmental Need Requester`), every Strategy and Budget role from those
rebuilds, and the `Reference Data Manager`. The only test guarding the page
asserted the *retired* Demand-era set, so it passed throughout and actively
locked in the wrong answer.

Two properties make that failure mode possible, and both are addressed here:

1. **The list is now declared, not edited in a fixture.** `LANDING_ROLES` below
   is the single source of truth, grouped by the specification that owns each
   role so a rebuild has an obvious place to register its rename.
2. **It is reconciled on every migrate**, not merged. A role removed from the
   tuple is removed from the live Page, so a retired role cannot survive in an
   existing environment the way `Demand Viewer` did.

**This page gates entry, not authority.** `get_procurement_home` is a
permission-scoped projection taking `user=frappe.session.user`, and every
destination screen re-checks its own role and scope on the server. Being listed
here means "this role has somewhere to go in this Desk", not "this role may see
everything on the page".
"""

from __future__ import annotations

import frappe

PAGE_NAME = "kt-procurement-home"

# Grouped by owning specification. When a module rebuild renames a role, change
# it *here* — the fixture JSON and the live record both follow.
#
# Roles with no holder today are deliberately included: "nobody holds it yet" is
# exactly the state every one of the 42 lockouts passed through on its way to
# breaking, and an empty role is the cheapest possible thing to admit.
LANDING_ROLES: tuple[str, ...] = (
	# --- Framework -------------------------------------------------------
	"Administrator",
	"System Manager",
	# --- Strategy Alignment (STR-CHG-001 v1.5) ---------------------------
	"Strategy Author",
	"Strategy Approver",
	"Strategy Viewer",
	# --- Budget & Funding (BUD-CHG-001 v1.2) -----------------------------
	"Budget Officer",
	"Budget Reviewer",
	"Budget Approver",
	"Budget Authority",
	"Budget Activation Authority",
	"Budget Viewer",
	"Accounting Officer",
	"Finance Confirmation Officer",
	"Finance Reviewer",
	# --- Departmental Needs (NDS-CHG-001 v1.1 §6) ------------------------
	# Mirrors `departmental_needs_page.LANDING_ROLES`. `Departmental Author`
	# is the v1.1 rename of the retired `Departmental Need Requester`, and its
	# absence here is what locked Grace Wanjiku and the other authors out.
	"Departmental Author",
	"Head of User Department",
	"Procurement Planner",
	"Auditor",
	# --- Procurement Planning (PLN-CHG-001 v1.1) -------------------------
	"Planning Authority",
	"Planning Reviewer",
	"Planning Contributor",
	"Planning Viewer",
	"Planning Officer",
	# --- Procurement Requisitions (REQ-CHG-001) --------------------------
	# REQ-CHG-001 v1.2 is Proposed for approval and may rename these; they are
	# kept as-is until it is approved, because the module and its users exist.
	"Requisitioner",
	"Requester",
	"Business Approver",
	"Department Approver",
	"Designated Approver",
	"Procurement Approval Authority",
	# --- Tender preparation and STD administration -----------------------
	"Procurement Officer",
	"Tender Initiator",
	"STD Configurator",
	"STD Reviewer",
	"STD Technical Inspector",
	"STD Template Activator",
	"STD Template Administrator",
	"STD Template Approver",
	"STD Template Auditor",
	"STD Template Importer",
	"STD Template Reviewer",
	# --- Configuration and Governance (CFG-CHG-002 v0.4) -----------------
	"Reference Data Manager",
	"PE Configuration Steward",
	"Central Configuration Approver",
	"Central Reference Data Steward",
	"Professional Configuration Reviewer / HoPF",
	"KenTender Support Analyst",
	"KenTender Task Administrator",
)

# Retired by their owning specification and refused re-entry. `Demand Viewer` is
# the Demand-era role NDS-BR-020 forbids retaining; it survived on this page
# with zero holders because the fixture was only ever added to. `Tender Manager`
# is worse than dead — `kentender_core.seeds.mvp1_role_user_cleanup` puts it in
# `ROLES_TO_DISABLE`, so it sat on the page as a role Frappe would refuse anyway.
RETIRED_ROLES: frozenset[str] = frozenset(
	{
		"Demand Viewer",
		"Tender Manager",
		"Departmental Need Requester",
		"Departmental Review Delegate",
		"Needs Configuration Manager",
	}
)


def reconcile() -> bool:
	"""Make the live Page's role list exactly `LANDING_ROLES`.

	Reconciles rather than merges, so a role dropped from the tuple is dropped
	from the environment. Returns True when the record changed.
	"""
	if not frappe.db.exists("Page", PAGE_NAME):
		return False
	page = frappe.get_doc("Page", PAGE_NAME)
	current = sorted({row.role for row in page.roles})
	wanted = sorted(set(LANDING_ROLES))
	if current == wanted:
		return False
	frappe.flags.allow_doctype_export = True
	page.set("roles", [{"role": role} for role in wanted])
	page.save(ignore_permissions=True)
	return True
