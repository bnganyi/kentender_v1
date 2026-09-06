# BUD-CHG-001 v1.3 Phase 8 (BUD-802) — fixture bootstrap for the Budget &
# Funding design-fidelity gate (`make ui-budget-fidelity-gate`).
#
# Fed to `bench console` as stdin by the Makefile target (this file lives
# under tests/ui/smoke/design-fidelity/, not inside any installed app's own
# Python package, so `bench execute <dotted.path>` cannot import it — piping
# it to `bench console` is the only way to run it without adding a file
# outside this task's allowed scope).
#
# Idempotent throughout: every fixture is guarded by an existence check, safe
# to re-run on every gate invocation, and creates only reusable seed-shaped
# data (no per-run randomness) so nothing needs to be purged between runs.
#
# Why this exists rather than reusing an existing seed module directly:
#   - kentender_budget.seeds.kentender_mvp_v1_portfolio.upsert_kentender_mvp_v1_portfolio
#     is the real, idempotent, contract-driven canonical seed (BUD-604/BUD-605)
#     and IS reused below — but it depends on world-building steps (the 3
#     named canonical Users already enabled, and the MOH-DIR-DHP/MOH-DIR-HRMD
#     Organisation Units existing) that normally come from the whole-site
#     KENTENDER_MVP_V1 orchestrator. That orchestrator cannot currently
#     complete on this dev site (kentender_core.seeds.kentender_mvp_v1.org's
#     upsert_org() also creates a second-PE Kisumu root Organisation Unit,
#     which trips OrganisationUnit._validate_single_root() — a pre-existing,
#     out-of-Budget's-scope defect already carried in
#     docs/mvp-1-r1/03_budget/IMPLEMENTATION_TRACKER.md's Phase 6 notes).
#   - kentender_budget.seeds.playwright_ui_fixtures is itself broken on
#     master/mvp1/dev: it imports `_context_id_for` from
#     kentender_mvp_v1_portfolio, a PE+FY "working context" helper Phase 6
#     deleted outright when Budget moved to a Fiscal-Year-only model. It is
#     v1.2-era dead code, out of this task's scope to fix (not in the allowed
#     file list), so it is not used here.
#
# This script therefore does the minimum extra world-building
# (2 Organisation Units, 1 Funding Source, the 3 canonical Users) the real
# canonical seed needs, then reuses that seed verbatim, then adds a handful
# of additional small, real, contract-driven fixtures for the lifecycle
# states no artboard-covered route can reach from the canonical seed alone
# (an unsubmitted Draft, an undecided initial-baseline submission, an
# unsubmitted successor Draft, and an FY with no Budget at all).

from __future__ import annotations

import json

import frappe
from frappe.utils import nowdate

frappe.set_user("Administrator")

from kentender_core.seeds.kentender_mvp_v1 import constants as C  # noqa: E402
from kentender_core.seeds._common import ensure_currency_kes  # noqa: E402

PE_MOH = C.PE_MOH

report: dict[str, object] = {}


# --- 1. The 2 Organisation Units the fixtures' owner_org_unit values use —
#     KT-STD-001 §8.2's site-seed units ("Digital Health", "Human Resources
#     Management and Development"), resolved through the shared register the
#     same way the canonical Budget seed does (`_unit_for`), never created
#     here. Unit codes are server-generated (`OU-MOH-{sequence}`, CFG v0.6
#     §4.3); the retired `MOH-DIR-*` mnemonic codes this seed used to insert
#     ad hoc created a second, duplicate "Digital Health"/"HRMD" pair on the
#     dev site (found 2026-09-06). ------------------------------------------

from kentender_budget.seeds.kentender_mvp_v1_portfolio import _unit_for  # noqa: E402

assert frappe.db.exists("Organisation Unit", PE_MOH), (
    f"Budget fidelity seed: root Organisation Unit {PE_MOH!r} must already exist "
    "(System Setup's own seed world) — refusing to invent a second root."
)
OU_DHP = _unit_for("grace.wanjiku@moh.example.test", "Departmental Author", "Digital Health")
OU_HRMD = _unit_for(
    "peter.kimani@moh.example.test", "Head of User Department", "Human Resources Management and Development"
)
assert OU_DHP and OU_HRMD, (
    "Budget fidelity seed: run `bench execute kentender_core.seeds.site_setup.run` first — "
    "the KT-STD-001 §8 units and assignments must already exist."
)
report["organisation_units"] = [OU_DHP, OU_HRMD]


# --- 2. Funding Source "Government of Kenya" — genuinely zero rows on this
#     dev site (a pre-existing, documented seed gap; see IMPLEMENTATION_
#     TRACKER.md's carried debts). Every Budget Line in every fixture below
#     needs a real, Available catalogue row to select. ---------------------

FUNDING_SOURCE = "Government of Kenya"
if not frappe.db.exists("Funding Source", FUNDING_SOURCE):
    frappe.get_doc(
        {"doctype": "Funding Source", "label": FUNDING_SOURCE, "record_status": "Available"}
    ).insert(ignore_permissions=True)
frappe.db.commit()
report["funding_source"] = FUNDING_SOURCE


# --- 3. The 3 canonical named Budget actors (Josphat Mwangi / Beatrice Kamau
#     / Naomi Chebet), enabled with "Desk User" (the Page.roles gate) plus
#     their own Frappe Role — the real authorisation grant (a User
#     Responsibility Assignment) comes from step 4 below.
#
#     Deliberately NOT calling kentender_core.seeds.kentender_mvp_v1.users.
#     upsert_canonical_users(): that function loops over ~20 personas in one
#     unbroken pass with no per-user commit, several of which (the Kisumu
#     ones — USER_KISUMU_OFFICER, USER_CGK_BUD_OFFICER, etc.) require
#     `Procuring Entity: PE-CGKIS` and `Organisation Unit: OU_CGK_HEALTH`.
#     Neither exists on this site (confirmed live, repeatedly, via raw SQL —
#     `SELECT name FROM \`tabProcuring Entity\`` returns only PE-MOH) — a
#     pre-existing, already-documented AUTH-ADR-001 v1.6 one-site-one-PE gap
#     in kentender_core's own shared seed world (IMPLEMENTATION_TRACKER.md's
#     Phase 6 carried-debt note), completely unrelated to Budget and out of
#     this task's scope to fix. Calling the shared function raises partway
#     through and never reaches Josphat/Naomi's own tuples (later in the
#     same loop than the Kisumu ones), which is exactly the failure this
#     comment exists to explain if it recurs. ------------------------------

from frappe.utils.password import update_password  # noqa: E402

_ACTORS = (
    (C.USER_BUD_OFFICER, "Josphat", "Mwangi", "Budget Officer"),
    (C.USER_BUD_APPROVER, "Beatrice", "Kamau", "Budget Approver"),
    (C.USER_BUD_AUDITOR, "Naomi", "Chebet", "Auditor"),
)
for email, first, last, role in _ACTORS:
    if not frappe.db.exists("User", email):
        frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": first,
                "last_name": last,
                "send_welcome_email": 0,
                "user_type": "System User",
            }
        ).insert(ignore_permissions=True)
    user = frappe.get_doc("User", email)
    if not user.enabled:
        user.enabled = 1
        user.save(ignore_permissions=True)
    current_roles = {row.role for row in user.get("roles")}
    missing = [r for r in ("Desk User", role) if r not in current_roles]
    if missing:
        user.add_roles(*missing)
    update_password(email, "Test@123")
frappe.db.commit()
report["canonical_users"] = [C.USER_BUD_OFFICER, C.USER_BUD_APPROVER, C.USER_BUD_AUDITOR]


# --- 4. The real, reusable canonical Budget portfolio seed (BUD-604) —
#     MOH-BUD-2027-001 Active Version 1 (DHI 100m / HWD 60m) only, exactly
#     the default §15.3/§15.4 baseline BUD-DES-01/04/04A/06 render. Nothing
#     this gate needs is written onto the canonical budget any more: the
#     isolated Submitted successor (§15.6) and the reservation (§15.4A —
#     created only at Requisition) live on the gate's own review budget in
#     step 5 below, so the site is left at the canonical baseline after a
#     run (2026-09-06: the earlier include_test_edges=True call parked a
#     Submitted V2 on the canonical budget, which now correctly replaces the
#     Officer's "Create revision" with the pending-task action — and the
#     DHI reservation contradicted §15.4's zero-reserved default). ---------

from kentender_budget.seeds import kentender_mvp_v1_portfolio as portfolio  # noqa: E402

portfolio_result = portfolio.upsert_kentender_mvp_v1_portfolio(include_test_edges=False)
frappe.db.commit()
report["portfolio"] = {"budget": C.BUD_ACTIVE, "version_1": C.BUD_ACTIVE_V1}


# --- helpers shared by the 3 isolated lifecycle-state fixtures below -------

from kentender_budget.seeds.kentender_mvp_v1_portfolio import _ensure_isolated_fy  # noqa: E402
from kentender_budget.services import budget_contracts as contracts  # noqa: E402
from kentender_budget.services import budget_line_contracts as lines_svc  # noqa: E402
from kentender_budget.services import budget_readiness_contracts as readiness  # noqa: E402


def _as(user: str):
    frappe.set_user(user)


def _budget_exists(ref: str) -> bool:
    return bool(frappe.db.exists("Procurement Budget", {"generated_reference": ref}))


# --- 6. BUD-DES-03 fixture — a Draft version with lines saved, never
#     submitted (the "Draft Budget Lines Editor" artboard's own state: tabs
#     visible, Save draft / Submit for review both still live). -----------

DRAFT_UNSUBMITTED_REF = "BUD-FIDELITY-DRAFT"
if not _budget_exists(DRAFT_UNSUBMITTED_REF):
    fy = _ensure_isolated_fy(2060)
    prior_user = frappe.session.user
    try:
        _as(C.USER_BUD_OFFICER)
        result = contracts.save_budget_version_draft(
            {
                "fiscal_year": fy,
                "approval_reference": f"{DRAFT_UNSUBMITTED_REF} (Fidelity gate fixture)",
                "approval_date": nowdate(),
                "authorised_total": 160_000_000,
                "approval_document": "/files/budget-fidelity-gate-draft-demo.pdf",
            }
        )
        if not result.get("ok"):
            frappe.throw(f"Budget fidelity seed: could not create draft fixture: {result.get('errors')}")
        budget_name = result["budget"]["id"]
        version_name = result["version"]["id"]
        frappe.db.set_value("Procurement Budget", budget_name, "generated_reference", DRAFT_UNSUBMITTED_REF, update_modified=False)
        frappe.db.set_value("Procurement Budget Version", version_name, "generated_reference", f"{DRAFT_UNSUBMITTED_REF}-V1", update_modified=False)
        lines_result = lines_svc.save_budget_lines_draft(
            {
                "budget_version": version_name,
                "lines": [
                    {"title": "Digital health infrastructure programme", "owner_org_unit": OU_DHP, "funding_source": FUNDING_SOURCE, "approved_amount": 100_000_000},
                    {"title": "Digital health workforce development", "owner_org_unit": OU_HRMD, "funding_source": FUNDING_SOURCE, "approved_amount": 60_000_000},
                ],
            }
        )
        if not lines_result.get("ok"):
            frappe.throw(f"Budget fidelity seed: could not save draft fixture lines: {lines_result.get('errors')}")
    finally:
        frappe.set_user(prior_user)
    frappe.db.commit()
draft_version_name = frappe.db.get_value("Procurement Budget Version", {"generated_reference": f"{DRAFT_UNSUBMITTED_REF}-V1"}, "name")
draft_version_number = frappe.db.get_value("Procurement Budget Version", draft_version_name, "version_number") if draft_version_name else None
report["draft_unsubmitted"] = {"budget_code": DRAFT_UNSUBMITTED_REF, "version_number": draft_version_number}


# --- 7. BUD-DES-13 family fixture — "Initial Baseline Review": a fresh
#     Budget's own first-ever Version 1 (no predecessor), Submitted for
#     approval, left undecided so the Approval task screen's `based_on` is
#     null (`changes.is_initial_baseline === true`, matching the artboard's
#     own "Version 1 has no predecessor" heading exactly). ------------------

INITIAL_BASELINE_REF = "BUD-FIDELITY-BASELINE"
if not _budget_exists(INITIAL_BASELINE_REF):
    fy = _ensure_isolated_fy(2061)
    prior_user = frappe.session.user
    try:
        _as(C.USER_BUD_OFFICER)
        result = contracts.save_budget_version_draft(
            {
                "fiscal_year": fy,
                "approval_reference": f"{INITIAL_BASELINE_REF} (Fidelity gate fixture)",
                "approval_date": nowdate(),
                "authorised_total": 160_000_000,
                "approval_document": "/files/budget-fidelity-gate-baseline-demo.pdf",
            }
        )
        if not result.get("ok"):
            frappe.throw(f"Budget fidelity seed: could not create initial-baseline fixture: {result.get('errors')}")
        budget_name = result["budget"]["id"]
        version_name = result["version"]["id"]
        frappe.db.set_value("Procurement Budget", budget_name, "generated_reference", INITIAL_BASELINE_REF, update_modified=False)
        frappe.db.set_value("Procurement Budget Version", version_name, "generated_reference", f"{INITIAL_BASELINE_REF}-V1", update_modified=False)
        lines_result = lines_svc.save_budget_lines_draft(
            {
                "budget_version": version_name,
                "lines": [
                    {"title": "Digital health infrastructure programme", "owner_org_unit": OU_DHP, "funding_source": FUNDING_SOURCE, "approved_amount": 100_000_000},
                    {"title": "Digital health workforce development", "owner_org_unit": OU_HRMD, "funding_source": FUNDING_SOURCE, "approved_amount": 60_000_000},
                ],
            }
        )
        if not lines_result.get("ok"):
            frappe.throw(f"Budget fidelity seed: could not save initial-baseline fixture lines: {lines_result.get('errors')}")
        submit_result = readiness.submit_budget_version({"budget_version": version_name})
        if not submit_result.get("ok"):
            frappe.throw(f"Budget fidelity seed: could not submit initial-baseline fixture: {submit_result.get('blockers')}")
    finally:
        frappe.set_user(prior_user)
    frappe.db.commit()
initial_baseline_version_name = frappe.db.get_value("Procurement Budget Version", {"generated_reference": f"{INITIAL_BASELINE_REF}-V1"}, "name")
report["initial_baseline_review"] = {"budget_code": INITIAL_BASELINE_REF, "version_name": initial_baseline_version_name}


# --- 8. BUD-DES-14/15 fixture — "Successor Revision Draft": its own Active
#     Version 1 baseline, then a Version 2 successor created but never
#     submitted (still Draft — Based on / Revision type editable, Save draft
#     / Submit for review both live). ---------------------------------------

SUCCESSOR_DRAFT_REF = "BUD-FIDELITY-SUCCESSOR"
if not _budget_exists(SUCCESSOR_DRAFT_REF):
    fy = _ensure_isolated_fy(2062)
    prior_user = frappe.session.user
    try:
        _as(C.USER_BUD_OFFICER)
        result = contracts.save_budget_version_draft(
            {
                "fiscal_year": fy,
                "approval_reference": f"{SUCCESSOR_DRAFT_REF} (Fidelity gate fixture)",
                "approval_date": nowdate(),
                "authorised_total": 160_000_000,
                "approval_document": "/files/budget-fidelity-gate-successor-demo.pdf",
            }
        )
        if not result.get("ok"):
            frappe.throw(f"Budget fidelity seed: could not create successor-draft baseline: {result.get('errors')}")
        budget_name = result["budget"]["id"]
        version_name = result["version"]["id"]
        frappe.db.set_value("Procurement Budget", budget_name, "generated_reference", SUCCESSOR_DRAFT_REF, update_modified=False)
        frappe.db.set_value("Procurement Budget Version", version_name, "generated_reference", f"{SUCCESSOR_DRAFT_REF}-V1", update_modified=False)
        lines_result = lines_svc.save_budget_lines_draft(
            {
                "budget_version": version_name,
                "lines": [
                    {"title": "Digital health infrastructure programme", "owner_org_unit": OU_DHP, "funding_source": FUNDING_SOURCE, "approved_amount": 100_000_000},
                    {"title": "Digital health workforce development", "owner_org_unit": OU_HRMD, "funding_source": FUNDING_SOURCE, "approved_amount": 60_000_000},
                ],
            }
        )
        if not lines_result.get("ok"):
            frappe.throw(f"Budget fidelity seed: could not save successor-draft baseline lines: {lines_result.get('errors')}")
        submit_result = readiness.submit_budget_version({"budget_version": version_name})
        if not submit_result.get("ok"):
            frappe.throw(f"Budget fidelity seed: could not submit successor-draft baseline: {submit_result.get('blockers')}")

        _as(C.USER_BUD_APPROVER)
        approve_result = readiness.approve_budget_version({"budget_version": version_name})
        if not approve_result.get("ok"):
            frappe.throw(f"Budget fidelity seed: could not approve successor-draft baseline: {approve_result.get('blockers')}")

        _as(C.USER_BUD_OFFICER)
        successor_result = contracts.create_budget_successor_version(
            SUCCESSOR_DRAFT_REF,
            {
                "revision_type": "Transfer",
                "approval_reference": f"{SUCCESSOR_DRAFT_REF}-V2 (Fidelity gate fixture)",
                "approval_date": nowdate(),
                "authorised_total": 160_000_000,
                "approval_document": "/files/budget-fidelity-gate-successor-v2-demo.pdf",
            },
        )
        if not successor_result.get("ok"):
            frappe.throw(f"Budget fidelity seed: could not create successor Version 2: {successor_result}")
        successor_version_name = successor_result["version"]["id"]
        successor_lines_result = lines_svc.save_budget_lines_draft(
            {
                "budget_version": successor_version_name,
                "lines": [
                    {"title": "Digital health infrastructure programme", "owner_org_unit": OU_DHP, "funding_source": FUNDING_SOURCE, "approved_amount": 90_000_000},
                    {"title": "Digital health workforce development", "owner_org_unit": OU_HRMD, "funding_source": FUNDING_SOURCE, "approved_amount": 70_000_000},
                ],
            }
        )
        if not successor_lines_result.get("ok"):
            frappe.throw(f"Budget fidelity seed: could not save successor Version 2 lines: {successor_lines_result.get('errors')}")
        # Deliberately never submitted — BUD-DES-14/15 is the Draft state.
    finally:
        frappe.set_user(prior_user)
    frappe.db.commit()
successor_draft_version_name = frappe.db.get_value("Procurement Budget Version", {"generated_reference": f"{SUCCESSOR_DRAFT_REF}-V2"}, "name")
successor_draft_version_number = frappe.db.get_value("Procurement Budget Version", successor_draft_version_name, "version_number") if successor_draft_version_name else None
report["successor_draft"] = {"budget_code": SUCCESSOR_DRAFT_REF, "version_number": successor_draft_version_number}


# --- 8b. BUD-DES-06A/07/08..11 fixture — "BUD-FIDELITY-REVIEW": its own
#     Active Version 1 (DHI 100m / HWD 60m), one KES 80m reservation on its
#     DHI line (the §15.4-shaped position the artboards were drawn against),
#     and a Transfer successor Version 2 (DHI 90m / HWD 70m) left Submitted
#     for approval, undecided — the Reviewer Task artboards' own state. -----

from kentender_budget.services import budget_check_reserve_contracts as check_reserve  # noqa: E402

REVIEW_REF = "BUD-FIDELITY-REVIEW"
REVIEW_DHI_LINE_REF = f"{REVIEW_REF}-DHI"
if not _budget_exists(REVIEW_REF):
    fy = _ensure_isolated_fy(2064)
    prior_user = frappe.session.user
    try:
        _as(C.USER_BUD_OFFICER)
        result = contracts.save_budget_version_draft(
            {
                "fiscal_year": fy,
                "approval_reference": f"{REVIEW_REF} (Fidelity gate fixture)",
                "approval_date": nowdate(),
                "authorised_total": 160_000_000,
                "approval_document": "/files/budget-fidelity-gate-review-demo.pdf",
            }
        )
        if not result.get("ok"):
            frappe.throw(f"Budget fidelity seed: could not create review baseline: {result.get('errors')}")
        budget_name = result["budget"]["id"]
        version_name = result["version"]["id"]
        frappe.db.set_value("Procurement Budget", budget_name, "generated_reference", REVIEW_REF, update_modified=False)
        frappe.db.set_value("Procurement Budget Version", version_name, "generated_reference", f"{REVIEW_REF}-V1", update_modified=False)
        lines_result = lines_svc.save_budget_lines_draft(
            {
                "budget_version": version_name,
                "lines": [
                    {"title": "Digital health infrastructure programme", "owner_org_unit": OU_DHP, "funding_source": FUNDING_SOURCE, "approved_amount": 100_000_000},
                    {"title": "Digital health workforce development", "owner_org_unit": OU_HRMD, "funding_source": FUNDING_SOURCE, "approved_amount": 60_000_000},
                ],
            }
        )
        if not lines_result.get("ok"):
            frappe.throw(f"Budget fidelity seed: could not save review baseline lines: {lines_result.get('errors')}")
        dhi_line = frappe.db.get_value(
            "Procurement Budget Line Version",
            {"budget_version": version_name, "title": "Digital health infrastructure programme"},
            "budget_line",
        )
        frappe.db.set_value("Procurement Budget Line", dhi_line, "generated_reference", REVIEW_DHI_LINE_REF, update_modified=False)
        submit_result = readiness.submit_budget_version({"budget_version": version_name})
        if not submit_result.get("ok"):
            frappe.throw(f"Budget fidelity seed: could not submit review baseline: {submit_result.get('blockers')}")

        _as(C.USER_BUD_APPROVER)
        approve_result = readiness.approve_budget_version({"budget_version": version_name})
        if not approve_result.get("ok"):
            frappe.throw(f"Budget fidelity seed: could not approve review baseline: {approve_result.get('blockers')}")

        # The KES 80m reservation (BUD-DES-06A/07) — through the real
        # check-and-reserve contracts, as the Finance Confirmation Officer.
        _as(C.USER_BUD_OFFICER)
        token = check_reserve.check_funding(
            plan_item="PPI-MOH-2027-021",
            plan_version="PLN-MOH-2027-021",
            finance_task="FNT-MOH-2027-021-001",
            source_set_hash="BUD-FIDELITY-GATE-HASH",
            allocations=[
                {
                    "budget_line": dhi_line,
                    "amount": 80_000_000,
                    "funding_source": FUNDING_SOURCE,
                    "plan_source_allocation": "BUD-FIDELITY-GATE-PSA",
                }
            ],
            correlation_id=frappe.generate_hash(length=12),
        )
        check_reserve.reserve_funding(
            token=token["token"],
            finance_task="FNT-MOH-2027-021-001",
            source_set_hash="BUD-FIDELITY-GATE-HASH",
            idempotency_key=frappe.generate_hash(length=12),
        )

        successor_result = contracts.create_budget_successor_version(
            REVIEW_REF,
            {
                "revision_type": "Transfer",
                "approval_reference": f"{REVIEW_REF}-V2 (Fidelity gate fixture)",
                "approval_date": nowdate(),
                "authorised_total": 160_000_000,
                "approval_document": "/files/budget-fidelity-gate-review-v2-demo.pdf",
            },
        )
        if not successor_result.get("ok"):
            frappe.throw(f"Budget fidelity seed: could not create review successor: {successor_result}")
        successor_name = successor_result["version"]["id"]
        prior_identity = {
            r.budget_line: r
            for r in frappe.get_all(
                "Procurement Budget Line Version",
                filters={"budget_version": version_name},
                fields=["budget_line", "title", "owner_org_unit", "funding_source"],
            )
        }
        successor_lines = lines_svc.save_budget_lines_draft(
            {
                "budget_version": successor_name,
                "lines": [
                    {
                        "budget_line": line,
                        "title": identity.title,
                        "owner_org_unit": identity.owner_org_unit or "",
                        "funding_source": identity.funding_source,
                        "approved_amount": 90_000_000 if identity.title.startswith("Digital health infrastructure") else 70_000_000,
                    }
                    for line, identity in prior_identity.items()
                ],
            }
        )
        if not successor_lines.get("ok"):
            frappe.throw(f"Budget fidelity seed: could not save review successor lines: {successor_lines.get('errors')}")
        submit_v2 = readiness.submit_budget_version({"budget_version": successor_name})
        if not submit_v2.get("ok"):
            frappe.throw(f"Budget fidelity seed: could not submit review successor: {submit_v2.get('blockers')}")
    finally:
        frappe.set_user(prior_user)
    frappe.db.commit()
report["review"] = {"budget_code": REVIEW_REF, "dhi_line": REVIEW_DHI_LINE_REF, "version_2": f"{REVIEW_REF}-V2"}


# --- 9. BUD-DES-02 / BUD-DES-16 "No baseline" fixture — a Fiscal Year with
#     literally zero Procurement Budget rows, ever. Just needs to exist; the
#     absence of a Budget for it is the whole point, so nothing else is
#     created here. ---------------------------------------------------------

EMPTY_FY = _ensure_isolated_fy(2063)
report["empty_fiscal_year"] = EMPTY_FY


frappe.set_user("Administrator")
ensure_currency_kes()
frappe.db.commit()
print("BUDGET_FIDELITY_SEED_OK " + json.dumps(report, default=str))
