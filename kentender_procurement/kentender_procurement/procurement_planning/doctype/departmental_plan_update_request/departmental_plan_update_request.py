# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Planner's request that one department update its accepted departmental plan because a budget line of the plan update is over its approved amount (owner decision 26 Sep 2026, the departmental correction route). The department decides whether to correct the estimate, change the requirement or mark it not proceeding, through the existing departmental plan update. Created only by RequestDepartmentalPlanUpdate; Answered when Procurement accepts that department's next update, Withdrawn when the plan update leaves preparation."""

from __future__ import annotations

from frappe.model.document import Document


class DepartmentalPlanUpdateRequest(Document):
	pass
