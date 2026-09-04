# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""kentender_budget — MVP-1 Budget & Funding (BUD-CHG-001 v1.2 clean rebuild)."""

app_name = "kentender_budget"
app_title = "Kentender Budget"
app_publisher = "KenTender"
app_description = "KenTender budget module (MVP-1 UI-first rebuild)."
app_email = "dev@kentender.local"
app_license = "mit"

required_apps = ["kentender_core", "kentender_strategy"]

from pathlib import Path


def _asset_version(abs_path: Path) -> int:
	# mtime-based cache bust; touch the source file after edits so workers re-import hooks.
	try:
		return int(abs_path.stat().st_mtime)
	except OSError:
		return 1


_CORE_PUBLIC = Path(__file__).resolve().parent.parent.parent / "kentender_core" / "kentender_core" / "public"

# kt_industry_tokens.css (owned by kentender_core, scoped under .kt-industry,
# never :root) is the one canonical design system for the whole application —
# AGENTS.md §6.6. Loaded here the same way any of this app's own
# app_include_css entries would be; Frappe serves every installed app's
# static assets from one shared /assets/<app_name>/ namespace.
app_include_css = [
	f"/assets/kentender_core/css/kt_industry_tokens.css?v={_asset_version(_CORE_PUBLIC / 'css/kt_industry_tokens.css')}",
]

# Never append ?v= to page_js — Frappe resolves these as disk paths.
page_js = {
	# BUD-CHG-001 v1.2 Phase 5 — BUD-UI-01/02/03/04/05 share this one Page.
	# Not "budget" — collides with the existing Budget doctype's own List
	# View route in Frappe's client router (see budget_funding_page.js).
	"budget-funding": "public/js/budget_funding_page.js",
}

after_migrate = "kentender_budget.install.after_migrate"
before_tests = "kentender_budget.install.before_tests"

# BUD-CHG-001 v1.3 §17.1 / AUTH-ADR-001 v1.6 §5.3 — Budget's own first
# production use of the declarative scope map (tracker D6): a DocType absent
# from this map falls through to native DocPerm; one present with zero
# matching User Responsibility Assignment rows is a hard deny, closing the
# gap a stale/unsynced Frappe Role grant would otherwise leave open.
#
# All four registered DocTypes are read only by Site-wide business roles
# (Budget Officer, Budget Approver, Finance Confirmation Officer, Auditor —
# kentender_core.services.business_role_registry), so no role ever narrows
# by the `ou_field` value itself; "name" is a real column on every DocType,
# used only so `scope_condition()` always has a syntactically valid column
# to reference if that ever changes. `owner_org_unit_id` on Procurement
# Budget Line Version is deliberately NOT used here (§17.1/§18: it is
# BUD-BR-007 line-eligibility data, never a scope field).
kentender_scope_map = {
	"Procurement Budget": "name",
	"Procurement Budget Version": "name",
	"Procurement Budget Line": "name",
	"Procurement Budget Line Version": "name",
}

permission_query_conditions = {
	"Procurement Budget": "kentender_core.services.authorization.permission_query_conditions",
	"Procurement Budget Version": "kentender_core.services.authorization.permission_query_conditions",
	"Procurement Budget Line": "kentender_core.services.authorization.permission_query_conditions",
	"Procurement Budget Line Version": "kentender_core.services.authorization.permission_query_conditions",
}

has_permission = {
	"Procurement Budget": "kentender_core.services.authorization.has_permission",
	"Procurement Budget Version": "kentender_core.services.authorization.has_permission",
	"Procurement Budget Line": "kentender_core.services.authorization.has_permission",
	"Procurement Budget Line Version": "kentender_core.services.authorization.has_permission",
}
