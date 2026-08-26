# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class STDCfgRuntimeManifest(Document):
	def validate(self):
		if frappe.db.exists(
			"STD Cfg Runtime Manifest",
			{
				"std_version_id": self.std_version_id,
				"manifest_type": self.manifest_type,
				"name": ["!=", self.name or ""],
			},
		):
			frappe.throw(
				_("A {0} manifest already exists for this Version").format(self.manifest_type),
				frappe.ValidationError,
			)
