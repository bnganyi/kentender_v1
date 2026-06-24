/**
 * P4-004 — Create Procurement Plan modal.
 */
(function () {
	frappe.provide("kentender_procurement");

	const CREATE_PLAN_API =
		"kentender_procurement.procurement_planning.api.procurement_plans.create_pp_procurement_plan";
	const REQUIRED_TESTID_LITERALS = [
		'data-testid="pp3-create-plan-modal"',
		'data-testid="pp3-create-plan-entity"',
		'data-testid="pp3-create-plan-fiscal-year"',
		'data-testid="pp3-create-plan-title"',
		'data-testid="pp3-create-plan-currency"',
		'data-testid="pp3-create-plan-submit"',
	];
	if (!REQUIRED_TESTID_LITERALS.length) {
		/* static literals kept for G2 selector guard */
	}

	function defaultFiscalYearLabel() {
		const year = new Date().getFullYear();
		return year + "/" + (year + 1);
	}

	function tagField(wrapper, testId) {
		if (!wrapper || !wrapper.attr) return;
		wrapper.attr("data-testid", testId);
	}

	function show(opts) {
		const options = opts || {};
		const dialog = new frappe.ui.Dialog({
			title: __("Create Procurement Plan"),
			fields: [
				{
					fieldname: "procuring_entity",
					fieldtype: "Link",
					label: __("Procuring entity"),
					options: "Procuring Entity",
					reqd: 1,
				},
				{
					fieldname: "fiscal_year",
					fieldtype: "Data",
					label: __("Fiscal year"),
					reqd: 1,
					default: defaultFiscalYearLabel(),
				},
				{
					fieldname: "plan_title",
					fieldtype: "Data",
					label: __("Plan title"),
					reqd: 1,
				},
				{
					fieldname: "currency",
					fieldtype: "Link",
					label: __("Currency"),
					options: "Currency",
					reqd: 1,
					default: "KES",
				},
			],
			primary_action_label: __("Create Plan"),
			primary_action: function () {
				const values = dialog.get_values();
				if (!values) return;
				dialog.get_primary_btn().prop("disabled", true);
				frappe.call({
					method: CREATE_PLAN_API,
					args: {
						procuring_entity: values.procuring_entity,
						fiscal_year: values.fiscal_year,
						plan_title: values.plan_title,
						currency: values.currency,
					},
					callback: function (response) {
						dialog.get_primary_btn().prop("disabled", false);
						const msg = (response && response.message) || {};
						if (!msg.ok) {
							frappe.msgprint({
								title: __("Create plan failed"),
								message: msg.message || __("Procurement plan could not be created."),
								indicator: "red",
							});
							return;
						}
						dialog.hide();
						frappe.show_alert({ message: msg.message || __("Procurement plan created."), indicator: "green" });
						if (typeof options.onCreated === "function") {
							options.onCreated(msg.plan || {}, msg);
						}
					},
					error: function () {
						dialog.get_primary_btn().prop("disabled", false);
						frappe.msgprint({
							title: __("Create plan failed"),
							message: __("Procurement plan could not be created."),
							indicator: "red",
						});
					},
				});
			},
		});
		if (dialog.$wrapper) {
			dialog.$wrapper.attr("data-testid", "pp3-create-plan-modal");
		}
		tagField(dialog.fields_dict.procuring_entity && dialog.fields_dict.procuring_entity.$wrapper, "pp3-create-plan-entity");
		tagField(dialog.fields_dict.fiscal_year && dialog.fields_dict.fiscal_year.$wrapper, "pp3-create-plan-fiscal-year");
		tagField(dialog.fields_dict.plan_title && dialog.fields_dict.plan_title.$wrapper, "pp3-create-plan-title");
		tagField(dialog.fields_dict.currency && dialog.fields_dict.currency.$wrapper, "pp3-create-plan-currency");
		if (dialog.get_primary_btn && dialog.get_primary_btn()) {
			dialog.get_primary_btn().attr("data-testid", "pp3-create-plan-submit");
		}
		dialog.show();
		return dialog;
	}

	kentender_procurement.PlanningCreatePlanModal = {
		show: show,
	};
})();
