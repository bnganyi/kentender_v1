# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Playwright fixtures for the STR-CHG-001 v1.7 §16.2 browser journeys.

The browser specs drive the real §14.3 Ministry of Health plan through its
real commands as the §14.1 actors (Esther Muthoni authors, Dr Alfred Ochieng
approves, Naomi Chebet reads, Samuel Otieno holds an expired assignment and
is the Forbidden fixture actor). Every actor and assignment comes from
`kentender_core.seeds.site_setup` — this module creates no user and grants
nothing; it only guarantees the standard test password so a browser can
log in, and puts the Strategy world back into a documented state before
each spec:

- `reset_default`            — the §14.3 plan Active at Version 1 and nothing
                               else: every open successor version and every
                               plan a browser run created is removed.
- `reset_submitted_fixture`  — default + the §14.4 Version 2 fixture,
                               Submitted for approval by Esther (the approver
                               journey's starting point).
- `reset_draft_fixture`      — default + a Draft Version 2 created by Esther
                               through `create_strategy_successor_version`.

Each builder returns a plain dict that `bench execute` prints as one JSON
line; a spec reads every id from it and never hardcodes one.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds import site_setup
from kentender_core.seeds.constants import TEST_PASSWORD
from kentender_strategy.seeds.kentender_mvp_v1_strategy import (
	APPROVER,
	AUTHOR,
	PLAN_TITLE,
	seed_str_des_v2_fixture,
	upsert_kentender_mvp_v1_strategy,
)
from kentender_strategy.services.strategy_writes import create_strategy_successor_version

AUDITOR = "naomi.chebet@moh.example.test"
NOBODY = "samuel.otieno@moh.example.test"
ACTORS = (AUTHOR, APPROVER, AUDITOR, NOBODY)

# A plan a browser run creates through the New strategic plan form is
# recognised — and removed on the next reset — by this title prefix.
BROWSER_PLAN_PREFIX = "Playwright —"


def _guard() -> None:
	if frappe.flags.in_test or frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests"):
		return
	frappe.throw(
		"Strategy Playwright fixtures are test data. Enable developer_mode or allow_tests "
		"on this site before building them."
	)


def _delete_version_tree(version_name: str) -> None:
	for indicator in frappe.get_all("Performance Indicator", filters={"plan_version_id": version_name}, pluck="name"):
		for target in frappe.get_all("Performance Target", filters={"indicator_id": indicator}, pluck="name"):
			frappe.delete_doc("Performance Target", target, force=1, ignore_permissions=True)
		frappe.delete_doc("Performance Indicator", indicator, force=1, ignore_permissions=True)
	for node in frappe.get_all("Strategy Node", filters={"plan_version_id": version_name}, pluck="name"):
		frappe.delete_doc("Strategy Node", node, force=1, ignore_permissions=True)
	frappe.delete_doc("Strategic Plan Version", version_name, force=1, ignore_permissions=True)


def _delete_plan(plan_name: str) -> None:
	for version in frappe.get_all("Strategic Plan Version", filters={"plan_id": plan_name}, pluck="name"):
		_delete_version_tree(version)
	frappe.delete_doc("Strategic Plan", plan_name, force=1, ignore_permissions=True)


def ensure_actors() -> dict[str, Any]:
	"""The §8.3 actors with the standard test password. Runs the canonical
	site seed only when an actor is missing (idempotent either way)."""
	_guard()
	if not all(frappe.db.exists("User", email) for email in ACTORS):
		site_setup.run(commit=False)
	from frappe.utils.password import update_password

	for email in ACTORS:
		update_password(email, TEST_PASSWORD)
	return {"actors": list(ACTORS)}


def _canonical_plan() -> str | None:
	return frappe.db.get_value("Strategic Plan", {"title": PLAN_TITLE}, "name")


def purge(*, commit: bool = True) -> dict[str, Any]:
	"""Remove what a browser run leaves behind: open versions of the
	canonical plan (a successor Draft/Submitted, or a Version 2 the run
	approved — which makes Version 1 Superseded, so that is reset too) and
	every plan whose title carries the browser prefix."""
	_guard()
	removed: dict[str, int] = {"versions": 0, "plans": 0}
	plan = _canonical_plan()
	if plan:
		versions = frappe.get_all(
			"Strategic Plan Version",
			filters={"plan_id": plan, "version_number": [">", 1]},
			pluck="name",
			order_by="version_number desc",
		)
		for version in versions:
			_delete_version_tree(version)
			removed["versions"] += 1
		first = frappe.db.get_value("Strategic Plan Version", {"plan_id": plan, "version_number": 1}, "name")
		if first and frappe.db.get_value("Strategic Plan Version", first, "status") != "Active":
			# Superseded by a fixture approval: the §14.3 seed is Version 1 Active.
			frappe.db.set_value("Strategic Plan Version", first, "status", "Active", update_modified=False)
	for name in frappe.get_all("Strategic Plan", filters={"title": ["like", f"{BROWSER_PLAN_PREFIX}%"]}, pluck="name"):
		_delete_plan(name)
		removed["plans"] += 1
	if commit:
		frappe.db.commit()
	return removed


def reset_default(*, commit: bool = True) -> dict[str, Any]:
	_guard()
	ensure_actors()
	removed = purge(commit=False)
	seeded = upsert_kentender_mvp_v1_strategy()["moh"]
	plan = seeded["plan"]
	version = seeded["plan_version"]
	if commit:
		frappe.db.commit()
	return {
		"plan": plan,
		"plan_reference": frappe.db.get_value("Strategic Plan", plan, "plan_id"),
		"version": version,
		"version_reference": frappe.db.get_value("Strategic Plan Version", version, "plan_version_id"),
		"removed": removed,
	}


def reset_submitted_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""§14.4 — Version 2 Submitted for approval by Esther (target 80 → 85)."""
	base = reset_default(commit=False)
	fixture = seed_str_des_v2_fixture()
	v2 = fixture["plan_version"]
	if commit:
		frappe.db.commit()
	return {
		**base,
		"v2": v2,
		"v2_reference": frappe.db.get_value("Strategic Plan Version", v2, "plan_version_id"),
	}


def reset_draft_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""Default + a Draft Version 2 created by Esther through the real
	successor command (the author's structure-editing starting point)."""
	base = reset_default(commit=False)
	frappe.set_user(AUTHOR)
	try:
		v2 = create_strategy_successor_version(base["plan"])["name"]
	finally:
		frappe.set_user("Administrator")
	if commit:
		frappe.db.commit()
	return {
		**base,
		"v2": v2,
		"v2_reference": frappe.db.get_value("Strategic Plan Version", v2, "plan_version_id"),
	}
