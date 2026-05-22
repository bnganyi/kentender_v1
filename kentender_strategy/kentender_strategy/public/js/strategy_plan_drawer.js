// Plan metadata drawer — create/edit without leaving workspace.

frappe.provide("kentender_strategy.strategy_plan_drawer");

(function () {
	function openDrawer(title, fields, onSave) {
		const d = new frappe.ui.Dialog({
			title: title,
			fields: fields,
			primary_action_label: __("Save"),
			primary_action(values) {
				onSave(values, d);
			},
		});
		d.show();
		return d;
	}

	kentender_strategy.strategy_plan_drawer = {
		openCreate(onDone) {
			openDrawer(__("New Strategic Plan"), [
				{ fieldname: "strategic_plan_name", fieldtype: "Data", label: __("Plan name"), reqd: 1 },
				{ fieldname: "procuring_entity", fieldtype: "Link", options: "Procuring Entity", label: __("Entity"), reqd: 1 },
				{ fieldname: "start_year", fieldtype: "Int", label: __("Start year"), reqd: 1, default: new Date().getFullYear() },
				{ fieldname: "end_year", fieldtype: "Int", label: __("End year"), reqd: 1, default: new Date().getFullYear() + 4 },
				{ fieldname: "description", fieldtype: "Small Text", label: __("Description") },
			], function (values, d) {
				frappe.call({
					method: "kentender_strategy.api.workspace.create_strategic_plan",
					args: { data: values },
					callback(r) {
						d.hide();
						const name = r.message && r.message.name;
						if (name && onDone) onDone(name);
						frappe.show_alert({ message: __("Plan created"), indicator: "green" });
					},
				});
			});
		},

		openEdit(planName, onDone) {
			frappe.db.get_doc("Strategic Plan", planName).then(function (doc) {
				openDrawer(__("Edit Plan Info"), [
					{ fieldname: "strategic_plan_name", fieldtype: "Data", label: __("Plan name"), reqd: 1, default: doc.strategic_plan_name },
					{ fieldname: "procuring_entity", fieldtype: "Link", options: "Procuring Entity", label: __("Entity"), reqd: 1, default: doc.procuring_entity },
					{ fieldname: "start_year", fieldtype: "Int", label: __("Start year"), reqd: 1, default: doc.start_year },
					{ fieldname: "end_year", fieldtype: "Int", label: __("End year"), reqd: 1, default: doc.end_year },
					{ fieldname: "description", fieldtype: "Small Text", label: __("Description"), default: doc.description },
				], function (values, d) {
					frappe.call({
						method: "kentender_strategy.api.workspace.update_strategic_plan_metadata",
						args: { plan_name: planName, data: values },
						callback() {
							d.hide();
							if (onDone) onDone();
							frappe.show_alert({ message: __("Plan updated"), indicator: "green" });
						},
					});
				});
			});
		},
	};
})();
