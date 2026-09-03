"""Repoint the Departmental Need Decision task link at the module-local task.

NDS-CHG-001 v1.1 §4.4 gives Departmental Needs its own `Departmental Need
Review Task`. The decision record still carried a `workflow_task` Link to
`kentender_core`'s `Workflow Task`, left over from the reversed D3 decision;
it was never populated, because core's task engine enforces the capability
store that §6 and NDS-AC-044 prohibit.

Runs pre-model-sync so the orphaned column is gone before the new
`review_task` field is created.
"""

import frappe


def execute():
	table = "tabDepartmental Need Decision"
	if not frappe.db.table_exists("Departmental Need Decision"):
		return
	columns = {row.get("Field") or row.get("column_name") for row in frappe.db.sql(f"desc `{table}`", as_dict=True)}
	if "workflow_task" not in columns:
		return
	populated = frappe.db.sql(
		f"select count(*) from `{table}` where ifnull(workflow_task, '') != ''"
	)[0][0]
	if populated:
		# The field was always written as NULL. A populated row means an
		# unexpected write path exists, so stop rather than discard audit data.
		frappe.throw(
			f"{populated} Departmental Need Decision rows carry a workflow_task value; "
			"reconcile them before dropping the column."
		)
	frappe.db.sql(f"alter table `{table}` drop column `workflow_task`")
	frappe.db.delete("DocField", {"parent": "Departmental Need Decision", "fieldname": "workflow_task"})
