frappe.ui.form.on("Budget", {
	refresh(frm) {
		applyCreateLayout(frm);
		mountBudgetShellHeader(frm);
		addSaveAndContinueButton(frm);
	},

	validate(frm) {
		if (!frm.is_new()) {
			return;
		}
		const amount = frm.doc.total_budget_amount;
		if (amount === null || amount === undefined || amount === "") {
			frappe.throw(__("Total Budget Amount is required."));
		}
		if (Number.isNaN(Number(amount))) {
			frappe.throw(__("Total Budget Amount must be numeric."));
		}
	},
});

function applyCreateLayout(frm) {
	const isNew = frm.is_new();
	frm.set_df_property("total_budget_amount", "reqd", 1);

	const createCoreFields = [
		"budget_name",
		"procuring_entity",
		"fiscal_year",
		"strategic_plan",
		"currency",
		"total_budget_amount",
	];
	const createHiddenFields = [
		"section_status",
		"status",
		"section_rejection",
		"rejection_reason",
		"column_break_rejection",
		"rejected_by",
		"rejected_at",
		"version_no",
		"is_current_version",
		"supersedes_budget",
		"created_by",
		"order_index",
	];

	if (isNew) {
		createHiddenFields.forEach((f) => frm.toggle_display(f, false));
		createCoreFields.forEach((f) => frm.toggle_display(f, true));
	} else {
		createHiddenFields.forEach((f) => frm.toggle_display(f, true));
	}
}

function addSaveAndContinueButton(frm) {
	if (!frm.is_new()) {
		return;
	}
	if (frm.__saveAndContinueButtonBound) {
		return;
	}
	frm.__saveAndContinueButtonBound = true;
	const btn = frm.add_custom_button(__("Save and Continue"), async function () {
		const amount = frm.doc.total_budget_amount;
		if (amount === null || amount === undefined || amount === "" || Number.isNaN(Number(amount))) {
			frappe.throw(__("Enter a valid Total Budget Amount before continuing."));
		}

		// Transient flag consumed by Budget.after_insert for redirect response.
		frm.doc.save_and_continue = 1;
		await frm.save();
		// Client-side fallback/primary UX for B2.1 flow.
		if (frm.doc.name) {
			if (typeof kentender_core !== "undefined" && kentender_core.kt_nav) {
				kentender_core.kt_nav.toBuilder("budget", frm.doc.name);
			} else {
				frappe.set_route("budget-builder", frm.doc.name);
			}
		}
	});
	$(btn).removeClass("btn-default").addClass("btn-primary");
}

function mountBudgetShellHeader(frm) {
	$(frm.wrapper).find(".kt-budget-module-shell-host").remove();
	const $page = $(frm.wrapper).find(".form-layout .form-page").first();
	if (!$page.length) {
		return;
	}
	const $host = $('<div class="kt-budget-module-shell-host mb-2"></div>');
	$page.prepend($host);
	if (
		typeof kentender_core !== "undefined" &&
		kentender_core.kt_shell &&
		kentender_core.kt_nav
	) {
		if (typeof kentender_core.kt_nav.ensureSidebar === "function") {
			kentender_core.kt_nav.ensureSidebar("budget");
		}
		kentender_core.kt_shell.mountHeader($host, {
			moduleId: "budget",
			recordTitle: frm.is_new() ? __("New Budget") : frm.doc.budget_name || frm.doc.name,
			taskLabel: frm.is_new() ? __("Create Budget") : kentender_core.kt_nav.taskLabel("budget", "form"),
		});
	}
}
