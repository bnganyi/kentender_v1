# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.9 §4.4A — one row of the effective-dated regulator reference
register. Rows are owned by their parent `Regulatory Reference` version and are
never edited in place (CFG-BR-015)."""

from frappe.model.document import Document


class RegulatoryReservationCategory(Document):
	pass
