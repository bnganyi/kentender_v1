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

(function applyEarlyDrawerBodyClass() {
	try {
		const search = window.location.search || "";
		if (/[?&]dia_drawer=1(?:&|$)/.test(search) || window.self !== window.top) {
			const root = document.documentElement;
			if (root) {
				root.setAttribute("data-dia-drawer", "1");
			}
			const ensurePreloadStyle = function () {
				if (document.getElementById("kt-dia-drawer-preload-style")) {
					return;
				}
				const style = document.createElement("style");
				style.id = "kt-dia-drawer-preload-style";
				style.textContent =
					'html[data-dia-drawer="1"] .page-head,' +
					'html[data-dia-drawer="1"] .content-page-head,' +
					'html[data-dia-drawer="1"] .layout-side-section,' +
					'html[data-dia-drawer="1"] .desk-sidebar,' +
					'html[data-dia-drawer="1"] .body-sidebar,' +
					'html[data-dia-drawer="1"] .form-sidebar,' +
					'html[data-dia-drawer="1"] .standard-actions,' +
					'html[data-dia-drawer="1"] .form-footer,' +
					'html[data-dia-drawer="1"] .navbar-breadcrumbs { display: none !important; }' +
					'html[data-dia-drawer="1"] .layout-main-section-wrapper,' +
					'html[data-dia-drawer="1"] .layout-main-section,' +
					'html[data-dia-drawer="1"] .page-container,' +
					'html[data-dia-drawer="1"] .container.page-body { width: 100% !important; max-width: 100% !important; margin: 0 !important; padding: 0 !important; }';
				(document.head || document.documentElement).appendChild(style);
			};
			ensurePreloadStyle();
			const apply = function () {
				if (document.body) {
					document.body.classList.add("kt-dia-embedded-drawer-form");
				}
			};
			if (document.body) {
				apply();
			} else {
				document.addEventListener("DOMContentLoaded", apply);
			}
		}
	} catch (eEarlyDrawer) {
		/* ignore */
	}
})();

kentender_procurement.dia_demand_form = (function () {
	let diaNavGuardBound = false;

	function routeToDiaWorkspace() {
		if (typeof kentender_core !== "undefined" && kentender_core.kt_nav) {
			kentender_core.kt_nav.toWorkbench("dia", { restore: true });
			return;
		}
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

	const FORM_STEPS = [
		{
			id: "identity",
			label: __("Identity"),
			sections: ["section_identifiers"],
			nextLabel: __("Next: Items & Value"),
		},
		{
			id: "items",
			label: __("Items & Value"),
			sections: ["section_items", "section_amount"],
			nextLabel: __("Next: Justification"),
		},
		{
			id: "justification",
			label: __("Justification"),
			sections: ["section_justification_delivery"],
			nextLabel: __("Next: Linkages"),
		},
		{
			id: "linkages",
			label: __("Linkages"),
			sections: ["section_budget_strategy", "column_delivery_side"],
			nextLabel: __("Review"),
		},
		{ id: "review", label: __("Review & Submit"), sections: [], nextLabel: "" },
	];

	const SUBMIT_REQUIRED_BY_STEP = {
		identity: [
			"title",
			"requesting_department",
			"procuring_entity",
			"requisition_type",
			"demand_type",
			"priority_level",
			"required_by_date",
		],
		items: ["items"],
		justification: ["beneficiary_summary", "specification_summary"],
		linkages: [],
		review: [],
	};

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
		let scrollHost = null;
		let prevScrollTop = 0;
		try {
			const g = frm.fields_dict.items && frm.fields_dict.items.grid;
			if (g && g.$wrapper) {
				scrollHost = g.$wrapper.find(".grid-body").get(0);
				if (scrollHost && typeof scrollHost.scrollTop === "number") {
					prevScrollTop = scrollHost.scrollTop;
				}
			}
		} catch (e0) {
			scrollHost = null;
		}
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
		if (scrollHost && typeof prevScrollTop === "number") {
			requestAnimationFrame(function () {
				scrollHost.scrollTop = prevScrollTop;
				requestAnimationFrame(function () {
					scrollHost.scrollTop = prevScrollTop;
				});
			});
		}
	}

	function runSaveValidation(frm, opts) {
		opts = opts || {};
		const mode = opts.mode || "draft";
		const msgs = [];
		const push = function (m) {
			msgs.push(m);
		};

		if (!(frm.doc.title || "").trim()) {
			push(__("Title is required."));
		}

		if (mode === "draft") {
			if (!msgs.length) {
				return true;
			}
			frappe.msgprint({
				title: __("Cannot save draft"),
				message: msgs.join("<br>"),
				indicator: "orange",
			});
			return false;
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
			push(__("Scope / requested outcome is required."));
		}
		if (!(frm.doc.beneficiary_summary || "").trim()) {
			push(__("Business justification is required."));
		}
		if (
			frm.doc.requested_delivery_period_days != null &&
			String(frm.doc.requested_delivery_period_days).trim() !== "" &&
			cint(frm.doc.requested_delivery_period_days) < 0
		) {
			push(__("Requested Delivery Period (days) must be zero or greater."));
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
				if (!(r.category || "").trim()) {
					push(__("Each line item needs a category."));
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

	function applyJustificationTextareaSizing(frm) {
		const targets = [
			["beneficiary_summary", 4],
			["specification_summary", 5],
		];
		for (let i = 0; i < targets.length; i++) {
			const fieldname = targets[i][0];
			const rows = targets[i][1];
			const fd = frm.fields_dict && frm.fields_dict[fieldname];
			if (!fd) {
				continue;
			}
			try {
				frm.set_df_property(fieldname, "rows", rows);
			} catch (eRows) {
				/* ignore */
			}
			if (fd.$input && fd.$input.length) {
				fd.$input.css({
					minHeight: "4.5rem",
					maxHeight: "8rem",
					height: "auto",
				});
			}
		}
	}

	function plainMetaText(value) {
		return String(value == null ? "" : value)
			.replace(/<[^>]*>/g, " ")
			.replace(/\s+/g, " ")
			.trim();
	}

	function buildFormMetaLine(frm) {
		const parts = [];
		if (frm.doc.status) {
			parts.push(String(frm.doc.status));
		}
		if (frm.doc.requisition_type) {
			parts.push(frm.doc.requisition_type);
		}
		if (frm.doc.total_amount != null && flt(frm.doc.total_amount) > 0) {
			parts.push(plainMetaText(formatCurrencyish(flt(frm.doc.total_amount), frm.doc.currency || "KES")));
		}
		if (frm.doc.required_by_date) {
			parts.push(__("Required by") + " " + String(frm.doc.required_by_date));
		}
		return parts.join(" · ");
	}

	function getCurrentStepIndex(frm) {
		if (typeof frm._dia_step_index !== "number") {
			frm._dia_step_index = 0;
		}
		return frm._dia_step_index;
	}

	function setCurrentStepIndex(frm, idx) {
		const max = FORM_STEPS.length - 1;
		frm._dia_step_index = Math.max(0, Math.min(max, idx));
		applyStepVisibility(frm);
		applyStageRequiredMarkers(frm, frm._dia_validation_stage || "draft");
		renderFormStepper(frm);
		renderStepFooter(frm);
		if (FORM_STEPS[frm._dia_step_index].id === "review") {
			renderReviewReadinessPanel(frm);
		}
	}

	function fieldStepMap(frm) {
		if (frm._dia_field_step_map) {
			return frm._dia_field_step_map;
		}
		const map = {};
		let currentStep = "identity";
		const order = (frm.meta && frm.meta.field_order) || [];
		for (let i = 0; i < order.length; i++) {
			const fn = order[i];
			if (fn === "section_items") {
				currentStep = "items";
			} else if (fn === "section_justification_delivery") {
				currentStep = "justification";
			} else if (fn === "section_budget_strategy") {
				currentStep = "linkages";
			} else if (fn === "section_exceptions") {
				currentStep = "review";
			}
			map[fn] = currentStep;
		}
		frm._dia_field_step_map = map;
		return map;
	}

	function buildSectionStepMap(frm) {
		if (frm._dia_section_step_map) {
			return frm._dia_section_step_map;
		}
		const map = {};
		let i;
		let j;
		for (i = 0; i < FORM_STEPS.length; i++) {
			const step = FORM_STEPS[i];
			const sections = step.sections || [];
			for (j = 0; j < sections.length; j++) {
				const secFn = sections[j];
				if (secFn.indexOf("section_") === 0) {
					map[secFn] = step.id;
				}
			}
		}
		const order = (frm.meta && frm.meta.field_order) || [];
		let pastExceptions = false;
		for (i = 0; i < order.length; i++) {
			const fn = order[i];
			if (fn === "section_exceptions") {
				pastExceptions = true;
			}
			if (pastExceptions && fn.indexOf("section_") === 0 && !map[fn]) {
				map[fn] = "review";
			}
		}
		frm._dia_section_step_map = map;
		return map;
	}

	function sectionShouldHide(sectionFieldname, step, sectionMap, showReviewPanel) {
		if (sectionFieldname === "section_exceptions") {
			return !showReviewPanel;
		}
		const secStep = sectionMap[sectionFieldname];
		return !!(secStep && secStep !== step.id);
	}

	function toggleFormSection(frm, sectionFieldname, hide) {
		const sec =
			(frm.layout && frm.layout.sections_dict && frm.layout.sections_dict[sectionFieldname]) ||
			null;
		let $sec = sec && sec.wrapper ? sec.wrapper : null;
		if (!$sec || !$sec.length) {
			$sec = $(frm.wrapper).find(
				'.form-section[data-fieldname="' + sectionFieldname + '"], .form-dashboard-section[data-fieldname="' + sectionFieldname + '"]'
			);
		}
		if (!$sec || !$sec.length) {
			return;
		}
		frm.set_df_property(sectionFieldname, "hidden", hide ? 1 : 0);
		if (sec && typeof sec.refresh === "function") {
			sec.refresh(hide);
		} else {
			$sec.toggleClass("hide-control", !!hide);
		}
		$sec.attr("data-dia-step-hidden", hide ? "1" : "0");
		if (hide) {
			$sec.addClass("empty-section").removeClass("visible-section");
			return;
		}
		$sec.removeClass("empty-section hide-control").addClass("visible-section");
	}

	const REVIEW_ONLY_SECTIONS = [
		"section_workflow_state",
		"section_submit_meta",
		"section_rejection",
	];

	const BUILDER_HIDDEN_SECTIONS = ["section_meta"];

	function applyStepVisibility(frm) {
		if (!frm._dia_builder_shell) {
			return;
		}
		const step = FORM_STEPS[getCurrentStepIndex(frm)];
		const sectionMap = buildSectionStepMap(frm);
		const showReviewPanel = step.id === "review";
		const sectionsDict = (frm.layout && frm.layout.sections_dict) || {};
		Object.keys(sectionsDict).forEach(function (sectionFieldname) {
			const hide = sectionShouldHide(sectionFieldname, step, sectionMap, showReviewPanel);
			toggleFormSection(frm, sectionFieldname, hide);
		});
		if (step.id !== "review") {
			let ri;
			for (ri = 0; ri < REVIEW_ONLY_SECTIONS.length; ri++) {
				toggleFormSection(frm, REVIEW_ONLY_SECTIONS[ri], true);
			}
		}
		let hi;
		for (hi = 0; hi < BUILDER_HIDDEN_SECTIONS.length; hi++) {
			toggleFormSection(frm, BUILDER_HIDDEN_SECTIONS[hi], true);
		}
		if (frm.layout && typeof frm.layout.refresh_sections === "function") {
			frm.layout.refresh_sections();
		}
		if (frm._dia_review_panel) {
			frm._dia_review_panel.toggle(showReviewPanel);
		}
	}

	function applyStageRequiredMarkers(frm, stage) {
		frm._dia_validation_stage = stage || "draft";
		if (!frm._dia_builder_shell) {
			return;
		}
		const step = FORM_STEPS[getCurrentStepIndex(frm)];
		const allManaged = []
			.concat(BASIC_REQUEST_FIELDS)
			.concat(JUSTIFICATION_FIELDS)
			.concat(["budget_line", "delivery_location"]);
		let i;
		for (i = 0; i < allManaged.length; i++) {
			frm.set_df_property(allManaged[i], "reqd", 0);
		}
		let required = [];
		if (stage === "submit") {
			required = SUBMIT_REQUIRED_BY_STEP[step.id] || [];
		} else if (step.id === "identity") {
			required = ["title"];
		}
		for (i = 0; i < required.length; i++) {
			if (frm.fields_dict[required[i]]) {
				frm.set_df_property(required[i], "reqd", 1);
			}
		}
	}

	function ensureLinkagesHelper(frm) {
		const fd = frm.fields_dict && frm.fields_dict.budget_line;
		if (!fd || !fd.$wrapper) {
			return;
		}
		let $help = fd.$wrapper.find(".kt-dia-linkages-helper");
		if (!$help.length) {
			$help = $(
				'<p class="help-box small text-muted kt-dia-linkages-helper">' +
					frappe.utils.escape_html(
						__(
							"Can be completed by a planner before planning handoff. Budget and strategy linkages are not required to save a draft or submit for approval."
						)
					) +
					"</p>"
			);
			fd.$wrapper.append($help);
		}
	}

	function renderReviewReadinessPanel(frm) {
		if (!frm._dia_review_panel) {
			const $panel = $(
				'<div class="kt-dia-review-readiness border rounded p-3 mb-3" data-testid="dia-builder-review-readiness" style="display:none"></div>'
			);
			if (frm._dia_form_stepper && frm._dia_form_stepper.length) {
				frm._dia_form_stepper.after($panel);
			} else {
				frm._dia_builder_shell.prepend($panel);
			}
			frm._dia_review_panel = $panel;
		}
		const $panel = frm._dia_review_panel;
		$panel.show().html(
			'<p class="text-muted small mb-2">' + frappe.utils.escape_html(__("Loading readiness checklist…")) + "</p>"
		);
		if (frm.is_new()) {
			frm._dia_submission_ready = false;
			$panel.html(
				'<p class="text-muted small mb-0">' +
					frappe.utils.escape_html(__("Save the draft first to load submission readiness.")) +
					"</p>"
			);
			renderStepFooter(frm);
			return;
		}
		frappe.call({
			method: "kentender_procurement.demand_intake.api.review.get_demand_review_data",
			args: { demand_name: frm.doc.name },
			callback: function (r) {
				const data = (r && r.message) || {};
				frm._dia_submission_ready = false;
				const view = data.review_view || "draft";
				let html = "";
				if (view === "pending_review") {
					const block = data.review_action_readiness || {};
					html =
						'<h5 class="mb-2">' +
						frappe.utils.escape_html(__("Review readiness")) +
						"</h5>" +
						'<ul class="mb-2">';
					const checks = block.checks || [];
					for (let i = 0; i < checks.length; i++) {
						const c = checks[i];
						const mark = c.ok ? "✓" : c.required ? "✗" : "!";
						html +=
							"<li>" +
							frappe.utils.escape_html(mark + " " + (c.label || c.id)) +
							"</li>";
					}
					html += "</ul>";
				} else if (view === "approved_outcome") {
					html =
						'<h5 class="mb-2">' +
						frappe.utils.escape_html(__("Approval outcome")) +
						"</h5>" +
						'<p class="text-muted small mb-0">' +
						frappe.utils.escape_html(__("This demand is approved. Use the Planning tab to confirm Planning Ready.")) +
						"</p>";
				} else {
					const sub = data.submission_readiness || {};
					frm._dia_submission_ready = !!(sub && sub.ready);
					const checks = sub.checks || [];
					html =
						'<h5 class="mb-2">' +
						frappe.utils.escape_html(__("Submission readiness")) +
						"</h5><ul class=\"mb-2\">";
					for (let i = 0; i < checks.length; i++) {
						const c = checks[i];
						const mark = c.ok ? "✓" : c.required ? "✗" : "!";
						html +=
							"<li>" +
							frappe.utils.escape_html(mark + " " + (c.label || c.id)) +
							(c.required === false && !c.ok
								? ' <span class="text-muted small">' +
									frappe.utils.escape_html(__("(optional — planner can complete later)")) +
									"</span>"
								: "") +
							"</li>";
					}
					html += "</ul>";
					if (!sub.ready) {
						html +=
							'<p class="text-muted small mb-0">' +
							frappe.utils.escape_html(
								__(
									"Strategy/budget linkages pending — can be completed by a planner before planning handoff."
								)
							) +
							"</p>";
					}
				}
				$panel.html(html);
				positionStepFooter(frm);
				renderStepFooter(frm);
			},
		});
	}

	function submitDemandFromForm(frm) {
		if (!basicItemsEditable(frm)) {
			return;
		}
		applyStageRequiredMarkers(frm, "submit");
		if (!runSaveValidation(frm, { mode: "submit" })) {
			return;
		}
		function doSubmit() {
			frappe.call({
				method: "kentender_procurement.demand_intake.api.lifecycle.submit_demand",
				args: { demand_name: frm.doc.name },
				callback: function (r) {
					if (!r || r.exc) {
						return;
					}
					frappe.show_alert({
						message: __("Submitted for approval"),
						indicator: "green",
					});
					frm.reload_doc();
				},
				error: function (err) {
					let msg = __("Could not submit demand");
					try {
						if (err && err._server_messages) {
							const arr = JSON.parse(err._server_messages);
							if (arr && arr.length) {
								const row = JSON.parse(arr[0]);
								if (row && row.message) {
									msg = row.message;
								}
							}
						}
					} catch (e1) {
						/* ignore */
					}
					frappe.msgprint({ title: __("Submit failed"), message: msg, indicator: "red" });
				},
			});
		}
		if (frm.is_dirty()) {
			frm.save(function () {
				doSubmit();
			});
			return;
		}
		doSubmit();
	}

	function positionStepFooter(frm) {
		const $footer = frm._dia_step_footer;
		if (!$footer || !$footer.length) {
			return;
		}
		const onReview = FORM_STEPS[getCurrentStepIndex(frm)].id === "review";
		const $anchor =
			onReview && frm._dia_review_panel && frm._dia_review_panel.length
				? frm._dia_review_panel
				: frm._dia_budget_strip && frm._dia_budget_strip.length
					? frm._dia_budget_strip
					: frm._dia_form_stepper;
		if ($anchor && $anchor.length && $footer.parent()[0] !== $anchor.parent()[0]) {
			$anchor.after($footer);
			return;
		}
		if ($anchor && $anchor.length) {
			$footer.insertAfter($anchor);
		}
	}

	function bindStepFooterNav(frm, idx, editable) {
		const $footer = frm._dia_step_footer;
		if (!$footer || !$footer.length) {
			return;
		}
		$footer.find("[data-dia-form-nav]").off("click.diaFooter").on("click.diaFooter", function () {
			const nav = this.getAttribute("data-dia-form-nav");
			const step = FORM_STEPS[idx];
			if (nav === "back") {
				setCurrentStepIndex(frm, idx - 1);
				return;
			}
			if (nav === "next") {
				if (editable && step.id === "identity") {
					applyStageRequiredMarkers(frm, "draft");
					if (!runSaveValidation(frm, { mode: "draft" })) {
						return;
					}
				}
				setCurrentStepIndex(frm, idx + 1);
				return;
			}
			if (nav === "save" && editable) {
				applyStageRequiredMarkers(frm, "draft");
				frm.save();
				return;
			}
			if (nav === "submit" && editable) {
				submitDemandFromForm(frm);
			}
		});
	}

	function renderStepFooter(frm) {
		if (!frm._dia_builder_shell) {
			return;
		}
		let $footer = frm._dia_step_footer;
		if (!$footer || !$footer.length) {
			$footer = $(
				'<div class="kt-dia-form-footer d-flex flex-wrap align-items-center gap-2 mt-3" data-testid="dia-builder-step-footer"></div>'
			);
			if (frm._dia_budget_strip && frm._dia_budget_strip.length) {
				frm._dia_budget_strip.after($footer);
			} else if (frm._dia_form_stepper && frm._dia_form_stepper.length) {
				frm._dia_form_stepper.after($footer);
			} else {
				frm._dia_builder_shell.append($footer);
			}
			frm._dia_step_footer = $footer;
		}
		const idx = getCurrentStepIndex(frm);
		const step = FORM_STEPS[idx];
		const editable = basicItemsEditable(frm);
		const onReview = step.id === "review";
		const submitReady = !!frm._dia_submission_ready;
		let html = "";
		if (idx > 0) {
			html +=
				'<button type="button" class="btn btn-default btn-sm" data-dia-form-nav="back" data-testid="dia-builder-step-back">' +
				frappe.utils.escape_html(__("Back")) +
				"</button>";
		}
		if (editable) {
			html +=
				'<button type="button" class="btn btn-default btn-sm" data-dia-form-nav="save" data-testid="dia-builder-save-draft">' +
				frappe.utils.escape_html(__("Save Draft")) +
				"</button>";
		}
		if (idx < FORM_STEPS.length - 1) {
			html +=
				'<button type="button" class="btn btn-primary btn-sm" data-dia-form-nav="next" data-testid="dia-builder-step-next">' +
				frappe.utils.escape_html(step.nextLabel || __("Next")) +
				"</button>";
		} else if (editable && onReview) {
			const submitLabel =
				frm.doc.status === "Rejected"
					? __("Re-submit for Approval")
					: __("Submit for Approval");
			html +=
				'<button type="button" class="btn btn-primary btn-sm' +
				(submitReady ? "" : " disabled") +
				'" data-dia-form-nav="submit" data-testid="dia-builder-submit"' +
				(submitReady ? "" : ' disabled="disabled" aria-disabled="true"') +
				'">' +
				frappe.utils.escape_html(submitLabel) +
				"</button>";
			if (!submitReady) {
				html +=
					'<span class="text-muted small" data-testid="dia-builder-submit-hint">' +
					frappe.utils.escape_html(__("Complete all required checks above to submit.")) +
					"</span>";
			}
		}
		if (!editable && frm.doc.status) {
			html +=
				'<span class="text-muted small ms-auto" data-testid="dia-builder-readonly-badge">' +
				frappe.utils.escape_html(String(frm.doc.status)) +
				" · " +
				frappe.utils.escape_html(__("Read-only")) +
				"</span>";
		}
		$footer.html(html);
		positionStepFooter(frm);
		bindStepFooterNav(frm, idx, editable);
	}

	function stepComplete(frm, stepId) {
		if (stepId === "identity") {
			return !!(frm.doc.title || "").trim();
		}
		if (stepId === "items") {
			return (frm.doc.items || []).length > 0 && flt(frm.doc.total_amount) > 0;
		}
		if (stepId === "justification") {
			return (
				!!(frm.doc.specification_summary || "").trim() && !!(frm.doc.beneficiary_summary || "").trim()
			);
		}
		if (stepId === "linkages") {
			return true;
		}
		if (stepId === "review") {
			return stepComplete(frm, "identity") && stepComplete(frm, "items") && stepComplete(frm, "justification");
		}
		return false;
	}

	function scrollToFormSection(frm, sectionFieldname) {
		const fd = frm.fields_dict && frm.fields_dict[sectionFieldname];
		if (!fd || !fd.$wrapper) {
			return;
		}
		const $sec = fd.$wrapper.closest(".form-section, .form-dashboard-section");
		if ($sec.length) {
			$sec[0].scrollIntoView({ behavior: "smooth", block: "start" });
		}
	}

	function renderFormStepper(frm) {
		const $nav = frm._dia_form_stepper;
		if (!$nav || !$nav.length) {
			return;
		}
		const steps = FORM_STEPS.map(function (s) {
			return {
				id: s.id,
				label: s.label,
				section: s.sections[0] || "section_exceptions",
			};
		});
		const activeIdx = getCurrentStepIndex(frm);
		let html = "";
		for (let i = 0; i < steps.length; i++) {
			const s = steps[i];
			const done = stepComplete(frm, s.id);
			const optional = s.id === "linkages";
			const mark = done ? "✓" : optional ? "○" : "!";
			html +=
				'<button type="button" class="kt-dia-form-step' +
				(done ? " is-complete" : "") +
				(i === activeIdx ? " is-active" : "") +
				'" data-dia-form-step="' +
				s.id +
				'" data-dia-form-step-index="' +
				i +
				'" data-testid="dia-builder-step-' +
				s.id +
				'">' +
				frappe.utils.escape_html(mark + " " + s.label) +
				"</button>";
		}
		$nav.html(html);
		$nav.find("[data-dia-form-step]").off("click.diaStepper").on("click.diaStepper", function () {
			const idx = cint(this.getAttribute("data-dia-form-step-index"));
			setCurrentStepIndex(frm, idx);
		});
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
		const $host = $(frm.wrapper).find(".kt-dia-module-shell-host");
		if (
			$host.length &&
			!frm._dia_in_drawer &&
			typeof kentender_core !== "undefined" &&
			kentender_core.kt_shell
		) {
			kentender_core.kt_shell.mountHeader($host, {
				moduleId: "dia",
				recordTitle: title,
				taskLabel: frm.is_new()
					? __("Create Demand")
					: kentender_core.kt_nav.taskLabel("dia", "edit"),
				metaLine: buildFormMetaLine(frm),
				statusHtml: statusBadgeHtml(frm.is_new() ? __("Draft") : frm.doc.status || ""),
			});
		}
		tagBuilderFieldTestIds(frm);
		applyJustificationTextareaSizing(frm);
		updateBudgetDecisionStrip(frm);
		renderFormStepper(frm);
		applyStepVisibility(frm);
		applyStageRequiredMarkers(frm, frm._dia_validation_stage || "draft");
		ensureLinkagesHelper(frm);
		renderStepFooter(frm);
		if (FORM_STEPS[getCurrentStepIndex(frm)].id === "review") {
			renderReviewReadinessPanel(frm);
		}
		if (frm.is_new() && frm.fields_dict && frm.fields_dict.request_date) {
			frm.set_df_property("request_date", "read_only", 1);
		}
	}

	function detectDrawerContext(frm) {
		if (frm._dia_in_drawer) {
			return;
		}
		let inDrawer = false;
		try {
			const params = frappe.utils.get_query_params ? frappe.utils.get_query_params() : {};
			if (params && (params.dia_drawer === "1" || params.dia_drawer === 1)) {
				inDrawer = true;
			}
		} catch (e1) {
			/* ignore */
		}
		if (!inDrawer) {
			try {
				inDrawer = window.self !== window.top;
			} catch (e2) {
				inDrawer = true;
			}
		}
		if (inDrawer) {
			frm._dia_in_drawer = true;
			document.body.classList.add("kt-dia-embedded-drawer-form");
		}
	}

	function ensure(frm) {
		detectDrawerContext(frm);
		bindDiaFormNavGuard();
		applyStrictDiaNavGuard();
		try {
			if (frappe.app && frappe.app.sidebar && typeof frappe.app.sidebar.setup === "function") {
				frappe.app.sidebar.setup("procurement");
			}
		} catch (eSidebar) {
			/* ignore */
		}
		if (frm._dia_builder_shell) {
			refresh(frm);
			return;
		}
		const $shellHost = frm._dia_in_drawer ? $() : $('<div class="kt-dia-module-shell-host mb-2"></div>');
		if (!frm._dia_in_drawer) {
			$(frm.wrapper).prepend($shellHost);
		}
		if (!frm._dia_in_drawer && typeof kentender_core !== "undefined" && kentender_core.kt_shell) {
			kentender_core.kt_shell.mountHeader($shellHost, {
				moduleId: "dia",
				recordTitle: frm.is_new()
					? __("New Demand")
					: frm.doc.demand_id || frm.doc.name || __("Demand"),
				taskLabel: frm.is_new()
					? __("Create Demand")
					: kentender_core.kt_nav.taskLabel("dia", "edit"),
			});
		}
		const $shell = $('<div class="kt-dia-builder-shell" data-testid="dia-builder-page"></div>');
		if (frm._dia_in_drawer) {
			const $anchor = $(frm.layout_main || frm.wrapper).find(".std-form-layout").first();
			if ($anchor.length) {
				$anchor.before($shell);
			} else {
				$(frm.layout_main || frm.wrapper).prepend($shell);
			}
		} else {
			$shellHost.after($shell);
		}
		$(frm.wrapper).addClass("kt-dia-demand-form-layout");
		if (frm._dia_in_drawer) {
			$(frm.wrapper).addClass("kt-dia-in-drawer");
		}
		if (!frm._dia_in_drawer) {
			document.body.classList.add("kt-dia-form-shell");
		}
		frm._dia_builder_shell = $shell;
		const $strip = $(
			'<div class="kt-dia-budget-decision-strip" data-testid="dia-builder-budget-strip" style="display:none"></div>'
		);
		const $stepper = $(
			'<div class="kt-dia-form-stepper kt-primary-tabs" data-testid="dia-builder-stepper" role="navigation" aria-label="' +
				frappe.utils.escape_html(__("Demand form steps")) +
				'"></div>'
		);
		$shell.append($stepper);
		$stepper.after($strip);
		frm._dia_form_stepper = $stepper;
		frm._dia_budget_strip = $strip;
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
		setCurrentStepIndex: setCurrentStepIndex,
		applyStageRequiredMarkers: applyStageRequiredMarkers,
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
		if (!frm.doc.request_date) {
			frm.doc.request_date = frappe.datetime.get_today();
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
		const ok = kentender_procurement.dia_demand_form.runSaveValidation(frm, { mode: "draft" });
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
