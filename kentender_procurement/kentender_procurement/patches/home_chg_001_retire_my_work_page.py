# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 (HOME6-0607, owner decision 5 Oct 2026) — retire the shared My Work Desk Page.

Home is the landing page and carries every kind of work My Work showed (Support issues and Supplier accounts joined
Home for that reason, FU-HOME-46). The Page's files are gone; this removes its database row so `/app/my-work` stops
answering. Frappe refuses to delete a standard Page outside developer mode unless a migrate is running (`in_migrate`),
and then removes the Page's own folder, which is already gone from the app. Existence-guarded and idempotent."""

from __future__ import annotations

import frappe

PAGE = "my-work"


def execute() -> None:
	if frappe.db.exists("Page", PAGE):
		in_migrate = frappe.flags.in_migrate
		frappe.flags.in_migrate = True
		try:
			frappe.delete_doc("Page", PAGE, force=True, ignore_permissions=True)
		finally:
			frappe.flags.in_migrate = in_migrate
		frappe.clear_cache()
	frappe.db.commit()
