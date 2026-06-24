/** P5-005 — Workbench Create Package modal. */
(function () {
	frappe.provide("kentender_procurement");

	const CREATE_PACKAGE_API =
		"kentender_procurement.procurement_planning.api.planning_inclusion.create_pp_package_from_planning_inclusion";

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function businessContextHtml(opts) {
		const o = opts || {};
		const demandLabel = String(o.demand_name || "").trim() || "—";
		const planLabel = String(o.active_plan_name || "").trim() || "—";
		const categoryLabel = String(o.category_label || "").trim() || "—";
		const methodLabel = String(o.method_label || "").trim() || "—";
		const valueLabel = String(o.value_label || "").trim() || "—";
		const fundingLabel = String(o.funding_label || "").trim() || "—";
		return (
			'<div class="pp2-create-package-modal__context" data-testid="pp2-create-package-modal">' +
			'<div class="pp2-include-plan-modal__context-row"><span class="text-muted small">' +
			esc(__("Demand")) +
			'</span><div class="small" data-testid="pp2-create-package-demand">' +
			esc(demandLabel) +
			"</div></div>" +
			'<div class="pp2-include-plan-modal__context-row"><span class="text-muted small">' +
			esc(__("Active plan")) +
			'</span><div class="small" data-testid="pp2-create-package-active-plan">' +
			esc(planLabel) +
			"</div></div>" +
			'<div class="pp2-include-plan-modal__context-row"><span class="text-muted small">' +
			esc(__("Category")) +
			'</span><div class="small" data-testid="pp2-create-package-category">' +
			esc(categoryLabel) +
			"</div></div>" +
			'<div class="pp2-include-plan-modal__context-row"><span class="text-muted small">' +
			esc(__("Method")) +
			'</span><div class="small" data-testid="pp2-create-package-method">' +
			esc(methodLabel) +
			"</div></div>" +
			'<div class="pp2-include-plan-modal__context-row"><span class="text-muted small">' +
			esc(__("Estimated value")) +
			'</span><div class="small" data-testid="pp2-create-package-value">' +
			esc(valueLabel) +
			"</div></div>" +
			'<div class="pp2-include-plan-modal__context-row"><span class="text-muted small">' +
			esc(__("Funding")) +
			'</span><div class="small" data-testid="pp2-create-package-funding">' +
			esc(fundingLabel) +
			"</div></div></div>"
		);
	}

	function showDuplicatePackageDialog(opts) {
		const o = opts || {};
		const packageName = String(o.existing_package_name || "").trim();
		const dialog = new frappe.ui.Dialog({
			title: __("Package already exists"),
			fields: [
				{
					fieldtype: "HTML",
					fieldname: "duplicate_message",
					options:
						'<div class="pp2-create-package-modal__duplicate" data-testid="pp2-create-package-duplicate-dialog">' +
						'<p class="small mb-2" data-testid="pp2-create-package-blocker-message">' +
						esc(
							String(o.blocker_message || "").trim() ||
								__(
									"A procurement package already exists for this included demand. Open the existing package to continue."
								)
						) +
						"</p>" +
						(packageName
							? '<p class="small mb-0" data-testid="pp2-create-package-existing-package-name">' +
								esc(packageName) +
								"</p>"
							: "") +
						"</div>",
				},
			],
			primary_action_label: __("Open Package"),
			primary_action: function () {
				dialog.hide();
				if (typeof o.onOpenExistingPackage === "function") {
					o.onOpenExistingPackage(o);
				}
			},
		});
		dialog.show();
		const primaryBtn = dialog.get_primary_btn ? dialog.get_primary_btn() : null;
		if (primaryBtn && primaryBtn.attr) {
			primaryBtn.attr("data-testid", "pp2-open-existing-package");
		}
		return { opened: true, dialog: dialog };
	}

	function showCreatePackageBlocker(opts) {
		const o = opts || {};
		if (o.duplicate_package === true) {
			return showDuplicatePackageDialog(o);
		}
		frappe.msgprint({
			title: __("Unable to create package"),
			indicator: "orange",
			message:
				'<div data-testid="pp2-create-package-blocker-message">' +
				esc(
					String(o.blocker_message || "").trim() ||
						__("This demand is not ready for package creation.")
				) +
				"</div>",
		});
		return { opened: false };
	}

	function open(opts) {
		const o = opts || {};
		if (o.create_allowed === false) {
			return showCreatePackageBlocker(o);
		}
		const inclusionCode = String(o.inclusion_code || "").trim();
		if (!inclusionCode) {
			frappe.show_alert({
				indicator: "orange",
				message: __("Planning inclusion is missing for package creation."),
			});
			return { opened: false };
		}
		const defaultTitle = String(o.package_title_default || o.demand_name || "").trim();
		const dialog = new frappe.ui.Dialog({
			title: __("Create Package"),
			fields: [
				{
					fieldtype: "HTML",
					fieldname: "context",
					options: businessContextHtml(o),
				},
				{
					fieldtype: "Data",
					fieldname: "package_title",
					label: __("Package title"),
					reqd: 1,
					default: defaultTitle,
				},
				{
					fieldtype: "Data",
					fieldname: "inclusion_code_fallback",
					hidden: 1,
					default: inclusionCode,
				},
			],
			primary_action_label: __("Create Package"),
			primary_action: function (values) {
				const packageTitle = String((values && values.package_title) || defaultTitle || "").trim();
				if (!packageTitle) {
					frappe.show_alert({
						indicator: "orange",
						message: __("Enter a package title."),
					});
					return;
				}
				dialog.hide();
				dialog.set_primary_action(__("Creating..."), function () {});
				frappe.call({
					method: CREATE_PACKAGE_API,
					args: { inclusion_code: inclusionCode },
					callback: function (response) {
						const message = response && response.message ? response.message : {};
						if (!message || !message.ok) {
							frappe.msgprint({
								title: __("Unable to create package"),
								message:
									String((message && message.message) || "").trim() ||
									__("The package could not be created."),
								indicator: "orange",
							});
							dialog.set_primary_action(__("Create Package"), dialog.primary_action);
							return;
						}
						frappe.show_alert({
							indicator: "green",
							message: __("Package created."),
						});
						if (typeof o.onSuccess === "function") {
							o.onSuccess(message);
						}
					},
					error: function () {
						dialog.set_primary_action(__("Create Package"), dialog.primary_action);
					},
				});
			},
		});
		dialog.show();
		const titleField = dialog.fields_dict && dialog.fields_dict.package_title;
		if (titleField && titleField.$wrapper && titleField.$wrapper.attr) {
			titleField.$wrapper.attr("data-testid", "pp2-create-package-title-field");
		}
		if (titleField && titleField.$input && titleField.$input.attr) {
			titleField.$input.attr("data-testid", "pp2-create-package-title-input");
		}
		const primaryBtn = dialog.get_primary_btn ? dialog.get_primary_btn() : null;
		if (primaryBtn && primaryBtn.attr) {
			primaryBtn.attr("data-testid", "pp2-confirm-create-package");
		}
		return { opened: true, dialog: dialog };
	}

	kentender_procurement.PlanningCreatePackageModal = {
		open: open,
	};
})();
