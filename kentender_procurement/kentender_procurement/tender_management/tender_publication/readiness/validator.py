# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0100 — Validate ``PublicationReadinessFinding`` payloads."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.tender_publication.readiness.schema import (
	PUBLICATION_CRITICAL_BLOCKER_CODES,
	PUBLICATION_READINESS_FINDING_INVALID,
	PUBLICATION_READINESS_KNOWN_CODES,
	PUBLICATION_READINESS_SEVERITIES,
)


def _throw_invalid(msg: str) -> None:
	frappe.throw(msg, title=PUBLICATION_READINESS_FINDING_INVALID, exc=frappe.ValidationError)


def validate_publication_readiness_finding(obj: Any) -> None:
	"""Validate a single finding dict: pack §5 keys, codes, severities, block flags."""
	if not isinstance(obj, dict):
		_throw_invalid(_("Publication readiness finding must be an object."))

	code = (obj.get("code") or "").strip()
	if not code:
		_throw_invalid(_("Publication readiness finding.code is required."))
	if code not in PUBLICATION_READINESS_KNOWN_CODES:
		_throw_invalid(_("Publication readiness finding has unknown code: {0}").format(code))

	sev = (obj.get("severity") or "").strip()
	if sev not in PUBLICATION_READINESS_SEVERITIES:
		_throw_invalid(_("Publication readiness finding.severity is invalid."))

	msg = (obj.get("message") or "").strip()
	if not msg:
		_throw_invalid(_("Publication readiness finding.message is required."))

	area = (obj.get("affected_area") or "").strip()
	if not area:
		_throw_invalid(_("Publication readiness finding.affected_area is required."))

	res = (obj.get("resolution_action") or "").strip()
	if not res:
		_throw_invalid(_("Publication readiness finding.resolution_action is required."))

	ba = obj.get("blocks_approval")
	bp = obj.get("blocks_publication")
	if not isinstance(ba, bool):
		_throw_invalid(_("Publication readiness finding.blocks_approval must be a boolean."))
	if not isinstance(bp, bool):
		_throw_invalid(_("Publication readiness finding.blocks_publication must be a boolean."))

	if code in PUBLICATION_CRITICAL_BLOCKER_CODES:
		if not ba or not bp:
			_throw_invalid(
				_("Critical readiness code {0} must block both approval and publication.").format(code),
			)

	aot = obj.get("affected_object_type")
	if aot is not None and not isinstance(aot, str):
		_throw_invalid(_("Publication readiness finding.affected_object_type must be a string or null."))
	aoc = obj.get("affected_object_code")
	if aoc is not None and not isinstance(aoc, str):
		_throw_invalid(_("Publication readiness finding.affected_object_code must be a string or null."))
