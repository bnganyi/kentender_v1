# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""X100 — Server-derived bid Issues register (cross-cutting, not checklist progress)."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_configurations.services.bid_evidence import (
	list_missing_metadata_items,
	portal_evidence_url,
)
from kentender_procurement.tender_configurations.services.electronic_bid import (
	_require_logged_in,
	create_or_get_draft,
)
from kentender_procurement.tender_configurations.services.published_tender_overview import (
	resolve_published_tender_backend,
)
from kentender_procurement.tender_configurations.services.section_status import (
	SEVERITY_BLOCKER,
	SEVERITY_INFORMATION,
	SEVERITY_WARNING,
	issue_item,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	portal_workspace_url,
)
from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
	portal_documents_url,
)


def portal_issues_url(publication_ref: str) -> str:
	return f"/tenders/{quote(cstr(publication_ref or '').strip(), safe='')}/issues"


def clear_issue_blockers_denied(published_tender_ref: str) -> None:
	"""Authoritative blockers are server-derived — clients may not clear them."""
	_ = published_tender_ref
	_require_logged_in()
	frappe.throw(
		frappe._("Authoritative blockers can only be cleared by correcting the underlying response."),
		frappe.PermissionError,
	)


def _docs_issues(published_tender_ref: str, backend: dict[str, Any]) -> list[dict[str, Any]]:
	from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
		get_tender_documents_addenda,
	)

	try:
		dto = get_tender_documents_addenda(published_tender_ref)
	except Exception:
		return []
	out: list[dict[str, Any]] = []
	pub_ref = cstr(backend.get("published_tender_ref") or published_tender_ref)
	docs_url = portal_documents_url(pub_ref)
	if not dto.get("documents_acknowledged"):
		code = "package_acknowledgement_required"
		if dto.get("acknowledgement_stale"):
			code = "acknowledgement_stale"
		out.append(
			issue_item(
				code=code,
				severity=SEVERITY_BLOCKER,
				message=cstr(
					(dto.get("readiness") or {}).get("blocker_message")
					or "Acknowledge the current tender documents for this publication."
				),
				section_key=cstr(dto.get("section_key") or "tender_documents_and_addenda"),
				correction_route=docs_url,
				resolved=0,
			)
		)
	if dto.get("addenda_block_submission"):
		out.append(
			issue_item(
				code="required_addendum_unacknowledged",
				severity=SEVERITY_BLOCKER,
				message="One or more required addenda are unacknowledged for the current version.",
				section_key=cstr(dto.get("section_key") or "tender_documents_and_addenda"),
				correction_route=docs_url,
				resolved=0,
			)
		)
	return out


def _evidence_issues(published_tender_ref: str) -> list[dict[str, Any]]:
	missing = list_missing_metadata_items(published_tender_ref)
	route = portal_evidence_url(published_tender_ref)
	out: list[dict[str, Any]] = []
	for item in missing:
		out.append(
			issue_item(
				code="evidence_missing_metadata",
				severity=SEVERITY_BLOCKER,
				message=frappe._(
					"Evidence “{0}” is missing required issuer, reference, issue date or validity."
				).format(cstr(item.get("title") or item.get("evidence_id"))),
				section_key="evidence_register",
				task_key=cstr(item.get("evidence_id") or ""),
				field_key="metadata",
				correction_route=route,
				resolved=0,
			)
		)
	return out


def get_issue_register(published_tender_ref: str) -> dict[str, Any]:
	"""Aggregate server-derived issues for the bidder's own bid."""
	_require_logged_in()
	backend = resolve_published_tender_backend(published_tender_ref)
	pub_ref = cstr(backend.get("published_tender_ref") or published_tender_ref)
	# Ensure a draft exists so evidence/docs derives bind to this bidder.
	create_or_get_draft(cstr(backend.get("configuration_id") or ""))

	issues: list[dict[str, Any]] = []
	issues.extend(_docs_issues(pub_ref, backend))
	issues.extend(_evidence_issues(pub_ref))

	# Deduplicate by code + task_key + field_key.
	seen: set[str] = set()
	unique: list[dict[str, Any]] = []
	for issue in issues:
		key = "|".join(
			[
				cstr(issue.get("code")),
				cstr(issue.get("section_key")),
				cstr(issue.get("task_key")),
				cstr(issue.get("field_key")),
			]
		)
		if key in seen:
			continue
		seen.add(key)
		unique.append(issue)

	severity_rank = {SEVERITY_BLOCKER: 0, SEVERITY_WARNING: 1, SEVERITY_INFORMATION: 2}
	unique.sort(key=lambda i: (severity_rank.get(cstr(i.get("severity")), 9), cstr(i.get("code"))))

	open_issues = [i for i in unique if not i.get("resolved")]
	return {
		"published_tender_ref": pub_ref,
		"workspace_url": portal_workspace_url(pub_ref),
		"issues_url": portal_issues_url(pub_ref),
		"evidence_url": portal_evidence_url(pub_ref),
		"overview_url": f"/tenders/{quote(pub_ref, safe='')}",
		"documents_url": portal_documents_url(pub_ref),
		"tender_title": cstr(
			frappe.db.get_value(
				"Tender Configuration", backend.get("configuration_id"), "tender_title"
			)
			or ""
		),
		"issues": unique,
		"open_count": len(open_issues),
		"blocker_count": sum(1 for i in open_issues if i.get("severity") == SEVERITY_BLOCKER),
		"empty": 1 if not unique else 0,
		"empty_message": "No current issues for this bid.",
	}
