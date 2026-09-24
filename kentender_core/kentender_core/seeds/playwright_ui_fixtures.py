# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.11 §10.1/§13 — System setup Playwright fixture worlds.

Every browser spec for `/app/system-setup` resets to one of these named
worlds before it runs, reading every id back from the returned dict rather
than hardcoding one. Each `reset_*` function is idempotent, uses only real
service commands (never a direct doctype write) and is `bench execute`-able.

- `reset_config`       — §10.1 CONFIG: the everyday setup world every screen
                          uses. This *is* the canonical seed
                          (`kentender_core.seeds.site_setup.run`), not a
                          parallel test-only copy: entity configured, FY
                          2027/28 (Upcoming) and FY 2026/27 (Current) exist,
                          Needs and Departmental-plan intake open for FY
                          2027/28 per the seed's own documented instants,
                          disposal-plan intake closed, funding sources and
                          the method/schedule baseline seeded.
- `reset_config_rules` — §10.1 CONFIG-RULES: Method eligibility and
                          Reservation rules each at Version 1, 1 Jul 2027 –
                          30 Jun 2028, source check still pending, fields
                          incomplete — the rule list/detail/source-check
                          specimens.

- `reset_config_swap`  — §10.1 CONFIG-SWAP: departmental plans open for FY
                          2026/27 with no closing date (closing FY 2027/28's).
- `restore_site`       — undoes every world: purge, canonical seed (reopens
                          the canonical year's plans and disposal plans),
                          seeded rules re-stamped fixture-verified. Every
                          browser spec that builds a world calls it last.

CONFIG itself differs from the canonical seed in one fact: disposal plans are
closed, as §10.1 draws them (the seed opens them, SEED-OPS v1.8).

CONFIG-FIRST (no entity/root) and CONFIG-EMPTY (no years, sources, rules or
schedules) are NOT site worlds: unconfiguring or emptying the one shared dev
site would break every other module. They are browser-side substitutes that
transform the server's own responses (`asFirstRun`/`asEmpty` in
tests/ui/smoke/system_setup/helpers.ts). The first-run save itself is proved
by the Python suite (atomic entity + root). Owner decision D17, 24 Sep 2026.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import add_to_date, now_datetime

from kentender_core.seeds import site_setup
from kentender_core.services import procurement_settings as settings
from kentender_core.services import regulatory_reference as register
from kentender_core.services import site_configuration as configuration

FIXTURE_NAMESPACE = "SYSTEM_SETUP_PW"

# §10.3 C02 edge-case specimens (expiry, stale write) that must never touch
# the one canonical open year every other module's own fixtures depend on —
# far-future, `responsibility_test_cleanup`'s own `FY_TEST_MIN_START_YEAR`
# range, but a distinct pair from the Python suite's Y1/Y2 (2096/2097) so the
# two never collide if a stale run of either is still on disk.
EDGE_YEAR_EXPIRED_START = 2098
EDGE_YEAR_STALE_START = 2099


def _guard() -> None:
	if frappe.flags.in_test or frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests"):
		return
	frappe.throw(
		"System setup Playwright fixtures are test data. Enable developer_mode or "
		"allow_tests on this site before building them."
	)


def purge(*, commit: bool = True) -> dict[str, int]:
	"""Remove what a browser run leaves behind: every row stamped with this
	module's own fixture namespace, across the record kinds Playwright specs
	are allowed to create. Never touches the canonical seed's own rows
	(those carry `site_setup.FIXTURE_TAG`, not `FIXTURE_NAMESPACE`)."""
	_guard()
	removed = {
		"regulatory_references": register.purge_fixture_references(FIXTURE_NAMESPACE),
		"method_and_schedule_profiles": settings.purge_fixture_profiles(FIXTURE_NAMESPACE),
		"funding_sources": settings.purge_playwright_funding_sources(),
		# Rules a spec added through the real Add rule screen (PW- identifiers).
		"playwright_rules": register.purge_playwright_rules(),
		# Calendars a spec added through the real screen ("Playwright…").
		"playwright_schedules": settings.purge_playwright_schedules(),
		"playwright_calendars": settings.purge_playwright_calendars(),
	}
	if commit:
		frappe.db.commit()
	return removed


def reset_config(*, commit: bool = True) -> dict[str, Any]:
	"""§10.1 CONFIG — run the real canonical seed (idempotent either way),
	then purge only this module's own stray fixture rows."""
	_guard()
	seed = site_setup.run(commit=False)
	removed = purge(commit=False)
	# §10.1 CONFIG draws disposal plans Closed; the canonical seed opens them
	# (SEED-OPS v1.8). Closed through the real command; `restore_site`
	# reopens them.
	for year in frappe.get_all("Fiscal Year", filters={configuration.DISPOSAL_FLAG_OPEN: 1}, pluck="name"):
		configuration.close_disposal_plan_submission(fiscal_year=year, reason="Playwright CONFIG world: disposal plans closed.")
	site = configuration.get_site_configuration()
	fy_open = configuration._fy_name(site_setup.DPP_INTAKE["start_year"])
	fy_current = configuration._fy_name(site_setup.DPP_INTAKE["start_year"] - 1)
	if commit:
		frappe.db.commit()
	return {
		"pe_code": (site.get("procuring_entity") or {}).get("pe_code", ""),
		"root_unit": (site.get("root_unit") or {}).get("id", ""),
		"fiscal_year_open": fy_open,
		"fiscal_year_current": fy_current,
		"needs_submission": site.get("needs_submission"),
		"dpp_submission": site.get("dpp_submission"),
		"disposal_plan_submission": site.get("disposal_plan_submission"),
		"seed": {k: seed.get(k) for k in ("regulatory_reference", "method_profiles", "schedule_profiles", "intake", "dpp_intake", "funding_sources")},
		"removed": removed,
	}


def reset_config_rules(*, commit: bool = True) -> dict[str, Any]:
	"""§10.1 CONFIG-RULES — Reservation rules at Version 1 for 1 Jul 2027 –
	30 Jun 2028, source check pending, fields incomplete: the rule
	list/detail/source-check specimens.

	Method eligibility is deliberately not built here: the canonical seed
	already carries a real, complete "Open Tender" Method eligibility
	version with actual Second Schedule data (`site_setup._seed_method_profiles`,
	`site_setup.PROFILE_EFFECTIVE`) — a second version for an overlapping
	window would supersede it rather than add an isolated pending specimen. Build a
	dedicated fixture-only method profile (a procurement method the
	canonical seed does not already cover, or a namespaced overlap-safe
	window) once Phase 3D's screen actually needs one."""
	base = reset_config(commit=False)

	reservation_set = frappe.db.get_value(register.SET_DOCTYPE, {"reference_key": "PW-RESERVATION-RULES"}, "name")
	if not reservation_set:
		reservation_set = register.create_regulatory_reference(
			reference_key="PW-RESERVATION-RULES",
			reference_kind="Reservation rules",
			display_name="Reservation rules",
			fixture_namespace=FIXTURE_NAMESPACE,
		)["reference_set"]
	from kentender_core.seeds.site_setup import _seed_save_reference_version

	reservation = _seed_save_reference_version(
		reference_set=reservation_set,
		payload={"obligation_code": "ANNUAL-RESERVATION-TARGET", "measure_stage": "PlanningAllocation"},
		effective_from="2027-07-01",
		effective_until="2028-06-30",
		fixture_namespace=FIXTURE_NAMESPACE,
	)

	if commit:
		frappe.db.commit()
	return {
		**base,
		"reservation_reference_set": reservation_set,
		"reservation_version": reservation["reference"],
	}


def reset_config_swap(*, commit: bool = True) -> dict[str, Any]:
	"""§10.1 CONFIG-SWAP — departmental plans open for FY 2026/27 with no
	closing date (which, one year at a time, closes FY 2027/28's); every
	other activity as CONFIG. Opened through the real command so the swap
	evidence is the real one; `restore_site` swaps back."""
	base = reset_config(commit=False)
	configuration.open_dpp_submission(
		fiscal_year=base["fiscal_year_current"], reason="Playwright CONFIG-SWAP world: departmental plans for the current year."
	)
	if commit:
		frappe.db.commit()
	return {**base, "dpp_submission": configuration.get_site_configuration().get("dpp_submission")}


SYSTEM_MANAGER = "pw.cfg.sysmgr@example.test"
FIXTURE_PASSWORD = "Test@123"
# C06 journeys (D24): the one user they assign, edit and revoke.
GRANTEE = "pw.cfg.grantee@example.test"
GRANTEE_UNIT_NAME = "Digital Health"


def ensure_system_manager(*, commit: bool = True) -> dict[str, str]:
	"""A System-Manager-only user (no Administrator, no business role —
	KT-STD-001 §3A.6/§8.6) so browser specs prove the second setup role
	(CFG11-EX-001) and its limits (no missing-root repair). Removed by
	`restore_site`."""
	_guard()
	from frappe.utils.password import update_password

	if not frappe.db.exists("User", SYSTEM_MANAGER):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": SYSTEM_MANAGER,
				"first_name": "Playwright",
				"last_name": "System Manager",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		)
		user.insert(ignore_permissions=True)
	user = frappe.get_doc("User", SYSTEM_MANAGER)
	user.set("roles", [])
	user.append("roles", {"role": "System Manager"})
	user.save(ignore_permissions=True)
	update_password(SYSTEM_MANAGER, FIXTURE_PASSWORD)
	if commit:
		frappe.db.commit()
	return {"user": SYSTEM_MANAGER, "password": FIXTURE_PASSWORD}


def _purge_grantee_assignments() -> int:
	names = frappe.get_all("User Responsibility Assignment", filters={"user": GRANTEE}, pluck="name")
	if names:
		for event in frappe.get_all(
			"Audit Event",
			filters={"document_type": "User Responsibility Assignment", "document_name": ("in", names)},
			pluck="name",
		):
			frappe.delete_doc("Audit Event", event, force=True, ignore_permissions=True)
	for name in names:
		frappe.delete_doc("User Responsibility Assignment", name, force=True, ignore_permissions=True)
	return len(names)


def reset_responsibilities(*, commit: bool = True) -> dict[str, Any]:
	"""C06 — one enabled Desk user with no business role and no assignment, and the
	canonical unit the journeys assign in. Idempotent; the assignments a
	spec makes, their history and the user are removed by `restore_site`."""
	_guard()
	frappe.set_user("Administrator")
	if not frappe.db.exists("User", GRANTEE):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": GRANTEE,
				"first_name": "Playwright",
				"last_name": "Grantee",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	_purge_grantee_assignments()
	user = frappe.get_doc("User", GRANTEE)
	user.enabled = 1
	# Desk access only, as the seed gives a plain business user; no business
	# role, so every responsibility it holds is one a spec granted.
	user.set("roles", [])
	user.append("roles", {"role": "Desk User"})
	user.save(ignore_permissions=True)
	unit = frappe.db.get_value("Organisation Unit", {"unit_name": GRANTEE_UNIT_NAME, "status": "Active"}, "name")
	if commit:
		frappe.db.commit()
	return {"user": GRANTEE, "full_name": "Playwright Grantee", "unit": unit, "unit_name": GRANTEE_UNIT_NAME}


def restore_site(*, commit: bool = True) -> dict[str, Any]:
	"""Undo every System setup world: drop this module's fixture rows, then
	re-run the canonical seed, which reopens the canonical year's
	departmental plans (closing any year a spec opened) and its disposal
	plans, and re-stamp the seeded rules fixture-verified. Safe to call when
	nothing was moved; every spec calls it last."""
	_guard()
	frappe.set_user("Administrator")
	removed = purge(commit=False)
	if frappe.db.exists("User", SYSTEM_MANAGER):
		frappe.delete_doc("User", SYSTEM_MANAGER, force=True, ignore_permissions=True)
		removed["system_manager"] = 1
	removed["grantee_assignments"] = _purge_grantee_assignments()
	if frappe.db.exists("User", GRANTEE):
		frappe.delete_doc("User", GRANTEE, force=True, ignore_permissions=True)
		removed["grantee"] = 1
	site_setup.run(commit=False)
	site_setup.stamp_procurement_rules_fixture_verified()
	if commit:
		frappe.db.commit()
	site = configuration.get_site_configuration()
	return {
		"removed": removed,
		"needs_submission": site.get("needs_submission"),
		"dpp_submission": site.get("dpp_submission"),
		"disposal_plan_submission": site.get("disposal_plan_submission"),
	}


def reset_fiscal_year_edge_cases(*, commit: bool = True) -> dict[str, Any]:
	"""§10.3 C02 — an expired-but-still-flagged intake and a plain open year
	for a stale-control-token scenario, on isolated far-future years.

	Both specimens use the **disposal-plan** module key deliberately. Intake
	is one-year-at-a-time per module key (CFG-BR-006), so opening `needs` or
	`dpp` on a fixture year would silently close the canonical year's own
	flag — the very flag Departmental Needs, Planning and Budget fixtures all
	read. Disposal-plan intake is closed on every year in the canonical seed,
	so claiming it here steals nothing (found the hard way: the first cut of
	this fixture used `needs` and moved the canonical open year)."""
	_guard()
	from kentender_core.tests.responsibility_test_cleanup import purge as purge_test_years

	purge_test_years(commit=False)

	# The stale specimen first, through the real command: it is the one that
	# legitimately holds the module's single open slot.
	stale_fy = configuration._fy_name(EDGE_YEAR_STALE_START)
	configuration.add_fiscal_year(start_year=EDGE_YEAR_STALE_START)
	configuration.open_disposal_plan_submission(
		fiscal_year=stale_fy,
		closes_at=str(add_to_date(now_datetime(), days=30)),
		reason="Playwright fixture: stale-write specimen.",
	)

	# The expiry specimen is written directly, and last. No legal command
	# sequence can produce it: `open_*` refuses a past instant, and opening
	# it through the command would close the stale specimen's flag (same
	# module key, one year at a time). A flag left at 1 with its instant
	# already passed is a real state — it is exactly what the site looks like
	# between the expiry instant and the hourly sweep — so `_effective_open`
	# reading it as closed is the behaviour under test.
	expired_fy = configuration._fy_name(EDGE_YEAR_EXPIRED_START)
	configuration.add_fiscal_year(start_year=EDGE_YEAR_EXPIRED_START)
	frappe.db.set_value(
		"Fiscal Year",
		expired_fy,
		{
			configuration.DISPOSAL_FLAG_OPEN: 1,
			configuration.DISPOSAL_FLAG_CLOSES_AT: add_to_date(now_datetime(), minutes=-5),
		},
		update_modified=False,
	)

	if commit:
		frappe.db.commit()
	return {
		"module_key": "disposal_plan",
		"expired_fiscal_year": expired_fy,
		"expired_label": configuration._fy_label(f"{EDGE_YEAR_EXPIRED_START}-07-01"),
		"stale_fiscal_year": stale_fy,
		"stale_label": configuration._fy_label(f"{EDGE_YEAR_STALE_START}-07-01"),
		"stale_expected_version": str(
			frappe.db.get_value("Fiscal Year", stale_fy, "modified")
		),
	}
