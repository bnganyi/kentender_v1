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
	"""CFG-CHG-002 v0.11 §4.3 — the namespaced intake flags on ERPNext Fiscal Year.

	KenTender uses the ERPNext DocType unchanged and adds only Custom Fields
	under the `kentender_` prefix — never a fork, override or shadow year
	table (§15.1/§16). `create_custom_fields` is idempotent, so this is the
	code-shipped equivalent of a fixture and survives a site rebuild.

	The flag pattern rule: a future module flag is a
	`kentender_{module}_{purpose}` check plus an optional `_closes_at`
	datetime, added HERE, not in the consuming module (§4.2/§4.3).

	v0.11 replaces the single shared `kentender_flag_changed_by`/`_at` pair
	with namespaced `kentender_{module_key}_intake_changed_by`/`_changed_at`/
	`_revision` per module key, so a reader can tell which module last
	touched a given year's flags (CFG10-CHG-007). The retired shared fields
	are dropped outright, not kept as a fallback — no migration was needed
	for this cutover (owner, 16 Sep 2026: dev site data may be torn down)."""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	from kentender_core.services.site_configuration import MODULE_AUDIT_FIELDS, MODULE_FLAG_FIELDS

	# Exact §4.3 field names come from `site_configuration.py`'s own
	# `MODULE_FLAG_FIELDS`/`MODULE_AUDIT_FIELDS` — the single source of truth
	# — rather than re-derived here, so the two can never drift apart (the
	# spec's own table is *not* uniform: needs/dpp carry a `_submission_`
	# infix, disposal_plan does not).
	MODULE_LABELS = {
		"needs": "Needs Submission",
		"dpp": "Departmental Plan Submission",
		"disposal_plan": "Disposal Plan Submission",
	}
	insert_after_by_key = {"needs": "disabled"}
	ordered_keys = list(MODULE_FLAG_FIELDS)
	for previous, current in zip(ordered_keys, ordered_keys[1:]):
		insert_after_by_key[current] = MODULE_AUDIT_FIELDS[previous][2]  # previous module's `_revision` field

	fields: list[dict] = []
	for key, (flag_open, flag_closes_at) in MODULE_FLAG_FIELDS.items():
		label = MODULE_LABELS[key]
		changed_by_field, changed_at_field, revision_field = MODULE_AUDIT_FIELDS[key]
		fields.append(
			{
				"fieldname": flag_open,
				"fieldtype": "Check",
				"label": f"KenTender: {label} Open",
				"default": "0",
				"read_only": 1,
				"no_copy": 1,
				"insert_after": insert_after_by_key[key],
				"description": "At most one Fiscal Year may have this enabled at any instant. Maintained only through System setup.",
			}
		)
		fields.append(
			{
				"fieldname": flag_closes_at,
				"fieldtype": "Datetime",
				"label": f"KenTender: {label} Closes At",
				"read_only": 1,
				"no_copy": 1,
				"insert_after": flag_open,
				"description": "Optional. Reaching this instant closes intake automatically.",
			}
		)
		fields.append(
			{
				"fieldname": changed_by_field,
				"fieldtype": "Link",
				"options": "User",
				"label": f"KenTender: {label} Changed By",
				"read_only": 1,
				"no_copy": 1,
				"insert_after": flag_closes_at,
			}
		)
		fields.append(
			{
				"fieldname": changed_at_field,
				"fieldtype": "Datetime",
				"label": f"KenTender: {label} Changed At",
				"read_only": 1,
				"no_copy": 1,
				"insert_after": changed_by_field,
			}
		)
		fields.append(
			{
				"fieldname": revision_field,
				"fieldtype": "Int",
				"label": f"KenTender: {label} Revision",
				"default": "0",
				"read_only": 1,
				"no_copy": 1,
				"insert_after": changed_at_field,
			}
		)
	create_custom_fields({"Fiscal Year": fields}, ignore_validate=True, update=True)

	# Retired v0.10/v0.11-draft fields — no external reader depends on any of
	# these (grepped repo-wide 16 Sep 2026), dropped outright rather than
	# migrated. The `_submission_open/_closes_at` pair only ever existed
	# transiently on this dev site from a since-corrected `kentender_disposal_plan_submission_*`
	# naming bug in this function itself.
	for retired in (
		"kentender_flag_changed_by",
		"kentender_flag_changed_at",
		"kentender_disposal_plan_submission_open",
		"kentender_disposal_plan_submission_closes_at",
	):
		existing = frappe.db.get_value("Custom Field", {"dt": "Fiscal Year", "fieldname": retired})
		if existing:
			frappe.delete_doc("Custom Field", existing, ignore_permissions=True, force=True)
		# Deleting the Custom Field record only removes the field
		# definition — Frappe's schema sync is additive-only and never drops
		# a column on its own, so the retired column would otherwise linger
		# in the database forever even though nothing can read or write it
		# through the framework any more.
		if frappe.db.has_column("Fiscal Year", retired):
			frappe.db.sql_ddl(f"ALTER TABLE `tabFiscal Year` DROP COLUMN `{retired}`")


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
