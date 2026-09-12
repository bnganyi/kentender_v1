# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.1.4 / §7.3 — the accepted departmental disposition
of one exact Need revision in one exact departmental Submission
(`NeedPlanningDispositionChanged.v1`), projected here as Planning
information. Separate from `Need Planning Usage Projection`: it changes
neither the Need's lifecycle nor its Active-plan usage."""

from __future__ import annotations

from frappe.model.document import Document


class NeedPlanningDispositionProjection(Document):
	pass
