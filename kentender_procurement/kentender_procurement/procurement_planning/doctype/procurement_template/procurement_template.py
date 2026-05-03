# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint
from frappe.utils.data import parse_json

VALID_METHODS = frozenset(
	("Open Tender", "Restricted Tender", "RFQ", "RFP", "Direct Procurement")
)
VALID_CONTRACT_TYPES = frozenset(("Fixed Price", "Cost Reimbursable", "T&M"))
COMPETITIVE_METHODS = frozenset(("Open Tender", "Restricted Tender", "RFQ", "RFP"))
VALID_REQUISITION_TYPES = frozenset(("Goods", "Works", "Services"))
VALID_DEMAND_TYPES = frozenset(("Planned", "Unplanned", "Emergency"))


class ProcurementTemplate(Document):
	def validate(self):
		self._set_defaults()
		self._validate_template_code_unique()
		self._validate_profile_links()
		self._validate_canonical_selects()
		self._validate_default_std_template()
		self._validate_applicable_lists()
		self._validate_allowed_methods()
		self._validate_grouping_strategy()
		self._validate_threshold_rules()
		self._validate_competitive_decision_profile()
		self._validate_schedule_ints()

	def _set_defaults(self):
		if self.is_active is None:
			self.is_active = 1
		if self.override_requires_justification is None:
			self.override_requires_justification = 1
		if self.high_risk_escalation_required is None:
			self.high_risk_escalation_required = 0

	def _validate_template_code_unique(self):
		if not self.template_code:
			return
		filters = {"template_code": self.template_code}
		if not self.is_new():
			filters["name"] = ("!=", self.name)
		if frappe.db.exists("Procurement Template", filters):
			frappe.throw(_("Template Code must be unique."), title=_("Duplicate template code"))

	def _validate_profile_links(self):
		for field, label, doctype in (
			("risk_profile_id", _("Risk Profile"), "Risk Profile"),
			("kpi_profile_id", _("KPI Profile"), "KPI Profile"),
			("vendor_management_profile_id", _("Vendor Management Profile"), "Vendor Management Profile"),
		):
			if not self.get(field):
				frappe.throw(_("{0} is required.").format(label), title=_("Missing profile"))
			if not frappe.db.exists(doctype, self.get(field)):
				frappe.throw(_("{0} is not valid.").format(label), title=_("Invalid profile"))
		if self.decision_criteria_profile_id and not frappe.db.exists(
			"Decision Criteria Profile", self.decision_criteria_profile_id
		):
			frappe.throw(_("Invalid Decision Criteria Profile."), title=_("Invalid profile"))

	def _validate_canonical_selects(self):
		if self.default_method not in VALID_METHODS:
			frappe.throw(
				_("Default Method must be one of: {0}.").format(", ".join(sorted(VALID_METHODS))),
				title=_("Invalid method"),
			)
		if self.default_contract_type not in VALID_CONTRACT_TYPES:
			frappe.throw(
				_("Default Contract Type must be one of: Fixed Price, Cost Reimbursable, T&M."),
				title=_("Invalid contract type"),
			)

	def _validate_default_std_template(self):
		if not self.default_std_template:
			return
		if not frappe.db.exists("STD Template", self.default_std_template):
			frappe.throw(
				_("Default STD Template is not valid."),
				title=_("Invalid STD template"),
			)

	def _parse_list_field(self, raw, label):
		if raw in (None, ""):
			frappe.throw(_("{0} is required.").format(label), title=_("Invalid applicability"))
		parsed = parse_json(raw) if isinstance(raw, str) else raw
		if not isinstance(parsed, list):
			frappe.throw(_("{0} must be a JSON list.").format(label), title=_("Invalid applicability"))
		return parsed

	def _validate_applicable_lists(self):
		req_types = self._parse_list_field(self.applicable_requisition_types, _("Applicable Requisition Types"))
		for item in req_types:
			if item not in VALID_REQUISITION_TYPES:
				frappe.throw(
					_("Invalid requisition type: {0}. Allowed: Goods, Works, Services.").format(item),
					title=_("Invalid applicability"),
				)
		demand_types = self._parse_list_field(self.applicable_demand_types, _("Applicable Demand Types"))
		for item in demand_types:
			if item not in VALID_DEMAND_TYPES:
				frappe.throw(
					_("Invalid demand type: {0}. Allowed: Planned, Unplanned, Emergency.").format(item),
					title=_("Invalid applicability"),
				)

	def _validate_allowed_methods(self):
		raw = self.allowed_methods
		if raw in (None, ""):
			return
		parsed = parse_json(raw) if isinstance(raw, str) else raw
		if not isinstance(parsed, list):
			frappe.throw(_("Allowed Methods must be a JSON list."), title=_("Invalid allowed methods"))
		for m in parsed:
			if m not in VALID_METHODS:
				frappe.throw(
					_("Invalid allowed method: {0}.").format(m),
					title=_("Invalid allowed methods"),
				)
		if parsed and self.default_method not in parsed:
			frappe.throw(
				_("Default Method must be included in Allowed Methods when Allowed Methods is set."),
				title=_("Invalid allowed methods"),
			)

	def _validate_grouping_strategy(self):
		raw = self.grouping_strategy
		if raw in (None, ""):
			frappe.throw(_("Grouping Strategy is required."), title=_("Invalid grouping"))
		parsed = parse_json(raw) if isinstance(raw, str) else raw
		if not isinstance(parsed, dict):
			frappe.throw(_("Grouping Strategy must be a JSON object."), title=_("Invalid grouping"))
		gb = parsed.get("group_by")
		if gb is not None:
			if not isinstance(gb, list):
				frappe.throw(_('Grouping Strategy "group_by" must be a list.'), title=_("Invalid grouping"))
			for key in gb:
				if not isinstance(key, str) or not key.strip():
					frappe.throw(
						_('Grouping Strategy "group_by" entries must be non-empty strings.'),
						title=_("Invalid grouping"),
					)

	def _validate_threshold_rules(self):
		raw = self.threshold_rules
		if raw in (None, ""):
			return
		parsed = parse_json(raw) if isinstance(raw, str) else raw
		if not isinstance(parsed, (dict, list)):
			frappe.throw(_("Threshold Rules must be a JSON object or list."), title=_("Invalid thresholds"))

	def _validate_competitive_decision_profile(self):
		if self.default_method in COMPETITIVE_METHODS and not self.decision_criteria_profile_id:
			frappe.throw(
				_(
					"Decision Criteria Profile is required when Default Method is competitive "
					"(Open Tender, Restricted Tender, RFQ, RFP)."
				),
				title=_("Missing decision criteria"),
			)

	def _validate_schedule_ints(self):
		for field in ("planning_lead_days", "procurement_cycle_days"):
			val = self.get(field)
			if val is None or val == "":
				continue
			iv = cint(val)
			if iv < 0:
				frappe.throw(
					_("{0} cannot be negative.").format(self.meta.get_label(field)),
					title=_("Invalid schedule"),
				)
			self.set(field, iv)
