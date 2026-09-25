# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.11 §4.10 — one Planning request to revise one Budget Line. A request and its outcome, never a revision: approved amounts change only through a successor Version (BUD-BR-028)."""

from __future__ import annotations

from frappe.model.document import Document


class BudgetRevisionRequest(Document):
	pass
