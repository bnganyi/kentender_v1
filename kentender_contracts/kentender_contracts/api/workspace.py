# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Contracts workspace read (CM-CHG-001 v0.8 section 7 `GetContractWorkspace`, 9.0, 10.3; tracker CM8-315, plan Phase 4).

One read for the one Desk page. It answers either the workspace (the contracts the signed-in user may read, filtered and paged **after** the authority filter, drawn as D01 or D01-S) or the stable
denial as data (`workspace-forbidden`, drawn as D-DENIED), never an exception for a user who simply has no part in contracts. A failure is the caller's D-ERR."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_contracts.boards import listing


@frappe.whitelist()
def get_contract_workspace(page: int = 1, page_size: int = 10, view: str = "", search: str = "", status: str = "", source: str = "") -> dict[str, Any]:
	return listing.workspace(frappe.session.user, page=page, page_size=page_size, view=view, search=search, status=status, source=source)
