# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Contracts workspace read (CM-CHG-001 v0.8 §7 `GetContractWorkspace`, §9.0, §10.3; tracker CM8-315).

One read for the one Desk page. It answers either the workspace (the contracts the signed-in user may read, counted and paged **after** the authority filter) or the
stable denial as data (`workspace-forbidden`, drawn as D-DENIED), never an exception for a user who simply has no part in contracts. A failure is the caller's D-ERR."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_contracts.services import audience, reads


@frappe.whitelist()
def get_contract_workspace(page: int = 1, page_size: int = 20) -> dict[str, Any]:
	user = frappe.session.user
	audiences = audience.workspace_audiences(user)
	if not audiences:
		return {"ok": True, "screen": "workspace-forbidden"}
	listed = reads.page(user, frappe.get_all("Contract Case", pluck="name", order_by="creation desc"), number=int(page), size=int(page_size))
	return {"ok": True, "screen": "workspace", "audiences": audiences, **listed}
