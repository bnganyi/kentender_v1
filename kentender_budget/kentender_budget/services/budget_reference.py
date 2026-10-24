# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""System-generated Budget / Budget Line / Revision references."""

from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.model.naming import make_autoname

from kentender_core.utils.series import raise_series_to
from kentender_strategy.services.strategy_reference import site_slug

BUD_REF_RE = re.compile(r"^[A-Z0-9]+-BUD-\d{4}$")
BL_REF_RE = re.compile(r"^[A-Z0-9]+-BL-\d{4}$")
BR_REF_RE = re.compile(r"^BR-[A-Z0-9]+-\d{4}$")


def _max_seq(doctype: str, field: str, prefix: str) -> int:
	if not frappe.db.has_column(doctype, field):
		return 0
	rows = frappe.db.sql(
		f"SELECT `{field}` FROM `tab{doctype}` WHERE `{field}` LIKE %s",
		(prefix + "%",),
	)
	max_seq = 0
	for (raw,) in rows:
		if not raw or not str(raw).startswith(prefix):
			continue
		tail = str(raw)[len(prefix) :]
		if tail.isdigit():
			max_seq = max(max_seq, int(tail))
	return max_seq


def _series_current(series_key: str) -> int | None:
	row = frappe.db.sql(
		"SELECT `current` FROM `tabSeries` WHERE `name`=%s",
		(series_key,),
	)
	return int(row[0][0]) if row else None


def _sync_series(prefix: str, current_max: int) -> None:
	"""Raise the never-reuse counter past the highest number in use. One atomic
	upsert (AUD-XC-130): the old read-then-insert let two concurrent first
	allocations both insert the counter."""
	raise_series_to(prefix, current_max)


def reset_unused_series(fiscal_year: str) -> list[str]:
	"""Canonical seed only: drop the never-reuse counter for the Budget and
	Budget Line prefixes when no record uses them any more, so a rebuilt
	canonical world numbers from 001/0001 again. A prefix still in use keeps
	its counter — no number is ever reissued while its record exists (the
	allocators above also sync the counter past any surviving row)."""
	slug = site_slug()
	start_year = frappe.db.get_value("Fiscal Year", fiscal_year, "year_start_date")
	prefixes = (
		("Procurement Budget", f"{slug}-BUD-{start_year.year if start_year else 0}-"),
		("Procurement Budget Line", f"{slug}-BL-"),
	)
	reset = []
	for doctype, prefix in prefixes:
		if not _max_seq(doctype, "generated_reference", prefix) and _series_current(prefix) is not None:
			frappe.db.sql("DELETE FROM `tabSeries` WHERE `name`=%s", (prefix,))
			reset.append(prefix)
	return reset


def allocate_budget_reference(fiscal_year: str) -> str:
	"""Allocate next never-reuse `{SITE}-BUD-{start_year}-###` for the FY
	(matches the BUD-CHG-001 v1.3 §15.3 seed ID pattern, e.g. `MOH-BUD-2027-001`).
	One site is one Procuring Entity — the prefix comes from the site's own
	configured entity, not a per-record PE."""
	slug = site_slug()
	start_year = frappe.db.get_value("Fiscal Year", fiscal_year, "year_start_date")
	start_year = start_year.year if start_year else 0
	prefix = f"{slug}-BUD-{start_year}-"
	_sync_series(prefix, _max_seq("Procurement Budget", "generated_reference", prefix))
	for _ in range(200):
		candidate = make_autoname(f"{prefix}.###")
		if not frappe.db.exists("Procurement Budget", {"generated_reference": candidate}):
			return candidate
	frappe.throw(_("Could not allocate a unique Budget reference"))


def _max_line_version_seq(prefix: str) -> int:
	"""The highest line number any Budget Line Version still carries (`{prefix}####-V#`). A Line Version can outlive its Line (a clean-up that
	removed the Line alone, found 18 October 2026), and its reference is unique, so its number is as much in use as the Line's own."""
	if not frappe.db.has_column("Procurement Budget Line Version", "generated_reference"):
		return 0
	rows = frappe.db.sql(
		"SELECT `generated_reference` FROM `tabProcurement Budget Line Version` WHERE `generated_reference` LIKE %s", (prefix + "%",)
	)
	max_seq = 0
	for (raw,) in rows:
		match = re.match(re.escape(prefix) + r"(\d+)-V\d+$", str(raw or ""))
		if match:
			max_seq = max(max_seq, int(match.group(1)))
	return max_seq


def allocate_budget_line_reference() -> str:
	"""Allocate next never-reuse `{SITE}-BL-####` (BUD-FR-020): a number is never reissued while a Line or a Line Version still carries it."""
	slug = site_slug()
	prefix = f"{slug}-BL-"
	_sync_series(prefix, max(_max_seq("Procurement Budget Line", "generated_reference", prefix), _max_line_version_seq(prefix)))
	for _ in range(200):
		candidate = make_autoname(f"{prefix}.####")
		if not frappe.db.exists("Procurement Budget Line", {"generated_reference": candidate}) and not frappe.db.exists(
			"Procurement Budget Line Version", {"generated_reference": ["like", candidate + "-V%"]}
		):
			return candidate
	frappe.throw(_("Could not allocate a unique Budget Line reference"))


def allocate_budget_version_reference(budget_reference: str, version_number: int) -> str:
	"""Deterministic `{budget_reference}-V{version_number}` (BUD-CHG-001 v1.2 §15.3
	seed IDs follow this exact pattern, e.g. `MOH-BUD-2027-001-V1`). No series
	needed — uniqueness follows directly from the already-sequential version_number."""
	return f"{budget_reference}-V{int(version_number)}"


def allocate_budget_line_version_reference(budget_line_reference: str, version_number: int) -> str:
	"""Deterministic `{budget_line_reference}-V{version_number}`."""
	return f"{budget_line_reference}-V{int(version_number)}"


def allocate_reservation_reference() -> str:
	"""Allocate next never-reuse `RSV-{SITE}-####` (BUD-UI-06 / Phase 5)."""
	slug = site_slug()
	prefix = f"RSV-{slug}-"
	_sync_series(prefix, _max_seq("Funding Reservation", "generated_reference", prefix))
	for _ in range(200):
		candidate = make_autoname(f"{prefix}.####")
		if not frappe.db.exists("Funding Reservation", {"generated_reference": candidate}):
			return candidate
	frappe.throw(_("Could not allocate a unique Funding Reservation reference"))


def allocate_commitment_reference() -> str:
	"""Allocate next never-reuse `COM-{SITE}-####` (BUD-CHG-001 §12 convert_reservation)."""
	slug = site_slug()
	prefix = f"COM-{slug}-"
	_sync_series(prefix, _max_seq("Procurement Commitment", "generated_reference", prefix))
	for _ in range(200):
		candidate = make_autoname(f"{prefix}.####")
		if not frappe.db.exists("Procurement Commitment", {"generated_reference": candidate}):
			return candidate
	frappe.throw(_("Could not allocate a unique Procurement Commitment reference"))


def allocate_correction_reference() -> str:
	"""Allocate next never-reuse `COR-{SITE}-####` (BUD-CHG-001 v1.13 proposal: a correction of a Closed commitment)."""
	slug = site_slug()
	prefix = f"COR-{slug}-"
	_sync_series(prefix, _max_seq("Commitment Correction", "generated_reference", prefix))
	for _ in range(200):
		candidate = make_autoname(f"{prefix}.####")
		if not frappe.db.exists("Commitment Correction", {"generated_reference": candidate}):
			return candidate
	frappe.throw(_("Could not allocate a unique Commitment Correction reference"))


def _allocate(doctype: str, code: str, label: str) -> str:
	slug = site_slug()
	prefix = f"{code}-{slug}-"
	_sync_series(prefix, _max_seq(doctype, "generated_reference", prefix))
	for _ in range(200):
		candidate = make_autoname(f"{prefix}.####")
		if not frappe.db.exists(doctype, {"generated_reference": candidate}):
			return candidate
	frappe.throw(_("Could not allocate a unique {0} reference").format(label))


def allocate_funding_request_reference() -> str:
	"""Allocate next never-reuse `CFR-{SITE}-####` (BUD-CHG-001 v1.16 §8.6: a contract funding request)."""
	return _allocate("Contract Funding Request", "CFR", "Contract Funding Request")


def allocate_entry_reference() -> str:
	"""Allocate next never-reuse `ECE-{SITE}-####` (BUD-CHG-001 v1.16 §4.12: an existing-contract commitment entry)."""
	return _allocate("Existing Contract Commitment Entry", "ECE", "Existing Contract Commitment Entry")
