# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe


def after_install():
	"""A fresh `bench install-app` / `bench reinstall` never fires after_migrate,
	so every step below used to land only on the *next* `bench migrate` — a
	rebuilt site came up with an empty PE Type catalogue (blocking the very
	first Procuring Entity) and one leaked Desk tile per module Workspace.

	Every step is idempotent, so running them here as well as on each migrate is
	safe. One limitation worth knowing: sibling KenTender apps install after this
	app, so their Workspaces do not exist yet and the Desk-tile sweep can only
	catch kentender_core's own here — the after_migrate pass catches the rest."""
	after_migrate()


def after_migrate():
	_ensure_user_kt_scope_fields()
	_hide_auto_generated_module_desktop_icons()
	_ensure_default_pe_types()
	_ensure_business_role_projections()
	_ensure_fiscal_year_flag_fields()


def _ensure_fiscal_year_flag_fields():
	"""CFG-CHG-002 v0.6 §4.2 — the namespaced intake flags on ERPNext Fiscal Year.

	KenTender uses the ERPNext DocType unchanged and adds only Custom Fields
	under the `kentender_` prefix — never a fork, override or shadow year
	table (§15.1/§16). `create_custom_fields` is idempotent, so this is the
	code-shipped equivalent of a fixture and survives a site rebuild.

	The flag pattern rule: a future module flag is a
	`kentender_{module}_{purpose}` check plus an optional `_closes_at`
	datetime, added HERE, not in the consuming module (§4.2)."""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	create_custom_fields(
		{
			"Fiscal Year": [
				{
					"fieldname": "kentender_needs_submission_open",
					"fieldtype": "Check",
					"label": "KenTender: Needs Submission Open",
					"default": "0",
					"read_only": 1,
					"no_copy": 1,
					"insert_after": "disabled",
					"description": "At most one Fiscal Year may have this enabled at any instant. Maintained only through System setup.",
				},
				{
					"fieldname": "kentender_needs_submission_closes_at",
					"fieldtype": "Datetime",
					"label": "KenTender: Needs Submission Closes At",
					"read_only": 1,
					"no_copy": 1,
					"insert_after": "kentender_needs_submission_open",
					"description": "Optional. Reaching this instant closes intake automatically.",
				},
				{
					"fieldname": "kentender_dpp_submission_open",
					"fieldtype": "Check",
					"label": "KenTender: Departmental Plan Submission Open",
					"default": "0",
					"read_only": 1,
					"no_copy": 1,
					"insert_after": "kentender_needs_submission_closes_at",
					"description": "CFG-CHG-002 v0.9 §4.2. At most one Fiscal Year may have this enabled at any instant; independent of needs intake. Maintained only through the site-configuration commands.",
				},
				{
					"fieldname": "kentender_dpp_submission_closes_at",
					"fieldtype": "Datetime",
					"label": "KenTender: Departmental Plan Submission Closes At",
					"read_only": 1,
					"no_copy": 1,
					"insert_after": "kentender_dpp_submission_open",
					"description": "Optional. Reaching this instant closes departmental-plan intake automatically.",
				},
				{
					"fieldname": "kentender_flag_changed_by",
					"fieldtype": "Link",
					"options": "User",
					"label": "KenTender: Flag Changed By",
					"read_only": 1,
					"no_copy": 1,
					"insert_after": "kentender_dpp_submission_closes_at",
				},
				{
					"fieldname": "kentender_flag_changed_at",
					"fieldtype": "Datetime",
					"label": "KenTender: Flag Changed At",
					"read_only": 1,
					"no_copy": 1,
					"insert_after": "kentender_flag_changed_by",
				},
			]
		},
		ignore_validate=True,
		update=True,
	)


def _ensure_business_role_projections():
	"""Create the Frappe Role each registered responsibility projects (§7.1).

	AUTH-ADR-001 v1.2 makes a Frappe Role a projection of an assignment, not a
	grant — but the projection still has to exist before a grant can add it.
	Role provisioning used to be imperative and seed-only, spread across five
	per-module `ensure_*_roles()` helpers, which is how role names drifted
	between modules in the first place. Idempotent: only ever fills a gap."""
	from kentender_core.services.business_role_registry import ensure_roles

	ensure_roles()


DEFAULT_PE_TYPES = (
	("MINISTRY", "Ministry"),
	("COUNTY_GOVERNMENT", "County Government"),
	("JUDICIARY", "Judiciary"),
	("COMMISSION", "Commission"),
	("STATE_CORPORATION", "State Corporation"),
	("PUBLIC_UNIVERSITY", "Public University"),
	("OTHER", "Other"),
)


def _ensure_default_pe_types():
	"""A blank PE Type catalogue leaves the New Procuring Entity screen with
	no option to select and no way to add one inline — this ships the same
	vocabulary Procuring Entity's own hardcoded entity_type Select already
	uses, so a fresh site isn't stuck at the very first governed record.
	Never overwrites a site's own PE Type rows — only fills a gap.

	Guard on count(), not `frappe.db.exists("PE Type")`: the single-argument
	form asks "is there a DocType by this name", not "does this table hold any
	row", so it stayed falsy with a populated catalogue and re-inserted on every
	after_migrate — a DuplicateEntryError that would abort the whole migrate."""
	if frappe.db.count("PE Type"):
		return
	for type_code, label in DEFAULT_PE_TYPES:
		frappe.get_doc(
			{
				"doctype": "PE Type",
				"type_code": type_code,
				"label": label,
				"status": "Active",
			}
		).insert(ignore_permissions=True)
	frappe.db.commit()


def _ensure_user_kt_scope_fields():
	"""Custom fields on User for entity-scoped Strategy permissions (spec §3)."""
	# kt_procuring_entity retired by CTX-CHG-001: the global working PE lives
	# in frappe.defaults (kt_working_procuring_entity), migrated by
	# migrate_kt_procuring_entity_to_working_pe.
	fields = [
		{
			"fieldname": "kt_primary_department",
			"label": "Primary Department (KenTender)",
			"fieldtype": "Link",
			"options": "Procuring Department",
			"insert_after": "username",
		},
	]
	for f in fields:
		if frappe.db.exists("Custom Field", {"dt": "User", "fieldname": f["fieldname"]}):
			continue
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "User",
				"module": "Kentender Core",
				**f,
			}
		).insert()
	frappe.clear_cache(doctype="User")


def _hide_auto_generated_module_desktop_icons():
	"""Frappe's create_desktop_icons() emits one Desk tile per public Workspace.

	KenTender ships its own tiles as fixtures — Procurement (the module shell)
	and Tenders (the public portal). Every module Workspace behind them (Bid
	Opening, Evaluation and Award, Platform Configuration & Governance, …) is
	reached from inside that shell, so an auto-generated tile for one is
	duplicate navigation scattered across the Desk.

	Two deliberate choices here. Hide rather than delete: create_desktop_icons()
	recreates these on every install and every `bench migrate`, so a deleted row
	simply comes back while a hidden one survives. And key off "auto-generated
	(standard=0) and points at a KenTender-owned Workspace" rather than the
	label list this function used to carry — that list only knew about Strategy
	and Budget, so every module added since leaked a new tile onto the Desk.

	The shipped standard=1 fixtures are never touched: their visibility and role
	gating belong to their own fixture (G0-013 asserts the Procurement tile stays
	visible and unrestricted)."""
	modules = frappe.get_all(
		"Module Def", filters={"app_name": ("like", "kentender%")}, pluck="name"
	)
	if not modules:
		return
	workspaces = frappe.get_all(
		"Workspace", filters={"module": ("in", modules)}, pluck="name"
	)
	if not workspaces:
		return
	for name in frappe.get_all(
		"Desktop Icon",
		filters={"link_to": ("in", workspaces), "standard": 0, "hidden": 0},
		pluck="name",
	):
		frappe.db.set_value("Desktop Icon", name, "hidden", 1)
	frappe.db.commit()
	frappe.clear_cache()
