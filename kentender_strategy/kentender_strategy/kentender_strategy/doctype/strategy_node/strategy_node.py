import frappe
from frappe import _
from frappe.model.document import Document


class StrategyNode(Document):
	def validate(self):
		self._validate_hierarchy()
		self._validate_target_fields()

	def _validate_hierarchy(self):
		pt = self.node_type
		parent = self.parent_strategy_node

		if pt == "Program":
			if parent:
				frappe.throw(_("Program must not have a parent node."))
		elif pt == "Objective":
			if not parent:
				frappe.throw(_("Objective must have a parent Program."))
			pdoc = frappe.get_doc("Strategy Node", parent)
			if pdoc.node_type != "Program":
				frappe.throw(_("Objective must be under a Program."))
			self._same_plan(pdoc)
		elif pt == "Target":
			if not parent:
				frappe.throw(_("Target must have a parent Objective."))
			pdoc = frappe.get_doc("Strategy Node", parent)
			if pdoc.node_type != "Objective":
				frappe.throw(_("Target must be under an Objective."))
			self._same_plan(pdoc)
		else:
			frappe.throw(_("Invalid node type."))

		if parent:
			pdoc = frappe.get_doc("Strategy Node", parent)
			self._same_plan(pdoc)

	def _same_plan(self, parent_doc):
		if self.strategic_plan != parent_doc.strategic_plan:
			frappe.throw(_("Parent and child must belong to the same Strategic Plan."))

	def _validate_target_fields(self):
		if self.node_type != "Target":
			self.target_year = None
			self.target_value = None
			self.target_unit = None

	def on_trash(self):
		if frappe.db.count("Strategy Node", {"parent_strategy_node": self.name}):
			frappe.throw(_("Delete child nodes first."))
