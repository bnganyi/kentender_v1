# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TM2 workbench — Section 11 terminology simplification (PLC usability handoff pack).

Business-readable labels appear in primary UI; technical tokens remain available for
Legal Basis / Evidence / Advanced surfaces and integration fields.
"""

from __future__ import annotations

from frappe import _

# Pack §11.2 — primary user-facing labels for technical terms.
_TECHNICAL_TERM_LABELS: dict[str, str] = {
	"STD Template": _("Official tender document template"),
	"STD Template Version": _("Official document version"),
	"Tender STD Instance": _("Tender-specific document setup"),
	"Bundle": _("Tender document package"),
	"DSM": _("Supplier submission checklist"),
	"DOM": _("Opening register rules"),
	"DEM": _("Evaluation rules"),
	"DCM": _("Contract carry-forward terms"),
	"Publication Snapshot": _("Published tender evidence snapshot"),
	"Tender STD Binding": _("Tender document binding"),
	"Readiness Validation": _("Publication readiness check"),
}

_TENDER_STATUS_LABELS: dict[str, str] = {
	"Draft": _("Draft"),
	"STD Instance Incomplete": _("Document setup incomplete"),
	"Ready for Publication Review": _("Ready for publication review"),
	"Returned for Correction": _("Returned for correction"),
	"Approved for Publication": _("Approved for publication"),
	"Published": _("Published"),
	"Addendum Pending": _("Addendum pending"),
	"Suspended Pending Addendum": _("Suspended pending addendum"),
	"Opening Ready": _("Opening ready"),
	"Closed": _("Closed"),
	"Closed - No Valid Submissions": _("Closed — no valid submissions"),
	"Evaluation Ready": _("Evaluation ready"),
	"Cancelled": _("Cancelled"),
}

_READINESS_STATUS_LABELS: dict[str, str] = {
	"Ready": _("Ready"),
	"Not Ready": _("Not ready"),
	"Blocked": _("Blocked"),
	"Not Assessed": _("Not assessed"),
	"Ready With Warnings": _("Ready with warnings"),
}

_CHECKLIST_BUSINESS_LABELS: dict[str, str] = {
	"package_lineage_valid": _("Package lineage verified"),
	"template_version_active": _("Official document version is active"),
	"std_instance_exists": _("Tender-specific document setup exists"),
	"parameters_complete": _("Tender parameters complete"),
	"sections_complete": _("Required document sections complete"),
	"bundle_current": _("Tender document package up to date"),
	"dsm_current": _("Supplier submission checklist up to date"),
	"dom_current": _("Opening register rules up to date"),
	"dem_current": _("Evaluation rules up to date"),
	"dcm_current": _("Contract carry-forward terms up to date"),
	"publication_snapshot": _("Published tender evidence snapshot available"),
	"timeline_valid": _("Submission timeline valid"),
	"supplier_access_valid": _("Supplier access rules valid"),
	"no_critical_blockers": _("No critical blockers"),
}

_DERIVED_OUTPUT_LABELS: dict[str, str] = {
	"bundle": _("Tender document package"),
	"dsm": _("Supplier submission checklist"),
	"dom": _("Opening register rules"),
	"dem": _("Evaluation rules"),
	"dcm": _("Contract carry-forward terms"),
}

_QUEUE_SLUG_LABELS: dict[str, str] = {
	"draft": _("Draft"),
	"std-incomplete": _("Document setup incomplete"),
	"ready-review": _("Review"),
	"returned": _("Returned"),
	"approved": _("Approved"),
	"published": _("Published"),
	"clarifications": _("Clarifications"),
	"addenda": _("Addenda"),
	"closing-soon": _("Closing soon"),
	"closed": _("Closed"),
	"opening-ready": _("Opening ready"),
	"evaluation-ready": _("Evaluation ready"),
	"cancelled": _("Cancelled"),
}


def business_label_for_technical_term(term: str) -> str:
	key = str(term or "").strip()
	if not key:
		return ""
	return str(_TECHNICAL_TERM_LABELS.get(key) or key)


def business_label_for_tender_status(status: str) -> str:
	st = str(status or "").strip()
	if not st:
		return ""
	return str(_TENDER_STATUS_LABELS.get(st) or st)


def business_label_for_readiness_status(status: str) -> str:
	rs = str(status or "").strip()
	if not rs:
		return ""
	return str(_READINESS_STATUS_LABELS.get(rs) or rs)


def business_label_for_checklist_row(row_id: str, fallback: str = "") -> str:
	rid = str(row_id or "").strip()
	if rid in _CHECKLIST_BUSINESS_LABELS:
		return str(_CHECKLIST_BUSINESS_LABELS[rid])
	return str(fallback or rid)


def business_label_for_derived_output(output_id: str, fallback: str = "") -> str:
	oid = str(output_id or "").strip().lower()
	if oid in _DERIVED_OUTPUT_LABELS:
		return str(_DERIVED_OUTPUT_LABELS[oid])
	return str(fallback or oid)


def business_label_for_queue_slug(slug: str) -> str:
	s = str(slug or "").strip()
	if not s:
		return _("All")
	return str(_QUEUE_SLUG_LABELS.get(s) or s)


def business_readiness_short_label(readiness_status: str) -> str:
	rs = business_label_for_readiness_status(readiness_status)
	if rs:
		return rs
	return _("Readiness not assessed")


_OUTPUT_FIELD_LABELS: dict[str, str] = {
	"bundle_output_code": _("Tender document package"),
	"dsm_output_code": _("Supplier submission checklist"),
	"dom_output_code": _("Opening register rules"),
	"dem_output_code": _("Evaluation rules"),
	"dcm_output_code": _("Contract carry-forward terms"),
	"publication_snapshot_code": _("Published tender evidence snapshot"),
	"tender_std_instance_code": _("Tender-specific document setup"),
	"binding_code": _("Tender document binding"),
	"std_template_version_code": _("Official document version"),
}


def business_label_for_output_field(field: str) -> str:
	key = str(field or "").strip()
	if not key:
		return ""
	return str(_OUTPUT_FIELD_LABELS.get(key) or key)


# Lifecycle audit trail — business-readable event labels (primary UI).
_AUDIT_EVENT_LABELS: dict[str, str] = {
	"Tender Created": _("Tender created"),
	"Tender STD Bound": _("Official document linked"),
	"STD Readiness Validation Run": _("Publication readiness check run"),
	"Tender Submitted for Publication Review": _("Submitted for publication review"),
	"Tender Returned for Correction": _("Returned for correction"),
	"Tender Approved for Publication": _("Approved for publication"),
	"Tender Published": _("Tender published"),
	"Publication Failed": _("Publication failed"),
	"Supplier Invited": _("Supplier invited"),
	"Supplier Viewed Tender": _("Supplier viewed tender"),
	"Supplier Downloaded Bundle": _("Supplier downloaded tender documents"),
	"Clarification Submitted": _("Clarification submitted"),
	"Clarification Response Drafted": _("Clarification response drafted"),
	"Clarification Response Approved": _("Clarification response approved"),
	"Clarification Published": _("Clarification published"),
	"Clarification Converted to Addendum": _("Clarification converted to addendum"),
	"Addendum Created": _("Addendum created"),
	"Addendum Impact Analysis Requested": _("Addendum impact analysis requested"),
	"Addendum Impact Analysis Completed": _("Addendum impact analysis completed"),
	"Addendum Approved": _("Addendum approved"),
	"Addendum Issued": _("Addendum issued"),
	"Addendum Cancelled": _("Addendum cancelled"),
	"Bid Draft Started": _("Bid draft started"),
	"Bid Draft Saved": _("Bid draft saved"),
	"Bid Submitted": _("Bid submitted"),
	"Bid Sealed": _("Bid sealed"),
	"Bid Replaced": _("Bid replaced"),
	"Bid Withdrawn": _("Bid withdrawn"),
	"Late Submission Rejected": _("Late submission rejected"),
	"Tender Closed": _("Tender closed"),
	"Opening Readiness Created": _("Opening readiness prepared"),
	"Evaluation Handoff Completed": _("Evaluation handoff completed"),
	"Contract Handoff Reference Created": _("Contract handoff created"),
	"Tender Cancelled": _("Tender cancelled"),
	"Retender Required": _("Retender required"),
	"Tender Superseded": _("Tender superseded"),
	"Access Denied": _("Access denied"),
	"Administrative Override": _("Administrative override"),
	"Other": _("Other event"),
}


def business_label_for_audit_event(event_type: str) -> str:
	et = str(event_type or "").strip()
	if not et:
		return ""
	return str(_AUDIT_EVENT_LABELS.get(et) or et.replace("_", " ").strip())


# Blocked-action table — business-readable action and reason labels.
_ACTION_CODE_LABELS: dict[str, str] = {
	"BID2_VIEW_SEALED_CONTENT": _("View sealed bid contents"),
	"BID2_SUBMIT": _("Submit bid"),
	"BID2_WITHDRAW": _("Withdraw bid"),
	"AUD2_EXPORT_EVIDENCE": _("Export tender evidence"),
	"TND2_PUBLISH": _("Publish tender"),
	"Access Denied": _("Access denied"),
}

_DENIAL_CODE_LABELS: dict[str, str] = {
	"AUTH_SEALED_BID_DENIED": _("Sealed bid content is protected before opening"),
	"AUTH_ACTION_AVAILABILITY_DENIED": _("Action is not permitted in the current tender state"),
	"AUTH_LEGACY_PATH_DENIED": _("This workflow path is no longer permitted"),
	"STD_AUTH_PERMISSION_DENIED": _("You do not have permission for this action"),
	"STD_AUTH_OBJECT_SCOPE_DENIED": _("This tender or record is outside your access scope"),
	"STD_AUTH_DCM_CONTRACT_BINDING_VIOLATION": _("Contract terms cannot be changed through this path"),
}


def business_label_for_action_code(action_code: str) -> str:
	ac = str(action_code or "").strip()
	if not ac:
		return ""
	if ac in _ACTION_CODE_LABELS:
		return str(_ACTION_CODE_LABELS[ac])
	return ac.replace("_", " ").strip()


def business_label_for_denial_code(denial_code: str) -> str:
	dc = str(denial_code or "").strip()
	if not dc:
		return ""
	if dc in _DENIAL_CODE_LABELS:
		return str(_DENIAL_CODE_LABELS[dc])
	# Fall back to a readable phrase without internal prefixes.
	human = dc.replace("_", " ").strip()
	for prefix in ("AUTH ", "STD AUTH ", "STD "):
		if human.upper().startswith(prefix):
			human = human[len(prefix) :].strip()
			break
	return human or dc


def format_denied_action_display_line(
	actor_display: str,
	action_code: str,
	denial_code: str = "",
	event_type: str = "",
) -> str:
	ad = str(actor_display or "").strip() or _("Unknown user")
	action = business_label_for_action_code(action_code) or business_label_for_audit_event(event_type)
	reason = business_label_for_denial_code(denial_code) or business_label_for_audit_event(event_type)
	if action and reason:
		return str(_("{0} — {1} blocked ({2})").format(ad, action, reason))
	if action:
		return str(_("{0} — {1} blocked").format(ad, action))
	return str(_("{0} — action blocked").format(ad))


def format_lifecycle_audit_display_line(
	timestamp: str,
	event_type: str,
	previous_state: str = "",
	new_state: str = "",
) -> str:
	ts = str(timestamp or "").strip()
	ev = business_label_for_audit_event(event_type)
	line = f"{ts} · {ev}".strip(" ·") if ts and ev else (ts or ev)
	ps = business_label_for_tender_status(previous_state) or str(previous_state or "").strip()
	ns = business_label_for_tender_status(new_state) or str(new_state or "").strip()
	if ps or ns:
		if ps and ns:
			line += f" ({ps} → {ns})"
		else:
			line += f" ({ns or ps})"
	return line


# Primary tab notices — no internal product codes, doc refs, or doctype names.
READ_ONLY_TAB_NOTICE_SUPPLIER_ACCESS: str = _(
	"This view is read-only. Supplier access changes follow governed workflows; bid contents are not shown here."
)
READ_ONLY_TAB_NOTICE_CLARIFICATIONS: str = _(
	"This view is read-only. Clarifications, responses, and addendum conversion follow governed workflows."
)
READ_ONLY_TAB_NOTICE_ADDENDA: str = _(
	"This view is read-only. Addendum creation, approval, issue, and document updates follow governed workflows."
)
READ_ONLY_TAB_NOTICE_SUBMISSIONS: str = _(
	"This view is read-only. Bid submission, sealing, and opening workflows are managed in their respective modules."
)
READ_ONLY_TAB_NOTICE_OPENING: str = _(
	"This view is read-only. Opening readiness preparation and handoff use governed actions in the Opening module."
)
READ_ONLY_TAB_NOTICE_EVALUATION: str = _(
	"This view is read-only. Evaluation criteria are not edited here; handoff actions use governed availability checks."
)
READ_ONLY_TAB_NOTICE_CONTRACT: str = _(
	"This view is read-only. Contract handoff creation uses governed actions and award context."
)
READ_ONLY_TAB_NOTICE_AUDIT: str = _(
	"This view is read-only. The lifecycle timeline and blocked-action records come from the tender audit trail."
)
EVIDENCE_EXPORT_TAB_NOTICE: str = ""
EVALUATION_RULES_READ_ONLY_NOTICE: str = _(
	"Evaluation rules are read-only here. Criteria are maintained in the Evaluation module."
)
CONTRACT_TERMS_READ_ONLY_NOTICE: str = _(
	"Contract carry-forward terms are read-only here. Contract terms are maintained in the Contract module."
)
CONTRACT_HANDOFF_SUMMARY_NOTICE: str = _(
	"Tender Management does not edit contract terms here; this tab is a read-only handoff summary."
)
EVALUATION_CRITERIA_FIXED_NOTICE: str = _(
	"Evaluation criteria are derived from the official tender document setup and cannot be modified in Tender Management."
)
WORKS_CONTRACT_VALUE_SOURCE_NOTICE: str = _(
	"Contract value source: corrected evaluated BOQ total from Evaluation/Award."
)
CONTRACT_UNCORRECTED_PRICE_EDUCATION: str = _(
	"Works contract handoff must use the corrected evaluated BOQ total; using the uncorrected total is not permitted."
)
