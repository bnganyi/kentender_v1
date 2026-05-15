# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-25 — Domain enumerations (doc 3 §4, doc 9 §5.3).

Canonical **ordered** tuples for Tender Management v2 select values. Use ``frozenset(VAR)`` at call
sites for membership checks; keep tuple order stable for UX and documentation diffs.

**Doc 9 §5.3** — ``PACK_*`` aliases must match these tuples for: tender status, STD readiness, addendum
status, and bid status (pack test contract).
"""

from __future__ import annotations

# --- §4.1 Tender Status ---------------------------------------------------------

TENDER_STATUS: tuple[str, ...] = (
	"Draft",
	"STD Instance Incomplete",
	"Ready for Publication Review",
	"Returned for Correction",
	"Approved for Publication",
	"Published",
	"Addendum Pending",
	"Suspended Pending Addendum",
	"Closed",
	"Closed - No Valid Submissions",
	"Opening Ready",
	"Opening Completed",
	"Evaluation Ready",
	"Evaluation In Progress",
	"Awarded",
	"Contract Handoff Completed",
	"Cancelled",
	"Retender Required",
	"Superseded",
	"Archived",
)

# --- §4.2 Procurement Method ----------------------------------------------------

PROCUREMENT_METHOD: tuple[str, ...] = (
	"Open Tender",
	"Restricted Tender",
	"RFQ",
	"RFP",
	"Direct Procurement",
	"Two-Stage Tender",
	"Framework Establishment",
	"Framework Call-Off",
	"Disposal",
)

# --- §4.3 Procurement Category --------------------------------------------------

PROCUREMENT_CATEGORY: tuple[str, ...] = (
	"Works",
	"Goods",
	"Consultancy Services",
	"Non-Consulting Services",
	"Disposal",
	"Framework",
	"Other",
)

# --- §4.4 Tender Visibility ----------------------------------------------------

TENDER_VISIBILITY: tuple[str, ...] = (
	"Internal Only",
	"Public",
	"Login Required",
	"Restricted",
	"Direct Invitation",
)

# --- §4.5 STD Readiness Status --------------------------------------------------

STD_READINESS_STATUS: tuple[str, ...] = (
	"Not Started",
	"Incomplete",
	"Blocked",
	"Warning",
	"Ready",
	"Invalidated by Change",
	"Superseded",
)

# --- §4.6 Publication Readiness Check Severity --------------------------------

PUBLICATION_READINESS_CHECK_SEVERITY: tuple[str, ...] = (
	"Info",
	"Warning",
	"High",
	"Critical",
)

# --- §4.7 Publication Status ----------------------------------------------------

PUBLICATION_STATUS: tuple[str, ...] = (
	"Pending",
	"Published",
	"Failed",
	"Superseded",
	"Withdrawn",
)

# --- §4.8 Invitation Status ---------------------------------------------------

INVITATION_STATUS: tuple[str, ...] = (
	"Draft",
	"Sent",
	"Delivered",
	"Accepted",
	"Declined",
	"Revoked",
	"Expired",
	"Superseded",
)

# --- §4.9 Participation Status ------------------------------------------------

PARTICIPATION_STATUS: tuple[str, ...] = (
	"Viewed Tender",
	"Downloaded Documents",
	"Expressed Interest",
	"Clarification Submitted",
	"Bid Draft Started",
	"Bid Submitted",
	"Bid Replaced",
	"Bid Withdrawn",
	"No Response",
	"Ineligible",
)

# --- §4.10 Clarification Status -----------------------------------------------

CLARIFICATION_STATUS: tuple[str, ...] = (
	"Submitted",
	"Under Review",
	"Response Drafted",
	"Pending Approval",
	"Published",
	"Rejected",
	"Converted to Addendum",
	"Withdrawn",
)

# --- §4.11 Clarification Visibility -------------------------------------------

CLARIFICATION_VISIBILITY: tuple[str, ...] = (
	"Requesting Supplier Only",
	"All Participants",
	"Public",
	"Internal Only",
)

# --- §4.12 Addendum Status ----------------------------------------------------

ADDENDUM_STATUS: tuple[str, ...] = (
	"Draft",
	"Impact Analysis Pending",
	"Impact Analysis Complete",
	"Pending Legal Review",
	"Pending Approval",
	"Approved",
	"Issued",
	"Cancelled",
	"Superseded",
	"Withdrawn",
)

# --- §4.13 Addendum Impact Type -----------------------------------------------

ADDENDUM_IMPACT_TYPE: tuple[str, ...] = (
	"No Structural Impact",
	"Parameter Change",
	"Deadline Change",
	"Works Requirement Change",
	"BOQ Change",
	"Submission Model Change",
	"Opening Model Change",
	"Evaluation Model Change",
	"Contract Carry-Forward Change",
	"Cancellation / Reissue Required",
)

# --- §4.14 Bid Status ---------------------------------------------------------

BID_STATUS: tuple[str, ...] = (
	"Draft",
	"Submitted",
	"Sealed",
	"Superseded",
	"Withdrawn",
	"Late Attempt Rejected",
	"Opened",
	"Excluded by System Rule",
	"Evaluation Locked",
)

# --- §4.15 Bid Component Type ---------------------------------------------------

BID_COMPONENT_TYPE: tuple[str, ...] = (
	"Administrative",
	"Technical",
	"Financial",
	"BOQ",
	"Tender Security",
	"Declaration",
	"Qualification Evidence",
	"Works Programme",
	"HSE Plan",
	"Environmental Social Evidence",
	"Other STD-Derived Component",
)

# --- §4.16 Closing Status -----------------------------------------------------

CLOSING_STATUS: tuple[str, ...] = (
	"Pending",
	"Closed On Time",
	"Closed With No Valid Submissions",
	"Closure Failed",
	"Manually Confirmed",
	"Reopened by Authorized Addendum",
)

# --- §4.17 Handoff Status -------------------------------------------------------

HANDOFF_STATUS: tuple[str, ...] = (
	"Not Ready",
	"Ready",
	"Sent",
	"Accepted",
	"Rejected",
	"Superseded",
)

# --- §4.18 Audit Event Type (domain labels) -----------------------------------

AUDIT_EVENT_TYPE: tuple[str, ...] = (
	"Tender Created",
	"Tender STD Bound",
	"STD Readiness Validation Run",
	"Tender Submitted for Publication Review",
	"Tender Returned for Correction",
	"Tender Approved for Publication",
	"Tender Published",
	"Publication Failed",
	"Supplier Invited",
	"Supplier Viewed Tender",
	"Supplier Downloaded Bundle",
	"Clarification Submitted",
	"Clarification Response Drafted",
	"Clarification Response Approved",
	"Clarification Published",
	"Clarification Converted to Addendum",
	"Addendum Created",
	"Addendum Impact Analysis Requested",
	"Addendum Impact Analysis Completed",
	"Addendum Approved",
	"Addendum Issued",
	"Addendum Cancelled",
	"Bid Draft Started",
	"Bid Draft Saved",
	"Bid Submitted",
	"Bid Sealed",
	"Bid Replaced",
	"Bid Withdrawn",
	"Late Submission Rejected",
	"Tender Closed",
	"Opening Readiness Created",
	"Evaluation Handoff Completed",
	"Contract Handoff Reference Created",
	"Tender Cancelled",
	"Retender Required",
	"Tender Superseded",
	"Access Denied",
	"Administrative Override",
)

# --- Doc 9 §5.3 (pack / test contract) — must match domain §4.1 / §4.5 / §4.12 / §4.14

PACK_TENDER_STATUS: tuple[str, ...] = TENDER_STATUS
PACK_STD_READINESS_STATUS: tuple[str, ...] = STD_READINESS_STATUS
PACK_ADDENDUM_STATUS: tuple[str, ...] = ADDENDUM_STATUS
PACK_BID_STATUS: tuple[str, ...] = BID_STATUS


def as_frozenset(values: tuple[str, ...]) -> frozenset[str]:
	"""Stable membership set from an ordered domain tuple."""
	return frozenset(values)


__all__ = (
	"TENDER_STATUS",
	"PROCUREMENT_METHOD",
	"PROCUREMENT_CATEGORY",
	"TENDER_VISIBILITY",
	"STD_READINESS_STATUS",
	"PUBLICATION_READINESS_CHECK_SEVERITY",
	"PUBLICATION_STATUS",
	"INVITATION_STATUS",
	"PARTICIPATION_STATUS",
	"CLARIFICATION_STATUS",
	"CLARIFICATION_VISIBILITY",
	"ADDENDUM_STATUS",
	"ADDENDUM_IMPACT_TYPE",
	"BID_STATUS",
	"BID_COMPONENT_TYPE",
	"CLOSING_STATUS",
	"HANDOFF_STATUS",
	"AUDIT_EVENT_TYPE",
	"PACK_TENDER_STATUS",
	"PACK_STD_READINESS_STATUS",
	"PACK_ADDENDUM_STATUS",
	"PACK_BID_STATUS",
	"as_frozenset",
)
