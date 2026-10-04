# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §4.6 (plan D2) — stable identity on the live canonical data.

post_model_sync, idempotent:
1. one `Plan Item` root per distinct `plan_item_id` carried by the per-Version
   `Annual Plan Item` rows, linked from every row; `scope_locked_since` /
   `first_authorised_requisition` from the earliest Active drawdown (§5.4.6);
2. `Departmental Plan Entry.direct_source_id` generated once per stable direct
   entry (`departmental_plan` + `entry_id`) and shared by every copy (§4.3);
3. `Plan Source Allocation.source_key` = `need:{need}` | `direct:{direct_source_id}`.
"""

from __future__ import annotations

import frappe


def execute() -> None:
	_plan_item_roots()
	_direct_source_ids()
	_source_keys()
	frappe.db.commit()


def _plan_item_roots() -> None:
	rows = frappe.db.sql(
		"""select i.plan_item_id, min(v.annual_plan) annual_plan
		from `tabAnnual Plan Item` i join `tabAnnual Plan Version` v on v.name = i.plan_version
		group by i.plan_item_id""",
		as_dict=True,
	)
	for row in rows:
		if not frappe.db.exists("Plan Item", row.plan_item_id):
			first = frappe.db.get_value(
				"Plan Drawdown Reference", {"plan_item_id": row.plan_item_id, "drawdown_state": "Active"},
				["creation", "requisition_reference"], order_by="creation asc", as_dict=True,
			)
			open_requests = frappe.db.count("Plan Item Correction Request", {"plan_item_id": row.plan_item_id, "status": ("in", ("Open", "In progress"))})
			frappe.get_doc({
				"doctype": "Plan Item", "plan_item_id": row.plan_item_id, "plan_item_reference": row.plan_item_id,
				"annual_plan": row.annual_plan, "scope_locked_since": first.creation if first else None,
				"first_authorised_requisition": first.requisition_reference if first else "",
				"authorisation_hold": 1 if open_requests else 0, "open_correction_requests": open_requests, "record_version": 0,
			}).db_insert()
		frappe.db.sql("update `tabAnnual Plan Item` set plan_item = %s where plan_item_id = %s and ifnull(plan_item, '') = ''", (row.plan_item_id, row.plan_item_id))


def _direct_source_ids() -> None:
	rows = frappe.db.sql(
		"""select e.name, e.entry_id, v.departmental_plan
		from `tabDepartmental Plan Entry` e join `tabDepartmental Plan Version` v on v.name = e.dpp_version
		where e.source_origin = 'Direct departmental requirement' and ifnull(e.direct_source_id, '') = ''
		order by e.creation""",
		as_dict=True,
	)
	by_stable: dict[tuple[str, str], str] = {}
	for row in rows:
		key = (row.departmental_plan, row.entry_id)
		if key not in by_stable:
			existing = frappe.db.sql(
				"""select e.direct_source_id from `tabDepartmental Plan Entry` e
				join `tabDepartmental Plan Version` v on v.name = e.dpp_version
				where v.departmental_plan = %s and e.entry_id = %s and ifnull(e.direct_source_id, '') != '' limit 1""",
				key,
			)
			by_stable[key] = existing[0][0] if existing else f"DSR-{frappe.generate_hash(length=10)}"
		frappe.db.set_value("Departmental Plan Entry", row.name, "direct_source_id", by_stable[key], update_modified=False)


def _source_keys() -> None:
	rows = frappe.db.sql(
		"""select a.name, a.need, e.direct_source_id
		from `tabPlan Source Allocation` a left join `tabDepartmental Plan Entry` e on e.name = a.dpp_entry
		where ifnull(a.source_key, '') = ''""",
		as_dict=True,
	)
	for row in rows:
		key = f"need:{row.need}" if row.need else (f"direct:{row.direct_source_id}" if row.direct_source_id else "")
		if key:
			frappe.db.set_value("Plan Source Allocation", row.name, "source_key", key, update_modified=False)
