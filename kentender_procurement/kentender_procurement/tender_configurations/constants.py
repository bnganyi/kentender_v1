# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender Configurations — status labels, tabs, and STD family display map."""

from __future__ import annotations

from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_APPROVED,
	PKG_READY_FOR_RELEASE,
	PKG_RELEASED,
)

DOCTYPE = "Tender Configuration"

# UI-00 §14 configuration status labels (exact)
STATUS_IN_PROGRESS = "In Progress"
STATUS_NEEDS_ATTENTION = "Needs Attention"
STATUS_READY_FOR_REVIEW = "Ready for Review"
STATUS_UNDER_REVIEW = "Under Review"
STATUS_READY_FOR_PUBLICATION = "Ready for Publication"
STATUS_COMPLETED = "Completed"

CONFIGURATION_STATUSES = (
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
	STATUS_READY_FOR_REVIEW,
	STATUS_UNDER_REVIEW,
	STATUS_READY_FOR_PUBLICATION,
	STATUS_COMPLETED,
)

# Active = blocks creating another configuration for the same package
ACTIVE_CONFIGURATION_STATUSES = frozenset(
	(
		STATUS_IN_PROGRESS,
		STATUS_NEEDS_ATTENTION,
		STATUS_READY_FOR_REVIEW,
		STATUS_UNDER_REVIEW,
		STATUS_READY_FOR_PUBLICATION,
	)
)

# Packages eligible for Ready to Configure
ELIGIBLE_PACKAGE_STATUSES = frozenset(
	(
		PKG_APPROVED,
		PKG_READY_FOR_RELEASE,
		PKG_RELEASED,
	)
)

# Dashboard tabs
TAB_READY_TO_CONFIGURE = "ready_to_configure"
TAB_IN_PROGRESS = "in_progress"
TAB_NEEDS_ATTENTION = "needs_attention"
TAB_READY_FOR_REVIEW = "ready_for_review"
TAB_READY_FOR_PUBLICATION = "ready_for_publication"
TAB_COMPLETED = "completed"

TAB_TO_STATUS = {
	TAB_IN_PROGRESS: STATUS_IN_PROGRESS,
	TAB_NEEDS_ATTENTION: STATUS_NEEDS_ATTENTION,
	TAB_READY_FOR_REVIEW: (STATUS_READY_FOR_REVIEW, STATUS_UNDER_REVIEW),
	TAB_READY_FOR_PUBLICATION: STATUS_READY_FOR_PUBLICATION,
	TAB_COMPLETED: STATUS_COMPLETED,
}

TAB_ACTION_LABELS = {
	TAB_READY_TO_CONFIGURE: "Create Configuration",
	TAB_IN_PROGRESS: "Continue Configuration",
	TAB_NEEDS_ATTENTION: "Fix Issues",
	TAB_READY_FOR_REVIEW: "Submit for Review",
	TAB_READY_FOR_PUBLICATION: "Open Handoff",
	TAB_COMPLETED: "View Configuration",
}

# User-facing STD family labels (UI-00 filters)
STD_FAMILY_LABELS = (
	"Information Technology",
	"Works",
	"Goods",
	"Consultancy",
	"Non-Consultancy",
)

# Map package category / required_std_category → (family_key, label, preferred STD Family codes)
# family_key is API-facing (C1-M2 uses "IT"); label is UI-facing.
_FAMILY_ALIASES: dict[str, tuple[str, str, tuple[str, ...]]] = {
	"information technology": ("IT", "Information Technology", ("KE-PPRA-IT",)),
	"it": ("IT", "Information Technology", ("KE-PPRA-IT",)),
	"ict": ("IT", "Information Technology", ("KE-PPRA-IT",)),
	"works": ("WORKS", "Works", ("KE-PPRA-WORKS",)),
	"goods": ("GOODS", "Goods", ("KE-PPRA-GOODS",)),
	"consultancy": ("CONSULTANCY", "Consultancy", ("KE-PPRA-CONSULTANCY",)),
	"services": ("CONSULTANCY", "Consultancy", ("KE-PPRA-CONSULTANCY",)),
	"non-consultancy": ("NON_CONSULTANCY", "Non-Consultancy", ("KE-PPRA-NON-CONSULTANCY",)),
	"non consultancy": ("NON_CONSULTANCY", "Non-Consultancy", ("KE-PPRA-NON-CONSULTANCY",)),
}

UI_01_ROUTE = "it-tender-configuration-overview"

# Fixture STD Version for tests/seed when Official Library has no ACTIVE version
FIXTURE_STD_FAMILY_CODE = "KE-PPRA-IT"
FIXTURE_STD_VERSION_ID = "TCFG-FIXTURE-IT-ACTIVE"
FIXTURE_STD_VERSION_LABEL = "IT Standard Tender Document — April 2022"
