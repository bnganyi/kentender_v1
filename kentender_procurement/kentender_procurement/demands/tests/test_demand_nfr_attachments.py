# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-NFR-007 — file ACL, private metadata; malware noted when infra absent."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.demands.api import (
	get_demand_form,
	remove_demand_attachment_form,
)
from kentender_procurement.demands.seeds.kentender_mvp_v1 import upsert_county_draft_demand
from kentender_procurement.demands.services.demand_permissions import (
	ERR_SCOPE,
	ROLE_REQUESTER,
	ensure_demand_roles,
)
from kentender_procurement.demands.tests._ac_helpers import create_draft, ensure_user


class TestDemandNfrAttachments(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_nfr007_private_metadata_and_cross_scope_deny(self) -> None:
		"""DIA-NFR-007 — private File metadata; MOH cannot touch county attachment."""
		moh = ensure_user(
			"dem-nfr007-moh@example.com",
			[ROLE_REQUESTER],
			pe=C.PE_MOH,
			ou=C.OU_DIR_DHP,
		)
		name = create_draft(moh, estimate=1000, title="NFR007 attachment demand")
		file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "nfr007-support.txt",
				"is_private": 1,
				"content": "nfr007 private attachment",
				"attached_to_doctype": "Demand",
				"attached_to_name": name,
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()

		frappe.set_user(moh)
		loaded = get_demand_form(demand=name)
		atts = loaded["demand"].get("attachments") or []
		self.assertEqual(len(atts), 1)
		self.assertEqual(atts[0]["is_private"], 1)
		self.assertEqual(atts[0]["file_name"], "nfr007-support.txt")
		self.assertTrue(atts[0].get("creation"))
		self.assertIn("id", atts[0])

		# County Draft attachment — MOH denied by Demand scope.
		frappe.set_user("Administrator")
		county = upsert_county_draft_demand(commit=False)
		county_file = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "county-secret.txt",
				"is_private": 1,
				"content": "county only",
				"attached_to_doctype": "Demand",
				"attached_to_name": county["demand"],
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()

		frappe.set_user(moh)
		with self.assertRaises(frappe.PermissionError) as ctx:
			remove_demand_attachment_form(
				demand=county["demand"], file_id=county_file.name
			)
		self.assertIn(ERR_SCOPE, str(ctx.exception))
		self.assertTrue(frappe.db.exists("File", county_file.name))

		# Wrong file id on owned Demand → scope denial.
		with self.assertRaises(frappe.PermissionError) as ctx2:
			remove_demand_attachment_form(demand=name, file_id=county_file.name)
		self.assertIn(ERR_SCOPE, str(ctx2.exception))

		# Malware: infrastructure not present — no scanner hook wired for Demands.
		self.assertFalse(bool(frappe.get_hooks("demand_attachment_malware_scan")))
