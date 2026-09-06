# Copyright (c) 2026, KenTender and contributors
""""Works Master" demo Strategy fixture — a real PE-MOH Primary plan,
hierarchy and target, consumed by kentender_budget's and
kentender_procurement's own cross-app seed/test suites.

This is a separate, pre-existing demo dataset from STR-CHG-001 v1.3's own
§16 MOH/Kisumu seed (kentender_mvp_v1_strategy.py) — same PE, different
fixture, different owner concern (budget/procurement handoff testing, not
the Strategy module's own acceptance contract).

Rebuilt for the Phase 1 domain model (Strategic Plan/Version split,
unified Strategy Node). The old schema gave every hierarchy level its own
business "code" (e.g. `OBJ-MOH-HOSP-RENOV`); STR-BR-016 and this rebuild's
Strategy Node design deliberately do not — identifiers are system-generated
only. `kentender_procurement`'s own "Works Master" R3/R4/R5 test suite
(~9 files: strategy_alignment_handoff.py and its direct callers/tests)
hardcodes those literal legacy codes and reads Strategy's tables directly,
bypassing the published contract layer (a pre-existing boundary violation,
not introduced here). Rebuilding that whole suite to stop hardcoding
codes Strategy's schema no longer has is real work belonging to
kentender_procurement's own tracker, not this change unit — out of scope
here; this module only guarantees a real, working PE-MOH plan/hierarchy/
target exists for callers that only need *a* valid fixture (this file's
own `upsert_works_master_strategy_hierarchy()` return dict), which is what
kentender_budget's and kentender_core's actual callers use.
"""

from __future__ import annotations

from typing import Any, Final

import frappe

from kentender_strategy.services.strategy_transitions import transition_plan_version

PE_MOH = "PE-MOH"
FIXTURE_TITLE = "Works Master Strategy Fixture (Demo)"
FIXTURE_NS = "works-master-strategy"

# Legacy names kept only so existing cross-app imports of these module
# attributes keep resolving (kentender_core.stable_platform_seed.validate
# imports them but never inspects their value) — not literal business
# codes on any record; the new schema has none.
STRATEGY_PLAN_CODE: Final[str] = "WORKS-MASTER-MOH-STRATEGY"
PROGRAM_CODE: Final[str] = "WORKS-MASTER-PROGRAMME"
OBJECTIVE_CODE: Final[str] = "WORKS-MASTER-OBJECTIVE"
TARGET_CODE: Final[str] = "WORKS-MASTER-TARGET"


def _seed_actors() -> dict[str, str]:
	"""CU-307 — two governed fixture actors on the one-site model: the
	same-version self-check (§6.2/§18.1) still requires distinct author and
	approver, and their authority is a real Enabled Site-wide User
	Responsibility Assignment granted through the administration command
	(idempotent), never a raw Role insert."""
	from kentender_core.services import responsibility_administration as administration
	from kentender_strategy.services.strategy_authorization import (
		ROLE_STRATEGY_APPROVER,
		ROLE_STRATEGY_AUTHOR,
		ensure_strategy_governance_roles,
	)

	ensure_strategy_governance_roles()
	actors = {
		"author": ("works.master.author@moh.example.test", ROLE_STRATEGY_AUTHOR, "Works Author"),
		"approver": ("works.master.approver@moh.example.test", ROLE_STRATEGY_APPROVER, "Works Approver"),
	}
	out: dict[str, str] = {}
	for key, (email, role, label) in actors.items():
		if not frappe.db.exists("User", email):
			doc = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": label,
					"enabled": 1,
					"send_welcome_email": 0,
					"user_type": "System User",
				}
			).insert(ignore_permissions=True)
			doc.add_roles("Desk User")
		administration.grant(
			user=email,
			business_role=role,
			organisation_unit="",
			fixture_namespace=FIXTURE_NS,
			actor="Administrator",
		)
		out[key] = email
	return out


def resolve_site_entity_code() -> str | None:
	"""CU-303 — the site's own configured entity code (one site = one PE);
	None while the site is unconfigured."""
	code = frappe.db.get_single_value("Site Procuring Entity", "pe_code")
	return code or None


def upsert_works_master_strategy_hierarchy(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
	"""Idempotent. Returns {"ok", "plan" (Strategic Plan Version name),
	"target" (Performance Target name), "objective" (Strategy Node name)} —
	the exact keys kentender_budget's own test reads."""
	pe = resolve_site_entity_code()
	if not pe:
		return {"ok": False, "reason": "STRATEGY_CONFIG_MISSING", "detail": "the site procuring entity is not configured"}

	existing_plan = frappe.db.get_value(
		"Strategic Plan", {"title": FIXTURE_TITLE, "fixture_namespace": FIXTURE_NS}, "name"
	)
	if existing_plan:
		version = frappe.db.get_value(
			"Strategic Plan Version", {"plan_id": existing_plan, "version_number": 1}, "name"
		)
		objective = frappe.db.get_value(
			"Strategy Node", {"plan_version_id": version, "node_type": "Strategic Objective"}, "name"
		)
		indicator = frappe.db.get_value("Performance Indicator", {"plan_version_id": version}, "name")
		target = frappe.db.get_value("Performance Target", {"indicator_id": indicator}, "name")
		return {"ok": True, "plan": version, "objective": objective, "target": target, "already_seeded": True}

	actors = _seed_actors()

	plan = frappe.get_doc(
		{
			"doctype": "Strategic Plan",
			"title": FIXTURE_TITLE,
			"plan_role": "Primary",
			"period_start": "2031-07-01",
			"period_end": "2035-06-30",
			"fixture_namespace": FIXTURE_NS,
		}
	)
	plan.insert(ignore_permissions=True)
	version = frappe.get_doc(
		{
			"doctype": "Strategic Plan Version",
			"plan_id": plan.name,
			"version_number": 1,
			"effective_from": "2031-07-01",
			"effective_to": "2035-06-30",
			"fixture_namespace": FIXTURE_NS,
		}
	)
	version.insert(ignore_permissions=True)

	pillar = frappe.get_doc(
		{
			"doctype": "Strategy Node",
			"plan_version_id": version.name,
			"node_type": "Pillar",
			"title": "Digital health infrastructure",
			"display_order": 1,
			"fixture_namespace": FIXTURE_NS,
		}
	)
	pillar.insert(ignore_permissions=True)
	programme = frappe.get_doc(
		{
			"doctype": "Strategy Node",
			"plan_version_id": version.name,
			"node_type": "Programme",
			"title": "Digital Health Services",
			"display_order": 2,
			"parent_node_id": pillar.name,
			"fixture_namespace": FIXTURE_NS,
		}
	)
	programme.insert(ignore_permissions=True)
	objective = frappe.get_doc(
		{
			"doctype": "Strategy Node",
			"plan_version_id": version.name,
			"node_type": "Strategic Objective",
			"title": "Reliable and accessible digital clinical services",
			"display_order": 3,
			"parent_node_id": programme.name,
			"fixture_namespace": FIXTURE_NS,
		}
	)
	objective.insert(ignore_permissions=True)
	indicator = frappe.get_doc(
		{
			"doctype": "Performance Indicator",
			"plan_version_id": version.name,
			"measures_node_id": objective.name,
			"indicator_name": "Availability of core clinical information systems",
			"definition": "Percentage of scheduled uptime achieved by core clinical information systems.",
			"unit": "Percentage",
			"fixture_namespace": FIXTURE_NS,
		}
	)
	indicator.insert(ignore_permissions=True)
	target = frappe.get_doc(
		{
			"doctype": "Performance Target",
			"indicator_id": indicator.name,
			"target_by_date": "2033-06-30",
			"comparison": "At least",
			"target_value": 99.9,
			"fixture_namespace": FIXTURE_NS,
		}
	)
	target.insert(ignore_permissions=True)

	try:
		frappe.set_user(actors["author"])
		transition_plan_version(version.name, "Submit for approval")
		frappe.set_user(actors["approver"])
		transition_plan_version(version.name, "Approve")
	finally:
		frappe.set_user("Administrator")

	return {"ok": True, "plan": version.name, "objective": objective.name, "target": target.name}
