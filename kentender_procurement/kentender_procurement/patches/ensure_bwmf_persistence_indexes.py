# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Composite unique indexes and lookup indexes for BWMF persistence (Phase 2B)."""

from __future__ import annotations

import frappe


def execute() -> None:
	# Uniqueness / versioned identity
	_add_unique("tabBWMF Manifest Version", "uniq_bwmf_manifest_id_version", "(manifest_id, manifest_version)")
	_add_unique("tabBWMF Response Version", "uniq_bwmf_response_id_version", "(response_id, version)")
	_add_unique(
		"tabBWMF Evidence Version",
		"uniq_bwmf_evidence_item_version",
		"(evidence_item, version)",
	)
	_add_unique(
		"tabBWMF Idempotency Record",
		"uniq_bwmf_idempotency_org_op_key",
		"(organization, operation, idempotency_key)",
	)

	# content_digest is NOT globally unique (identical bytes may be referenced by many items/orgs).
	_drop_index_if_exists("tabBWMF Evidence Version", "content_digest")
	_add_index("tabBWMF Evidence Version", "idx_bwmf_evidence_content_digest", "(content_digest)")

	# Practical lookup indexes
	_add_index(
		"tabBWMF Response Version",
		"idx_bwmf_response_lookup",
		"(workspace, section_key, task_ref, scope_ref, response_id)",
	)
	_add_index("tabBWMF Evidence Link", "idx_bwmf_evidence_link_ws_task", "(workspace, task_ref, evidence_version)")
	_add_index(
		"tabBWMF Validation Finding",
		"idx_bwmf_validation_finding_snap",
		"(parent, rule_code, severity)",
	)
	_add_index(
		"tabBWMF Manifest Resource",
		"idx_bwmf_manifest_resource_lookup",
		"(manifest_version, resource_type, resource_id)",
	)
	_add_index(
		"tabBWMF Workspace Manifest Binding",
		"idx_bwmf_workspace_active",
		"(workspace, is_active)",
	)
	_add_index("tabBWMF Audit Event", "idx_bwmf_audit_org_type_at", "(organization, event_type, event_at)")

	# Drop legacy single-column unique on submission/compile idempotency if present
	_drop_index_if_exists("tabBWMF Submission", "idempotency_key")
	_drop_index_if_exists("tabBWMF Compile Request", "idempotency_key")
	_drop_index_if_exists("tabBWMF Compile Run", "idempotency_key")

	# Phase 2B: remove disposable workspace money sample column if present
	try:
		frappe.db.sql_ddl("alter table `tabBWMF Workspace` drop column `amount_sample`")
	except Exception:
		pass

	# Phase 2 lifecycle alignment: drop legacy workspace.state if present (canonical field is status)
	try:
		frappe.db.sql_ddl("alter table `tabBWMF Workspace` drop column `state`")
	except Exception:
		pass


def _index_exists(table: str, index_name: str) -> bool:
	return bool(
		frappe.db.sql(
			"""
			select 1 from information_schema.statistics
			where table_schema = database() and table_name=%s and index_name=%s
			limit 1
			""",
			(table, index_name),
		)
	)


def _add_unique(table: str, index_name: str, columns: str) -> None:
	if _index_exists(table, index_name):
		return
	try:
		frappe.db.sql_ddl(f"alter table `{table}` add unique index `{index_name}` {columns}")
	except Exception:
		frappe.log_error(title=f"BWMF unique index {index_name}")


def _add_index(table: str, index_name: str, columns: str) -> None:
	if _index_exists(table, index_name):
		return
	try:
		frappe.db.sql_ddl(f"create index `{index_name}` on `{table}` {columns}")
	except Exception:
		frappe.log_error(title=f"BWMF index {index_name}")


def _drop_index_if_exists(table: str, index_name: str) -> None:
	if not _index_exists(table, index_name):
		return
	try:
		frappe.db.sql_ddl(f"alter table `{table}` drop index `{index_name}`")
	except Exception:
		frappe.log_error(title=f"BWMF drop index {index_name}")
