# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Rendered pages of an opened bid (BOP-CHG-001 v0.10 §4: "Raw bid contents
remain in governed package storage"; plan D5).

The pages exist only after a lawful reveal, for the committee's review and
signing. They are kept under the site's private folder, outside every
DocType and File record, and reached only through Bid Opening's own guarded
read. The package bytes themselves are never stored by Bid Opening."""

from __future__ import annotations

import hashlib
import os

import frappe

FOLDER = "kt_bop_renders"


def _path(entry_id: str) -> str:
	safe = "".join(c for c in entry_id if c.isalnum() or c in "-_")
	return frappe.get_site_path("private", FOLDER, f"{safe}.pdf")


def save(entry_id: str, pdf: bytes) -> str:
	os.makedirs(frappe.get_site_path("private", FOLDER), exist_ok=True)
	path = _path(entry_id)
	with open(path + ".tmp", "wb") as fh:
		fh.write(pdf)
	os.replace(path + ".tmp", path)
	return hashlib.sha256(pdf).hexdigest()


def read(entry_id: str) -> bytes | None:
	path = _path(entry_id)
	if not os.path.exists(path):
		return None
	with open(path, "rb") as fh:
		return fh.read()


def remove(entry_ids: list[str]) -> int:
	removed = 0
	for entry_id in entry_ids:
		if os.path.exists(_path(entry_id)):
			os.remove(_path(entry_id))
			removed += 1
	return removed
