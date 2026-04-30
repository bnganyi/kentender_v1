from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate


_KPI_ROWS: tuple[dict[str, object], ...] = (
    {
        "id": "draft_versions",
        "label": _("Draft Versions"),
        "testid": "std-kpi-draft-versions",
        "select_queue_id": "draft_versions",
        "select_work_tab": "templates",
    },
    {
        "id": "validation_blocked",
        "label": _("Validation Blocked"),
        "testid": "std-kpi-validation-blocked",
        "select_queue_id": "validation_blocked",
        "select_work_tab": "mywork",
        "risk_level": "high",
    },
    {
        "id": "legal_review_pending",
        "label": _("Legal Review Pending"),
        "testid": "std-kpi-legal-review-pending",
        "select_queue_id": "legal_review",
        "select_work_tab": "templates",
    },
    {
        "id": "policy_review_pending",
        "label": _("Policy Review Pending"),
        "testid": "std-kpi-policy-review-pending",
        "select_queue_id": "policy_review",
        "select_work_tab": "templates",
    },
    {
        "id": "active_versions",
        "label": _("Active Versions"),
        "testid": "std-kpi-active-versions",
        "select_queue_id": "active_versions",
        "select_work_tab": "active_versions",
    },
    {
        "id": "instances_blocked",
        "label": _("Instances Blocked"),
        "testid": "std-kpi-instances-blocked",
        "select_queue_id": "instance_blocked",
        "select_work_tab": "instances",
    },
    {
        "id": "generation_failures",
        "label": _("Generation Failures"),
        "testid": "std-kpi-generation-failures",
        "select_queue_id": "generation_failed",
        "select_work_tab": "generation_jobs",
        "risk_level": "high",
    },
    {
        "id": "addendum_impact_pending",
        "label": _("Addendum Impact Pending"),
        "testid": "std-kpi-addendum-impact-pending",
        "select_queue_id": "addendum_impact",
        "select_work_tab": "addendum_impacts",
        "risk_level": "high",
    },
)

_SCOPE_TABS: tuple[dict[str, str], ...] = (
    {"id": "mywork", "label": _("My Work"), "testid": "std-scope-my-work"},
    {"id": "templates", "label": _("Templates"), "testid": "std-scope-templates"},
    {"id": "active_versions", "label": _("Active Versions"), "testid": "std-scope-active-versions"},
    {"id": "instances", "label": _("STD Instances"), "testid": "std-scope-std-instances"},
    {"id": "generation_jobs", "label": _("Generation Jobs"), "testid": "std-scope-generation-jobs"},
    {"id": "addendum_impacts", "label": _("Addendum Impacts"), "testid": "std-scope-addendum-impacts"},
    {"id": "audit_view", "label": _("Audit View"), "testid": "std-scope-audit-view"},
)

_QUEUE_ROWS: tuple[dict[str, str], ...] = (
    {"id": "draft_versions", "label": _("Draft Versions"), "scope_tab_id": "templates", "testid": "std-queue-draft-versions"},
    {"id": "structure_in_progress", "label": _("Structure In Progress"), "scope_tab_id": "templates", "testid": "std-queue-structure-in-progress"},
    {"id": "validation_blocked", "label": _("Validation Blocked"), "scope_tab_id": "mywork", "testid": "std-queue-validation-blocked"},
    {"id": "validation_passed", "label": _("Validation Passed"), "scope_tab_id": "templates", "testid": "std-queue-validation-passed"},
    {"id": "legal_review", "label": _("Legal Review"), "scope_tab_id": "templates", "testid": "std-queue-legal-review"},
    {"id": "policy_review", "label": _("Policy Review"), "scope_tab_id": "templates", "testid": "std-queue-policy-review"},
    {"id": "approved", "label": _("Approved"), "scope_tab_id": "templates", "testid": "std-queue-approved"},
    {"id": "active_versions", "label": _("Active"), "scope_tab_id": "active_versions", "testid": "std-queue-active"},
    {"id": "suspended", "label": _("Suspended"), "scope_tab_id": "active_versions", "testid": "std-queue-suspended"},
    {"id": "superseded", "label": _("Superseded"), "scope_tab_id": "active_versions", "testid": "std-queue-superseded"},
    {"id": "draft_instances", "label": _("Draft Instances"), "scope_tab_id": "instances", "testid": "std-queue-draft-instances"},
    {"id": "instance_blocked", "label": _("Instance Blocked"), "scope_tab_id": "instances", "testid": "std-queue-instance-blocked"},
    {"id": "instance_ready", "label": _("Instance Ready"), "scope_tab_id": "instances", "testid": "std-queue-instance-ready"},
    {"id": "published_locked", "label": _("Published Locked"), "scope_tab_id": "instances", "testid": "std-queue-published-locked"},
    {"id": "generation_failed", "label": _("Generation Failed"), "scope_tab_id": "generation_jobs", "testid": "std-queue-generation-failed"},
    {"id": "addendum_impact", "label": _("Addendum Impact"), "scope_tab_id": "addendum_impacts", "testid": "std-queue-addendum-impact"},
    {"id": "archived", "label": _("Archived"), "scope_tab_id": "audit_view", "testid": "std-queue-archived"},
)

_OBJECT_TYPES: tuple[str, ...] = (
    "Template Version",
    "Applicability Profile",
    "STD Instance",
    "Generation Job",
    "Generated Output",
    "Addendum Impact",
    "Readiness Run",
)

# Roles from STD Works roles matrix §3.1–3.2 (Desk chrome filtering).
_STD_GOVERNANCE_ROLES: frozenset[str] = frozenset(
    {
        "STD Administrator",
        "Senior STD Administrator",
        "STD Legal Reviewer",
        "STD Policy Reviewer",
        "STD Governance Approver",
        "STD Configuration Auditor",
        "STD Technical Maintainer",
        "STD Support Analyst",
    }
)
_STD_INSTANCE_OPERATIONS_ROLES: frozenset[str] = frozenset(
    {
        "Procurement Officer",
        "Technical Officer",
        "Technical Officer / Engineer",
        "Quantity Surveyor",
        "Quantity Surveyor / BOQ Preparer",
        "Procurement Manager",
        "Legal Reviewer",
        "Compliance Reviewer",
        "Auditor",
        "Auditor / Oversight User",
    }
)
_INSTANCE_OPERATIONS_SCOPE_IDS: frozenset[str] = frozenset(
    {"mywork", "instances", "generation_jobs", "addendum_impacts", "audit_view"}
)
_INSTANCE_OPERATIONS_KPI_IDS: frozenset[str] = frozenset(
    {
        "validation_blocked",
        "active_versions",
        "instances_blocked",
        "generation_failures",
        "addendum_impact_pending",
    }
)


def _stdlib_role_names(user: str | None = None) -> set[str]:
    return set(frappe.get_roles(user or frappe.session.user))


def resolve_std_workbench_chrome(
    roles: set[str],
) -> tuple[str, list[dict[str, object]], list[dict[str, str]], list[dict[str, str]]]:
    """Return (visibility_policy, kpis, scope_tabs, queues) for the current role mix."""
    if not roles or roles & {"Administrator", "System Manager", "All"}:
        return (
            "full_governance",
            [dict(x) for x in _KPI_ROWS],
            [dict(x) for x in _SCOPE_TABS],
            [dict(x) for x in _QUEUE_ROWS],
        )
    if roles & _STD_GOVERNANCE_ROLES:
        return (
            "full_governance",
            [dict(x) for x in _KPI_ROWS],
            [dict(x) for x in _SCOPE_TABS],
            [dict(x) for x in _QUEUE_ROWS],
        )
    if roles & _STD_INSTANCE_OPERATIONS_ROLES:
        kpis = [dict(x) for x in _KPI_ROWS if str(x.get("id") or "") in _INSTANCE_OPERATIONS_KPI_IDS]
        scopes = [dict(x) for x in _SCOPE_TABS if x["id"] in _INSTANCE_OPERATIONS_SCOPE_IDS]
        queues = [
            dict(x) for x in _QUEUE_ROWS if str(x.get("scope_tab_id") or "") in _INSTANCE_OPERATIONS_SCOPE_IDS
        ]
        return ("instance_operational", kpis, scopes, queues)
    return (
        "full_governance",
        [dict(x) for x in _KPI_ROWS],
        [dict(x) for x in _SCOPE_TABS],
        [dict(x) for x in _QUEUE_ROWS],
    )


def build_std_header_actions() -> list[dict[str, object]]:
    """Global STD workbench header CTAs (permission-gated; client renders allowed only)."""

    def _can_create(doctype: str) -> bool:
        try:
            return bool(frappe.has_permission(doctype, "create"))
        except Exception:
            return False

    def _can_read(doctype: str) -> bool:
        try:
            return bool(frappe.has_permission(doctype, "read"))
        except Exception:
            return False

    def _can_run_safety_report() -> bool:
        roles = _stdlib_role_names()
        return bool(
            {
                "Administrator",
                "System Manager",
                "STD Auditor",
                "Head of Procurement and Disposal Unit (HPDU)",
                "Procurement Compliance Officer",
            }.intersection(roles)
        )

    return [
        {
            "id": "new_template_version",
            "label": str(_("New Template Version")),
            "testid": "std-header-new-template-version",
            "allowed": _can_create("STD Template Version"),
        },
        {
            "id": "new_applicability_profile",
            "label": str(_("New Applicability Profile")),
            "testid": "std-header-new-applicability-profile",
            "allowed": _can_create("STD Applicability Profile"),
        },
        {
            "id": "find_std_instance",
            "label": str(_("Find STD Instance")),
            "testid": "std-header-find-std-instance",
            "allowed": _can_read("STD Instance"),
        },
        {
            "id": "my_reviews",
            "label": str(_("My Reviews")),
            "testid": "std-header-my-reviews",
            "allowed": _can_read("STD Template Version") or _can_read("STD Instance"),
        },
        {
            "id": "evidence_export",
            "label": str(_("Evidence Export")),
            "testid": "std-header-evidence-export",
            "allowed": _can_read("STD Template Version") or _can_read("STD Instance"),
        },
        {
            "id": "production_safety_report",
            "label": str(_("Production Safety Report")),
            "testid": "std-header-production-safety-report",
            "allowed": _can_run_safety_report(),
        },
        {
            "id": "settings",
            "label": str(_("Settings")),
            "testid": "std-header-settings",
            "allowed": "System Manager" in _stdlib_role_names(),
        },
    ]


def _count(doctype: str, filters: dict | None = None) -> int:
    rows = frappe.get_list(
        doctype,
        filters=filters or {},
        fields=[{"COUNT": "*", "as": "count"}],
        limit=1,
    )
    if not rows:
        return 0
    return int((rows[0] or {}).get("count") or 0)


def _build_counts() -> dict[str, int]:
    return {
        "draft_versions": _count("STD Template Version", {"version_status": ["in", ["Draft", "Structure In Progress"]]}),
        "validation_blocked": _count("STD Template Version", {"version_status": "Validation Blocked"})
        + _count("STD Instance", {"readiness_status": "Blocked"}),
        "legal_review_pending": _count("STD Template Version", {"legal_review_status": "Pending"}),
        "policy_review_pending": _count("STD Template Version", {"policy_review_status": "Pending"}),
        "active_versions": _count("STD Template Version", {"version_status": "Active"}),
        "instances_blocked": _count("STD Instance", {"instance_status": "Blocked"})
        + _count("STD Instance", {"readiness_status": "Blocked"}),
        "generation_failures": _count("STD Generation Job", {"status": "Failed"}),
        "addendum_impact_pending": _count(
            "STD Addendum Impact Analysis",
            {"status": ["in", ["Analysis Pending", "Analysis Complete", "Approved", "Regeneration Required"]]},
        ),
    }


def _as_filters_dict(filters) -> dict:
    if not filters:
        return {}
    if isinstance(filters, str):
        return frappe.parse_json(filters) or {}
    if isinstance(filters, dict):
        return filters
    return {}


def _contains(haystack: str, needle: str) -> bool:
    return needle in (haystack or "").lower()


def _queue_match(row: dict, queue_id: str) -> bool:
    q = (queue_id or "").strip().lower()
    if not q:
        return True
    typ = row.get("object_type")
    status = str(row.get("status") or "")
    if q == "draft_versions":
        return typ == "Template Version" and status == "Draft"
    if q == "structure_in_progress":
        return typ == "Template Version" and status == "Structure In Progress"
    if q == "validation_blocked":
        return (typ == "Template Version" and status == "Validation Blocked") or (
            typ == "STD Instance" and row.get("readiness_status") == "Blocked"
        )
    if q == "validation_passed":
        return typ == "Template Version" and status == "Validation Passed"
    if q == "legal_review":
        return typ == "Template Version" and str(row.get("legal_review_status") or "") == "Pending"
    if q == "policy_review":
        return typ == "Template Version" and str(row.get("policy_review_status") or "") == "Pending"
    if q == "approved":
        return typ == "Template Version" and status == "Approved"
    if q == "active_versions":
        return typ == "Template Version" and status == "Active"
    if q == "suspended":
        return typ == "Template Version" and status == "Suspended"
    if q == "superseded":
        return typ == "Template Version" and status == "Superseded"
    if q == "draft_instances":
        return typ == "STD Instance" and status == "Draft"
    if q == "instance_blocked":
        return typ == "STD Instance" and (status == "Blocked" or row.get("readiness_status") == "Blocked")
    if q == "instance_ready":
        return typ == "STD Instance" and row.get("readiness_status") == "Ready"
    if q == "published_locked":
        return typ == "STD Instance" and status == "Published Locked"
    if q == "generation_failed":
        return typ == "Generation Job" and status == "Failed"
    if q == "addendum_impact":
        return typ == "Addendum Impact" and status in ("Analysis Pending", "Analysis Complete", "Approved", "Regeneration Required")
    if q == "archived":
        return status in ("Archived", "Superseded")
    return True


def _row_matches_filters(row: dict, filters: dict) -> bool:
    object_type = str(filters.get("object_type") or "").strip()
    if object_type and object_type != row.get("object_type"):
        return False
    procurement_category = str(filters.get("procurement_category") or "").strip()
    if procurement_category and procurement_category != str(row.get("procurement_category") or ""):
        return False
    works_profile_type = str(filters.get("works_profile_type") or "").strip().lower()
    if works_profile_type and works_profile_type not in str(row.get("works_profile_type") or "").lower():
        return False
    for filt_key, row_key in (
        ("template_version_status", "status"),
        ("profile_status", "status"),
        ("instance_status", "status"),
        ("readiness_status", "readiness_status"),
        ("generation_status", "status"),
        ("output_status", "status"),
        ("legal_review_status", "legal_review_status"),
        ("policy_review_status", "policy_review_status"),
    ):
        expected = str(filters.get(filt_key) or "").strip()
        if expected and expected != str(row.get(row_key) or ""):
            return False
    if int(filters.get("has_failed_generation") or 0) and not (
        row.get("object_type") == "Generation Job" and str(row.get("status") or "") == "Failed"
    ):
        return False
    if int(filters.get("has_critical_blockers") or 0) and not (
        (row.get("object_type") == "Template Version" and str(row.get("status") or "") == "Validation Blocked")
        or (row.get("object_type") == "STD Instance" and str(row.get("readiness_status") or "") == "Blocked")
    ):
        return False
    assigned_to_me = int(filters.get("assigned_to_me") or 0)
    if assigned_to_me and row.get("owner") != frappe.session.user:
        return False
    created_from = str(filters.get("created_from") or "").strip()
    if created_from and str(row.get("created_on") or ""):
        try:
            if getdate(str(row.get("created_on"))) < getdate(created_from):
                return False
        except Exception:
            pass
    created_to = str(filters.get("created_to") or "").strip()
    if created_to and str(row.get("created_on") or ""):
        try:
            if getdate(str(row.get("created_on"))) > getdate(created_to):
                return False
        except Exception:
            pass
    return True


def _collect_rows(limit: int = 80) -> list[dict]:
    rows: list[dict] = []
    for row in frappe.get_list(
        "STD Template Family",
        fields=["template_code", "template_title", "procurement_category", "family_status", "owner", "modified"],
        order_by="modified desc",
        limit=limit,
    ):
        rows.append(
            {
                "object_type": "Template Family",
                "code": row.get("template_code"),
                "title": row.get("template_title") or row.get("template_code"),
                "status": row.get("family_status"),
                "procurement_category": row.get("procurement_category"),
                "owner": row.get("owner"),
                "created_on": row.get("modified"),
            }
        )
    for row in frappe.get_list(
        "STD Template Version",
        fields=[
            "version_code",
            "template_code",
            "version_label",
            "version_status",
            "legal_review_status",
            "policy_review_status",
            "procurement_category",
            "works_profile_type",
            "owner",
            "modified",
        ],
        order_by="modified desc",
        limit=limit,
    ):
        rows.append(
            {
                "object_type": "Template Version",
                "code": row.get("version_code"),
                "title": row.get("version_label") or row.get("version_code"),
                "status": row.get("version_status"),
                "template_code": row.get("template_code"),
                "legal_review_status": row.get("legal_review_status"),
                "policy_review_status": row.get("policy_review_status"),
                "procurement_category": row.get("procurement_category"),
                "works_profile_type": row.get("works_profile_type"),
                "owner": row.get("owner"),
                "created_on": row.get("modified"),
            }
        )
    for row in frappe.get_list(
        "STD Applicability Profile",
        fields=["profile_code", "profile_title", "version_code", "profile_status", "procurement_category", "works_profile_type", "owner", "modified"],
        order_by="modified desc",
        limit=limit,
    ):
        rows.append(
            {
                "object_type": "Applicability Profile",
                "code": row.get("profile_code"),
                "title": row.get("profile_title") or row.get("profile_code"),
                "status": row.get("profile_status"),
                "version_code": row.get("version_code"),
                "procurement_category": row.get("procurement_category"),
                "works_profile_type": row.get("works_profile_type"),
                "owner": row.get("owner"),
                "created_on": row.get("modified"),
            }
        )
    for row in frappe.get_list(
        "STD Instance",
        fields=["instance_code", "tender_code", "instance_status", "readiness_status", "owner", "modified"],
        order_by="modified desc",
        limit=limit,
    ):
        rows.append(
            {
                "object_type": "STD Instance",
                "code": row.get("instance_code"),
                "title": row.get("tender_code") or row.get("instance_code"),
                "status": row.get("instance_status"),
                "readiness_status": row.get("readiness_status"),
                "tender_code": row.get("tender_code"),
                "owner": row.get("owner"),
                "created_on": row.get("modified"),
            }
        )
    for row in frappe.get_list(
        "STD Generation Job",
        fields=["generation_job_code", "job_type", "status", "instance_code", "owner", "modified"],
        order_by="modified desc",
        limit=limit,
    ):
        rows.append(
            {
                "object_type": "Generation Job",
                "code": row.get("generation_job_code"),
                "title": row.get("job_type") or row.get("generation_job_code"),
                "status": row.get("status"),
                "job_type": row.get("job_type"),
                "owner": row.get("owner"),
                "created_on": row.get("modified"),
            }
        )
    for row in frappe.get_list(
        "STD Generated Output",
        fields=["output_code", "output_type", "status", "instance_code", "owner", "modified"],
        order_by="modified desc",
        limit=limit,
    ):
        rows.append(
            {
                "object_type": "Generated Output",
                "code": row.get("output_code"),
                "title": row.get("output_type") or row.get("output_code"),
                "status": row.get("status"),
                "output_type": row.get("output_type"),
                "owner": row.get("owner"),
                "created_on": row.get("modified"),
            }
        )
    for row in frappe.get_list(
        "STD Addendum Impact Analysis",
        fields=["impact_analysis_code", "addendum_code", "status", "instance_code", "owner", "modified"],
        order_by="modified desc",
        limit=limit,
    ):
        rows.append(
            {
                "object_type": "Addendum Impact",
                "code": row.get("impact_analysis_code"),
                "title": row.get("addendum_code") or row.get("impact_analysis_code"),
                "status": row.get("status"),
                "addendum_code": row.get("addendum_code"),
                "owner": row.get("owner"),
                "created_on": row.get("modified"),
            }
        )
    for row in frappe.get_list(
        "STD Readiness Run",
        fields=["readiness_run_code", "object_type", "object_code", "status", "owner", "run_at"],
        order_by="run_at desc",
        limit=limit,
    ):
        rows.append(
            {
                "object_type": "Readiness Run",
                "code": row.get("readiness_run_code"),
                "title": (row.get("object_type") or "") + " " + (row.get("object_code") or ""),
                "status": row.get("status"),
                "owner": row.get("owner"),
                "created_on": row.get("run_at"),
            }
        )
    return rows


@frappe.whitelist()
def get_std_workbench_kpi_strip() -> dict:
    if frappe.session.user in (None, "Guest"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    roles = _stdlib_role_names()
    _policy, kpi_defs, scope_defs, queue_defs = resolve_std_workbench_chrome(roles)

    counts = _build_counts()
    rows: list[dict] = []
    for definition in kpi_defs:
        row = dict(definition)
        row["value"] = int(counts.get(str(row["id"]), 0))
        rows.append(row)

    return {
        "ok": True,
        "kpis": rows,
        "scope_tabs": [dict(x) for x in scope_defs],
        "queues": [dict(x) for x in queue_defs],
        "default_scope_tab_id": "mywork",
        "default_queue_id": "validation_blocked",
        "visibility_policy": _policy,
        "header_actions": build_std_header_actions(),
    }


@frappe.whitelist()
def search_std_workbench_objects(
    query: str | None = None,
    queue_id: str | None = None,
    scope_tab_id: str | None = None,
    filters=None,
    limit: int | str = 50,
) -> dict:
    if frappe.session.user in (None, "Guest"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    roles = _stdlib_role_names()
    _visibility_policy, _kpis, scope_defs, queue_defs = resolve_std_workbench_chrome(roles)
    allowed_scope_ids = {str(x.get("id") or "") for x in scope_defs if x.get("id")}
    allowed_queue_ids = {str(x.get("id") or "") for x in queue_defs if x.get("id")}
    needle = str(query or "").strip().lower()
    filt = _as_filters_dict(filters)
    scope = str(scope_tab_id or "").strip()
    if scope and allowed_scope_ids and scope not in allowed_scope_ids:
        raise frappe.PermissionError(_("Not permitted for this workbench scope."))
    qid = str(queue_id or "").strip()
    if qid and allowed_queue_ids and qid not in allowed_queue_ids:
        raise frappe.PermissionError(_("Not permitted for this queue."))
    max_rows = max(1, min(int(limit or 50), 200))
    rows = _collect_rows(limit=max_rows)
    out: list[dict] = []
    for row in rows:
        if scope:
            queue_defs = [q for q in _QUEUE_ROWS if q.get("scope_tab_id") == scope]
            if queue_defs and row.get("object_type") not in _OBJECT_TYPES:
                continue
        if needle:
            blob = " ".join(
                [
                    str(row.get("code") or ""),
                    str(row.get("title") or ""),
                    str(row.get("status") or ""),
                    str(row.get("object_type") or ""),
                ]
            ).lower()
            if not _contains(blob, needle):
                continue
        if not _queue_match(row, str(queue_id or "")):
            continue
        if not _row_matches_filters(row, filt):
            continue
        out.append(row)
        if len(out) >= max_rows:
            break
    return {"ok": True, "results": out, "total": len(out)}


@frappe.whitelist()
def get_std_action_availability(
    object_type: str | None = None,
    object_code: str | None = None,
    actor: str | None = None,
) -> dict:
    """Server-side action availability for STD workbench detail panel (STD-CURSOR-1006)."""
    if frappe.session.user in (None, "Guest"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    from kentender_procurement.std_engine.services.action_availability_service import (
        build_std_action_availability,
        validate_actor_override,
    )

    effective_user = validate_actor_override(actor)
    return build_std_action_availability(
        str(object_type or "").strip(),
        str(object_code or "").strip(),
        effective_user,
    )
