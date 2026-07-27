# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Organization / bidder party isolation helpers."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_MANIFEST_VERSION,
	DT_WORKSPACE,
)


def assert_org_party_match(
	*,
	organization: str,
	bidder_party: str,
	row_organization: str,
	row_bidder_party: str,
) -> None:
	if organization != row_organization or bidder_party != row_bidder_party:
		frappe.throw(
			_("Tenant isolation violation for organization/bidder party."),
			title="BWMF_ISOLATION_VIOLATION",
		)


def scoped_filters(organization: str, bidder_party: str) -> dict[str, str]:
	return {"organization": organization, "bidder_party": bidder_party}


def assert_workspace_tenant(
	*,
	workspace: str,
	organization: str,
	bidder_party: str,
) -> dict[str, Any]:
	row = frappe.db.get_value(
		DT_WORKSPACE,
		workspace,
		["name", "organization", "bidder_party", "workspace_id", "published_tender_ref"],
		as_dict=True,
	)
	if not row:
		frappe.throw(_("Unknown BWMF workspace."), title="BWMF_WORKSPACE_NOT_FOUND")
	assert_org_party_match(
		organization=organization,
		bidder_party=bidder_party,
		row_organization=row.organization,
		row_bidder_party=row.bidder_party,
	)
	return row


def assert_manifest_in_org_scope(*, manifest_name: str, organization: str | None = None) -> dict[str, Any]:
	"""Load manifest; reject missing. Organization cross-check is via workspace/published tender callers."""
	row = frappe.db.get_value(
		DT_MANIFEST_VERSION,
		manifest_name,
		["name", "manifest_id", "manifest_version", "payload_digest", "lifecycle_state", "published_tender_ref"],
		as_dict=True,
	)
	if not row:
		frappe.throw(_("Unknown BWMF manifest version."), title="BWMF_MANIFEST_NOT_FOUND")
	return row


def assert_same_workspace_manifest_binding(
	*,
	workspace: str,
	manifest_name: str,
) -> None:
	"""Reject cross-workspace / unbound manifest use when an active binding exists for another manifest."""
	active = frappe.db.get_value(
		"BWMF Workspace Manifest Binding",
		{"workspace": workspace, "is_active": 1},
		["manifest_doc", "organization", "bidder_party"],
		as_dict=True,
	)
	if active and active.manifest_doc and active.manifest_doc != manifest_name:
		frappe.throw(
			_("Manifest is not the active binding for this workspace."),
			title="BWMF_CROSS_MANIFEST_LINK",
		)


def assert_row_org_party(
	*,
	doctype: str,
	name: str,
	organization: str,
	bidder_party: str,
) -> None:
	row = frappe.db.get_value(doctype, name, ["organization", "bidder_party"], as_dict=True)
	if not row:
		frappe.throw(_("Missing {0} reference.").format(doctype), title="BWMF_REF_MISSING")
	assert_org_party_match(
		organization=organization,
		bidder_party=bidder_party,
		row_organization=row.organization,
		row_bidder_party=row.bidder_party,
	)
