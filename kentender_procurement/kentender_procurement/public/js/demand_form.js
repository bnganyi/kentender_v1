// Demand Form — DIA builder: E1 shell, E2 layout, E3 Basic+Items, E4 Strategy/Budget, E5 Delivery/Exceptions/Workflow/Closure, E6 full lock + save validation.

frappe.provide("kentender_procurement.dia_demand_form");

(function () {
	if (frappe._kt_dia_budget_line_formatter) {
		return;
	}
	frappe._kt_dia_budget_line_formatter = true;
	frappe.form.link_formatters = frappe.form.link_formatters || {};
	function _fromCache(doctype, value) {
		const cache = frappe._kt_link_display_cache && frappe._kt_link_display_cache[doctype];
		return cache && cache[value] ? cache[value] : null;
	}
	function _registerFormatter(doctype) {
		frappe.form.link_formatters[doctype] = function (value) {
			if (!value) {
				return "";
			}
			return _fromCache(doctype, value) || value;
		};
	}
	_registerFormatter("Budget Line");
	_registerFormatter("Procuring Department");
	_registerFormatter("Procuring Entity");
	_registerFormatter("Strategic Plan");
	_registerFormatter("Strategy Program");
	_registerFormatter("Sub Program");
	_registerFormatter("Strategy Objective");
	_registerFormatter("Strategy Target");
	_registerFormatter("Budget");
	_registerFormatter("Funding Source");
	frappe.form.link_formatters["Budget Line"] = function (value) {
		if (!value) {
			return "";
		}
		if (frappe._kt_budget_line_link_cache && frappe._kt_budget_line_link_cache[value]) {
			return frappe._kt_budget_line_link_cache[value];
		}
		return value;
	};
})();

kentender_procurement.dia_demand_form = (function () {
	let diaNavGuardBound = false;

	function routeToDiaWorkspace() {
		if (typeof frappe !== "undefined" && typeof frappe.set_route === "function") {
			frappe.set_route("Workspaces", "Demand Intake and Approval");
		}
	}

	function isNativeDemandListHref(href) {
		if (!href) {
			return false;
		}
		const h = String(href).toLowerCase();
		return (
			h === "/desk/demand" ||
			h === "/app/demand" ||
			h.indexOf("#list/demand") >= 0 ||
			h.indexOf("/desk/demand?") >= 0 ||
			h.indexOf("/app/demand?") >= 0
		);
	}

	function bindDiaFormNavGuard() {
		if (diaNavGuardBound || typeof window === "undefined" || !window.jQuery) {
			return;
		}
		diaNavGuardBound = true;
		window.jQuery(document).on("click.ktDiaDemandNav", "a", function (ev) {
			try {
				if (!frappe || !frappe.get_route) {
					return;
				}
				const rt = frappe.get_route() || [];
				if (!(rt[0] === "Form" && rt[1] === "Demand")) {
					return;
				}
				const a = ev.currentTarget;
				const href = (a && a.getAttribute && a.getAttribute("href")) || "";
				if (!isNativeDemandListHref(href)) {
					return;
				}
				ev.preventDefault();
				ev.stopPropagation();
				routeToDiaWorkspace();
			} catch (e) {
				/* ignore */
			}
		});
	}

	function applyStrictDiaNavGuard() {
		try {
			if (!frappe || !frappe.get_route) {
				return;
			}
			const rt = frappe.get_route() || [];
			if (!(rt[0] === "Form" && rt[1] === "Demand")) {
				return;
			}
			if (typeof window === "undefined" || !window.jQuery) {
				return;
			}
			const $ = window.jQuery;
			$("a").each(function () {
				const href = (this.getAttribute && this.getAttribute("href")) || "";
				if (!isNativeDemandListHref(href)) {
					return;
				}
				const $a = $(this);
				$a.attr("data-dia-guarded", "1");
				$a.attr("title", __("Use DIA workspace navigation."));
				$a.css({
					opacity: "0.45",
					pointerEvents: "none",
					cursor: "not-allowed",
				});
				if ($a.closest(".breadcrumb-item, .breadcrumb").length) {
					$a.hide();
				}
			});
		} catch (e) {
			/* ignore */
		}
	}

	const SKIP_FIELD_TYPES = new Set([
		"Section Break",
		"Column Break",
		"Tab Break",
		"HTML",
		"Button",
		"Heading",
	]);

	const BASIC_REQUEST_FIELDS = [
		"title",
		"procuring_entity",
		"requesting_department",
		"request_date",
		"required_by_date",
		"priority_level",
		"demand_type",
		"requisition_type",
	];

	const JUSTIFICATION_FIELDS = ["beneficiary_summary", "specification_summary"];

	const DERIVED_STRATEGY_FIELDS = [
		"strategic_plan",
		"program",
		"sub_program",
		"output_indicator",
		"performance_target",
	];

	const BUDGET_SNAPSHOT_FIELDS = [
		"budget",
		"funding_source",
		"reservation_status",
		"reservation_reference",
		"available_budget_at_check",
		"budget_check_datetime",
	];

	const DELIVERY_FIELDS = ["delivery_location", "requested_delivery_period_days"];

	const EXCEPTION_FIELDS = ["impact_if_not_procured", "emergency_justification"];

	const WORKFLOW_BUILDER_READ_ONLY_FIELDS = ["status", "planning_status", "reservation_status"];

	function cint(v) {
		if (frappe.utils && typeof frappe.utils.cint === "function") {
			return frappe.utils.cint(v);
		}
		const n = parseInt(v, 10);
		return Number.isFinite(n) ? n : 0;
	}

	function flt(v, precision) {
		if (frappe.utils && typeof frappe.utils.flt === "function") {
			return frappe.utils.flt(v, precision);
		}
		const n = parseFloat(v);
		return Number.isFinite(n) ? n : 0;
	}

	function basicItemsEditable(frm) {
		if (frm.is_new()) {
			return true;
		}
		const s = frm.doc.status;
		return s === "Draft" || s === "Rejected";
	}

	function applyE5ConditionalVisibility(frm) {
		const dt = frm.doc.demand_type;
		const planned = dt === "Planned";
		const emergency = dt === "Emergency";
		frm.set_df_property("impact_if_not_procured", "hidden", planned ? 1 : 0);
		frm.set_df_property("emergency_justification", "hidden", emergency ? 0 : 1);
		frm.set_df_property("is_exception", "hidden", planned ? 1 : 0);
		tagExceptionSection(frm, emergency, planned);
	}

	function applyE6LockAllFields(frm) {
		const fields = frm.meta && frm.meta.fields ? frm.meta.fields : [];
		let i;
		for (i = 0; i < fields.length; i++) {
			const df = fields[i];
			if (!df || !df.fieldname) {
				continue;
			}
			if (SKIP_FIELD_TYPES.has(df.fieldtype)) {
				continue;
			}
			if (df.fieldtype === "Table") {
				frm.set_df_property(df.fieldname, "read_only", 1);
				continue;
			}
			frm.set_df_property(df.fieldname, "read_only", 1);
		}
	}

	function applyE6RestoreFromMeta(frm) {
		const fields = frm.meta && frm.meta.fields ? frm.meta.fields : [];
		let i;
		for (i = 0; i < fields.length; i++) {
			const df = fields[i];
			if (!df || !df.fieldname) {
				continue;
			}
			if (SKIP_FIELD_TYPES.has(df.fieldtype)) {
				continue;
			}
			const ro = df.read_only ? 1 : 0;
			frm.set_df_property(df.fieldname, "read_only", ro);
		}
	}

	function applyE5WorkflowBuilderLocks(frm) {
		let i;
		for (i = 0; i < WORKFLOW_BUILDER_READ_ONLY_FIELDS.length; i++) {
			frm.set_df_property(WORKFLOW_BUILDER_READ_ONLY_FIELDS[i], "read_only", 1);
		}
	}

	function tagE5WorkflowWrappers(frm) {
		let i;
		for (i = 0; i < WORKFLOW_BUILDER_READ_ONLY_FIELDS.length; i++) {
			const name = WORKFLOW_BUILDER_READ_ONLY_FIELDS[i];
			const fd = frm.fields_dict[name];
			if (fd && fd.$wrapper) {
				fd.$wrapper.closest(".form-group").addClass("kt-dia-e5-workflow-field");
			}
		}
	}

	function cacheBudgetLineDisplay(lineId, d) {
		if (!lineId || !d) {
			return;
		}
		if (!frappe._kt_budget_line_link_cache) {
			frappe._kt_budget_line_link_cache = {};
		}
		const name = d.budget_line_name ? String(d.budget_line_name).trim() : "";
		const code = d.budget_line_code ? String(d.budget_line_code).trim() : "";
		let dis = name;
		if (name && code) {
			dis = name + " (" + code + ")";
		} else if (code) {
			dis = code;
		}
		if (dis) {
			frappe._kt_budget_line_link_cache[lineId] = dis;
		}
	}

	function cacheLinkDisplay(doctype, id, name, code) {
		if (!doctype || !id) {
			return;
		}
		if (!frappe._kt_link_display_cache) {
			frappe._kt_link_display_cache = {};
		}
		if (!frappe._kt_link_display_cache[doctype]) {
			frappe._kt_link_display_cache[doctype] = {};
		}
		const n = (name || "").trim();
		const c = (code || "").trim();
		let display = n || c;
		if (n && c && n !== c) {
			display = n + " (" + c + ")";
		}
		if (!display) {
			display = id;
		}
		frappe._kt_link_display_cache[doctype][id] = display;
	}

	function cacheLinkDisplaysFromContext(d) {
		if (!d) {
			return;
		}
		cacheLinkDisplay("Procuring Entity", d.procuring_entity, d.procuring_entity_name, d.procuring_entity_code);
		cacheLinkDisplay("Strategic Plan", d.strategic_plan, d.strategic_plan_name, d.strategic_plan_code);
		cacheLinkDisplay("Strategy Program", d.program, d.program_title, d.program_code);
		cacheLinkDisplay("Sub Program", d.sub_program, d.sub_program_title, d.sub_program_code);
		cacheLinkDisplay(
			"Strategy Objective",
			d.output_indicator,
			d.output_indicator_title,
			d.output_indicator_code
		);
		cacheLinkDisplay(
			"Strategy Target",
			d.performance_target,
			d.performance_target_title,
			d.performance_target_code
		);
		cacheLinkDisplay("Budget", d.budget, d.budget_name, d.budget_code);
		cacheLinkDisplay(
			"Funding Source",
			d.funding_source,
			d.funding_source_title,
			d.funding_source_code
		);
	}

	function formatCurrencyish(val, currency) {
		try {
			if (typeof frappe !== "undefined" && frappe.format) {
				return frappe.format(val, { fieldtype: "Currency", options: currency || undefined });
			}
		} catch (e) {
			/* ignore */
		}
		return String(val);
	}

	function updateBudgetDecisionStrip(frm) {
		if (frm._dia_strip_timer) {
			clearTimeout(frm._dia_strip_timer);
			frm._dia_strip_timer = null;
		}
		frm._dia_strip_timer = setTimeout(function () {
			frm._dia_strip_timer = null;
			updateBudgetDecisionStripRun(frm);
		}, 200);
	}

	function updateBudgetDecisionStripRun(frm) {
		const $el = frm._dia_budget_strip;
		if (!$el || !$el.length) {
			return;
		}
		if (!isBasicItemsEditable(frm)) {
			$el.hide().empty();
			return;
		}
		const bl = frm.doc.budget_line;
		const amt = flt(frm.doc.total_amount);
		if (!bl || amt <= 0) {
			$el
				.html(
					'<span class="text-muted small">' +
						__("Add line items and pick a budget line to compare requested value with available budget.") +
						"</span>"
				)
				.show();
			return;
		}
		$el.html(
			'<span class="text-muted small">' + __("Checking budget…") + "</span>"
		);
		$el.show();
		frappe.call({
			method: "kentender_budget.api.dia_budget_control.check_available_budget",
			args: { budget_line_id: bl, amount: amt },
			callback: function (r) {
				const msg = r && r.message;
				if (!msg || !msg.ok || !msg.data) {
					$el.html(
						'<span class="text-warning small">' + __("Could not check budget. Save and retry if this persists.") + "</span>"
					);
					return;
				}
				const b = msg.data;
				const cur = b.currency || (frm._dia_bl_ctx && frm._dia_bl_ctx.currency) || "";
				const rq = formatCurrencyish(amt, cur);
				const av = formatCurrencyish(flt(b.amount_available), cur);
				let h =
					'<span class="kt-dia-budget-strip__ok">' +
					__("Requested") +
					": " +
					rq +
					" · " +
					__("available") +
					": " +
					av +
					"</span> ";
				if (b.is_sufficient === false) {
					const sh = formatCurrencyish(flt(b.shortfall), cur);
					h +=
						'<span class="text-danger">' +
						__("Over available balance by") +
						" " +
						sh +
						". " +
						__("A formal reservation is only created on finance approval.") +
						"</span>";
				} else {
					h +=
						'<span class="text-muted small">' + __("A formal reservation is created on finance approval when applicable.") + "</span>";
				}
				$el.html(h);
			},
		});
	}

	function tagDiaFormChrome(frm) {
		const t = frm.fields_dict && frm.fields_dict.total_amount;
		if (t && t.$wrapper) {
			t.$wrapper.addClass("kt-dia-total-derived-summary");
		}
	}

	function tagExceptionSection(frm, emergency, planned) {
		const fd = frm.fields_dict && frm.fields_dict.is_exception;
		if (!fd || !fd.$wrapper) {
			return;
		}
		const $fs = fd.$wrapper.closest(".form-section, .form-dashboard-section");
		$fs.removeClass("kt-dia-exception-block kt-dia-exception-block--hot");
		if (planned) {
			return;
		}
		$fs.addClass("kt-dia-exception-block");
		if (emergency) {
			$fs.addClass("kt-dia-exception-block--hot");
		}
	}

	function applyBuilderFieldPermissions(frm) {
		applyE5ConditionalVisibility(frm);
		const hasShell = !!frm._dia_builder_shell;
		if (hasShell) {
			frm.set_df_property("status", "hidden", 1);
			frm.set_df_property("planning_status", "hidden", 1);
		} else {
			frm.set_df_property("status", "hidden", 0);
			frm.set_df_property("planning_status", "hidden", 0);
		}
		const locked = !basicItemsEditable(frm);
		let i;

		if (locked) {
			applyE6LockAllFields(frm);
			if (!frm.is_new() && typeof frm.disable_save === "function") {
				frm.disable_save();
			}
		} else {
			if (typeof frm.enable_save === "function") {
				frm.enable_save();
			}
			applyE6RestoreFromMeta(frm);
			applyE5WorkflowBuilderLocks(frm);

			const alwaysRo = DERIVED_STRATEGY_FIELDS.concat(BUDGET_SNAPSHOT_FIELDS);
			for (i = 0; i < alwaysRo.length; i++) {
				frm.set_df_property(alwaysRo[i], "read_only", 1);
			}

			for (i = 0; i < BASIC_REQUEST_FIELDS.length; i++) {
				frm.set_df_property(BASIC_REQUEST_FIELDS[i], "read_only", 0);
			}
			frm.set_df_property("items", "read_only", 0);

			for (i = 0; i < JUSTIFICATION_FIELDS.length; i++) {
				frm.set_df_property(JUSTIFICATION_FIELDS[i], "read_only", 0);
			}
			frm.set_df_property("budget_line", "read_only", 0);

			for (i = 0; i < DELIVERY_FIELDS.length; i++) {
				frm.set_df_property(DELIVERY_FIELDS[i], "read_only", 0);
			}
			for (i = 0; i < EXCEPTION_FIELDS.length; i++) {
				frm.set_df_property(EXCEPTION_FIELDS[i], "read_only", 0);
			}
		}

		tagE4DerivedWrappers(frm);
		tagE5WorkflowWrappers(frm);
		tagDiaFormChrome(frm);
	}

	function tagE4DerivedWrappers(frm) {
		let i;
		for (i = 0; i < DERIVED_STRATEGY_FIELDS.length; i++) {
			const name = DERIVED_STRATEGY_FIELDS[i];
			const fd = frm.fields_dict[name];
			if (fd && fd.$wrapper) {
				fd.$wrapper.closest(".form-group").addClass("kt-dia-e4-derived-trace");
			}
		}
	}

	function clearBudgetLineDerivatives(frm) {
		frm._dia_bl_ctx = null;
		const clears = [
			"budget",
			"funding_source",
			"strategic_plan",
			"program",
			"sub_program",
			"output_indicator",
			"performance_target",
		];
		let i;
		for (i = 0; i < clears.length; i++) {
			frm.set_value(clears[i], null);
		}
	}

	function suppressBudgetLineHandler(frm, fn) {
		frm._dia_suppress_budget_line_sync = true;
		try {
			fn();
		} finally {
			setTimeout(function () {
				frm._dia_suppress_budget_line_sync = false;
			}, 0);
		}
	}

	function fetchBudgetLineContextIntoForm(frm) {
		const bl = frm.doc.budget_line;
		if (!bl) {
			frm._dia_bl_ctx = null;
			updateBudgetDecisionStrip(frm);
			return;
		}
		frappe.call({
			method: "kentender_budget.api.dia_budget_control.get_budget_line_context",
			args: { budget_line_id: bl },
			callback: function (r) {
				const msg = r && r.message;
				if (!msg || !msg.ok || !msg.data) {
					const err = (msg && msg.message) || __("Could not load budget line.");
					frappe.msgprint({ title: __("Budget line"), message: err, indicator: "orange" });
					suppressBudgetLineHandler(frm, function () {
						clearBudgetLineDerivatives(frm);
						frm.set_value("budget_line", "");
					});
					return;
				}
				const d = msg.data;
				if (frm.doc.procuring_entity && d.procuring_entity && frm.doc.procuring_entity !== d.procuring_entity) {
					frappe.msgprint({
						title: __("Budget line"),
						message: __(
							"This budget line belongs to a different procuring entity. Choose a line for the same entity as on this demand."
						),
						indicator: "red",
					});
					suppressBudgetLineHandler(frm, function () {
						clearBudgetLineDerivatives(frm);
						frm.set_value("budget_line", "");
					});
					return;
				}
				frm.set_value("budget", d.budget || null);
				frm.set_value("funding_source", d.funding_source || null);
				frm.set_value("strategic_plan", d.strategic_plan || null);
				frm.set_value("program", d.program || null);
				frm.set_value("sub_program", d.sub_program || null);
				frm.set_value("output_indicator", d.output_indicator || null);
				frm.set_value("performance_target", d.performance_target || null);
				frm._dia_bl_ctx = d;
				cacheBudgetLineDisplay(bl, d);
				cacheLinkDisplaysFromContext(d);
				try {
					if (frm.fields_dict.budget_line) {
						frm.fields_dict.budget_line.refresh();
					}
					[
						"procuring_entity",
						"strategic_plan",
						"program",
						"sub_program",
						"output_indicator",
						"performance_target",
						"budget",
						"funding_source",
					].forEach(function (fname) {
						if (frm.fields_dict[fname] && typeof frm.fields_dict[fname].refresh === "function") {
							frm.fields_dict[fname].refresh();
						}
					});
				} catch (e2) {
					/* ignore */
				}
				updateBudgetDecisionStrip(frm);
			},
		});
	}

	function recalcDemandFinancials(frm) {
		const rows = frm.doc.items || [];
		let sum = 0;
		for (let i = 0; i < rows.length; i++) {
			const r = rows[i];
			if (!r || !r.name) {
				continue;
			}
			const lt = flt(r.quantity) * flt(r.estimated_unit_cost);
			frappe.model.set_value("Demand Item", r.name, "line_total", lt);
			sum += lt;
		}
		const cur = flt(frm.doc.total_amount);
		const next = flt(sum);
		if (flt(cur, 3) !== flt(next, 3)) {
			frm.set_value("total_amount", next);
		}
		updateBudgetDecisionStrip(frm);
	}

	function runSaveValidation(frm) {
		const msgs = [];
		const push = function (m) {
			msgs.push(m);
		};

		if (!(frm.doc.title || "").trim()) {
			push(__("Title is required."));
		}
		if (!frm.doc.procuring_entity) {
			push(__("Procuring Entity is required."));
		}
		if (!frm.doc.requesting_department) {
			push(__("Department is required."));
		}
		if (!frm.doc.request_date) {
			push(__("Request Date is required."));
		}
		if (!frm.doc.required_by_date) {
			push(__("Required By Date is required."));
		}
		if (!(frm.doc.specification_summary || "").trim()) {
			push(__("“What is being requested” (specification summary) is required."));
		}
		if (!(frm.doc.delivery_location || "").trim()) {
			push(__("Delivery Location is required."));
		}
		if (
			frm.doc.requested_delivery_period_days != null &&
			String(frm.doc.requested_delivery_period_days).trim() !== "" &&
			cint(frm.doc.requested_delivery_period_days) < 0
		) {
			push(__("Requested Delivery Period (days) must be zero or greater."));
		}
		if (!frm.doc.budget_line) {
			push(__("Budget Line is required."));
		}

		const rows = frm.doc.items || [];
		if (!rows.length) {
			push(__("Add at least one line item."));
		} else {
			let i;
			for (i = 0; i < rows.length; i++) {
				const r = rows[i];
				if (!(r.item_description || "").trim()) {
					push(__("Each line item needs a description."));
					break;
				}
				if (!(r.uom || "").trim()) {
					push(__("Each line item needs a unit of measure."));
					break;
				}
				if (flt(r.quantity) <= 0) {
					push(__("Each line item needs a quantity greater than zero."));
					break;
				}
				if (flt(r.estimated_unit_cost) < 0) {
					push(__("Estimated unit cost cannot be negative."));
					break;
				}
			}
		}
		if (flt(frm.doc.total_amount) <= 0) {
			push(__("Requested amount must be greater than zero."));
		}

		const dt = frm.doc.demand_type;
		if (dt === "Unplanned" || dt === "Emergency") {
			if (!(frm.doc.beneficiary_summary || "").trim()) {
				push(__("Who benefits & why is required for Unplanned or Emergency demands."));
			}
			if (!(frm.doc.impact_if_not_procured || "").trim()) {
				push(__("Impact if Not Procured is required for Unplanned or Emergency demands."));
			}
		}
		if (dt === "Emergency") {
			if (!(frm.doc.emergency_justification || "").trim()) {
				push(__("Emergency Justification is required for Emergency demands."));
			}
		}

		if (dt !== "Emergency" && frm.doc.request_date && frm.doc.required_by_date) {
			const rq = String(frm.doc.request_date);
			const rd = String(frm.doc.required_by_date);
			if (rd < rq) {
				push(__("Required By Date must be on or after Request Date."));
			}
		}

		if (!msgs.length) {
			return true;
		}
		frappe.msgprint({
			title: __("Cannot save"),
			message: "<ul><li>" + msgs.join("</li><li>") + "</li></ul>",
			indicator: "red",
		});
		return false;
	}

	function esc(s) {
		if (frappe.utils && typeof frappe.utils.escape_html === "function") {
			return frappe.utils.escape_html(s == null ? "" : String(s));
		}
		return String(s == null ? "" : String(s))
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/"/g, "&quot;")
			.replace(/'/g, "&#39;");
	}

	function statusBadgeClass(status) {
		const s = (status || "").toLowerCase();
		if (s.indexOf("draft") >= 0) {
			return "badge kt-dia-badge kt-dia-badge--status kt-dia-badge--st-draft";
		}
		if (s.indexOf("pending") >= 0 && s.indexOf("hod") >= 0) {
			return "badge kt-dia-badge kt-dia-badge--status kt-dia-badge--st-pending-hod";
		}
		if (s.indexOf("pending") >= 0 && s.indexOf("finance") >= 0) {
			return "badge kt-dia-badge kt-dia-badge--status kt-dia-badge--st-pending-fin";
		}
		if (s.indexOf("approved") >= 0) {
			return "badge kt-dia-badge kt-dia-badge--status kt-dia-badge--st-approved";
		}
		if (s.indexOf("planning ready") >= 0) {
			return "badge kt-dia-badge kt-dia-badge--status kt-dia-badge--st-planning";
		}
		if (s.indexOf("reject") >= 0) {
			return "badge kt-dia-badge kt-dia-badge--status kt-dia-badge--st-rejected";
		}
		if (s.indexOf("cancel") >= 0) {
			return "badge kt-dia-badge kt-dia-badge--status kt-dia-badge--st-cancelled";
		}
		return "badge kt-dia-badge kt-dia-badge--status kt-dia-badge--st-neutral";
	}

	function statusBadgeHtml(status) {
		const st = status || "";
		return '<span class="' + statusBadgeClass(st) + '">' + esc(st) + "</span>";
	}

	function buildActionButtons(actions, demandName) {
		if (!actions || !actions.length) {
			return "";
		}
		let h = '<div class="kt-dia-builder-shell__actions-inner btn-toolbar flex-wrap">';
		for (let i = 0; i < actions.length; i++) {
			const a = actions[i];
			const base =
				"btn btn-sm " +
				(a.danger ? "btn-danger" : a.primary ? "btn-primary" : "btn-default");
			h +=
				'<button type="button" class="' +
				base +
				'" data-dia-fh-act="' +
				esc(a.id) +
				'" data-dia-fh-method="' +
				esc(a.method || "") +
				'" data-dia-fh-reason="' +
				esc(a.reason || "") +
				'" data-dia-fh-name="' +
				esc(demandName) +
				'" data-testid="dia-form-header-action-' +
				esc(a.id) +
				'">' +
				esc(a.label || "") +
				"</button>";
		}
		h += "</div>";
		return h;
	}

	function runHeaderRpc(frm, btn) {
		const nm = btn.getAttribute("data-dia-fh-name");
		const method = btn.getAttribute("data-dia-fh-method");
		const reasonKind = (btn.getAttribute("data-dia-fh-reason") || "").trim();
		if (!nm || !method) {
			return;
		}
		function callWith(extra) {
			frappe.call({
				method: method,
				args: Object.assign({ demand_name: nm }, extra || {}),
				callback: function (r) {
					if (!r || r.exc) {
						return;
					}
					frappe.show_alert({ message: __("Updated"), indicator: "green" });
					frm.reload_doc();
				},
				error: function (r) {
					let msg = __("Request failed");
					try {
						if (r && r._server_messages) {
							const arr = JSON.parse(r._server_messages);
							if (arr && arr.length) {
								const row = JSON.parse(arr[0]);
								if (row && row.message) {
									msg = row.message;
								}
							}
						} else if (r && r.message) {
							msg = r.message;
						}
					} catch (e1) {
						/* ignore */
					}
					frappe.msgprint({ title: __("Could not complete action"), message: msg, indicator: "red" });
				},
			});
		}
		if (reasonKind === "cancellation") {
			frappe.prompt(
				[
					{
						fieldname: "cancellation_reason",
						fieldtype: "Small Text",
						label: __("Cancellation reason"),
						reqd: 1,
					},
				],
				function (vals) {
					callWith({ cancellation_reason: vals.cancellation_reason });
				},
				__("Cancel demand"),
				__("Cancel")
			);
			return;
		}
		if (reasonKind === "return") {
			frappe.prompt(
				[
					{
						fieldname: "reason",
						fieldtype: "Small Text",
						label: __("Return reason"),
						reqd: 1,
					},
				],
				function (vals) {
					callWith({ reason: vals.reason });
				},
				__("Return to draft"),
				__("Return")
			);
			return;
		}
		if (reasonKind === "rejection") {
			frappe.prompt(
				[
					{
						fieldname: "rejection_reason",
						fieldtype: "Small Text",
						label: __("Rejection reason"),
						reqd: 1,
					},
				],
				function (vals) {
					callWith({ rejection_reason: vals.rejection_reason });
				},
				__("Reject demand"),
				__("Reject")
			);
			return;
		}
		callWith();
	}

	function bindActionClicks(frm) {
		const $s = frm._dia_builder_shell;
		if (!$s) {
			return;
		}
		$s.find("[data-dia-fh-actions]").off("click.diaFh");
		$s.find("[data-dia-fh-actions]").on("click.diaFh", "button[data-dia-fh-method]", function (ev) {
			const t = ev.currentTarget;
			if (!t.getAttribute("data-dia-fh-method")) {
				return;
			}
			ev.preventDefault();
			runHeaderRpc(frm, t);
		});
	}

	function loadHeaderActions(frm) {
		const $s = frm._dia_builder_shell;
		if (!$s) {
			return;
		}
		const $act = $s.find("[data-dia-fh-actions]");
		const $hint = $s.find("[data-dia-fh-hint]");
		if (frm.is_new()) {
			$act.empty();
			$hint.text(__("Save once to enable workflow actions in the header.")).show();
			return;
		}
		$hint.hide();
		frappe.call({
			method: "kentender_procurement.demand_intake.api.dia_detail.get_dia_demand_form_header",
			args: { name: frm.doc.name },
			callback: function (r) {
				if (!r || !r.message || !r.message.ok) {
					$act.empty();
					return;
				}
				const msg = r.message;
				$act.html(buildActionButtons(msg.actions || [], frm.doc.name));
				bindActionClicks(frm);
			},
		});
	}

	function tagBuilderFieldTestIds(frm) {
		const map = {
			title: "dia-field-title",
			required_by_date: "dia-field-required-by-date",
			priority_level: "dia-field-priority",
			demand_type: "dia-field-demand-type",
			budget_line: "dia-field-budget-line",
			beneficiary_summary: "dia-field-justification",
			specification_summary: "dia-field-specification-summary",
			impact_if_not_procured: "dia-field-impact-if-not-procured",
			emergency_justification: "dia-field-emergency-justification",
		};
		Object.keys(map).forEach(function (fn) {
			const fd = frm.fields_dict && frm.fields_dict[fn];
			if (fd && fd.$wrapper) {
				const $g = fd.$wrapper.closest(".form-group");
				if ($g && $g.length) {
					$g.attr("data-testid", map[fn]);
				}
			}
		});
		const $items = frm.fields_dict && frm.fields_dict.items && frm.fields_dict.items.$wrapper;
		if ($items && $items.length) {
			$items.closest(".form-section, .frappe-control").first().attr("data-testid", "dia-builder-section-items");
		}
		try {
			const $save = $(frm.wrapper).find(".standard-actions .btn-primary").first();
			if ($save.length) {
				const lbl = ($save.text() || "").trim().toLowerCase();
				if (lbl.indexOf("save") >= 0) {
					$save.attr("data-testid", "dia-builder-save-draft");
				}
			}
		} catch (e0) {
			/* ignore */
		}
	}

	function refresh(frm) {
		const $s = frm._dia_builder_shell;
		if (!$s) {
			return;
		}
		applyStrictDiaNavGuard();
		const title = frm.is_new()
			? __("New Demand")
			: frm.doc.demand_id || frm.doc.name || __("Demand");
		$s.find("[data-dia-fh-title]").text(title);
		const st = frm.is_new() ? __("Draft") : frm.doc.status || "";
		$s.find("[data-dia-fh-badge]").html(statusBadgeHtml(st));
		loadHeaderActions(frm);
		tagBuilderFieldTestIds(frm);
		updateBudgetDecisionStrip(frm);
	}

	function ensure(frm) {
		bindDiaFormNavGuard();
		applyStrictDiaNavGuard();
		if (frm._dia_builder_shell) {
			refresh(frm);
			return;
		}
		const inner =
			'<div class="kt-dia-builder-shell__inner">' +
			'<button type="button" class="btn btn-xs btn-default kt-dia-builder-shell__back" data-testid="dia-builder-back">' +
			"← " +
			esc(__("Demand Intake and Approval")) +
			"</button>" +
			'<div class="kt-dia-builder-shell__titlewrap">' +
			'<span class="kt-dia-builder-shell__title" data-dia-fh-title></span>' +
			'<span class="kt-dia-builder-shell__badges" data-dia-fh-badge></span>' +
			"</div>" +
			'<div class="kt-dia-builder-shell__actions" data-dia-fh-actions></div>' +
			"</div>" +
			'<p class="text-muted small mb-0 kt-dia-builder-shell__hint" data-dia-fh-hint style="display:none"></p>';
		const $shell = $('<div class="kt-dia-builder-shell" data-testid="dia-builder-page">' + inner + "</div>");
		$(frm.wrapper).addClass("kt-dia-demand-form-layout");
		$(frm.wrapper).prepend($shell);
		frm._dia_builder_shell = $shell;
		const $strip = $(
			'<div class="kt-dia-budget-decision-strip" data-testid="dia-builder-budget-strip" style="display:none"></div>'
		);
		$shell.after($strip);
		frm._dia_budget_strip = $strip;
		$shell.find(".kt-dia-builder-shell__back").on("click", function (e) {
			e.preventDefault();
			routeToDiaWorkspace();
		});
		refresh(frm);
	}

	return {
		ensure: ensure,
		refresh: refresh,
		applyBuilderFieldPermissions: applyBuilderFieldPermissions,
		applyBasicAndItemsEditMode: applyBuilderFieldPermissions,
		recalcDemandFinancials: recalcDemandFinancials,
		isBasicItemsEditable: basicItemsEditable,
		fetchBudgetLineContextIntoForm: fetchBudgetLineContextIntoForm,
		clearBudgetLineDerivatives: clearBudgetLineDerivatives,
		runSaveValidation: runSaveValidation,
		updateBudgetStrip: updateBudgetDecisionStrip,
	};
})();

frappe.ui.form.on("Demand", {
	onload_post_render(frm) {
		kentender_procurement.dia_demand_form.ensure(frm);
	},
	before_save(frm) {
		if (!frm.doc.requested_by) {
			frm.doc.requested_by = frappe.session.user;
		}
		if (!frm.doc.created_by) {
			frm.doc.created_by = frappe.session.user;
		}
	},
	validate(frm) {
		if (!frm.doc.requested_by) {
			frm.doc.requested_by = frappe.session.user;
		}
		if (!frm.doc.created_by) {
			frm.doc.created_by = frappe.session.user;
		}
		if (!kentender_procurement.dia_demand_form.isBasicItemsEditable(frm)) {
			return;
		}
		const ok = kentender_procurement.dia_demand_form.runSaveValidation(frm);
		if (!ok) {
			frappe.validated = false;
		}
	},
	refresh(frm) {
		const dia = kentender_procurement.dia_demand_form;
		dia.applyBuilderFieldPermissions(frm);
		if (dia.isBasicItemsEditable(frm)) {
			dia.recalcDemandFinancials(frm);
		}
		if (frm._dia_builder_shell) {
			dia.refresh(frm);
		}
	},
	status(frm) {
		kentender_procurement.dia_demand_form.applyBuilderFieldPermissions(frm);
	},
	demand_type(frm) {
		const dt = frm.doc.demand_type;
		if (dt === "Planned") {
			frm.set_value("impact_if_not_procured", "");
		}
		if (dt !== "Emergency") {
			frm.set_value("emergency_justification", "");
		}
		kentender_procurement.dia_demand_form.applyBuilderFieldPermissions(frm);
	},
	budget_line(frm) {
		const dia = kentender_procurement.dia_demand_form;
		if (frm._dia_suppress_budget_line_sync) {
			return;
		}
		if (!dia.isBasicItemsEditable(frm)) {
			return;
		}
		if (!frm.doc.budget_line) {
			dia.clearBudgetLineDerivatives(frm);
			dia.updateBudgetStrip(frm);
			return;
		}
		dia.fetchBudgetLineContextIntoForm(frm);
	},
	procuring_entity(frm) {
		const dia = kentender_procurement.dia_demand_form;
		if (frm._dia_suppress_budget_line_sync) {
			return;
		}
		if (!dia.isBasicItemsEditable(frm) || !frm.doc.budget_line) {
			return;
		}
		dia.fetchBudgetLineContextIntoForm(frm);
	},
	items_add(frm) {
		const dia = kentender_procurement.dia_demand_form;
		if (!dia.isBasicItemsEditable(frm)) {
			return;
		}
		setTimeout(function () {
			dia.recalcDemandFinancials(frm);
		}, 0);
	},
	items_remove(frm) {
		const dia = kentender_procurement.dia_demand_form;
		if (dia.isBasicItemsEditable(frm)) {
			dia.recalcDemandFinancials(frm);
		}
	},
});

frappe.ui.form.on("Demand Item", {
	quantity(frm) {
		const dia = kentender_procurement.dia_demand_form;
		if (dia.isBasicItemsEditable(frm)) {
			dia.recalcDemandFinancials(frm);
		}
	},
	estimated_unit_cost(frm) {
		const dia = kentender_procurement.dia_demand_form;
		if (dia.isBasicItemsEditable(frm)) {
			dia.recalcDemandFinancials(frm);
		}
	},
});
