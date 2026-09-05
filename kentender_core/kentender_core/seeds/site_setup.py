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
	# CFG-CHG-002 v0.9 §4.1 / PLN-CHG-001 v1.12 §14.6 — the configured route.
	"statutory_approval_route": "Cabinet Secretary",
	"entity_is_county": False,
}

UNITS = (
	# (unit name, parent unit name or None for the root)
	("Directorate of Digital Health and Policy", None),
	("Digital Health", "Directorate of Digital Health and Policy"),
	("Human Resources Management and Development", None),
)

FISCAL_START_YEARS = (2026, 2027)
INTAKE = {"start_year": 2027, "closes_at": "2026-11-25 23:59:00"}
# PLN-CHG-001 v1.12 §14.1 — departmental-plan intake for FY 2027/28 closes
# 30 Nov 2026, 23:59:59 EAT (stored UTC).
DPP_INTAKE = {"start_year": 2027, "closes_at": "2026-11-30 20:59:59"}

# CFG-CHG-002 v0.9 §3 — the requirement-type and procurement-method
# catalogues Configuration & Governance owns (PLN-CHG-001 v1.12 §14.1: four
# types incl. Works; the eleven Third Schedule methods, Open Tender first).
REQUIREMENT_TYPES = ("Non-consulting services", "Consulting services", "Goods", "Works")
PROCUREMENT_METHODS = (
	"Open Tender",
	"Direct Procurement",
	"Restricted Tender",
	"Request for Quotations",
	"Low Value Procurement",
	"Community Participation",
	"Design Competition",
	"Electronic Reverse Auction",
	"Force Account",
	"Competitive Negotiations",
	"Request for Proposals",
)

# CFG-CHG-002 v0.9 §4.4A / PLN-CHG-001 v1.12 §14.1 — the Second Schedule
# matrix in force for FY 2027/28. `max_amount` 0 = no fixed maximum.
_KES = 1.0
THRESHOLD_BANDS = (
	# (method, goods max, works max, services max, basis, reference)
	("Low Value Procurement", 50_000, 100_000, 50_000, "Per item per financial year", "Second Schedule; s.107"),
	("Request for Quotations", 3_000_000, 5_000_000, 3_000_000, "Per request", "Second Schedule; s.105"),
	("Restricted Tender", 30_000_000, 30_000_000, 20_000_000, "Per procurement", "Second Schedule; s.102(1)(b)"),
	("Open Tender", 0, 0, 0, "Funds allocated", "Second Schedule; s.96"),
	("Request for Proposals", 0, 0, 0, "Funds allocated", "Second Schedule; s.116"),
	("Direct Procurement", 0, 0, 0, "Section conditions", "Second Schedule; s.103"),
	("Community Participation", 0, 0, 0, "Funds allocated", "reg 109"),
	("Design Competition", 0, 0, 0, "Funds allocated", "s.92(1)"),
	("Electronic Reverse Auction", 0, 0, 0, "Funds allocated", "s.92(1)"),
	("Force Account", 0, 0, 0, "Funds allocated", "reg 95"),
	("Competitive Negotiations", 0, 0, 0, "Funds allocated", "s.92(1)"),
)
# PLN-CHG-001 v1.12 §4.9 governed reservation values; rank 1 = highest
# advantage (section 156 / regulation 153), 0 = None.
RESERVATION_CATEGORIES = (
	("None", 0, False, ""),
	("Youth", 1, False, "s.157(4); reg 149"),
	("Women", 1, False, "s.157(4); reg 149"),
	("Persons with disabilities", 1, False, "s.157(4); reg 149"),
	("Other disadvantaged group", 2, False, "s.157(4)"),
	("Micro, small and medium enterprise", 3, False, "s.157(4)"),
	("Regional — county", 4, True, "reg 151"),
	("Regional — sub-county", 4, True, "reg 151"),
	("Regional — constituency", 4, True, "reg 151"),
	("National reservation — citizen contractor", 5, False, "s.157(8)(a); reg 163"),
)
REGULATORY_REFERENCE = {
	"gazette_reference": "PPADR 2020 Second Schedule (rev. 2022) — FY 2027/28",
	"effective_from": "2027-07-01",
	"reservation_target_percent": 30,
	"county_resident_target_percent": 20,
	"exclusive_preference_works_amount": 1_000_000_000,
	"exclusive_preference_goods_services_amount": 500_000_000,
}

ACTORS = (
	# (local part, full name)
	("grace.wanjiku", "Grace Wanjiku"),
	("peter.kimani", "Dr Peter Kimani"),
	("julia.njeri", "Julia Njeri"),
	("mercy.kilonzo", "Mercy Kilonzo"),
	("samuel.otieno", "Samuel Otieno"),
	# NDS-CHG-001 v1.6 §14.2 (2026-09-04): Departmental Needs' Auditor actor,
	# per KT-STD-001 §8.3's shared register. Extends the register the same way
	# CU-307 extended Mercy's assignments — one canonical fixture world, not a
	# module-owned duplicate.
	("naomi.chebet", "Naomi Chebet"),
	# STR-CHG-001 v1.7 §14.1 / KT-STD-001 §8.3 (2026-09-05) — Strategy's own
	# named actors. Supersede CU-307's Mercy stand-in below, which existed
	# only because these two did not yet exist.
	("esther.muthoni", "Esther Muthoni"),
	("alfred.ochieng", "Dr Alfred Ochieng"),
)

ASSIGNMENTS = (
	# (user local part, business role, unit name or None, kwargs)
	("grace.wanjiku", "Departmental Author", "Digital Health", {}),
	# §8.3 — the Cartesian-product regression fixture: the same user holds a
	# different role in a different unit.
	("grace.wanjiku", "Head of User Department", "Human Resources Management and Development", {}),
	# NDS-CHG-001 v1.6 §14.2 (2026-09-04): Grace authors in both departments
	# the module's default Needs live in.
	("grace.wanjiku", "Departmental Author", "Human Resources Management and Development", {}),
	("peter.kimani", "Head of User Department", "Human Resources Management and Development", {}),
	# NDS-CHG-001 v1.6 §14.2 (2026-09-04): Peter reviews both departments the
	# module's default Needs live in. Digital Health and HRMD share no
	# covering parent below the site root, so §14.2's fallback applies — two
	# exact leaf assignments rather than one parent grant.
	("peter.kimani", "Head of User Department", "Digital Health", {}),
	(
		"julia.njeri",
		"Head of User Department",
		"Digital Health",
		{
			"appointment_type": "Acting",
			"authority_reference": "MOH/HR/ACT/2026/041",
			# SEED-001 §3.1 states this window as 1 Oct-30 Nov 2026, but her
			# Need-0004 acceptance (kentender_mvp_r1.py) is authorised against
			# real wall-clock time when the seed actually runs, with no
			# time-travel override available on the review command — a window
			# that narrow makes the canonical seed unable to run outside those
			# two months. Widened deliberately (owner decision, 2026-09-05) so
			# the seed stays reliably runnable; the design-clock stamp on her
			# decision still reads 25 Nov 2026 regardless of real run date.
			"effective_from": "2026-09-01 00:00:00",
			"effective_to": "2027-06-30 23:59:59",
		},
	),
	("mercy.kilonzo", "Procurement Planner", None, {}),
	# STR-CHG-001 v1.7 §14.1 / KT-STD-001 §8.3 (2026-09-05) — Strategy's own
	# named actors now exist; supersedes CU-307's Mercy stand-in.
	("esther.muthoni", "Strategy Author", None, {}),
	("alfred.ochieng", "Strategy Approver", None, {}),
	# NDS-CHG-001 v1.6 §14.2 (2026-09-04) — Site-wide Auditor, read-only.
	("naomi.chebet", "Auditor", None, {}),
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
		"dpp_intake": _seed_dpp_intake(),
		"catalogues": _seed_catalogues(),
		"regulatory_reference": _seed_regulatory_reference(),
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
				"statutory_approval_route": SITE["statutory_approval_route"],
				"entity_is_county": SITE["entity_is_county"],
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


def _seed_dpp_intake() -> str:
	target = configuration._fy_name(DPP_INTAKE["start_year"])
	if frappe.db.get_value("Fiscal Year", target, configuration.DPP_FLAG_OPEN):
		return f"already open: {target}"
	configuration.open_dpp_submission(
		fiscal_year=target,
		closes_at=DPP_INTAKE["closes_at"],
		reason="Departmental procurement plans called for FY 2027/28 under regulation 40(3).",
	)
	return f"opened: {target}"


def _seed_catalogues() -> dict[str, int]:
	created = 0
	for doctype, titles in (("Requirement Type", REQUIREMENT_TYPES), ("Procurement Method", PROCUREMENT_METHODS)):
		for title in titles:
			if frappe.db.exists(doctype, title):
				if frappe.db.get_value(doctype, title, "status") != "Active":
					frappe.db.set_value(doctype, title, "status", "Active", update_modified=False)
				continue
			frappe.get_doc({"doctype": doctype, "title": title, "status": "Active"}).insert(ignore_permissions=True)
			created += 1
	return {"created": created, "requirement_types": len(REQUIREMENT_TYPES), "procurement_methods": len(PROCUREMENT_METHODS)}


def _seed_regulatory_reference(fiscal_year: str = "", fixture_namespace: str = FIXTURE_TAG) -> str:
	from kentender_core.services import regulatory_reference as register

	fiscal_year = fiscal_year or configuration._fy_name(DPP_INTAKE["start_year"])
	bands = []
	for method, goods, works, services, basis, reference in THRESHOLD_BANDS:
		for category, amount in (("Goods", goods), ("Works", works), ("Services", services)):
			bands.append(
				{
					"procurement_category": category,
					"procurement_method": method,
					"max_amount": amount,
					"basis": basis,
					"statutory_reference": reference,
				}
			)
	outcome = register.register_regulatory_reference(
		fiscal_year=fiscal_year,
		effective_from=REGULATORY_REFERENCE["effective_from"],
		gazette_reference=REGULATORY_REFERENCE["gazette_reference"],
		threshold_bands=bands,
		reservation_categories=[
			{"category": name, "advantage_rank": rank, "is_regional": regional, "statutory_reference": ref}
			for name, rank, regional, ref in RESERVATION_CATEGORIES
		],
		reservation_target_percent=REGULATORY_REFERENCE["reservation_target_percent"],
		county_resident_target_percent=REGULATORY_REFERENCE["county_resident_target_percent"],
		exclusive_preference_works_amount=REGULATORY_REFERENCE["exclusive_preference_works_amount"],
		exclusive_preference_goods_services_amount=REGULATORY_REFERENCE["exclusive_preference_goods_services_amount"],
		market_prices=[],
		schedule_buffers=[],
		fixture_namespace=fixture_namespace,
	)
	return f"{outcome['reference']}{'' if outcome['created'] else ' (existing)'}"


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
