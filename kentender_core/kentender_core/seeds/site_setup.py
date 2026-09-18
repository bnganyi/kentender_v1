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
# PLN-CHG-001 v1.23 §4.4 — the governed requirement-type catalogue carries its
# own procurement category. The Planner selects only the type; the server
# derives the category from this catalogue entry and rejects a client-supplied
# one. Never re-express this mapping as a module constant in a consumer.
REQUIREMENT_TYPES = (
	("Non-consulting services", "Services"),
	("Consulting services", "Services"),
	("Goods", "Goods"),
	("Works", "Works"),
)
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
	# BUD-CHG-001 v1.6 §15.1 / KT-STD-001 §8.3 (2026-09-06) — Budget's own
	# named actors, in the shared register rather than a module-owned copy.
	("josphat.mwangi", "Josphat Mwangi"),
	("beatrice.kamau", "Beatrice Kamau"),
	# REQ-CHG-001 v1.6 §16.1 / KT-STD-001 §8.3 (2026-09-06) — the Head of
	# Procurement Function actor Requisitions authorisation names.
	("charles.mutiso", "Charles Mutiso"),
	# TPR-CHG-001 v0.6 §13.2 / KT-STD-001 §8.3 (2026-09-08) — the Procurement
	# Officer who prepares the Tender; a different person from the Head of
	# Procurement Function who approves it (§10.3).
	("brian.wafula", "Brian Wafula"),
	# PLN-CHG-001 v1.18 §10.1 / KT-STD-001 §8.3 (2026-09-12, plan D19) —
	# Planning's Accounting Officer and statutory approver join the shared
	# register here instead of being created by the Planning seed.
	("amina.hassan", "Amina Hassan"),
	("daniel.rotich", "Daniel Rotich"),
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
	# PLN-CHG-001 v1.18 §13.1 (2026-09-12, plan D19): Peter takes Digital
	# Health over from Julia's acting period — dated, not open-ended, so the
	# fixture chronology (Julia certifies DHI on 25 Nov 2026, Peter may act
	# from December) is real at command time under the frozen seed clock.
	("peter.kimani", "Head of User Department", "Digital Health", {"effective_from": "2026-12-01 00:00:00"}),
	(
		"julia.njeri",
		"Head of User Department",
		"Digital Health",
		{
			"appointment_type": "Acting",
			"authority_reference": "MOH/HR/ACT/2026/041",
			# PLN-CHG-001 v1.18 §13.1 / SEED-001 §3.1 — 1 Oct through 30 Nov
			# 2026 inclusive. The 5 Sep 2026 stop-gap that widened this window
			# (so a real-clock seed could act as Julia) is retired by plan D19:
			# seeds now run each command under the frozen clock at its fixture
			# instant (kentender_core.seeds.clock), so her 25 Nov 2026
			# decisions are authorised for real. The retired stop-gap row is
			# revoked by `_reconcile_superseded_fixture_assignments`.
			"effective_from": "2026-10-01 00:00:00",
			"effective_to": "2026-11-30 23:59:59",
		},
	),
	("mercy.kilonzo", "Procurement Planner", None, {}),
	# STR-CHG-001 v1.7 §14.1 / KT-STD-001 §8.3 (2026-09-05) — Strategy's own
	# named actors now exist; supersedes CU-307's Mercy stand-in.
	("esther.muthoni", "Strategy Author", None, {}),
	("alfred.ochieng", "Strategy Approver", None, {}),
	# NDS-CHG-001 v1.6 §14.2 (2026-09-04) — Site-wide Auditor, read-only.
	("naomi.chebet", "Auditor", None, {}),
	# BUD-CHG-001 v1.6 §15.1 — Josphat holds Budget Officer and, separately,
	# Finance Confirmation Officer (the no-self-approval fixture); Beatrice
	# is the Budget Approver. All Site-wide (§7).
	("josphat.mwangi", "Budget Officer", None, {}),
	("josphat.mwangi", "Finance Confirmation Officer", None, {}),
	("beatrice.kamau", "Budget Approver", None, {}),
	# REQ-CHG-001 v1.6 §16.1 — Charles authorises Requisitions and, later,
	# approves Tenders (TPR-CHG-001). Site-wide (§8).
	("charles.mutiso", "Head of Procurement Function", None, {}),
	# TPR-CHG-001 v0.6 §5 — Site-wide Procurement Officer (prepares, never
	# approves, the same Version — §10.3).
	("brian.wafula", "Procurement Officer", None, {}),
	# PLN-CHG-001 v1.18 §6 / §10.1 — Site-wide adoption and statutory
	# capacity (the capacity itself resolves from the site's configured
	# route at decision time).
	("amina.hassan", "Accounting Officer", None, {}),
	("daniel.rotich", "Plan Statutory Approver", None, {}),
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

# BUD-CHG-001 v1.6 §15.2 — the one governed funding source every Budget
# fixture draws on. Configuration & Governance owns the catalogue (FU-05
# records the pending CFG-CHG-002 v0.8 §4.4 schema reconciliation); the
# Budget seed fails closed if this row is absent, never creates it.
# PLN-CHG-001 v1.18 §10.11 C03 (2026-09-12) — the three governed values the
# Procurement settings artboard lists; Budget draws on the first.
FUNDING_SOURCES = ("Government of Kenya", "Development partner", "Appropriation in Aid")

# TPR-CHG-001 v0.6 §8.5 / plan D6 — the one governed contact office the
# Ministry of Health fixture names for clarifications, notices and the
# contract contact (§13.5). Email on the KT-STD-001 §8.1 fixture domain; no
# telephone is invented.
CONTACT_OFFICES = (
	# (office name, contact email, contact phone, address)
	("Ministry of Health Procurement Office", "procurement@moh.example.test", "", "Afya House, Cathedral Road, Nairobi"),
)


def contact_office_display(office_name: str) -> str:
	"""The rendered contact string for a seeded office (mirrors
	`ContactOffice.display()` without a document load)."""
	for name, email, phone, _address in CONTACT_OFFICES:
		if name == office_name:
			return ", ".join(p for p in (name, email, phone) if p)
	return office_name

# PLN-CHG-001 v1.18 §5.5.1 / §10.1 / §10.11 C04 (2026-09-12) — the method
# eligibility and procedure schedule profiles the Procurement settings tab
# maintains. Every seeded row is `Production verification pending`: the
# figures reproduce the §10.1 display example (21/30/5/2/14; buffers are
# Planning assumptions) and the Second Schedule limits above, none of which
# has been verified against primary law here (v1.18 §15.2 prerequisite;
# plan D16 keeps the fixture-verified set in the Planning seed).
# `effective_from` starts on Planning's own earliest baseline invitation
# date (`procurement_planning.seeds.kentender_mvp_v1.ITEM_VALUES`), not on
# the FY's own start (2027-07-01): Planning invites before the FY it plans
# for opens, and a profile scoped to exactly the FY window left that
# invitation with no rule in force at all (SEED-OPS-001 v1.2 change log).
PROFILE_EFFECTIVE = {"effective_from": "2027-05-01", "effective_until": "2028-06-30"}
PROFILE_SOURCE = {
	"source_instrument": "Public Procurement and Asset Disposal Regulations — source verification pending",
	"provision": "Verification required",
	"applicability_basis": "Planned invitation date",
}
# Methods whose admissibility depends on circumstances a Planner declares and
# a separate authorisation may govern (v1.18 §5.5.3.3; LAW §2 conditions).
DECLARATION_METHODS = {
	"Direct Procurement": ("s.103", "Accounting Officer", "Before invitation"),
	"Restricted Tender": ("s.102", "Accounting Officer", "Before invitation"),
	"Competitive Negotiations": ("s.131", "Accounting Officer", "Before invitation"),
	"Force Account": ("reg 95", "Accounting Officer", "Before commencement"),
}
# Open Tender schedule profiles for the three categories (§10.1 names the
# goods and services profiles; works follows the same example periods).
SCHEDULE_PROFILE_CATEGORIES = (("Goods", "Open Tender — goods"), ("Services", "Open Tender — services"), ("Works", "Open Tender — works"))
SCHEDULE_MILESTONES = (
	# (milestone, default days for the period closing at it, basis, statutory ref)
	("invitation", None, "Statutory", "reg 42 — Third Schedule col. 9"),
	("bid_opening", 21, "Statutory", "Verification required"),
	("evaluation_completion", 30, "Statutory", "Third Schedule col. 11 — verification required"),
	("award_approval", 5, "Planning assumption", ""),
	("award_notification", 2, "Planning assumption", ""),
	("contract_signing", 14, "Statutory", "Verification required"),
	("delivery_completion", None, "Source-derived", "Earliest source required-by date"),
)
REMINDER_THRESHOLD_DAYS = 7

# PLN-CHG-001 v1.18 §13.1 / plan D19 — the two stop-gap assignment rows the
# 5 Sep 2026 seed created and this seed retires (revoked with a reason, never
# deleted): Julia's widened acting window and Peter's undated Digital Health
# authority. Identified exactly; nothing else is touched.
SUPERSEDED_STOPGAP_ASSIGNMENTS = (
	("julia.njeri", "Head of User Department", "Digital Health", "2026-09-01 00:00:00", "2027-06-30 23:59:59"),
	("peter.kimani", "Head of User Department", "Digital Health", None, None),
)
STOPGAP_REVOCATION_REASON = (
	"PLN-CHG-001 v1.18 §13.1 fixture correction (plan D19): replaced by the dated assignment the shared register now specifies."
)

# REQ-CHG-001 v1.6 D2 — the one governed delivery/inspection location
# the Ministry of Health fixture uses (§13.2, §16.1).
DELIVERY_LOCATIONS = (
	("Ministry of Health Headquarters, Afya House, Nairobi", "Afya House, Cathedral Road, Nairobi"),
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
		"funding_sources": _seed_funding_sources(),
		"delivery_locations": _seed_delivery_locations(),
		"contact_offices": _seed_contact_offices(),
		"regulatory_reference": _seed_regulatory_reference(),
		"method_profiles": _seed_method_profiles(),
		"schedule_profiles": _seed_schedule_profiles(),
		"procurement_settings": _seed_procurement_settings(),
		"uoms": _seed_uoms(),
		"users": _seed_users(),
		"retired_assignments": _reconcile_superseded_fixture_assignments(),
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
		# The PE and its root are meant to exist together (configure_procuring_
		# entity creates both in one transaction) but nothing enforces that
		# invariant once they can drift apart independently - e.g. a
		# `wipe`/`rebuild` cycle interrupted between the two, or the root
		# deleted by some other path. Self-heal here rather than letting
		# _seed_units() fail deep inside with "root organisation unit is
		# missing" for a state this seed itself is meant to fix.
		if not structure._root():
			configuration.repair_organisation_root()
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
	for title, category in REQUIREMENT_TYPES:
		if frappe.db.exists("Requirement Type", title):
			updates = {}
			if frappe.db.get_value("Requirement Type", title, "status") != "Active":
				updates["status"] = "Active"
			if frappe.db.get_value("Requirement Type", title, "procurement_category") != category:
				updates["procurement_category"] = category
			if updates:
				frappe.db.set_value("Requirement Type", title, updates, update_modified=False)
			continue
		frappe.get_doc(
			{"doctype": "Requirement Type", "title": title, "procurement_category": category, "status": "Active"}
		).insert(ignore_permissions=True)
		created += 1
	for title in PROCUREMENT_METHODS:
		if frappe.db.exists("Procurement Method", title):
			if frappe.db.get_value("Procurement Method", title, "status") != "Active":
				frappe.db.set_value("Procurement Method", title, "status", "Active", update_modified=False)
			continue
		frappe.get_doc({"doctype": "Procurement Method", "title": title, "status": "Active"}).insert(ignore_permissions=True)
		created += 1
	return {"created": created, "requirement_types": len(REQUIREMENT_TYPES), "procurement_methods": len(PROCUREMENT_METHODS)}


def _seed_funding_sources() -> dict[str, int]:
	created = 0
	for label in FUNDING_SOURCES:
		if frappe.db.exists("Funding Source", label):
			if frappe.db.get_value("Funding Source", label, "record_status") != "Available":
				frappe.db.set_value("Funding Source", label, "record_status", "Available", update_modified=False)
			continue
		frappe.get_doc({"doctype": "Funding Source", "label": label, "record_status": "Available"}).insert(
			ignore_permissions=True
		)
		created += 1
	return {"created": created, "total": len(FUNDING_SOURCES)}


def _seed_delivery_locations() -> dict[str, int]:
	created = 0
	for location_name, address in DELIVERY_LOCATIONS:
		if frappe.db.exists("Delivery Location", location_name):
			frappe.db.set_value("Delivery Location", location_name, {"address": address, "status": "Active"}, update_modified=False)
			continue
		frappe.get_doc(
			{
				"doctype": "Delivery Location",
				"location_name": location_name,
				"address": address,
				"status": "Active",
				"fixture_namespace": FIXTURE_TAG,
			}
		).insert(ignore_permissions=True)
		created += 1
	return {"created": created, "total": len(DELIVERY_LOCATIONS)}


def _seed_contact_offices() -> dict[str, int]:
	created = 0
	for office_name, contact_email, contact_phone, address in CONTACT_OFFICES:
		if frappe.db.exists("Contact Office", office_name):
			frappe.db.set_value(
				"Contact Office", office_name,
				{"contact_email": contact_email, "contact_phone": contact_phone, "address": address, "status": "Active"},
				update_modified=False,
			)
			continue
		frappe.get_doc(
			{
				"doctype": "Contact Office",
				"office_name": office_name,
				"contact_email": contact_email,
				"contact_phone": contact_phone,
				"address": address,
				"status": "Active",
				"fixture_namespace": FIXTURE_TAG,
			}
		).insert(ignore_permissions=True)
		created += 1
	return {"created": created, "total": len(CONTACT_OFFICES)}


def _seed_regulatory_reference(fiscal_year: str = "", fixture_namespace: str = FIXTURE_TAG, *, verification_status: str = "Production verification pending", reservation_target_percent=None, county_target_percent=None) -> str:
	"""CFG-CHG-002 v0.11 Phase 2b — seeds the "Reservation rules" kind's
	Regulatory Reference Set/Version for `fiscal_year`. `threshold_matrix`
	is no longer seeded here at all: it is now derived at read time from
	`Procurement Method Profile` (D10), which `_seed_method_profiles` already
	seeds with the same Second Schedule figures — closes the former
	duplicate-write (FU-08). Signature and find-or-create/override behaviour
	are unchanged so every existing caller (Requisitions/Planning Playwright
	fixtures, Planning's own test world) keeps working without modification."""
	from kentender_core.services import regulatory_reference as register

	fiscal_year = fiscal_year or configuration._fy_name(DPP_INTAKE["start_year"])
	fy_row = frappe.db.get_value("Fiscal Year", fiscal_year, ["year_start_date", "year_end_date"], as_dict=True)
	if not fy_row:
		frappe.throw(f"Unknown fiscal year: {fiscal_year}.")

	reference_key = "RESERVATION-RULES"
	reference_set = frappe.db.get_value(register.SET_DOCTYPE, {"reference_key": reference_key}, "name")
	if not reference_set:
		reference_set = register.create_regulatory_reference(
			reference_key=reference_key,
			reference_kind="Reservation rules",
			display_name="Reservation rules",
			fixture_namespace=fixture_namespace,
		)["reference_set"]

	target = REGULATORY_REFERENCE["reservation_target_percent"] if reservation_target_percent is None else reservation_target_percent
	county_target = REGULATORY_REFERENCE["county_resident_target_percent"] if county_target_percent is None else county_target_percent

	# Find-or-create, like every sibling profile seed (`_profile_exists`).
	# Without this the seed saved a brand-new version on every run — each one
	# superseding the last — so the canonical set climbed a version per
	# `site_setup.run()`, per gate and per test run (found live at v21).
	existing = frappe.db.get_value(
		register.DOCTYPE,
		{
			"reference_set": reference_set,
			"status": "Active",
			"effective_from": fy_row["year_start_date"],
		},
		"name",
	)
	if existing:
		return existing

	outcome = register.save_regulatory_reference_version(
		reference_set=reference_set,
		payload={
			"obligation_code": "ANNUAL-RESERVATION-TARGET",
			"target_percent": target,
			"county_target_percent": county_target,
			"denominator_basis": "AnnualProcurementBudget",
			"overlap_policy": "Independent",
			"categories": [
				{"category": name, "advantage_rank": rank, "is_regional": regional, "statutory_reference": ref}
				for name, rank, regional, ref in RESERVATION_CATEGORIES
			],
		},
		effective_from=fy_row["year_start_date"],
		effective_until=fy_row["year_end_date"],
		applicability_basis="FiscalYearStart",
		verification_status=verification_status,
		source_instrument=PROFILE_SOURCE["source_instrument"],
		provision=PROFILE_SOURCE["provision"],
		fixture_namespace=fixture_namespace,
	)
	return outcome["reference"]


def _profile_exists(doctype: str, filters: dict) -> str:
	return frappe.db.get_value(
		doctype, {"status": "Active", "effective_from": PROFILE_EFFECTIVE["effective_from"], **filters}, "name"
	) or ""


def _seed_method_profiles(*, effective: dict | None = None, verification_status: str | None = None, fixture_namespace: str = FIXTURE_TAG) -> dict[str, int]:
	"""One `Production verification pending` eligibility profile per admitted
	method, built from the Second Schedule bands above plus a declaration
	condition where circumstances govern admissibility. Find-or-skip on
	(method, effective_from); a rerun creates no second Version."""
	from kentender_core.services import procurement_settings as settings

	effective = effective or PROFILE_EFFECTIVE
	created = 0
	for method, goods, works, services, basis, reference in THRESHOLD_BANDS:
		if _profile_exists(settings.METHOD_PROFILE, {"procurement_method": method, "effective_from": effective["effective_from"]}):
			continue
		conditions = []
		for category, amount in (("Goods", goods), ("Works", works), ("Services", services)):
			conditions.append(
				{
					"condition_id": f"{category[:1]}-VALUE",
					"kind": "Known fact",
					"description": (
						f"Estimated value within the Second Schedule limit for {category.lower()} (KES {amount:,.0f}, {basis.lower()})."
						if amount
						else f"No fixed maximum for {category.lower()}: determined by the funds allocated or the section's conditions."
					),
					"procurement_category": category,
					"maximum_amount": amount,
					"cumulative_basis": basis,
					"mandatory": True,
					"statutory_reference": reference,
				}
			)
		if method in DECLARATION_METHODS:
			ref, actor, stage = DECLARATION_METHODS[method]
			conditions.append(
				{
					"condition_id": "CIRCUMSTANCES",
					"kind": "Declaration",
					"description": "Circumstances supporting the selected method.",
					"procurement_category": "",
					"mandatory": True,
					"required_evidence": "Method eligibility record",
					"authorisation_actor": actor,
					"authorisation_stage": stage,
					"statutory_reference": ref,
				}
			)
		settings.register_method_profile_version(
			procurement_method=method,
			conditions=conditions,
			verification_status=verification_status or settings.VERIFICATION_PENDING,
			fixture_namespace=fixture_namespace,
			**effective,
			**PROFILE_SOURCE,
		)
		created += 1
	return {"created": created, "total": len(THRESHOLD_BANDS)}


def _seed_schedule_profiles(*, effective: dict | None = None, verification_status: str | None = None, fixture_namespace: str = FIXTURE_TAG, limits: dict | None = None, estimated_delivery_default_days: int | None = None) -> dict[str, int]:
	"""The Open Tender schedule profiles for goods, services and works at
	`Production verification pending` (statutory minimum/maximum cells blank
	= verification required; buffers labelled Planning assumption). The other
	eight methods deliberately have none: catalogue membership is not
	operational support (v1.18 §5.5.3.3)."""
	from kentender_core.services import procurement_settings as settings

	effective = effective or PROFILE_EFFECTIVE
	limits = limits or {}  # milestone → (minimum_days, maximum_days) for a fixture-verified set
	created = 0
	for category, profile_name in SCHEDULE_PROFILE_CATEGORIES:
		if _profile_exists(settings.SCHEDULE_PROFILE, {"procurement_method": "Open Tender", "procurement_category": category, "effective_from": effective["effective_from"]}):
			continue
		settings.register_schedule_profile_version(
			procurement_method="Open Tender",
			procurement_category=category,
			profile_name=profile_name,
			procedure="Planning example",
			milestones=[
				{
					"milestone": key,
					"label": settings.MILESTONE_LABELS[key],
					"sequence": index + 1,
					"applies": True,
					"counting_rule": "Calendar days",
					"minimum_days": limits.get(key, (None, None))[0],
					"maximum_days": limits.get(key, (None, None))[1],
					"default_days": default,
					"basis": basis,
					"statutory_reference": ref,
				}
				for index, (key, default, basis, ref) in enumerate(SCHEDULE_MILESTONES)
			],
			counting_rule="Calendar days",
			estimated_delivery_period_default_days=estimated_delivery_default_days,
			verification_status=verification_status or settings.VERIFICATION_PENDING,
			fixture_namespace=fixture_namespace,
			**effective,
			**PROFILE_SOURCE,
		)
		created += 1
	return {"created": created, "total": len(SCHEDULE_PROFILE_CATEGORIES)}


def _seed_procurement_settings() -> dict[str, int]:
	from kentender_core.services import procurement_settings as settings

	current = frappe.db.get_single_value(settings.SETTINGS, "approaching_milestone_threshold_days")
	if int(current or 0) == REMINDER_THRESHOLD_DAYS:
		return {"approaching_milestone_threshold_days": REMINDER_THRESHOLD_DAYS, "changed": 0}
	settings.set_reminder_threshold_days(days=REMINDER_THRESHOLD_DAYS)
	return {"approaching_milestone_threshold_days": REMINDER_THRESHOLD_DAYS, "changed": 1}


def _reconcile_superseded_fixture_assignments() -> list[str]:
	"""Revoke, with a reason, exactly the two stop-gap rows the 5 Sep 2026
	seed granted (§13.1 / plan D19). Matched on user, role, unit and the
	exact period they carried; any other row is left alone."""
	units = {
		row["unit_name"]: row["name"]
		for row in frappe.get_all("Organisation Unit", fields=["name", "unit_name"], limit_page_length=0)
	}
	revoked: list[str] = []
	for local, role, unit_name, effective_from, effective_to in SUPERSEDED_STOPGAP_ASSIGNMENTS:
		unit = units.get(unit_name)
		if not unit:
			continue
		rows = frappe.get_all(
			"User Responsibility Assignment",
			filters={"user": f"{local}@moh.example.test", "business_role": role, "organisation_unit": unit, "status": "Enabled"},
			fields=["name", "effective_from", "effective_to"],
		)
		for row in rows:
			row_from = str(row["effective_from"] or "") or None
			row_to = str(row["effective_to"] or "") or None
			if row_from == effective_from and row_to == effective_to:
				administration.revoke(row["name"], reason=STOPGAP_REVOCATION_REASON, actor="Administrator")
				revoked.append(row["name"])
	return revoked


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
		if frappe.conf.get("developer_mode"):
			# Development sites only: the register's actors log in with the
			# shared fixture password so browser journeys can be driven; a
			# production site never receives a known password from a seed.
			from frappe.utils.password import update_password

			from kentender_core.seeds.constants import TEST_PASSWORD

			update_password(email, TEST_PASSWORD)
		out.append(email)
	return out


def reset_site_setup(*, commit: bool = False) -> dict[str, int]:
	"""Tear down everything `run()` creates or converges, for a caller that has
	already torn down every module stage on top of it (site is the foundation
	every other stage's Fiscal Years, Organisation Units and actors reference,
	so this must run last, never on its own — `canonical.run(wipe=True)` is
	the sanctioned entry point).

	Three things `run()` touches are deliberately left alone, matching
	SEED-OPS-001 §3.2: the ERPNext Company (`_seed_company` never creates one
	if any exists, and never will here either), the Requirement Type /
	Procurement Method catalogues, and UOM enablement — none of the three
	carries a fixture_namespace, because they are Configuration & Governance's
	shared reference data, not this seed's own rows, whatever this seed does
	to activate them.

	Resets the Site Procuring Entity Single doctype directly rather than
	through a command: CFG-BR-001 has no "unconfigure" command to call — a
	real Procuring Entity is never meant to un-onboard itself — so a caller
	that genuinely wants a blank site accepts the same direct-delete
	authority this whole teardown path already exercises everywhere else.
	"""
	from kentender_core.services import organisation_structure as structure
	from kentender_core.services import regulatory_reference as register
	from kentender_core.services import site_configuration as configuration

	deleted: dict[str, int] = {}
	# Procurement Method Profile, Procedure Schedule Profile, Regulatory
	# Reference and its Set are audit-immutable by design (their own
	# on_trash refuses deletion) with exactly one sanctioned override: the
	# same kt_fixture_purge flag the document's own fixture-purge callers
	# already set — canonical.py's clear_non_canonical() uses it on
	# Regulatory Reference for exactly this reason.
	_PURGE_FLAGGED = {"Procurement Method Profile", "Procedure Schedule Profile", "Regulatory Reference", "Regulatory Reference Set"}

	def delete(doctype: str, names: list[str]) -> None:
		for name in names:
			if not frappe.db.exists(doctype, name):
				continue
			if doctype in _PURGE_FLAGGED:
				doc = frappe.get_doc(doctype, name)
				doc.flags.kt_fixture_purge = True
				doc.delete(ignore_permissions=True, force=True)
			else:
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True, delete_permanently=True)
		if names:
			deleted[doctype] = deleted.get(doctype, 0) + len(names)

	# Assignments and users first: everything below is what they were granted
	# on or authored through, and Frappe's own ownership/modified-by columns
	# would otherwise point at a user this function is about to delete.
	assignment_names = frappe.get_all(
		"User Responsibility Assignment",
		filters={"fixture_namespace": FIXTURE_TAG},
		pluck="name",
	)
	delete("User Responsibility Assignment", assignment_names)

	actor_emails = [f"{local}@moh.example.test" for local, _ in ACTORS]
	for email in actor_emails:
		if not frappe.db.exists("User", email):
			continue
		for doctype, field in (
			("User Responsibility Assignment", "user"),
			("User Scope Assignment", "user"),
			("User Permission", "user"),
			("Notification Log", "for_user"),
			("Contact", "user"),
		):
			if not frappe.db.exists("DocType", doctype) or not frappe.db.has_column(doctype, field):
				continue
			delete(doctype, frappe.get_all(doctype, filters={field: email}, pluck="name"))
		frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		deleted["User"] = deleted.get("User", 0) + 1

	# Profiles and the regulatory reference: every row, not just this seed's
	# own FIXTURE_TAG namespace. These four doctypes are audit-immutable
	# (on_trash refuses deletion outside the kt_fixture_purge flag `delete()`
	# already sets above), so nothing but a deliberate purge like this one
	# ever removes them — nothing outside a full wipe should call this
	# function (it has exactly one caller, `canonical.run(wipe=True)`), and
	# other test suites' own namespaces (e.g. Planning's, Regulatory
	# Reference's own test suite) were found accumulating hundreds of rows
	# here with no other path that ever cleans them up.
	from kentender_core.services import procurement_settings as settings

	for doctype in (settings.METHOD_PROFILE, settings.SCHEDULE_PROFILE):
		delete(doctype, frappe.get_all(doctype, pluck="name"))
	delete(register.DOCTYPE, frappe.get_all(register.DOCTYPE, pluck="name"))
	delete(register.SET_DOCTYPE, frappe.get_all(register.SET_DOCTYPE, pluck="name"))

	# Delivery Location / Contact Office: every row, not just this seed's own
	# named ones — neither carries a fixture_namespace column (an existing
	# row is updated in place on a rerun without ever being stamped if it
	# predates this seed), and other modules' own test suites were found
	# leaving obviously-disposable rows behind here (e.g. "Test Delivery
	# Location — Requisitions") with no other path that ever removes them.
	delete("Delivery Location", frappe.get_all("Delivery Location", pluck="name"))
	delete("Contact Office", frappe.get_all("Contact Office", pluck="name"))

	# Fiscal Years, then Organisation Units, then the site identity itself —
	# the two things every stage above ultimately hangs off, so last.
	fy_names = [configuration._fy_name(year) for year in FISCAL_START_YEARS]
	delete("Fiscal Year", [name for name in fy_names if frappe.db.exists("Fiscal Year", name)])

	unit_names = [name for name, _parent in UNITS]
	root = structure._root()
	if root:
		unit_names.append(root)
	pending = [u for u in unit_names if frappe.db.exists("Organisation Unit", u)]
	for _ in range(8):
		if not pending:
			break
		remaining = []
		for unit in pending:
			if frappe.db.count("Organisation Unit", {"parent_organisation_unit": unit}):
				remaining.append(unit)
				continue
			frappe.delete_doc("Organisation Unit", unit, force=True, ignore_permissions=True)
			deleted["Organisation Unit"] = deleted.get("Organisation Unit", 0) + 1
		pending = remaining

	if configuration.is_configured():
		for field in ("pe_name", "pe_code", "pe_type", "ppra_registration", "statutory_approval_route"):
			frappe.db.set_single_value(configuration.SITE_PE_DOCTYPE, field, "")
		frappe.db.set_single_value(configuration.SITE_PE_DOCTYPE, "entity_is_county", 0)
		frappe.db.set_single_value(configuration.SITE_PE_DOCTYPE, "timezone", "Africa/Nairobi")
		deleted["Site Procuring Entity"] = 1

	if commit:
		frappe.db.commit()
	return deleted


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
