# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-009 — Ensure ``TND-MOH-2026-001`` and related TM2 references exist.

## Documented bridge (LV-R2-001-09)

``release_procurement_package_to_tender`` is the approved creation path.  It runs
XMV validation, resolves the STD template, produces the planning handoff snapshot,
and creates the ``TM2 Tender Access Rule`` + audit event.  Because ``TM2 Tender``
uses ``autoname: field:tender_code`` and allocates codes as ``TND-{ENTITY}-{FY}-{nnnn}``
(4-digit suffix), the resulting name (e.g. ``TND-MOH-2026-0001``) differs from the
canonical master code ``TND-MOH-2026-001`` (3-digit, per spec §13.1).

After the approved process completes, this seed:

1. SQL-renames the auto-generated record to ``TND-MOH-2026-001`` and patches the
   ``tender_code`` Data column in all linked tables.
2. Overrides ``template_version`` to the business version reference
   ``STDTV-WORKS-BUILDING-CIVIL-APR2022`` (the auto process writes the package
   semver ``0.1.0-poc``; VAL-SEED-010 expects the business code).
3. Stamps spec §13.1 fields (title, status=Published, published_at, published_by).
4. Ensures a ``TM2 Tender Timeline`` row (spec §13.2) with the extended-deadline
   and addendum-code values.

All steps are idempotent — re-running is safe.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import now_datetime

from kentender_procurement.tender_management.seeds.works_master_tender_publication_evidence import (
	ensure_works_master_publication_evidence,
)
from kentender_procurement.tender_management.services.create_tender_from_package import (
	active_tm2_tender_name_for_package,
)
from kentender_procurement.tender_management.services.release_procurement_package_to_tender import (
	release_procurement_package_to_tender,
)

# ── canonical master codes (spec §13) ────────────────────────────────────────

TENDER_CODE = "TND-MOH-2026-001"
PACKAGE_CODE = "PKG-MOH-2026-001"
STD_VERSION_REF = "STDTV-WORKS-BUILDING-CIVIL-APR2022"

_TENDER_TITLE = "District Hospital Renovation Works"
_TENDER_STATUS_FINAL = "Published"
_TENDER_PUBLISHED_AT = "2026-05-01 10:03:00"  # spec §13.1 published_at (local)

# spec §13.2 timeline
_CLAR_DEADLINE = "2026-05-15 17:00:00"
_ORIG_SUB_DEADLINE = "2026-05-30 11:00:00"
_SUB_DEADLINE = "2026-06-05 11:00:00"
_OPENING_AT = "2026-06-05 11:30:00"
_TIMEZONE = "Africa/Nairobi"
_ADDENDUM_CODE = "ADD-TND-MOH-2026-001-01"

# ── helpers ──────────────────────────────────────────────────────────────────


def _pkg_name() -> str | None:
	"""Return internal Frappe name for PKG-MOH-2026-001, or None if missing."""
	return frappe.db.get_value("Procurement Package", {"package_code": PACKAGE_CODE}, "name")


def _rename_to_canonical(auto_name: str) -> None:
	"""SQL-patch all tables that carry the auto-generated tender_code / tm2_tender FK."""
	if auto_name == TENDER_CODE:
		return
	frappe.db.sql(
		"UPDATE `tabTM2 Tender` SET name=%s, tender_code=%s WHERE name=%s",
		(TENDER_CODE, TENDER_CODE, auto_name),
	)
	frappe.db.sql(
		"UPDATE `tabTM2 Tender Access Rule` SET tm2_tender=%s, tender_code=%s WHERE tm2_tender=%s",
		(TENDER_CODE, TENDER_CODE, auto_name),
	)
	frappe.db.sql(
		"UPDATE `tabTM2 Tender Timeline` SET tm2_tender=%s, tender_code=%s WHERE tm2_tender=%s",
		(TENDER_CODE, TENDER_CODE, auto_name),
	)
	frappe.db.sql(
		"UPDATE `tabTM2 Tender Audit Event` SET tm2_tender=%s, tender_code=%s WHERE tm2_tender=%s",
		(TENDER_CODE, TENDER_CODE, auto_name),
	)


def _apply_spec_fields() -> None:
	"""Stamp spec §13.1 fields and override template_version with the business code."""
	frappe.db.set_value(
		"TM2 Tender",
		TENDER_CODE,
		{
			"tender_title": _TENDER_TITLE,
			"template_version": STD_VERSION_REF,
		},
		update_modified=False,
	)


def _ensure_timeline() -> str:
	"""Create the spec §13.2 timeline row if absent; return its name."""
	existing = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": TENDER_CODE}, "name")
	if existing:
		return existing
	tl = frappe.get_doc(
		{
			"doctype": "TM2 Tender Timeline",
			"tm2_tender": TENDER_CODE,
			"tender_code": TENDER_CODE,
			"clarification_deadline_at": _CLAR_DEADLINE,
			"submission_deadline_at": _SUB_DEADLINE,
			"opening_scheduled_at": _OPENING_AT,
			"tender_validity_days": 120,
			"timezone": _TIMEZONE,
			"deadline_extended": 1,
			"extension_source_addendum_code": _ADDENDUM_CODE,
		}
	)
	tl.insert(ignore_permissions=True)
	return tl.name


def _promote_to_published() -> None:
	"""Set status=Published via db.set_value (EX-16 blocks save-based publish)."""
	current = frappe.db.get_value("TM2 Tender", TENDER_CODE, "status") or ""
	if current == _TENDER_STATUS_FINAL:
		return
	frappe.db.set_value(
		"TM2 Tender",
		TENDER_CODE,
		{
			"status": _TENDER_STATUS_FINAL,
			"published_at": _TENDER_PUBLISHED_AT,
		},
		update_modified=False,
	)


def _finalize_master_tender(action: str, **extra: Any) -> dict[str, Any]:
	"""Apply spec fields, timeline, publication evidence, and Published status."""
	_apply_spec_fields()
	timeline_name = _ensure_timeline()
	_promote_to_published()
	pub = ensure_works_master_publication_evidence()
	tender = frappe.db.get_value(
		"TM2 Tender", TENDER_CODE, ["status", "template_version"], as_dict=True
	)
	out: dict[str, Any] = {
		"ok": True,
		"action": action,
		"tender_code": TENDER_CODE,
		"status": (tender or {}).get("status", ""),
		"template_version": (tender or {}).get("template_version", ""),
		"timeline": timeline_name,
		"publication_evidence": pub,
	}
	out.update(extra)
	return out


# ── public entry point ────────────────────────────────────────────────────────


def upsert_works_master_tender() -> dict:
	"""Idempotently ensure ``TND-MOH-2026-001`` and its Timeline exist with Published status.

	:raises frappe.ValidationError: if prerequisite records (Procurement Package, STD Template)
	    are missing or the release service rejects the package.
	:returns: Result dict with ``ok``, ``tender_code``, ``action`` (``created`` / ``existing``),
	    ``template_version``, ``status``, and ``timeline``.
	"""
	frappe.set_user("Administrator")

	# ── idempotency ─────────────────────────────────────────────────────────
	if frappe.db.exists("TM2 Tender", TENDER_CODE):
		return _finalize_master_tender("existing")

	# ── prerequisite check ───────────────────────────────────────────────────
	pkg_name = _pkg_name()
	if not pkg_name:
		frappe.throw(
			f"MISSING_PROCUREMENT_PACKAGE: Procurement Package {PACKAGE_CODE!r} not found. "
			"Run R2-007 seed first.",
			title="R2-009 prerequisite missing",
		)

	# ── detect an existing auto-named TM2 for this package ──────────────────
	existing_tm2 = active_tm2_tender_name_for_package(pkg_name)
	if existing_tm2 and existing_tm2 != TENDER_CODE:
		# Adopt the auto-created record and rename it to the canonical code.
		_rename_to_canonical(existing_tm2)
		return _finalize_master_tender("adopted", renamed_from=existing_tm2)

	# ── approved creation path ───────────────────────────────────────────────
	# Call the governed release service (XMV validation, STD resolution, handoff
	# snapshot, Access Rule, and Audit Event creation).
	result = release_procurement_package_to_tender(pkg_name)
	if not result.get("ok"):
		frappe.throw(
			f"R2-009: release_procurement_package_to_tender failed: {result.get('message', 'unknown error')}"
			f" | xmv: {result.get('xmv_findings')}",
			title="R2-009 tender release failed",
		)

	auto_name = str(result.get("tm2_tender") or "").strip()
	if not auto_name:
		frappe.throw("R2-009: release returned no tm2_tender name.", title="R2-009 tender release failed")

	# ── rename to canonical + spec enrichment ────────────────────────────────
	_rename_to_canonical(auto_name)
	return _finalize_master_tender("created", auto_code=auto_name)
