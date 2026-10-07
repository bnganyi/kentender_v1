# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin
from kentender_procurement.procurement_planning.write_family import PLANNING_WRITE_FAMILY


class PlanGovernanceDecision(CommandWriteGuardMixin, Document):
	command_write_family = PLANNING_WRITE_FAMILY
