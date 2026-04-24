// Procurement Package — D4 builder (Desk Form): tabs, demand lines panel, Save / Submit / Back.

frappe.provide("kentender_procurement");
frappe.provide("kentender_procurement.pp_package_builder");

(function () {
	const READONLY_STATUSES = [
		"Submitted",
		"Approved",
		"Ready for Tender",
		"Released to Tender",
		"Rejected",
	];
	const TAB_TESTIDS = [
		"pp-builder-section-definition",
		"pp-builder-section-template-method",
		"pp-builder-section-demand-lines",
		"pp-builder-section-financial-schedule",
		"pp-builder-section-risk",
		"pp-builder-section-kpi",
		"pp-builder-section-decision-criteria",
		"pp-builder-section-vendor-management",
		"pp-builder-section-workflow",
		"pp-builder-section-notes",
	];
	const TAB_STATE = {
		NOT_STARTED: "NOT_STARTED",
		IN_PROGRESS: "IN_PROGRESS",
		COMPLETE: "COMPLETE",
		ERROR: "ERROR",
	};
	const TAB_STATUS_GLYPH = {
		NOT_STARTED: "○",
		IN_PROGRESS: "◔",
		COMPLETE: "✓",
		ERROR: "⚠",
	};
	const TAB_META = [
		{ key: "definition", label: __("Definition"), testid: TAB_TESTIDS[0], fieldname: "tab_definition" },
		{
			key: "template_method",
			label: __("Template and method"),
			testid: TAB_TESTIDS[1],
			fieldname: "tab_template_method",
		},
		{
			key: "demand_lines",
			label: __("Demand assignment"),
			testid: TAB_TESTIDS[2],
			fieldname: "tab_demand_lines",
		},
		{
			key: "financial_schedule",
			label: __("Financial and schedule"),
			testid: TAB_TESTIDS[3],
			fieldname: "tab_financial_schedule",
		},
		{ key: "risk", label: __("Risk and mitigation"), testid: TAB_TESTIDS[4], fieldname: "tab_risk" },
		{ key: "kpi", label: __("KPI profile"), testid: TAB_TESTIDS[5], fieldname: "tab_kpi" },
		{ key: "decision", label: __("Decision criteria"), testid: TAB_TESTIDS[6], fieldname: "tab_decision" },
		{
			key: "vendor",
			label: __("Vendor management"),
			testid: TAB_TESTIDS[7],
			fieldname: "tab_vendor",
		},
		{
			key: "workflow",
			label: __("Workflow and approval"),
			testid: TAB_TESTIDS[8],
			fieldname: "tab_workflow",
		},
		{ key: "notes", label: __("Notes"), testid: TAB_TESTIDS[9], fieldname: "tab_notes" },
	];
	const STEP_PREREQS = {
		template_method: ["definition"],
		demand_lines: [],
		financial_schedule: ["definition", "template_method"],
		risk: ["financial_schedule"],
		kpi: ["financial_schedule"],
		decision: ["template_method"],
		vendor: ["template_method"],
		workflow: [],
		notes: [],
	};

	function escapeHtml(s) {
		if (s == null || s === undefined) return "";
		return String(s)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	function routeToProcurementPlanning() {
		if (typeof frappe !== "undefined" && frappe.set_route) {
			try {
				frappe.set_route("Workspaces", "Procurement Planning");
				return;
			} catch (e) {
				/* fallback below */
			}
		}
		if (typeof window !== "undefined") {
			window.location.href = "/app/procurement-planning";
		}
	}

	function ppBootRoles() {
		return (frappe.boot && frappe.boot.user && frappe.boot.user.roles) || [];
	}

	/** E2 — Planner / admin may author packages; officers & authorities use the workbench APIs. */
	function ppIsPlannerLike() {
		const r = ppBootRoles();
		return (
			r.indexOf("Procurement Planner") >= 0 ||
			r.indexOf("Administrator") >= 0 ||
			r.indexOf("System Manager") >= 0
		);
	}

	function applyTabTestids(frm) {
		try {
			const $root = frm.$wrapper && frm.$wrapper.find ? frm.$wrapper : null;
			if (!$root) return;
			$root.find(".form-tabs-list .nav-link").each(function (idx) {
				const tid = TAB_TESTIDS[idx];
				if (tid) {
					window.jQuery(this).attr("data-testid", tid);
				}
			});
		} catch (e) {
			/* ignore */
		}
	}

	function wireDemandAssignmentActions(frm) {
		const $root = frm.$wrapper && frm.$wrapper.find ? frm.$wrapper : null;
		if (!$root) return;
		$root.off("click.ktpp-demand-save");
		$root.off("click.ktpp-demand-open");
		$root.on("click.ktpp-demand-save", "#kt-pp-builder-save-package", function () {
			frm.save();
		});
		$root.on("click.ktpp-demand-open", "#kt-pp-builder-open-planning", function () {
			routeToProcurementPlanning();
		});
	}

	function applyBuilderPageClass(frm) {
		try {
			const $w = frm.$wrapper && frm.$wrapper.find ? frm.$wrapper.find(".form-layout") : null;
			if ($w && $w.length) {
				$w.first().addClass("kt-pp-package-builder");
				$w.first().attr("data-testid", "pp-builder-page");
			}
		} catch (e2) {
			/* ignore */
		}
	}

	function applyReferenceQueries(frm) {
		frm.set_query("plan_id", function () {
			return {
				query: "kentender_procurement.procurement_planning.api.reference_search.search_procurement_plan",
			};
		});
		frm.set_query("template_id", function () {
			return {
				query: "kentender_procurement.procurement_planning.api.reference_search.search_procurement_template",
			};
		});
		frm.set_query("risk_profile_id", function () {
			return { query: "kentender_procurement.procurement_planning.api.reference_search.search_risk_profile" };
		});
		frm.set_query("kpi_profile_id", function () {
			return { query: "kentender_procurement.procurement_planning.api.reference_search.search_kpi_profile" };
		});
		frm.set_query("decision_criteria_profile_id", function () {
			return {
				query:
					"kentender_procurement.procurement_planning.api.reference_search.search_decision_criteria_profile",
			};
		});
		frm.set_query("vendor_management_profile_id", function () {
			return {
				query:
					"kentender_procurement.procurement_planning.api.reference_search.search_vendor_management_profile",
			};
		});
	}

	function applyAutoCodeUi(frm) {
		try {
			frm.set_df_property("package_code", "read_only", 1);
			frm.set_df_property("package_code", "reqd", 0);
			const code = String(frm.doc.package_code || "").trim();
			const hideAutoCodeInput = frm.is_new() && !code;
			frm.set_df_property("package_code", "hidden", hideAutoCodeInput ? 1 : 0);
			frm.set_df_property("column_def_code", "hidden", hideAutoCodeInput ? 1 : 0);
			frm.set_df_property(
				"package_code",
				"description",
				code ? __("System-generated package code.") : __("Auto-generated on save.")
			);
			if (!code && frm.fields_dict && frm.fields_dict.package_code) {
				const ctrl = frm.fields_dict.package_code;
				const input = ctrl.$input;
				if (input && input.length) {
					input.attr("placeholder", __("Auto-generated on save"));
				}
			}
			frm.refresh_field("package_code");
			frm.refresh_field("column_def_code");
		} catch (e) {
			/* ignore */
		}
	}

	function ensureCreatedByDefault(frm) {
		if (!frm.is_new()) return;
		if (frm.doc.created_by) return;
		if (!frappe.session || !frappe.session.user) return;
		frm.set_value("created_by", frappe.session.user);
	}

	function hasValue(v) {
		return !(v == null || v === undefined || String(v).trim() === "");
	}

	function shouldRequireSchedule(frm, tmeta) {
		if (!tmeta) return false;
		return Number(tmeta.planning_lead_days || 0) > 0 || Number(tmeta.procurement_cycle_days || 0) > 0;
	}

	function decisionCriteriaRequired(frm) {
		const m = String(frm.doc.procurement_method || "").toLowerCase();
		return m === "open tender" || m === "rfq";
	}

	function computeTabStates(frm) {
		const tmeta = frm.__kt_pp_template_meta || null;
		const linesCount = Number(frm.__kt_pp_lines_count || 0);
		const states = {};

		const defStarted =
			hasValue(frm.doc.package_name) ||
			hasValue(frm.doc.package_code) ||
			hasValue(frm.doc.plan_id) ||
			hasValue(frm.doc.template_id);
		const defComplete =
			hasValue(frm.doc.package_name) &&
			hasValue(frm.doc.plan_id) &&
			hasValue(frm.doc.template_id) &&
			(frm.is_new() || hasValue(frm.doc.package_code));
		states.definition = !defStarted ? TAB_STATE.NOT_STARTED : defComplete ? TAB_STATE.COMPLETE : TAB_STATE.ERROR;

		const tmStarted = hasValue(frm.doc.procurement_method) || hasValue(frm.doc.contract_type);
		const tmComplete = hasValue(frm.doc.procurement_method) && hasValue(frm.doc.contract_type);
		states.template_method = !tmStarted ? TAB_STATE.NOT_STARTED : tmComplete ? TAB_STATE.COMPLETE : TAB_STATE.ERROR;

		states.demand_lines = linesCount > 0 ? TAB_STATE.COMPLETE : TAB_STATE.NOT_STARTED;

		const est = Number(frm.doc.estimated_value || 0);
		const schedRequired = shouldRequireSchedule(frm, tmeta);
		const schedStarted = hasValue(frm.doc.schedule_start) || hasValue(frm.doc.schedule_end);
		const schedComplete = !schedRequired || (hasValue(frm.doc.schedule_start) && hasValue(frm.doc.schedule_end));
		const finStarted = schedStarted || est > 0;
		// Financial/Schedule progression is based on required schedule fields; estimated value is derived.
		const finComplete = schedComplete;
		states.financial_schedule = !finStarted ? TAB_STATE.NOT_STARTED : finComplete ? TAB_STATE.COMPLETE : TAB_STATE.ERROR;

		const riskStarted = hasValue(frm.doc.risk_profile_id);
		states.risk = !riskStarted ? TAB_STATE.NOT_STARTED : riskStarted ? TAB_STATE.COMPLETE : TAB_STATE.ERROR;

		const kpiRequired = !!(tmeta && hasValue(tmeta.kpi_profile_id));
		const kpiStarted = hasValue(frm.doc.kpi_profile_id);
		const kpiComplete = !kpiRequired || kpiStarted;
		states.kpi = !kpiStarted ? (kpiRequired ? TAB_STATE.ERROR : TAB_STATE.NOT_STARTED) : kpiComplete ? TAB_STATE.COMPLETE : TAB_STATE.ERROR;

		const decRequired = decisionCriteriaRequired(frm);
		const decStarted = hasValue(frm.doc.decision_criteria_profile_id);
		const decComplete = !decRequired || decStarted;
		states.decision = !decStarted
			? decRequired
				? TAB_STATE.ERROR
				: TAB_STATE.NOT_STARTED
			: decComplete
				? TAB_STATE.COMPLETE
				: TAB_STATE.ERROR;

		const vendorRequired = !!(tmeta && hasValue(tmeta.vendor_management_profile_id));
		const vendorStarted = hasValue(frm.doc.vendor_management_profile_id);
		const vendorComplete = !vendorRequired || vendorStarted;
		states.vendor = !vendorStarted
			? vendorRequired
				? TAB_STATE.ERROR
				: TAB_STATE.NOT_STARTED
			: vendorComplete
				? TAB_STATE.COMPLETE
				: TAB_STATE.ERROR;

		states.workflow = TAB_STATE.COMPLETE;
		states.notes =
			hasValue(frm.doc.planner_notes) || hasValue(frm.doc.exception_notes)
				? TAB_STATE.IN_PROGRESS
				: TAB_STATE.NOT_STARTED;
		return states;
	}

	function applyTemplateDrivenTabVisibility(frm) {
		const tmeta = frm.__kt_pp_template_meta || null;
		const showKpi = !!(tmeta && hasValue(tmeta.kpi_profile_id));
		const showVendor = !!(tmeta && hasValue(tmeta.vendor_management_profile_id));
		const showDemandAssignment = !frm.is_new();
		try {
			frm.set_df_property("tab_kpi", "hidden", showKpi ? 0 : 1);
			frm.set_df_property("tab_vendor", "hidden", showVendor ? 0 : 1);
			frm.set_df_property("tab_demand_lines", "hidden", showDemandAssignment ? 0 : 1);
			frm.refresh_fields(["tab_kpi", "tab_vendor", "tab_demand_lines"]);
		} catch (e) {
			/* ignore */
		}
	}

	function enforceDemandAssignmentTabAccess(frm) {
		const $root = frm.$wrapper && frm.$wrapper.find ? frm.$wrapper : null;
		if (!$root) return;
		const idx = TAB_META.findIndex(function (m) {
			return m.key === "demand_lines";
		});
		if (idx < 0) return;
		const $link = $root.find(".form-tabs-list .nav-link").eq(idx);
		const shouldShow = !frm.is_new();

		if (!$link.length) return;
		if (shouldShow) {
			$link.show();
			$link.removeClass("disabled");
			$link.css("pointer-events", "");
			return;
		}

		// Hide and disable on unsaved docs to avoid dead-step navigation.
		const isActive = $link.hasClass("active");
		$link.hide();
		$link.addClass("disabled");
		$link.css("pointer-events", "none");
		if (isActive) {
			goToTabByKey(frm, "definition");
		}
	}

	function renderBuilderSummary(frm, states) {
		const $root = frm.$wrapper && frm.$wrapper.find ? frm.$wrapper : null;
		if (!$root) return;
		let slot = $root.find("#kt-pp-builder-progress");
		const tabs = $root.find(".form-tabs-list").first();
		if (!tabs || !tabs.length) return;
		if (!slot.length) {
			slot = window.jQuery('<div id="kt-pp-builder-progress" class="kt-pp-builder-progress"></div>');
			tabs.before(slot);
		}
		const visibleKeys = TAB_META.filter(function (m) {
			try {
				const df = frappe.meta.get_docfield("Procurement Package", m.fieldname, frm.doc.name);
				return !(df && Number(df.hidden) === 1);
			} catch (e) {
				return true;
			}
		}).map(function (m) {
			return m.key;
		});
		const completableKeys = visibleKeys.filter(function (k) {
			return k !== "workflow" && k !== "notes";
		});
		const completeCount = completableKeys.filter(function (k) {
			return states[k] === TAB_STATE.COMPLETE;
		}).length;
		const pct = completableKeys.length ? Math.round((completeCount / completableKeys.length) * 100) : 100;
		const missingLabels = TAB_META.filter(function (m) {
			return (
				visibleKeys.indexOf(m.key) >= 0 &&
				m.key !== "workflow" &&
				m.key !== "notes" &&
				states[m.key] !== TAB_STATE.COMPLETE
			);
		}).map(function (m) {
			return m.label;
		});
		let html =
			'<div class="kt-pp-builder-progress__line"><strong>' +
			escapeHtml(__("Package completeness")) +
			":</strong> " +
			escapeHtml(String(pct)) +
			"%</div>";
		if (missingLabels.length) {
			html +=
				'<div class="kt-pp-builder-progress__missing">' +
				escapeHtml(__("Missing")) +
				": " +
				escapeHtml(missingLabels.join(", ")) +
				"</div>";
		}
		const suggestion = frm.__kt_pp_next_tab_suggestion;
		if (suggestion) {
			html +=
				'<button type="button" class="btn btn-link btn-sm p-0 mt-1 kt-pp-builder-next" data-next-tab="' +
				escapeHtml(suggestion.key) +
				'">' +
				escapeHtml(__("Next: {0} ->").replace("{0}", suggestion.label)) +
				"</button>";
		}
		slot.html(html);
		slot.find(".kt-pp-builder-next").on("click", function () {
			const key = window.jQuery(this).attr("data-next-tab") || "";
			goToTabByKey(frm, key);
		});
	}

	function applyTabStatusIndicators(frm, states) {
		const $root = frm.$wrapper && frm.$wrapper.find ? frm.$wrapper : null;
		if (!$root) return;
		$root.find(".form-tabs-list .nav-link").each(function (idx) {
			const meta = TAB_META[idx];
			if (!meta) return;
			const state = states[meta.key] || TAB_STATE.NOT_STARTED;
			const glyph = TAB_STATUS_GLYPH[state] || TAB_STATUS_GLYPH.NOT_STARTED;
			const $lnk = window.jQuery(this);
			const baseLabel = String($lnk.attr("data-kt-base-label") || "").trim() || meta.label;
			$lnk.attr("data-kt-base-label", baseLabel);
			$lnk.attr("data-kt-state", state);
			$lnk.find(".kt-pp-tab-state").remove();
			$lnk.contents().filter(function () {
				return this.nodeType === 3;
			}).remove();
			$lnk.prepend(document.createTextNode(baseLabel + " "));
			$lnk.append('<span class="kt-pp-tab-state" aria-hidden="true">' + escapeHtml(glyph) + "</span>");
		});
	}

	function getActiveTabKey(frm) {
		const $root = frm.$wrapper && frm.$wrapper.find ? frm.$wrapper : null;
		if (!$root) return "definition";
		const active = $root.find(".form-tabs-list .nav-link.active").first();
		const idx = active.length ? active.parent().index() : 0;
		return (TAB_META[idx] && TAB_META[idx].key) || "definition";
	}

	function goToTabByKey(frm, key) {
		const idx = TAB_META.findIndex(function (m) {
			return m.key === key;
		});
		if (idx < 0) return;
		const $root = frm.$wrapper && frm.$wrapper.find ? frm.$wrapper : null;
		if (!$root) return;
		const el = $root.find(".form-tabs-list .nav-link").eq(idx);
		if (el && el.length) el.trigger("click");
	}

	function nextIncompleteTab(states, frm) {
		const active = getActiveTabKey(frm);
		const aIdx = TAB_META.findIndex(function (m) {
			return m.key === active;
		});
		for (let i = aIdx + 1; i < TAB_META.length; i++) {
			const t = TAB_META[i];
			if (states[t.key] !== TAB_STATE.COMPLETE && states[t.key] !== TAB_STATE.NOT_STARTED) {
				return t;
			}
			if (states[t.key] === TAB_STATE.NOT_STARTED) {
				return t;
			}
		}
		for (let j = 0; j < TAB_META.length; j++) {
			const tt = TAB_META[j];
			if (states[tt.key] !== TAB_STATE.COMPLETE) return tt;
		}
		return null;
	}

	function softProgressionWarning(targetKey, states, frm) {
		const needs = STEP_PREREQS[targetKey] || [];
		const miss = needs.filter(function (k) {
			return states[k] !== TAB_STATE.COMPLETE;
		});
		if (!miss.length) return "";
		const lbl = TAB_META.filter(function (m) {
			return miss.indexOf(m.key) >= 0;
		}).map(function (m) {
			return m.label;
		});
		return __("Complete {0} first.").replace("{0}", lbl.join(", "));
	}

	function wireGuidedTabs(frm, states) {
		const $root = frm.$wrapper && frm.$wrapper.find ? frm.$wrapper : null;
		if (!$root) return;
		const tabs = $root.find(".form-tabs-list .nav-link");
		tabs.off(".ktppguide");
		tabs.on("click.ktppguide", function () {
			const idx = window.jQuery(this).parent().index();
			const meta = TAB_META[idx];
			if (!meta) return;
			const msg = softProgressionWarning(meta.key, states, frm);
			if (msg) {
				frappe.show_alert({ indicator: "orange", message: msg });
			}
			if (meta.key === "demand_lines") {
				scheduleDemandLinesRender(frm);
			}
		});
	}

	function scheduleDemandLinesRender(frm) {
		loadAndRenderLines(frm);
	}

	function refreshBuilderGuidance(frm) {
		const states = computeTabStates(frm);
		frm.__kt_pp_tab_states = states;
		applyTemplateDrivenTabVisibility(frm);
		enforceDemandAssignmentTabAccess(frm);
		applyTabStatusIndicators(frm, states);
		renderBuilderSummary(frm, states);
		wireGuidedTabs(frm, states);
	}

	function loadTemplateMeta(frm) {
		const tpl = frm.doc.template_id;
		if (!tpl) {
			frm.__kt_pp_template_meta = null;
			refreshBuilderGuidance(frm);
			return Promise.resolve();
		}
		return frappe.db
			.get_doc("Procurement Template", tpl)
			.then(function (doc) {
				frm.__kt_pp_template_meta = doc || null;
				refreshBuilderGuidance(frm);
			})
			.catch(function () {
				frm.__kt_pp_template_meta = null;
				refreshBuilderGuidance(frm);
			});
	}

	function wireToolbar(frm) {
		try {
			frm.remove_custom_button(__("Back to Procurement Planning"), __("Planning"));
		} catch (e0) {
			/* ignore */
		}
		try {
			frm.remove_custom_button(__("Submit for approval"), __("Actions"));
		} catch (e0b) {
			/* ignore */
		}
		try {
			frm.remove_custom_button(__("Choose template…"), __("Template and method"));
		} catch (e0c) {
			/* ignore */
		}

		frm.add_custom_button(__("Back to Procurement Planning"), routeToProcurementPlanning, __("Planning"));

		try {
			const $p = frm.page && frm.page.btn_primary;
			if ($p && $p.length) {
				$p.attr("data-testid", "pp-builder-save");
			}
		} catch (e) {
			/* ignore */
		}

		const canWrite = frappe.model.can_write("Procurement Package", frm.doc.name) || frm.is_new();
		const plannerLike = ppIsPlannerLike();
		if (
			plannerLike &&
			canWrite &&
			(frm.doc.status === "Draft" ||
				frm.doc.status === "Completed" ||
				frm.doc.status === "Returned") &&
			!frm.is_new()
		) {
			frm.add_custom_button(
				__("Choose template…"),
				function () {
					if (window.kentender_procurement && window.kentender_procurement.pp_template_selector) {
						window.kentender_procurement.pp_template_selector.open({ mode: "form", frm: frm });
					}
				},
				__("Template and method")
			);
		}
		if (plannerLike && canWrite && frm.doc.status === "Completed") {
			frm.add_custom_button(
				__("Submit for approval"),
				function () {
					frappe.confirm(__("Submit this package for approval?"), function () {
						frappe.call({
							method: "kentender_procurement.procurement_planning.api.workflow.submit_package",
							args: { package_id: frm.doc.name },
							callback: function (r) {
								if (r && r.exc) {
									frappe.msgprint({
										title: __("Could not submit"),
										message: __("Server rejected the transition."),
										indicator: "red",
									});
									return;
								}
								frappe.show_alert({ message: __("Submitted"), indicator: "green" });
								frm.reload_doc();
							},
						});
					});
				},
				__("Actions")
			);
			setTimeout(function () {
				try {
					const $wrap = frm.$wrapper.find(".form-inner-toolbar, .page-actions").first();
					$wrap.find(".btn").each(function () {
						const t = (this.textContent || "").trim();
						if (t === __("Submit for approval").trim()) {
							window.jQuery(this).attr("data-testid", "pp-builder-submit");
						}
					});
				} catch (e3) {
					/* ignore */
				}
			}, 50);
		}
	}

	function applyReadonlyMode(frm) {
		const locked = !frm.is_new() && READONLY_STATUSES.indexOf(frm.doc.status) >= 0;
		if (!locked) {
			return;
		}
		const meta = frm.meta && frm.meta.fields ? frm.meta.fields : [];
		const skip = new Set([
			"Tab Break",
			"Section Break",
			"Column Break",
			"HTML",
			"Button",
			"Heading",
		]);
		let i;
		for (i = 0; i < meta.length; i++) {
			const df = meta[i];
			if (!df || !df.fieldname) continue;
			if (skip.has(df.fieldtype)) continue;
			if (
				df.fieldname === "status" ||
				df.fieldname === "workflow_reason" ||
				df.fieldname === "planner_notes" ||
				df.fieldname === "exception_notes"
			) {
				continue;
			}
			try {
				frm.set_df_property(df.fieldname, "read_only", 1);
			} catch (e) {
				/* ignore */
			}
		}
		try {
			frm.set_df_property("planner_notes", "read_only", 0);
			frm.set_df_property("exception_notes", "read_only", 0);
		} catch (e2) {
			/* ignore */
		}
	}

	function loadAndRenderLines(frm) {
		frm.set_df_property("demand_lines_html", "hidden", 0);
		if (frm.is_new()) {
			frm.__kt_pp_lines_count = 0;
			frm.set_df_property(
				"demand_lines_html",
				"options",
				[
					'<div class="kt-pp-builder-lines-help text-muted small" data-testid="pp-builder-demand-lines-help">',
					"<p><strong>Demand assignment</strong></p>",
					"<p>Demand lines are managed in Procurement Planning.</p>",
					"<p>To assign demand to this package:</p>",
					"<p>1. Save the package</p>",
					"<p>2. Open Procurement Planning</p>",
					"<p>3. Select this package and assign demand lines</p>",
					"<p><strong>Save this package before assigning demand lines.</strong></p>",
					'<button type="button" class="btn btn-sm btn-default" id="kt-pp-builder-save-package">',
					escapeHtml(__("Save Package")),
					"</button>",
					"</div>",
				].join("")
			);
			frm.refresh_field("demand_lines_html");
			wireDemandAssignmentActions(frm);
			refreshBuilderGuidance(frm);
			return true;
		}

		frm.set_df_property(
			"demand_lines_html",
			"options",
			[
				'<div class="kt-pp-builder-lines-help text-muted small" data-testid="pp-builder-demand-lines-help">',
				"<p><strong>Demand assignment</strong></p>",
				"<p>Demand lines are managed in Procurement Planning.</p>",
				"<p>To assign demand to this package:</p>",
				"<p>1. Open Procurement Planning</p>",
				"<p>2. Select this package and assign demand lines</p>",
				"<p>Loading summary...</p>",
				'<button type="button" class="btn btn-sm btn-primary" id="kt-pp-builder-open-planning">',
				escapeHtml(__("Open Planning Workbench")),
				"</button>",
				"</div>",
			].join("")
		);
		frm.refresh_field("demand_lines_html");

		frappe.call({
			method: "kentender_procurement.procurement_planning.api.package_line_edit.get_pp_package_lines",
			args: { package: frm.doc.name },
			callback: function (r) {
				const msg = r && r.message;
				const lines = msg && msg.ok ? msg.lines || [] : [];
				let total = 0;
				const demandIds = new Set();
				let i;
				for (i = 0; i < lines.length; i++) {
					const line = lines[i] || {};
					total += Number(line.amount || 0);
					if (line.demand_id) {
						demandIds.add(String(line.demand_id));
					}
				}
				frm.__kt_pp_lines_count = lines.length;
				frm.set_df_property(
					"demand_lines_html",
					"options",
					[
						'<div class="kt-pp-builder-lines-help text-muted small" data-testid="pp-builder-demand-lines-help">',
						"<p><strong>Demand assignment</strong></p>",
						"<p>Demand lines are managed in Procurement Planning.</p>",
						"<p>To assign demand to this package:</p>",
						"<p>1. Open Procurement Planning</p>",
						"<p>2. Select this package and assign demand lines</p>",
						"<p>",
						escapeHtml(__("Assigned demand lines: {0}").replace("{0}", String(lines.length))),
						"</p>",
						"<p>",
						escapeHtml(__("Total assigned value: {0}").replace("{0}", String(Math.round(total).toLocaleString()))),
						"</p>",
						"<p>",
						escapeHtml(__("Source demands: {0}").replace("{0}", String(demandIds.size))),
						"</p>",
						'<button type="button" class="btn btn-sm btn-primary" id="kt-pp-builder-open-planning">',
						escapeHtml(__("Open Planning Workbench")),
						"</button>",
						"</div>",
					].join("")
				);
				frm.refresh_field("demand_lines_html");
				wireDemandAssignmentActions(frm);
				refreshBuilderGuidance(frm);
			},
		});
		return true;
	}

	frappe.ui.form.on("Procurement Package", {
		onload_post_render: function (frm) {
			scheduleDemandLinesRender(frm);
		},
		refresh: function (frm) {
			applyBuilderPageClass(frm);
			applyTabTestids(frm);
			applyReferenceQueries(frm);
			wireDemandAssignmentActions(frm);
			ensureCreatedByDefault(frm);
			applyAutoCodeUi(frm);
			wireToolbar(frm);
			applyReadonlyMode(frm);
			loadTemplateMeta(frm);
			scheduleDemandLinesRender(frm);
		},
		after_save: function (frm) {
			applyAutoCodeUi(frm);
			refreshBuilderGuidance(frm);
			const next = nextIncompleteTab(frm.__kt_pp_tab_states || computeTabStates(frm), frm);
			frm.__kt_pp_next_tab_suggestion = next ? { key: next.key, label: next.label } : null;
			refreshBuilderGuidance(frm);
			if (next) {
				frappe.show_alert({
					indicator: "blue",
					message: __("Next: {0}").replace("{0}", next.label),
				});
			}
		},
		template_id: function (frm) {
			loadTemplateMeta(frm);
			applyAutoCodeUi(frm);
		},
		package_name: function (frm) {
			refreshBuilderGuidance(frm);
		},
		plan_id: function (frm) {
			refreshBuilderGuidance(frm);
			applyAutoCodeUi(frm);
		},
		procurement_method: function (frm) {
			refreshBuilderGuidance(frm);
		},
		contract_type: function (frm) {
			refreshBuilderGuidance(frm);
		},
		decision_criteria_profile_id: function (frm) {
			refreshBuilderGuidance(frm);
		},
		vendor_management_profile_id: function (frm) {
			refreshBuilderGuidance(frm);
		},
		kpi_profile_id: function (frm) {
			refreshBuilderGuidance(frm);
		},
		risk_profile_id: function (frm) {
			refreshBuilderGuidance(frm);
		},
		schedule_start: function (frm) {
			refreshBuilderGuidance(frm);
		},
		schedule_end: function (frm) {
			refreshBuilderGuidance(frm);
		},
	});
})();
