"""Create Gate 01 authorization DocTypes through Frappe's standard lifecycle."""

from __future__ import annotations

import frappe


ADMIN_PERMISSIONS = [
	{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
	{"role": "Administrator", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
]


def _f(label: str, fieldname: str, fieldtype: str = "Data", **extra):
	return {"label": label, "fieldname": fieldname, "fieldtype": fieldtype, **extra}


SCHEMAS = [
	{
		"name": "Capability Profile",
		"autoname": "field:profile_id",
		"title_field": "profile_name",
		"fields": [
			_f("Profile ID", "profile_id", reqd=1, unique=1, search_index=1, in_list_view=1),
			_f("Profile Name", "profile_name", reqd=1, in_list_view=1),
			_f("Capabilities", "capabilities", "JSON", reqd=1),
			_f("Entity-wide Scope Permitted", "allows_entity_wide", "Check", default="0"),
			_f("Status", "status", "Select", options="Draft\nActive\nSuspended\nEnded", default="Draft", reqd=1, in_list_view=1),
			_f("Effective From", "effective_from", "Datetime"),
			_f("Effective To", "effective_to", "Datetime"),
			_f("Concurrency Token", "concurrency_token", read_only=1, reqd=1),
		],
	},
	{
		"name": "Operational Scope Assignment",
		"autoname": "field:assignment_id",
		"fields": [
			_f("Assignment ID", "assignment_id", reqd=1, unique=1, search_index=1, in_list_view=1),
			_f("User", "user_id", "Link", options="User", reqd=1, search_index=1, in_list_view=1),
			_f("Capability Profile", "capability_profile_id", "Link", options="Capability Profile", reqd=1, in_list_view=1),
			_f("Procuring Entity", "procuring_entity_id", "Link", options="Procuring Entity", reqd=1, search_index=1, in_list_view=1),
			_f("Organisation Unit", "organisation_unit_id", "Link", options="Organisation Unit", search_index=1),
			_f("Include Descendants", "include_descendants", "Check", default="0"),
			_f("Resource Scope Type", "resource_scope_type", "Link", options="DocType"),
			_f("Resource Scope ID", "resource_scope_id", "Dynamic Link", options="resource_scope_type"),
			_f("Effective From", "effective_from", "Datetime", reqd=1),
			_f("Effective To", "effective_to", "Datetime"),
			_f("Status", "status", "Select", options="Draft\nActive\nSuspended\nEnded", default="Draft", reqd=1, in_list_view=1),
			_f("Assigned By", "assigned_by", "Link", options="User", read_only=1),
			_f("Assigned At", "assigned_at", "Datetime", read_only=1),
			_f("Ended By", "ended_by", "Link", options="User", read_only=1),
			_f("Ended At", "ended_at", "Datetime", read_only=1),
			_f("End Reason", "end_reason", "Small Text"),
			_f("Concurrency Token", "concurrency_token", read_only=1, reqd=1),
		],
	},
	{
		"name": "Workflow Queue",
		"autoname": "field:queue_id",
		"title_field": "queue_name",
		"fields": [
			_f("Queue ID", "queue_id", reqd=1, unique=1, search_index=1, in_list_view=1),
			_f("Queue Name", "queue_name", reqd=1, in_list_view=1),
			_f("Module", "module_name", reqd=1),
			_f("Required Capability", "required_capability", reqd=1),
			_f("Procuring Entity", "procuring_entity_id", "Link", options="Procuring Entity", reqd=1, search_index=1),
			_f("Status", "status", "Select", options="Draft\nActive\nSuspended\nEnded", default="Draft", reqd=1, in_list_view=1),
			_f("Effective From", "effective_from", "Datetime", reqd=1),
			_f("Effective To", "effective_to", "Datetime"),
			_f("Concurrency Token", "concurrency_token", read_only=1, reqd=1),
		],
	},
	{
		"name": "Workflow Queue Membership",
		"autoname": "field:membership_id",
		"fields": [
			_f("Membership ID", "membership_id", reqd=1, unique=1, search_index=1),
			_f("Queue", "queue_id", "Link", options="Workflow Queue", reqd=1, in_list_view=1),
			_f("User", "user_id", "Link", options="User", reqd=1, search_index=1, in_list_view=1),
			_f("Effective From", "effective_from", "Datetime", reqd=1),
			_f("Effective To", "effective_to", "Datetime"),
			_f("Status", "status", "Select", options="Draft\nActive\nSuspended\nEnded", default="Draft", reqd=1, in_list_view=1),
			_f("Concurrency Token", "concurrency_token", read_only=1, reqd=1),
		],
	},
	{
		"name": "Workflow Routing Rule",
		"autoname": "field:routing_version_id",
		"fields": [
			_f("Routing Version ID", "routing_version_id", reqd=1, unique=1, search_index=1, in_list_view=1),
			_f("Routing Rule ID", "routing_rule_id", reqd=1, search_index=1, in_list_view=1),
			_f("Version", "version", "Int", reqd=1, in_list_view=1),
			_f("Module", "module_name", reqd=1),
			_f("Task Type", "task_type", reqd=1, search_index=1),
			_f("Procuring Entity", "procuring_entity_id", "Link", options="Procuring Entity", reqd=1, search_index=1),
			_f("Organisation Unit", "organisation_unit_id", "Link", options="Organisation Unit"),
			_f("Include Descendants", "include_descendants", "Check", default="0"),
			_f("Resource Scope Type", "resource_scope_type", "Link", options="DocType"),
			_f("Resource Scope ID", "resource_scope_id", "Dynamic Link", options="resource_scope_type"),
			_f("Required Capability", "required_capability", reqd=1),
			_f("Assignee Strategy", "assignee_strategy", "Select", options="Named user\nNamed claimable queue", reqd=1),
			_f("Assigned User", "assignee_user_id", "Link", options="User"),
			_f("Queue", "queue_id", "Link", options="Workflow Queue"),
			_f("Priority", "priority", "Int", default="100", reqd=1),
			_f("Effective From", "effective_from", "Datetime", reqd=1),
			_f("Effective To", "effective_to", "Datetime"),
			_f("Fallback Rule", "fallback_rule_id", "Data"),
			_f("Status", "status", "Select", options="Draft\nActive\nSuperseded\nEnded", default="Draft", reqd=1, in_list_view=1),
			_f("Approved By", "approved_by", "Link", options="User", read_only=1),
			_f("Approved At", "approved_at", "Datetime", read_only=1),
		],
	},
	{
		"name": "Workflow Task",
		"autoname": "field:task_id",
		"fields": [
			_f("Task ID", "task_id", reqd=1, unique=1, search_index=1, in_list_view=1),
			_f("Task Iteration", "task_iteration", "Int", default="1", reqd=1),
			_f("Module", "module_name", reqd=1),
			_f("Task Type", "task_type", reqd=1, search_index=1, in_list_view=1),
			_f("Subject Type", "subject_type", "Link", options="DocType", reqd=1),
			_f("Subject ID", "subject_id", "Dynamic Link", options="subject_type", reqd=1, search_index=1),
			_f("Related Record References", "related_record_refs", "JSON"),
			_f("Procuring Entity", "procuring_entity_id", "Link", options="Procuring Entity", reqd=1, search_index=1),
			_f("Financial Year", "financial_year_id", "Data", reqd=1, search_index=1),
			_f("Organisation Unit", "organisation_unit_id", "Link", options="Organisation Unit"),
			_f("Resource Scopes", "resource_scopes", "JSON"),
			_f("Routing Rule ID", "routing_rule_id", reqd=1),
			_f("Routing Rule Version", "routing_rule_version", "Int", reqd=1),
			_f("Assignee Type", "assignee_type", "Select", options="User\nQueue", reqd=1),
			_f("Assigned User", "assigned_user_id", "Link", options="User", search_index=1),
			_f("Queue", "queue_id", "Link", options="Workflow Queue", search_index=1),
			_f("Claimed By", "claimed_by", "Link", options="User", search_index=1),
			_f("Claimed At", "claimed_at", "Datetime"),
			_f("State", "state", "Select", options="Open\nCompleted\nReturned\nCancelled\nSuperseded\nStale", default="Open", reqd=1, in_list_view=1),
			_f("Predecessor Task", "predecessor_task_id", "Link", options="Workflow Task"),
			_f("Created By Actor", "created_by_actor", "Link", options="User", reqd=1),
			_f("Created At", "created_at", "Datetime", reqd=1),
			_f("Due At", "due_at", "Datetime"),
			_f("Concurrency Token", "concurrency_token", read_only=1, reqd=1),
			_f("Idempotency Key", "idempotency_key", unique=1, search_index=1, reqd=1),
		],
	},
	{
		"name": "Authorization Delegation",
		"autoname": "field:delegation_id",
		"fields": [
			_f("Delegation ID", "delegation_id", reqd=1, unique=1, search_index=1, in_list_view=1),
			_f("Delegator", "delegator_user_id", "Link", options="User", reqd=1),
			_f("Delegate", "delegate_user_id", "Link", options="User", reqd=1),
			_f("Capability Profile", "capability_profile_id", "Link", options="Capability Profile", reqd=1),
			_f("Procuring Entity", "procuring_entity_id", "Link", options="Procuring Entity", reqd=1),
			_f("Organisation Unit", "organisation_unit_id", "Link", options="Organisation Unit"),
			_f("Effective From", "effective_from", "Datetime", reqd=1),
			_f("Effective To", "effective_to", "Datetime", reqd=1),
			_f("Reason", "reason", "Small Text", reqd=1),
			_f("Status", "status", "Select", options="Scheduled\nActive\nEnded\nRevoked", default="Scheduled", reqd=1, in_list_view=1),
			_f("Approved By", "approved_by", "Link", options="User"),
			_f("Approved At", "approved_at", "Datetime"),
			_f("Concurrency Token", "concurrency_token", read_only=1, reqd=1),
		],
	},
	{
		"name": "Separation of Duties Rule",
		"autoname": "field:rule_id",
		"fields": [
			_f("Rule ID", "rule_id", reqd=1, unique=1, search_index=1, in_list_view=1),
			_f("Rule Name", "rule_name", reqd=1),
			_f("First Capability", "first_capability", reqd=1),
			_f("Second Capability", "second_capability", reqd=1),
			_f("Enforcement Level", "enforcement_level", "Select", options="Assignment\nWorkflow instance\nBoth", reqd=1),
			_f("Module", "module_name"),
			_f("Status", "status", "Select", options="Draft\nActive\nSuspended\nEnded", default="Draft", reqd=1, in_list_view=1),
			_f("Effective From", "effective_from", "Datetime", reqd=1),
			_f("Effective To", "effective_to", "Datetime"),
			_f("Approved By", "approved_by", "Link", options="User"),
			_f("Approved At", "approved_at", "Datetime"),
		],
	},
]


def generate() -> list[str]:
	"""Generate and export all Gate 01 DocTypes idempotently."""
	frappe.flags.allow_doctype_export = True
	created = []
	for schema in SCHEMAS:
		if frappe.db.exists("DocType", schema["name"]):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "DocType",
				"module": "Kentender Core",
				"custom": 0,
				"engine": "InnoDB",
				"track_changes": 1,
				"permissions": ADMIN_PERMISSIONS,
				**schema,
			}
		)
		doc.insert(ignore_permissions=True)
		created.append(doc.name)
	frappe.db.commit()
	return created
