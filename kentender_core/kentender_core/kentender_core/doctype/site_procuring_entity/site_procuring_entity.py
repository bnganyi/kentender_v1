# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.6 §4.1 — the site's one Procuring Entity.

A Frappe Single, so singularity is structural: a fixture, a direct insert or a
second create command cannot produce a second entity, because there is no
table to insert into. Because a Single cannot be the target of a Link, legal
provenance on issued evidence records is a name-and-code snapshot, never a
foreign key — a later rename does not rewrite history.

The controller enforces only the record-local invariants (code format and
immutability); the first-run transaction that also creates the root
Organisation Unit lives in ``services/site_configuration.py``.
"""

from __future__ import annotations

import re

import frappe
from frappe.model.document import Document

PE_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]{2,19}$")


class SiteProcuringEntity(Document):
	def validate(self):
		self.pe_code = (self.pe_code or "").strip().upper()
		self.pe_name = " ".join((self.pe_name or "").split())

		if not PE_CODE_PATTERN.fullmatch(self.pe_code):
			frappe.throw(
				"Enter an uppercase entity code of 3–20 letters, digits or hyphens.",
				title="CFG_PE_INVALID",
			)
		if not (2 <= len(self.pe_name) <= 200):
			frappe.throw(
				"Enter the entity's official legal name (2–200 characters).",
				title="CFG_PE_INVALID",
			)
		if not (self.timezone or "").strip():
			self.timezone = "Africa/Nairobi"
		# CFG-BR-014 — a route is required and has no None value. A record
		# configured before v0.9 derives one from its entity type on first save
		# rather than failing every later descriptive edit.
		from kentender_core.services.site_configuration import STATUTORY_APPROVAL_ROUTES, _valid_route

		route = (self.get("statutory_approval_route") or "").strip()
		if route and route not in STATUTORY_APPROVAL_ROUTES:
			frappe.throw("Select the statutory approval route.", title="CFG_PE_INVALID")
		if not route:
			self.statutory_approval_route = _valid_route("", self.pe_type)

		# CFG-BR-002 — pe_code is immutable after first save, on every path
		# including a direct API or fixture write, not only the UI command.
		stored = frappe.db.get_single_value("Site Procuring Entity", "pe_code")
		if stored and stored != self.pe_code:
			frappe.throw(
				"The Procuring Entity code cannot be changed after it is set.",
				title="CFG_PE_CODE_IMMUTABLE",
			)
