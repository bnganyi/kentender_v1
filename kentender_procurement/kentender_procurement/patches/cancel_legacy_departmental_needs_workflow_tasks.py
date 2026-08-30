"""Cancel legacy NDS Workflow Tasks stranded Open in My Work.

The pre-v1.1 Departmental Needs module routed reviews through kentender_core's
Workflow Task engine (`departmental_needs.*` task types). NDS-CHG-001 v1.1
replaced that with the role-assigned `Departmental Need Review Task`, but the
retirement left the old engine rows at state Open — surfacing dead
"Open task" rows in My Work for anyone operationally scoped to the PE (their
subject Needs no longer even exist). v1.1 never creates a
`departmental_needs.*` Workflow Task, so every one of them is legacy.
"""

from __future__ import annotations

import frappe


def execute():
	names = frappe.get_all(
		"Workflow Task",
		filters={"task_type": ["like", "departmental_needs.%"], "state": "Open"},
		pluck="name",
	)
	for name in names:
		frappe.db.set_value("Workflow Task", name, "state", "Cancelled", update_modified=False)
	if names:
		frappe.db.commit()
