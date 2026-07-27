# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Optimistic concurrency for BWMF response versions."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_RESPONSE_VERSION,
)


def assert_expected_response_version(response_id: str, expected_version: int) -> None:
	"""Raise if the latest version for response_id is not expected_version."""
	latest = frappe.db.sql(
		"""
		select version from `tabBWMF Response Version`
		where response_id=%s
		order by version desc
		limit 1
		""",
		(response_id,),
	)
	current = int(latest[0][0]) if latest else 0
	if current != int(expected_version):
		frappe.throw(
			_("Optimistic concurrency conflict for response {0}: expected version {1}, found {2}.").format(
				response_id, expected_version, current
			),
			title="BWMF_CONCURRENCY_CONFLICT",
		)


def next_response_version(response_id: str) -> int:
	latest = frappe.db.sql(
		"""
		select coalesce(max(version), 0) from `tabBWMF Response Version`
		where response_id=%s
		""",
		(response_id,),
	)
	return int(latest[0][0]) + 1
