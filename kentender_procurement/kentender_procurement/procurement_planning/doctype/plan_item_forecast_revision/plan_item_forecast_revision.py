# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §4.9A — append-only forecast revision log. Written only
by the cascade commands in services/schedule.py; never edited or deleted."""

import frappe
from frappe.model.document import Document


class PlanItemForecastRevision(Document):
	def validate(self):
		if not self.is_new():
			frappe.throw("A forecast revision is append-only.", title="PLN_STALE_WRITE")
		if not (20 <= len((self.reason or "").strip()) <= 500):
			frappe.throw("State why the forecast date is changing (20–500 characters).", title="PLN_FORECAST_REASON_REQUIRED")

	def on_trash(self):
		if not getattr(self.flags, "kt_fixture_purge", False):
			frappe.throw("A forecast revision is append-only.", title="PLN_STALE_WRITE")
