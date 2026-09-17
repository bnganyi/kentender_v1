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

CONFIG-FIRST (no entity/root configured), CONFIG-SWAP (a same-module
cross-year opening) and CONFIG-EMPTY (an isolated no-data world) are
deliberately not built here yet: each needs the concrete screen that
consumes it decided first (CONFIG-FIRST in particular means temporarily
unconfiguring the site, which only the specific first-run test should ever
do, scoped to its own setUp/tearDown — see
`kentender_core.tests.test_site_configuration.ConfigurationTestCase.blank_site`
for the existing safe pattern). Add them here once the owning Phase 3
sub-phase needs them, not speculatively.
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
	reservation = register.save_regulatory_reference_version(
		reference_set=reservation_set,
		payload={"obligation_code": "ANNUAL-RESERVATION-TARGET"},
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
