# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0100 — Build and bridge publication readiness findings.

``publication_finding_from_code`` applies pack §5 defaults (critical → block
approval+publication; warnings → non-blocking by default).

``publication_finding_from_std_blocker`` maps a subset of
``StdInstanceReadinessService`` blocker codes to publication pack codes for
PUB-0110. Callers must map ``STALE_OUTPUTS_PRESENT`` to the specific
``*_NOT_CURRENT`` code once the stale output type is known.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.tender_publication.readiness.schema import (
	PUBLICATION_READINESS_BRIDGE_UNKNOWN,
	PUBLICATION_READINESS_DEFAULT_AFFECTED_AREA,
	PUBLICATION_READINESS_DEFAULT_MESSAGES,
	PUBLICATION_READINESS_DEFAULT_RESOLUTIONS,
	PUBLICATION_READINESS_FINDING_INVALID,
	PUBLICATION_READINESS_KNOWN_CODES,
	default_blocks_for_code,
	is_critical_code,
)
from kentender_procurement.tender_management.tender_publication.readiness.validator import (
	validate_publication_readiness_finding,
)

# Minimal 1:1 bridge from STDINST readiness blocker codes (readiness.py) to pack §5 codes.
STD_READINESS_CODE_TO_PUBLICATION_CODE: dict[str, str] = {
	"TEMPLATE_OR_PROFILE_MISSING": "TEMPLATE_LINEAGE_INVALID",
	"BUNDLE_MISSING": "BUNDLE_NOT_CURRENT",
	"DSM_MISSING": "DSM_NOT_CURRENT",
	"DOM_MISSING": "DOM_NOT_CURRENT",
	"DEM_MISSING": "DEM_NOT_CURRENT",
	"DCM_MISSING": "DCM_NOT_CURRENT",
	"BOQ_MISSING": "BOQ_INCOMPLETE",
	"BOQ_INVALID": "BOQ_INCOMPLETE",
	"WORKS_REQUIREMENTS_INCOMPLETE": "WORKS_REQUIREMENTS_INCOMPLETE",
	# PUB-0110: STD uses aggregate codes; map to closest pack §5 critical codes (refine in later tickets).
	"PARAMETERS_INCOMPLETE": "TDS_INCOMPLETE",
	"REQUIRED_ATTACHMENTS_INCOMPLETE": "TDS_INCOMPLETE",
}


def publication_finding_from_code(code: str, **overrides: Any) -> dict[str, Any]:
	"""Build a validated finding dict for ``code`` with pack defaults; ``overrides`` merged last."""
	pc = (code or "").strip()
	if pc not in PUBLICATION_READINESS_KNOWN_CODES:
		frappe.throw(
			_("Unknown publication readiness code: {0}").format(pc),
			title=PUBLICATION_READINESS_FINDING_INVALID,
			exc=frappe.ValidationError,
		)
	ba, bp = default_blocks_for_code(pc)
	severity = "Critical" if is_critical_code(pc) else "Warning"

	row: dict[str, Any] = {
		"code": pc,
		"severity": severity,
		"message": PUBLICATION_READINESS_DEFAULT_MESSAGES[pc],
		"affected_area": PUBLICATION_READINESS_DEFAULT_AFFECTED_AREA[pc],
		"resolution_action": PUBLICATION_READINESS_DEFAULT_RESOLUTIONS[pc],
		"blocks_approval": ba,
		"blocks_publication": bp,
	}
	row.update(overrides)
	validate_publication_readiness_finding(row)
	return row


def publication_finding_from_std_blocker(std_code: str, message: str | None = None) -> dict[str, Any]:
	"""Map STD instance readiness ``std_code`` to a publication finding when a mapping exists."""
	sc = (std_code or "").strip()
	pub = STD_READINESS_CODE_TO_PUBLICATION_CODE.get(sc)
	if not pub:
		frappe.throw(
			_("No publication readiness bridge for STD blocker code: {0}").format(sc),
			title=PUBLICATION_READINESS_BRIDGE_UNKNOWN,
			exc=frappe.ValidationError,
		)
	ov: dict[str, Any] = {}
	if message and message.strip():
		ov["message"] = message.strip()
	return publication_finding_from_code(pub, **ov)
