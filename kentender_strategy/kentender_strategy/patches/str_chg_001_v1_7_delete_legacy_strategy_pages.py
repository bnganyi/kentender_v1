# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.7 §10 — one Desk Page, `strategy`, carries every canonical
Strategy route (`/app/strategy`, `/app/strategy/plan/{plan_id}[/...]`,
`/app/strategy/approval/{plan_version_id}[/...]`). The three Phase 7 Pages
(`strategy-portfolio`, `strategy-plan-workspace`, `strategy-review-task`)
are replaced, not aliased (tracker rule 4): their JSON records and
controllers are gone from the app, and this patch removes the Page rows a
synced site still holds so the old routes fail closed instead of opening
an empty container.
"""

from __future__ import annotations

import frappe

LEGACY_PAGES = ("strategy-portfolio", "strategy-plan-workspace", "strategy-review-task")


def execute() -> None:
	for page in LEGACY_PAGES:
		frappe.db.delete("Has Role", {"parenttype": "Page", "parent": page})
		if frappe.db.exists("Page", page):
			frappe.delete_doc("Page", page, force=True, ignore_permissions=True)
	frappe.db.commit()
