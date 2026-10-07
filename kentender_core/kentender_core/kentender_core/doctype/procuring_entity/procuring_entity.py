# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class ProcuringEntity(Document):
	def validate(self):
		self._require_single_entity_over_http()
		if not (self.legal_name or "").strip() and (self.entity_name or "").strip():
			self.legal_name = self.entity_name
		if not (self.entity_name or "").strip() and (self.legal_name or "").strip():
			self.entity_name = self.legal_name
		if not (self.entity_reference or "").strip():
			self.entity_reference = make_autoname("PE-.########")
		if not self.status:
			self.status = "Active"

	def _require_single_entity_over_http(self) -> None:
		"""AUD-XC-017 / RG-07: one site, one Procuring Entity (AUTH-ADR-001 §19). The rule used to live only in
		`reference_data_api`, so `POST /api/resource/Procuring Entity` (or the Desk form) skipped it. A new
		entity arriving over HTTP is checked here whatever route it took; seeds, patches and in-process
		fixtures are not requests and keep using their own services."""
		if not self.is_new() or getattr(frappe.local, "request", None) is None:
			return
		from kentender_core.services.reference_data_transitions import require_single_entity

		require_single_entity(self.entity_code or self.name or "")
