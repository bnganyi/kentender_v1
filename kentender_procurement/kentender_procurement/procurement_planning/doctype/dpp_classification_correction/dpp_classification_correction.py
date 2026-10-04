# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.23 §4.4 — `DPPClassificationCorrection`.

Immutable, append-only evidence. A correction never edits the accepted
departmental decision, the certified source facts or any existing Plan
Version; it appends a superseding classification and shifts only the
effective-classification projection used for new Planning work.
"""

from frappe.model.document import Document

from kentender_procurement.procurement_planning.errors import fail


class DPPClassificationCorrection(Document):
	def on_update(self) -> None:
		if not self.is_new() and self.get_doc_before_save():
			fail(
				"PLN_BASELINE_LOCKED",
				"A recorded classification correction cannot be edited. Record a further correction instead.",
			)

	def on_trash(self) -> None:
		fail(
			"PLN_BASELINE_LOCKED",
			"A recorded classification correction cannot be deleted.",
		)
