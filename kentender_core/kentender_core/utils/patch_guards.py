# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Guards for one-shot destructive patches (AUD-XC-125, AUD-XC-127).

A patch that drops a doctype or empties a table was authorised for the dev
site, where "no production data exists" (owner, Aug-Sep 2026). A patch cannot
know which site it is running on, and Frappe runs every patch a site has not
logged: a restored backup or a rebuilt droplet would silently lose real rows.
These helpers make each such patch fail closed.

- `doctype_is_shipped` — a patch must never delete the DocType record of a
  doctype an installed app still ships.
- `require_empty_or_authorised` — refuse to destroy rows unless every listed
  table is empty (a fresh install) or the site owner has set
  `kt_allow_destructive_patches` in site_config.json for this migrate.
"""

from __future__ import annotations

import glob
import os
from collections.abc import Iterable

import frappe

SITE_FLAG = "kt_allow_destructive_patches"


def doctype_is_shipped(doctype: str) -> bool:
	"""True when any installed app still ships this DocType's definition."""
	scrubbed = frappe.scrub(doctype)
	for app in frappe.get_installed_apps():
		pattern = os.path.join(frappe.get_app_path(app), "*", "doctype", scrubbed, f"{scrubbed}.json")
		if glob.glob(pattern):
			return True
	return False


def row_counts(doctypes: Iterable[str]) -> dict[str, int]:
	"""Rows per doctype whose table exists (a missing table counts as nothing)."""
	counts: dict[str, int] = {}
	for doctype in doctypes:
		if frappe.db.table_exists(doctype):
			n = frappe.db.sql(f"select count(*) from `tab{doctype}`")[0][0]
			if n:
				counts[doctype] = int(n)
	return counts


def require_empty_or_authorised(patch: str, doctypes: Iterable[str]) -> None:
	"""Fail closed before a destructive patch touches rows it was not asked to lose."""
	counts = row_counts(doctypes)
	if not counts or frappe.conf.get(SITE_FLAG):
		return
	listed = ", ".join(f"{name} ({n})" for name, n in sorted(counts.items()))
	frappe.throw(
		f"{patch} would destroy rows on this site: {listed}. It was authorised only for a site that holds no "
		f"production data. If this is a development or test site, set \"{SITE_FLAG}\": 1 in its site_config.json "
		"and run migrate again; otherwise stop and review the rows first.",
		title="DESTRUCTIVE_PATCH_BLOCKED",
	)
