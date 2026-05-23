// Budget metadata drawer — create/edit budget info without leaving workspace.

frappe.provide("kentender_budget.budget_metadata_drawer");

(function () {
	kentender_budget.budget_metadata_drawer = {
		openEdit(budgetName, onDone) {
			if (!budgetName) return;
			frappe.db.get_doc("Budget", budgetName).then(function (doc) {
				const d = new frappe.ui.Dialog({
					title: __("Edit Budget Info"),
					fields: [
						{
							fieldname: "budget_name",
							label: __("Budget name"),
							fieldtype: "Data",
							reqd: 1,
							default: doc.budget_name,
						},
						{
							fieldname: "strategic_plan",
							label: __("Strategic plan"),
							fieldtype: "Link",
							options: "Strategic Plan",
							reqd: 1,
							default: doc.strategic_plan,
						},
						{
							fieldname: "procuring_entity",
							label: __("Procuring entity"),
							fieldtype: "Link",
							options: "Procuring Entity",
							reqd: 1,
							default: doc.procuring_entity,
						},
						{
							fieldname: "fiscal_year",
							label: __("Fiscal year"),
							fieldtype: "Int",
							reqd: 1,
							default: doc.fiscal_year,
						},
						{
							fieldname: "currency",
							label: __("Currency"),
							fieldtype: "Link",
							options: "Currency",
							reqd: 1,
							default: doc.currency,
						},
						{
							fieldname: "total_budget_amount",
							label: __("Total budget amount"),
							fieldtype: "Currency",
							reqd: 1,
							default: doc.total_budget_amount,
						},
						{
							fieldname: "notes",
							label: __("Notes"),
							fieldtype: "Small Text",
							default: doc.notes || "",
						},
					],
					primary_action_label: __("Save"),
					primary_action: function (values) {
						frappe.call({
							method: "frappe.client.save",
							args: {
								doc: Object.assign({ doctype: "Budget", name: budgetName }, values),
							},
							callback: function () {
								d.hide();
								frappe.show_alert({ message: __("Budget updated"), indicator: "green" });
								document.dispatchEvent(new CustomEvent("kt-budget-panel-changed"));
								if (onDone) onDone();
							},
						});
					},
				});
				d.show();
			});
		},
	};
})();
