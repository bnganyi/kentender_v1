# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KT-STD-001 v1.1 §8 — the canonical site fixture world, seeded through the
same public commands as the UI (§8.6: seeds never write a governed DocType
directly; they are deterministic and idempotent, create no legacy authority
row, and never grant a business role to Administrator).

Run:
  bench --site <site> execute kentender_core.seeds.site_setup.run

Idempotency: every step is find-or-skip. Organisation units are addressed by
their §8.2 names (the add command's normalised-sibling rule already collapses
a re-run onto the existing unit); unit *codes* are server-generated
`OU-MOH-{sequence}` values — the §8.2 mnemonic codes (`OU-MOH-DHP`) cannot be
produced through the governed command, which never accepts a user-entered
code (CFG v0.6 §4.3). Recorded as conflict C4 in the tracker.

Conflicting authoritative data fails the seed rather than being repaired
(§8.6): a site configured as a different Procuring Entity raises.
"""

from __future__ import annotations

import frappe

from kentender_core.services import organisation_structure as structure
from kentender_core.services import responsibility_administration as administration
from kentender_core.services import site_configuration as configuration

FIXTURE_TAG = "KT_STD_001_S8"

SITE = {
	"pe_name": "Ministry of Health",
	"pe_code": "PE-MOH",
	"pe_type": "National Government Ministry",
	"ppra_registration": "PPRA/PE/2019/0114",
	"timezone": "Africa/Nairobi",
}

UNITS = (
	# (unit name, parent unit name or None for the root)
	("Directorate of Digital Health and Policy", None),
	("Digital Health", "Directorate of Digital Health and Policy"),
	("Human Resources Management and Development", None),
)

FISCAL_START_YEARS = (2026, 2027)
INTAKE = {"start_year": 2027, "closes_at": "2026-11-25 23:59:00"}

ACTORS = (
	# (local part, full name)
	("grace.wanjiku", "Grace Wanjiku"),
	("peter.kimani", "Dr Peter Kimani"),
	("julia.njeri", "Julia Njeri"),
	("mercy.kilonzo", "Mercy Kilonzo"),
	("samuel.otieno", "Samuel Otieno"),
)

ASSIGNMENTS = (
	# (user local part, business role, unit name or None, kwargs)
	("grace.wanjiku", "Departmental Author", "Digital Health", {}),
	# §8.3 — the Cartesian-product regression fixture: the same user holds a
	# different role in a different unit.
	("grace.wanjiku", "Head of User Department", "Human Resources Management and Development", {}),
	("peter.kimani", "Head of User Department", "Human Resources Management and Development", {}),
	(
		"julia.njeri",
		"Head of User Department",
		"Digital Health",
		{
			"appointment_type": "Acting",
			"authority_reference": "MOH/HR/ACT/2026/041",
			"effective_from": "2026-10-01 00:00:00",
			"effective_to": "2026-11-30 23:59:59",
		},
	),
	("mercy.kilonzo", "Procurement Planner", None, {}),
	# CU-307 (owner decision 2026-09-03): an existing actor authors strategy —
	# Mercy holds the Site-wide Strategy Author responsibility. Extends the
	# KT-STD §8.3 register; approvers are granted through the admin UI.
	("mercy.kilonzo", "Strategy Author", None, {}),
	(
		"samuel.otieno",
		"Head of User Department",
		"Directorate of Digital Health and Policy",
		{
			"effective_from": "2026-01-01 00:00:00",
			"effective_to": "2026-08-31 23:59:59",
		},
	),
)

ENABLED_UOMS = (
	"Each",
	"Programme",
	"Set",
	"Lot",
	"Kilogram",
	"Litre",
	"Metre",
	"Square Metre",
	"Cubic Metre",
	"Service Month",
)


def run(*, commit: bool = True) -> dict:
	result = {
		"site": _seed_site(),
		"units": _seed_units(),
		"company": _seed_company(),
		"fiscal_years": _seed_fiscal_years(),
		"intake": _seed_intake(),
		"uoms": _seed_uoms(),
		"users": _seed_users(),
		"assignments": _seed_assignments(),
	}
	if commit:
		frappe.db.commit()
	return result


def _seed_site() -> str:
	if configuration.is_configured():
		stored = frappe.db.get_single_value(configuration.SITE_PE_DOCTYPE, "pe_code")
		if stored != SITE["pe_code"]:
			# §8.6 — never repair, alias or overwrite conflicting authority.
			frappe.throw(
				f"This site is configured as {stored}, not {SITE['pe_code']}. "
				"The canonical seed refuses to overwrite a different site identity."
			)
		# Descriptive fields converge idempotently through the same command.
		configuration.update_procuring_entity(
			payload={
				"pe_name": SITE["pe_name"],
				"pe_type": SITE["pe_type"],
				"ppra_registration": SITE["ppra_registration"],
				"timezone": SITE["timezone"],
			}
		)
		return "updated"
	configuration.configure_procuring_entity(**SITE)
	return "configured"


def _seed_units() -> dict[str, str]:
	root = structure._root()
	created: dict[str, str] = {}
	by_name = {"__root__": root}
	for name, parent_name in UNITS:
		parent = by_name["__root__"] if parent_name is None else by_name[parent_name]
		outcome = structure.add_organisation_unit(parent_id=parent, name=name)
		by_name[name] = outcome["unit"]
		created[name] = outcome["unit"]
	return created


def _seed_company() -> str:
	existing = frappe.get_all("Company", pluck="name", limit_page_length=2)
	if existing:
		# One Company corresponds to the site PE (§7 of the ADR). A site that
		# already runs accounting keeps its Company; the seed never creates a
		# competing legal entity beside it.
		return f"existing: {existing[0]}"
	frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": SITE["pe_name"],
			"abbr": "MOH",
			"default_currency": "KES",
			"country": "Kenya",
		}
	).insert(ignore_permissions=True)
	return SITE["pe_name"]


def _seed_fiscal_years() -> list[str]:
	out = []
	for year in FISCAL_START_YEARS:
		name = configuration._fy_name(year)
		if frappe.db.exists("Fiscal Year", name):
			out.append(f"existing: {name}")
			continue
		configuration.add_fiscal_year(start_year=year)
		out.append(name)
	return out


def _seed_intake() -> str:
	target = configuration._fy_name(INTAKE["start_year"])
	if frappe.db.get_value("Fiscal Year", target, configuration.FLAG_OPEN):
		return f"already open: {target}"
	configuration.open_needs_submission(
		fiscal_year=target,
		closes_at=INTAKE["closes_at"],
		reason="Annual needs call issued under circular MOH/PROC/2026/07.",
	)
	return f"opened: {target}"


def _seed_uoms() -> dict[str, int]:
	enabled = 0
	for uom in ENABLED_UOMS:
		if frappe.db.exists("UOM", uom):
			frappe.db.set_value("UOM", uom, "enabled", 1, update_modified=False)
		else:
			frappe.get_doc({"doctype": "UOM", "uom_name": uom, "enabled": 1}).insert(
				ignore_permissions=True
			)
		enabled += 1
	disabled = frappe.db.sql(
		"""update `tabUOM` set enabled = 0 where name not in %(keep)s and enabled = 1""",
		{"keep": ENABLED_UOMS},
	)
	remaining = frappe.db.count("UOM", {"enabled": 1})
	return {"enabled": enabled, "enabled_total": remaining}


def _seed_users() -> list[str]:
	out = []
	for local, full_name in ACTORS:
		email = f"{local}@moh.example.test"
		if not frappe.db.exists("User", email):
			first, _, last = full_name.partition(" ")
			doc = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": first,
					"last_name": last,
					"send_welcome_email": 0,
					"user_type": "System User",
					"enabled": 1,
				}
			)
			doc.insert(ignore_permissions=True)
			doc.add_roles("Desk User")
		out.append(email)
	return out


def _seed_assignments() -> list[str]:
	units = {
		row["unit_name"]: row["name"]
		for row in frappe.get_all(
			"Organisation Unit", fields=["name", "unit_name"], limit_page_length=0
		)
	}
	out = []
	for local, role, unit_name, kwargs in ASSIGNMENTS:
		outcome = administration.grant(
			user=f"{local}@moh.example.test",
			business_role=role,
			organisation_unit=units[unit_name] if unit_name else "",
			fixture_namespace=FIXTURE_TAG,
			actor="Administrator",
			**kwargs,
		)
		out.append(f"{outcome['assignment']}{'' if outcome['created'] else ' (existing)'}")
	return out
