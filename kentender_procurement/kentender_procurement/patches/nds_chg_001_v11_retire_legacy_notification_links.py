"""Delete Notification Log rows that deep-link to the retired NDS routes.

`nds_chg_001_v11_retire_legacy_pages` removed the four pre-v1.1 Desk pages.
Notifications the old module had already sent outlived them: their `link` still
points at `/app/departmental-needs-{new,edit,review,detail}?need=…`, so the row
renders in the user's activity list and resolves to nothing when clicked.

§17 forbids a compatibility redirect, and NDS-BR-020 forbids any legacy route
surviving in a live surface, so the rows go rather than being rewritten onto
the canonical `/app/departmental-needs/{need_reference}`. Rewriting would also
be wrong on the facts: the identifiers they carry (NDS-MOH-2026-000n, and one
malformed NDS-MOH-2027-002) belong to fixtures the rebuild deleted, so the
canonical route would 404 just the same.

Only the query-string form is matched. The canonical route is
`/app/departmental-needs/…` with no `-` after "needs", so a `-` immediately
after the prefix is what distinguishes a retired page from a live Need.

Runs post-model-sync: it edits Notification Log rows, not schema.
"""

import frappe

LEGACY_LINK_PATTERN = "/app/departmental-needs-%"


def execute():
	rows = frappe.db.get_all(
		"Notification Log",
		filters={"link": ("like", LEGACY_LINK_PATTERN)},
		pluck="name",
	)
	if not rows:
		return
	for name in rows:
		frappe.delete_doc(
			"Notification Log",
			name,
			force=True,
			ignore_permissions=True,
			delete_permanently=True,
		)
	print(f"Removed {len(rows)} Notification Log rows linking to retired Departmental Needs pages")
