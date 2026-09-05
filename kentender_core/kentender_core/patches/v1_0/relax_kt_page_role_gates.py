"""KT-STD-001 v1.2 §3A — a page-load denial must resolve to the module's own
inline Forbidden panel, never the framework's stock permission modal.

Every affected Page's own fixture JSON already ships with an empty `roles`
list, but Frappe's doctype/page sync is additive only for standard-doc child
tables: it inserts rows a fixture adds, it never deletes rows a fixture
removed. A site that had already synced the old, restrictive `roles` list
(the state of every KenTender site through 2026-09-05) keeps those `Has
Role` rows forever unless something explicitly deletes them — which is
exactly what stopped the Vue app from ever mounting for a user who held none
of them, producing the "Not permitted" popup this change unit exists to fix.

One-time, idempotent: deletes the live `Has Role` rows for these six Pages
regardless of what they contain. Each page's own service layer is the real
authorization gate now (see the corresponding `*_ui_contracts.py` /
`*_authorization.py` / `*_permissions.py` / `site_configuration.py` changes
landed in the same change).
"""

from __future__ import annotations

import frappe

_PAGES = (
	"procurement-planning",
	"strategy-portfolio",
	"budget-funding",
	"departmental-needs",
	"system-setup",
	"reference-data",
)


def execute() -> None:
	frappe.db.delete("Has Role", {"parenttype": "Page", "parent": ("in", _PAGES)})
