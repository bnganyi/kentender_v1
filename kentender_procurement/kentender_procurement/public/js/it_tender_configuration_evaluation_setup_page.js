// CFG-07 — Evaluation Setup (C2-CFG7).
// Route contract: /desk/it-tender-configuration-evaluation-setup/<configuration_id>
(function () {
	"use strict";

	var SURFACE_ID = "CFG-07";
	var PAGE_SLUG = "it-tender-configuration-evaluation-setup";
	var GET_API =
		"kentender_procurement.tender_configurations.get_tender_configuration_evaluation_setup";
	var SAVE_API =
		"kentender_procurement.tender_configurations.save_tender_configuration_evaluation_setup";
	var STORAGE_KEY = "kt_cl_cfg07_configuration_id";
	var SUBTITLE = "Define how bids will be evaluated.";
	var DRAWER_HOST_ID = "kt-cl-cfg07-drawer-host";
	var CONTINUE_ROUTE = "it-tender-configuration-forms-and-evidence";
	var BACK_ROUTE = "it-tender-configuration-overview";

	var SETUP_COMPLETE = "Complete";

	var STAGE_PRELIM = "Preliminary";
	var STAGE_QUAL = "Qualification";
	var STAGE_TECH = "Technical";
	var STAGE_FIN = "Financial";
	var STAGE_PREF = "Preference";

	var BASIS_PASS = "Pass/Fail";
	var BASIS_SCORED = "Scored";
	var BASIS_LOWEST = "Lowest evaluated price";
	var BASIS_PREF = "Preference rule";
	var BASIS_POST = "Post-qualification";

	var EVIDENCE_REQUIRED = "Required";

	var TAB_ALL = "all_criteria";
	var TAB_PRELIM = "preliminary_checks";
	var TAB_QUAL = "qualification";
	var TAB_TECH = "technical_evaluation";
	var TAB_FIN = "financial_evaluation";
	var TAB_PREF = "preferences_reservations";
	var TAB_NEEDS = "needs_attention";

	var TAB_OPTIONS = [
		{ key: TAB_ALL, label: "All Criteria", testid: "kt-cl-cfg07-tab-all" },
		{
			key: TAB_PRELIM,
			label: "Preliminary Checks",
			testid: "kt-cl-cfg07-tab-prelim",
		},
		{
			key: TAB_QUAL,
			label: "Qualification",
			testid: "kt-cl-cfg07-tab-qual",
		},
		{
			key: TAB_TECH,
			label: "Technical Evaluation",
			testid: "kt-cl-cfg07-tab-tech",
		},
		{
			key: TAB_FIN,
			label: "Financial Evaluation",
			testid: "kt-cl-cfg07-tab-fin",
		},
		{
			key: TAB_PREF,
			label: "Preferences & Reservations",
			testid: "kt-cl-cfg07-tab-pref",
		},
		{
			key: TAB_NEEDS,
			label: "Needs Attention",
			testid: "kt-cl-cfg07-tab-needs",
		},
	];

	var state = {
		payload: null,
		configurationId: null,
		page: null,
		mounting: false,
		dirty: false,
		saving: false,
		criteria: [],
		minimumTechnicalScore: "",
		tabFilter: TAB_ALL,
		editingIndex: -1,
		drawerOpen: false,
		showIssuesPanel: false,
		issuesExpanded: false,
	};

	function surface() {
		var reg = kentender_core.cl_surface_registry;
		return reg && typeof reg.get === "function" ? reg.get(SURFACE_ID) : null;
	}

	function c() {
		return kentender_core.cl_components || kentender_core.cl.components;
	}

	function esc(v) {
		return frappe.utils.escape_html(v == null ? "" : String(v));
	}

	function configurationId() {
		var route = frappe.get_route() || [];
		if (route.length > 1 && route[1]) {
			return String(route[1]).trim();
		}
		if (frappe.route_options && frappe.route_options.configuration_id) {
			return String(frappe.route_options.configuration_id).trim();
		}
		try {
			var params = new URLSearchParams(window.location.search || "");
			if (params.get("configuration_id")) {
				return String(params.get("configuration_id")).trim();
			}
		} catch (e) {
			/* ignore */
		}
		try {
			var stored = window.sessionStorage.getItem(STORAGE_KEY);
			if (stored) {
				return stored;
			}
		} catch (e2) {
			/* ignore */
		}
		return null;
	}

	function payloadCriteria(data) {
		if (!data) {
			return [];
		}
		return (data.criteria || data.items || []).slice();
	}

	function emptyHtml() {
		return (
			'<div class="rounded border border-outline-variant bg-surface-container-lowest p-6" data-testid="kt-cl-cfg07-empty">' +
			'<p class="text-body-md text-on-surface-variant">' +
			__("Select a tender configuration from Configuration Home.") +
			"</p>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary mt-4" data-action="back-home" data-testid="kt-cl-cfg07-back">' +
			__("Back to Configuration Home") +
			"</button></div>"
		);
	}

	function displayStatus(row) {
		var setup = String((row && (row.setup_status_label || row.status_label)) || "");
		if (setup === SETUP_COMPLETE) {
			return SETUP_COMPLETE;
		}
		return "Needs attention";
	}

	function statusChip(label) {
		var display = displayStatus({ setup_status_label: label, status_label: label });
		var key = String(display || "Needs attention")
			.toLowerCase()
			.replace(/\s+/g, "-");
		return (
			'<span class="kt-cl-cfg06-status kt-cl-cfg06-status--' +
			esc(key) +
			'">' +
			esc(display) +
			"</span>"
		);
	}

	function issuesHtml(data) {
		var blockers = data.blockers || [];
		var warnings = data.warnings || [];
		var hasProgress = !!(data && data.has_progress);
		var showPanel = blockers.length > 0 && (hasProgress || state.showIssuesPanel);
		if (!blockers.length || !showPanel) {
			return (
				'<div class="kt-cl-cfg06-issues hidden" data-testid="kt-cl-cfg07-blockers" aria-hidden="true"></div>'
			);
		}
		var n = blockers.length;
		var warnN = warnings.length;
		var summary =
			n === 1
				? __("1 item needs attention")
				: __("{0} items need attention", [n]);
		if (warnN > 0) {
			summary +=
				" · " +
				(warnN === 1 ? __("1 warning") : __("{0} warnings", [warnN]));
		}
		var items = blockers
			.map(function (b) {
				return "<li>" + esc(b.message || "") + "</li>";
			})
			.join("");
		var expanded = !!state.issuesExpanded;
		return (
			'<div class="kt-cl-cfg06-issues' +
			(expanded ? " kt-cl-cfg06-issues--open" : "") +
			'" data-testid="kt-cl-cfg07-blockers" data-expanded="' +
			(expanded ? "true" : "false") +
			'">' +
			'<button type="button" class="kt-cl-cfg06-issues-toggle" data-action="toggle-issues" data-testid="kt-cl-cfg07-issues" aria-expanded="' +
			(expanded ? "true" : "false") +
			'">' +
			'<span class="kt-cl-cfg06-issues-toggle-main">' +
			'<span class="material-symbols-outlined" aria-hidden="true">error</span>' +
			'<span data-testid="kt-cl-cfg07-issues-summary">' +
			esc(summary) +
			"</span>" +
			'<span class="kt-cl-cfg06-issues-hint">' +
			esc(__("Review details")) +
			"</span></span>" +
			'<span class="material-symbols-outlined kt-cl-cfg06-issues-chevron" aria-hidden="true">' +
			(expanded ? "expand_less" : "expand_more") +
			"</span></button>" +
			'<div class="kt-cl-cfg06-issues-body' +
			(expanded ? "" : " hidden") +
			'" data-testid="kt-cl-cfg07-issues-list"' +
			(expanded ? "" : " hidden") +
			"><ul>" +
			items +
			"</ul></div></div>"
		);
	}

	function criterionMatchesTab(row, tabKey) {
		if (!tabKey || tabKey === TAB_ALL) {
			return true;
		}
		var stage = String((row && (row.stage || row.stage_label)) || "");
		var setup = String((row && row.setup_status_label) || "");
		if (tabKey === TAB_PRELIM) {
			return stage === STAGE_PRELIM;
		}
		if (tabKey === TAB_QUAL) {
			return stage === STAGE_QUAL;
		}
		if (tabKey === TAB_TECH) {
			return stage === STAGE_TECH;
		}
		if (tabKey === TAB_FIN) {
			return stage === STAGE_FIN;
		}
		if (tabKey === TAB_PREF) {
			return stage === STAGE_PREF;
		}
		if (tabKey === TAB_NEEDS) {
			return setup !== SETUP_COMPLETE;
		}
		return true;
	}

	function filteredCriteria() {
		var tabKey = state.tabFilter || TAB_ALL;
		var out = [];
		(state.criteria || []).forEach(function (row, idx) {
			if (criterionMatchesTab(row, tabKey)) {
				out.push({ row: row, index: idx });
			}
		});
		return out;
	}

	function scoringSummaryHtml(data) {
		var summary = (data && data.scoring_summary) || {};
		if (summary.show_scoring_summary) {
			var total =
				summary.technical_scoring_total != null
					? summary.technical_scoring_total
					: summary.technical_marks_total != null
						? summary.technical_marks_total
						: "—";
			var minScore =
				summary.minimum_technical_score != null && summary.minimum_technical_score !== ""
					? summary.minimum_technical_score
					: summary.technical_pass_mark || "";
			var allocated =
				summary.allocated_technical_marks != null
					? summary.allocated_technical_marks
					: summary.configured_scored_marks != null
						? summary.configured_scored_marks
						: 0;
			var status = summary.setup_status || summary.status_label || "Needs attention";
			var allocatedNum = typeof allocated === "number" ? allocated : parseFloat(allocated) || 0;
			var totalNum = typeof total === "number" ? total : parseFloat(total) || 0;
			var remaining =
				summary.marks_remaining != null
					? summary.marks_remaining
					: Math.max(0, totalNum - allocatedNum);
			var pct = totalNum > 0 ? Math.min(100, Math.round((allocatedNum / totalNum) * 100)) : 0;
			var needs = status !== SETUP_COMPLETE;
			var statusHint =
				summary.allocation_hint ||
				(needs && !minScore
					? __("Enter the minimum technical score (overall aggregate threshold).")
					: needs
						? __(
								"Complete the remaining technical scored criteria so allocated marks equal {0}.",
								[String(total)]
						  )
						: "");
			return (
				'<div class="kt-cl-cfg07-scoring" data-testid="kt-cl-cfg07-scoring-summary">' +
				'<div class="kt-cl-cfg07-scoring-card">' +
				'<p class="kt-cl-cfg07-scoring-label">' +
				esc(__("Technical scoring total")) +
				"</p>" +
				'<p class="kt-cl-cfg07-scoring-value">' +
				esc(String(total)) +
				"</p>" +
				'<p class="kt-cl-cfg07-scoring-hint">' +
				esc(__("Total marks available for scored technical criteria (usually 100).")) +
				"</p></div>" +
				'<div class="kt-cl-cfg07-scoring-card">' +
				'<p class="kt-cl-cfg07-scoring-label">' +
				esc(__("Minimum technical score")) +
				"</p>" +
				'<div class="kt-cl-cfg07-scoring-input-wrap">' +
				'<input type="text" class="kt-cl-cfg07-scoring-input" inputmode="decimal" data-action="min-tech-score" data-testid="kt-cl-cfg07-min-tech-score" value="' +
				esc(String(minScore || "")) +
				'" placeholder="' +
				esc(__("e.g. 75")) +
				'" aria-label="' +
				esc(__("Minimum technical score")) +
				'" />' +
				'<span class="kt-cl-cfg07-scoring-of"> / ' +
				esc(String(total)) +
				"</span></div>" +
				'<p class="kt-cl-cfg07-scoring-hint">' +
				esc(
					__(
						"Overall aggregate threshold to pass technical evaluation — not per criterion."
					)
				) +
				"</p></div>" +
				'<div class="kt-cl-cfg07-scoring-card">' +
				'<p class="kt-cl-cfg07-scoring-label">' +
				esc(__("Allocated technical marks")) +
				"</p>" +
				'<p class="kt-cl-cfg07-scoring-value kt-cl-cfg07-scoring-value--split">' +
				"<span>" +
				esc(String(allocated)) +
				"</span>" +
				'<span class="kt-cl-cfg07-scoring-of"> / ' +
				esc(String(total)) +
				"</span></p>" +
				'<div class="kt-cl-cfg07-scoring-bar" aria-hidden="true"><span style="width:' +
				pct +
				'%"></span></div>' +
				'<p class="kt-cl-cfg07-scoring-hint">' +
				esc(
					remaining > 0
						? __("Sum of maximum marks on scored Technical criteria.")
						: __("Sum of maximum marks on scored Technical criteria.")
				) +
				"</p></div>" +
				'<div class="kt-cl-cfg07-scoring-card' +
				(needs ? " kt-cl-cfg07-scoring-card--alert" : "") +
				'">' +
				'<p class="kt-cl-cfg07-scoring-label">' +
				esc(__("Setup status")) +
				"</p>" +
				'<div class="kt-cl-cfg07-scoring-status">' +
				statusChip(status) +
				"</div>" +
				(statusHint
					? '<p class="kt-cl-cfg07-scoring-hint">' + esc(statusHint) + "</p>"
					: "") +
				"</div></div>"
			);
		}
		if (summary.pass_fail_message) {
			return (
				'<div class="kt-cl-cfg07-scoring kt-cl-cfg07-scoring--passfail" data-testid="kt-cl-cfg07-scoring-summary">' +
				'<p class="kt-cl-cfg07-scoring-passfail">' +
				esc(summary.pass_fail_message) +
				"</p></div>"
			);
		}
		return "";
	}

	function tableHeadHtml() {
		return (
			'<div class="kt-cl-cfg07-table-head" data-testid="kt-cl-cfg07-table-head">' +
			"<h3>" +
			__("Criteria Management") +
			"</h3>" +
			'<div class="kt-cl-cfg07-table-actions" data-testid="kt-cl-cfg07-table-actions">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="add-criterion" data-testid="kt-cl-cfg07-add">' +
			'<span class="material-symbols-outlined" aria-hidden="true">add</span>' +
			__("Add Criterion") +
			"</button>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="import-criteria" data-testid="kt-cl-cfg07-import">' +
			'<span class="material-symbols-outlined" aria-hidden="true">download</span>' +
			__("Import Suggested Criteria") +
			"</button></div></div>"
		);
	}

	function tabsRowHtml() {
		var tabs = TAB_OPTIONS.map(function (opt) {
			var active = (state.tabFilter || TAB_ALL) === opt.key;
			return (
				'<button type="button" class="kt-cl-cfg06-tab' +
				(active ? " kt-cl-cfg06-tab--active" : "") +
				'" data-action="set-tab" data-tab="' +
				esc(opt.key) +
				'" data-testid="' +
				esc(opt.testid) +
				'" aria-selected="' +
				(active ? "true" : "false") +
				'">' +
				esc(opt.label) +
				"</button>"
			);
		}).join("");
		return (
			'<div class="kt-cl-cfg07-tabs-row" data-testid="kt-cl-cfg07-tabs-row">' +
			'<div class="kt-cl-cfg06-tabs" data-testid="kt-cl-cfg07-tabs" role="tablist" aria-label="' +
			esc(__("Evaluation setup tabs")) +
			'">' +
			tabs +
			"</div></div>"
		);
	}

	function tableHtml(data) {
		var comp = c();
		var cols = [
			{ label: __("Criterion ID") },
			{ label: __("Criterion") },
			{ label: __("Stage") },
			{ label: __("Evaluation Basis") },
			{ label: __("Source / Link") },
			{ label: __("Marks / Rule") },
			{ label: __("Bidder Evidence") },
			{ label: __("Status") },
			{ label: __("Action") },
		];
		var visible = filteredCriteria();
		var rows = visible.map(function (entry) {
			var row = entry.row || {};
			var idx = entry.index;
			var action = row.action_label || "Edit";
			if (action === "Continue") {
				action = "Fix";
			}
			var setup = row.setup_status_label || row.status_label || "Needs attention";
			return {
				id: row.criterion_id || String(idx),
				cells: [
					{ text: row.criterion_id || "", cls: "kt-cl-cfg06-cell-mono" },
					{ text: row.criterion_name || "—" },
					{ text: row.stage_label || row.stage || "—" },
					{ text: row.evaluation_basis_label || row.evaluation_basis || "—" },
					{ text: row.source_label || row.source_type || "—" },
					{ text: row.marks_or_rule_display || "—" },
					{ text: row.bidder_evidence_label || row.bidder_evidence || "—" },
					{ html: statusChip(setup) },
					{
						html:
							'<div class="kt-cl-cfg06-row-actions">' +
							'<button type="button" class="kt-cl-cfg06-row-action" data-action="edit-criterion" data-index="' +
							idx +
							'" data-testid="kt-cl-cfg07-row-action-' +
							esc(row.criterion_id || String(idx)) +
							'">' +
							esc(action) +
							"</button>" +
							'<button type="button" class="kt-cl-cfg06-row-delete" data-action="delete-criterion" data-index="' +
							idx +
							'" data-testid="kt-cl-cfg07-row-delete-' +
							esc(row.criterion_id || String(idx)) +
							'" title="' +
							esc(__("Remove")) +
							'" aria-label="' +
							esc(__("Remove")) +
							'"><span class="material-symbols-outlined" aria-hidden="true">delete</span></button></div>',
					},
				],
			};
		});
		var table = comp.queueTable({
			columns: cols,
			rows: rows,
			footerText: __("Total Criteria: {0}", [rows.length]),
			showPageSize: false,
			pagination: null,
		});
		return (
			'<section class="kt-cl-cfg07-table-card" data-testid="kt-cl-cfg07-table-card">' +
			tableHeadHtml() +
			tabsRowHtml() +
			'<div data-testid="kt-cl-cfg07-table">' +
			table +
			"</div></section>"
		);
	}

	function pageHtml(data) {
		var comp = c();
		var ctx = data.context || data;
		return (
			'<div data-testid="kt-cl-cfg07-root" data-configuration-id="' +
			esc(data.configuration_id || "") +
			'">' +
			comp.configurationContextStrip(ctx) +
			issuesHtml(data) +
			'<div class="kt-cl-cfg07-main" data-testid="kt-cl-cfg07-main">' +
			scoringSummaryHtml(data) +
			tableHtml(data) +
			"</div>" +
			comp.wizardStepFooter({
				testid: "kt-cl-cfg07-footer",
				backTestid: "kt-cl-cfg07-back",
				saveTestid: "kt-cl-cfg07-save",
				continueTestid: "kt-cl-cfg07-continue",
				backLabel: __("Back to Configuration Home"),
				saveLabel: __("Save Evaluation Setup"),
				continueLabel: __("Continue to Forms & Evidence"),
				saveDisabled: true,
				continueDisabled: !data.can_continue,
				extraEndActions: [
					{
						label: __("Run Check"),
						action: "run-check",
						testid: "kt-cl-cfg07-run-check",
						variant: "secondary",
					},
				],
			}) +
			"</div>"
		);
	}

	function optionsFor(key) {
		var opts = (state.payload && state.payload.options && state.payload.options[key]) || [];
		return opts;
	}

	function selectOpts(options, selected) {
		return (
			'<option value="">' +
			esc(__("Select…")) +
			"</option>" +
			(options || [])
				.map(function (o) {
					var val = typeof o === "object" ? o.value || o.label || o.key : o;
					var label = typeof o === "object" ? o.label || o.value || o.key : o;
					return (
						'<option value="' +
						esc(val) +
						'"' +
						(selected === val ? " selected" : "") +
						">" +
						esc(label) +
						"</option>"
					);
				})
				.join("")
		);
	}

	function fieldWrap(label, controlHtml, required) {
		return (
			'<div class="kt-cl-cfg06-field">' +
			"<label>" +
			esc(label) +
			(required ? ' <span class="kt-cl-cfg06-req">*</span>' : "") +
			"</label>" +
			controlHtml +
			"</div>"
		);
	}

	function sectionTitle(n, label) {
		return (
			'<h3 class="kt-cl-cfg06-section-title">' +
			esc(String(n) + ". " + label) +
			"</h3>"
		);
	}

	function refDisplay(ref) {
		if (!ref || !(ref.id || ref.code || ref.name)) {
			return "None";
		}
		var name = ref.name || ref.code || ref.id;
		var code = ref.code || ref.id;
		if (name && code && name !== code) {
			return name + " (" + code + ")";
		}
		return name || code || "None";
	}

	function nextCriterionId() {
		var fromPayload = state.payload && state.payload.next_criterion_id;
		var maxN = 0;
		(state.criteria || []).forEach(function (r) {
			var m = String((r && r.criterion_id) || "").match(/^EVAL-(\d+)$/i);
			if (m) {
				maxN = Math.max(maxN, parseInt(m[1], 10));
			}
		});
		if (fromPayload) {
			var pm = String(fromPayload).match(/^EVAL-(\d+)$/i);
			if (pm) {
				maxN = Math.max(maxN, parseInt(pm[1], 10) - 1);
			}
		}
		var padded = String(maxN + 1);
		while (padded.length < 3) {
			padded = "0" + padded;
		}
		return "EVAL-" + padded;
	}

	function technicalMarksTotal() {
		var fromPayload = state.payload && state.payload.technical_marks_total;
		return fromPayload != null ? fromPayload : 100;
	}

	function drawerHeaderTitle(isNew) {
		return isNew ? __("Add Evaluation Criterion") : __("Edit Evaluation Criterion");
	}

	function ruleScoreFieldsHtml(row) {
		var basis = row.evaluation_basis || row.evaluation_basis_label || "";
		var stage = row.stage || row.stage_label || "";
		var parts = [];

		if (basis === BASIS_PASS || basis === BASIS_POST) {
			parts.push(
				fieldWrap(
					__("Pass/Fail Rule"),
					'<textarea class="kt-cl-cfg06-textarea" rows="2" data-drawer-field="pass_fail_rule" data-testid="kt-cl-cfg07-drawer-pass-rule" placeholder="' +
						esc(__("Describe the pass/fail rule")) +
						'">' +
						esc(row.pass_fail_rule || "") +
						"</textarea>",
					true
				)
			);
		}
		if (basis === BASIS_SCORED) {
			parts.push(
				fieldWrap(
					__("Marks"),
					'<input type="text" class="kt-cl-cfg06-input" data-drawer-field="marks" data-testid="kt-cl-cfg07-drawer-marks" placeholder="' +
						esc(__("e.g. 20")) +
						'" value="' +
						esc(row.marks || "") +
						'" />',
					true
				)
			);
			if (stage === STAGE_TECH) {
				parts.push(
					'<p class="kt-cl-cfg07-drawer-field-hint" data-testid="kt-cl-cfg07-drawer-min-score-hint">' +
						esc(
							__(
								"Set the overall Minimum technical score in the scoring summary above — not per criterion."
							)
						) +
						"</p>"
				);
			}
		}
		if (basis === BASIS_LOWEST) {
			parts.push(
				fieldWrap(
					__("Financial Evaluation Rule"),
					'<textarea class="kt-cl-cfg06-textarea" rows="2" data-drawer-field="financial_evaluation_rule" data-testid="kt-cl-cfg07-drawer-fin-rule" placeholder="' +
						esc(__("Describe how evaluated prices will be compared")) +
						'">' +
						esc(row.financial_evaluation_rule || "") +
						"</textarea>",
					true
				)
			);
		}
		if (basis === BASIS_PREF) {
			parts.push(
				fieldWrap(
					__("Preference Rule"),
					'<textarea class="kt-cl-cfg06-textarea" rows="2" data-drawer-field="preference_rule" data-testid="kt-cl-cfg07-drawer-pref-rule" placeholder="' +
						esc(__("Describe the preference or reservation rule")) +
						'">' +
						esc(row.preference_rule || "") +
						"</textarea>",
					true
				)
			);
		}
		if (!parts.length) {
			parts.push(
				'<p class="text-body-sm text-on-surface-variant" data-testid="kt-cl-cfg07-drawer-rule-hint">' +
					esc(__("Select an evaluation basis to configure marks or rules.")) +
					"</p>"
			);
		}
		return parts.join("");
	}

	function drawerHtml(row, isNew) {
		row = row || {};
		var criterionId = row.criterion_id || (isNew ? nextCriterionId() : "");
		var reqRef = refDisplay(row.related_requirement_ref);
		var priceRef = refDisplay(row.related_price_item_ref);
		var msRef = refDisplay(row.related_milestone_ref);
		var tdsRef = row.related_tds_key ? row.related_tds_key : "None";
		var disclosure = row.disclosure_check || "Incomplete";

		return (
			'<div class="kt-cl-cfg06-drawer-overlay" data-testid="kt-cl-cfg07-drawer-overlay" data-dismiss="explicit-only" role="dialog" aria-modal="true">' +
			'<aside class="kt-cl-cfg06-drawer" data-testid="kt-cl-cfg07-drawer">' +
			'<header class="kt-cl-cfg06-drawer-header">' +
			"<div>" +
			'<h2 data-testid="kt-cl-cfg07-drawer-title">' +
			esc(drawerHeaderTitle(isNew)) +
			"</h2>" +
			'<p class="kt-cl-cfg06-drawer-eyebrow">' +
			esc(__("CFG-07 EVALUATION SETUP")) +
			"</p></div>" +
			'<button type="button" class="kt-cl-cfg06-drawer-close" data-action="close-drawer" data-testid="kt-cl-cfg07-drawer-close" aria-label="' +
			__("Close") +
			'"><span class="material-symbols-outlined" aria-hidden="true">close</span></button></header>' +
			'<div class="kt-cl-cfg06-drawer-body" data-testid="kt-cl-cfg07-drawer-body">' +
			"<section>" +
			sectionTitle(1, __("Criterion")) +
			fieldWrap(
				__("Criterion ID"),
				'<p class="kt-cl-cfg06-readonly" data-testid="kt-cl-cfg07-drawer-id" data-criterion-id="' +
					esc(criterionId) +
					'">' +
					esc(criterionId || __("Assigned on save")) +
					"</p>",
				false
			) +
			fieldWrap(
				__("Criterion Name"),
				'<input type="text" class="kt-cl-cfg06-input" data-drawer-field="criterion_name" data-testid="kt-cl-cfg07-drawer-name" placeholder="' +
					esc(__("e.g. Compute node technical compliance")) +
					'" value="' +
					esc(row.criterion_name || "") +
					'" />',
				true
			) +
			fieldWrap(
				__("Stage"),
				'<select class="kt-cl-cfg06-select" data-drawer-field="stage" data-testid="kt-cl-cfg07-drawer-stage">' +
					selectOpts(optionsFor("stage"), row.stage || "") +
					"</select>",
				true
			) +
			fieldWrap(
				__("Evaluation Basis"),
				'<select class="kt-cl-cfg06-select" data-drawer-field="evaluation_basis" data-testid="kt-cl-cfg07-drawer-basis">' +
					selectOpts(optionsFor("evaluation_basis"), row.evaluation_basis || "") +
					"</select>",
				true
			) +
			fieldWrap(
				__("Source / Link"),
				'<select class="kt-cl-cfg06-select" data-drawer-field="source_type" data-testid="kt-cl-cfg07-drawer-source">' +
					selectOpts(optionsFor("source_type"), row.source_type || "") +
					"</select>",
				true
			) +
			fieldWrap(
				__("Bidder-facing Wording"),
				'<textarea class="kt-cl-cfg06-textarea" rows="3" data-drawer-field="bidder_facing_wording" data-testid="kt-cl-cfg07-drawer-wording" placeholder="' +
					esc(__("Exact wording that will appear in the tender document")) +
					'">' +
					esc(row.bidder_facing_wording || "") +
					"</textarea>",
				true
			) +
			"</section>" +
			"<section>" +
			sectionTitle(2, __("Rule / Score")) +
			'<div data-testid="kt-cl-cfg07-drawer-rule-host">' +
			ruleScoreFieldsHtml(row) +
			"</div>" +
			"</section>" +
			"<section>" +
			sectionTitle(3, __("Evidence")) +
			fieldWrap(
				__("Bidder Evidence Requirement"),
				'<select class="kt-cl-cfg06-select" data-drawer-field="bidder_evidence" data-testid="kt-cl-cfg07-drawer-evidence">' +
					selectOpts(optionsFor("bidder_evidence"), row.bidder_evidence || "") +
					"</select>",
				true
			) +
			fieldWrap(
				__("Evidence Instruction"),
				'<textarea class="kt-cl-cfg06-textarea" rows="2" data-drawer-field="evidence_instruction" data-testid="kt-cl-cfg07-drawer-evidence-instruction" placeholder="' +
					esc(__("Required when evidence is Required")) +
					'">' +
					esc(row.evidence_instruction || "") +
					"</textarea>",
				false
			) +
			"</section>" +
			"<section>" +
			sectionTitle(4, __("Evaluator Guidance")) +
			fieldWrap(
				__("Evaluator Guidance"),
				'<textarea class="kt-cl-cfg06-textarea" rows="3" data-drawer-field="evaluator_guidance" data-testid="kt-cl-cfg07-drawer-guidance" placeholder="' +
					esc(__("Optional guidance for evaluators — must not introduce hidden criteria")) +
					'">' +
					esc(row.evaluator_guidance || "") +
					"</textarea>",
				false
			) +
			fieldWrap(
				__("Disclosure Check"),
				'<p class="kt-cl-cfg06-readonly" data-testid="kt-cl-cfg07-drawer-disclosure">' +
					esc(disclosure) +
					"</p>",
				false
			) +
			"</section>" +
			'<section data-testid="kt-cl-cfg07-drawer-references">' +
			sectionTitle(5, __("References")) +
			'<dl class="kt-cl-cfg06-refs-readonly">' +
			"<div><dt>" +
			__("Related TDS Value") +
			"</dt><dd>" +
			esc(tdsRef) +
			"</dd></div>" +
			"<div><dt>" +
			__("Related Requirement") +
			"</dt><dd>" +
			esc(reqRef) +
			"</dd></div>" +
			"<div><dt>" +
			__("Related Price Item") +
			"</dt><dd>" +
			esc(priceRef) +
			"</dd></div>" +
			"<div><dt>" +
			__("Related Milestone") +
			"</dt><dd>" +
			esc(msRef) +
			"</dd></div>" +
			"<div><dt>" +
			__("Related Form / Evidence Item") +
			"</dt><dd>" +
			esc(__("Configured in Forms & Evidence.")) +
			"</dd></div></dl></section></div>" +
			'<footer class="kt-cl-cfg06-drawer-footer">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="save-criterion" data-testid="kt-cl-cfg07-drawer-save">' +
			__("Save Criterion") +
			"</button>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="close-drawer">' +
			__("Cancel") +
			"</button></footer></aside></div>"
		);
	}

	function ensureDrawerHost() {
		var host = document.getElementById(DRAWER_HOST_ID);
		if (!host) {
			host = document.createElement("div");
			host.id = DRAWER_HOST_ID;
			document.body.appendChild(host);
		}
		return $(host);
	}

	function closeDrawer() {
		state.drawerOpen = false;
		state.editingIndex = -1;
		var $host = ensureDrawerHost();
		$host.empty().off(".cfg07drawer");
	}

	function openDrawer(index) {
		state.drawerOpen = true;
		state.editingIndex = typeof index === "number" ? index : -1;
		var isNew = state.editingIndex < 0;
		var row = isNew ? {} : state.criteria[state.editingIndex] || {};

		var $host = ensureDrawerHost();
		$host.html(drawerHtml(row, isNew));
		$host.off(".cfg07drawer");
		$host.on("click.cfg07drawer", "[data-action='close-drawer']", function (e) {
			e.preventDefault();
			closeDrawer();
		});
		// Explicit dismiss only (X / Cancel). Do not close on overlay/backdrop click —
		// that discards in-progress criterion fields without confirmation.
		$host.on("click.cfg07drawer", "[data-action='save-criterion']", function (e) {
			e.preventDefault();
			saveDrawerCriterion($host);
		});
		$host.on(
			"change.cfg07drawer",
			'[data-testid="kt-cl-cfg07-drawer-stage"], [data-testid="kt-cl-cfg07-drawer-basis"]',
			function () {
				refreshDrawerRuleFields($host);
			}
		);
	}

	function refreshDrawerRuleFields($host) {
		var draft = collectDrawer($host);
		var $ruleHost = $host.find('[data-testid="kt-cl-cfg07-drawer-rule-host"]');
		if (!$ruleHost.length) {
			return;
		}
		$ruleHost.html(ruleScoreFieldsHtml(draft));
	}

	function collectDrawer($host) {
		var row = {};
		$host.find("[data-drawer-field]").each(function () {
			var key = String($(this).attr("data-drawer-field") || "");
			row[key] = String($(this).val() || "").trim();
		});
		var previewId = String(
			$host.find('[data-testid="kt-cl-cfg07-drawer-id"]').attr("data-criterion-id") || ""
		).trim();
		if (state.editingIndex >= 0 && state.criteria[state.editingIndex]) {
			var existing = state.criteria[state.editingIndex];
			row.criterion_id = existing.criterion_id || previewId;
			row.related_requirement_id = existing.related_requirement_id || "";
			row.related_price_item_id = existing.related_price_item_id || "";
			row.related_milestone_id = existing.related_milestone_id || "";
			row.related_tds_key = existing.related_tds_key || "";
			row.related_requirement_ref = existing.related_requirement_ref || null;
			row.related_price_item_ref = existing.related_price_item_ref || null;
			row.related_milestone_ref = existing.related_milestone_ref || null;
		} else {
			row.criterion_id = previewId || nextCriterionId();
			row.related_requirement_id = "";
			row.related_price_item_id = "";
			row.related_milestone_id = "";
			row.related_tds_key = "";
		}
		return row;
	}

	function persistableCriteria() {
		return (state.criteria || []).map(function (r) {
			return {
				criterion_id: r.criterion_id || "",
				criterion_name: r.criterion_name || "",
				stage: r.stage || r.stage_label || "",
				evaluation_basis: r.evaluation_basis || r.evaluation_basis_label || "",
				source_type: r.source_type || r.source_label || "",
				bidder_facing_wording: r.bidder_facing_wording || "",
				pass_fail_rule: r.pass_fail_rule || "",
				marks: r.marks || "",
				financial_evaluation_rule: r.financial_evaluation_rule || "",
				preference_rule: r.preference_rule || "",
				bidder_evidence: r.bidder_evidence || r.bidder_evidence_label || "",
				evidence_instruction: r.evidence_instruction || "",
				evaluator_guidance: r.evaluator_guidance || "",
				related_requirement_id: r.related_requirement_id || "",
				related_price_item_id: r.related_price_item_id || "",
				related_milestone_id: r.related_milestone_id || "",
				related_tds_key: r.related_tds_key || "",
			};
		});
	}

	function sharedMinimumTechnicalScore(preferred) {
		var preferredVal = String(preferred || "").trim();
		if (preferredVal) {
			return preferredVal;
		}
		if (state.minimumTechnicalScore != null && String(state.minimumTechnicalScore).trim()) {
			return String(state.minimumTechnicalScore).trim();
		}
		var summary = state.payload && state.payload.scoring_summary;
		if (summary) {
			return String(
				summary.minimum_technical_score || summary.technical_pass_mark || ""
			).trim();
		}
		return String((state.payload && state.payload.minimum_technical_score) || "").trim();
	}

	function saveDrawerCriterion($host) {
		var row = collectDrawer($host);
		if (state.editingIndex >= 0) {
			state.criteria[state.editingIndex] = Object.assign(
				{},
				state.criteria[state.editingIndex],
				row
			);
		} else {
			state.criteria.push(row);
		}
		state.dirty = true;
		closeDrawer();
		if (state.page) {
			saveEvaluationSetup($(state.page.main), state.page, { fromDrawer: true });
		}
	}

	function setDirty($root, dirty) {
		state.dirty = !!dirty;
		$root.find('[data-testid="kt-cl-cfg07-save"]').prop("disabled", !state.dirty || state.saving);
	}

	function refreshContinue($root, canContinue) {
		var can =
			typeof canContinue === "boolean"
				? canContinue
				: !!(state.payload && state.payload.can_continue);
		$root.find('[data-testid="kt-cl-cfg07-continue"]').prop("disabled", !can || state.saving);
	}

	function remountWithPayload(page, data, opts) {
		opts = opts || {};
		var sh = kentender_core.cl_shell;
		var surf = surface();
		var pageHeader = {
			title: __("Evaluation Setup"),
			subtitle: __(SUBTITLE),
			hideBreadcrumbs: true,
		};
		if (surf && surf.chrome && surf.chrome.toolbar) {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}
		state.payload = data;
		if (!opts.keepClientList) {
			state.criteria = payloadCriteria(data);
			state.dirty = false;
		}
		if (data && data.scoring_summary) {
			state.minimumTechnicalScore = String(
				data.scoring_summary.minimum_technical_score ||
					data.scoring_summary.technical_pass_mark ||
					data.minimum_technical_score ||
					""
			);
		} else if (data) {
			state.minimumTechnicalScore = String(data.minimum_technical_score || "");
		}
		sh.mountContent(page.main, {
			pageHeader: pageHeader,
			mainHtml: data ? pageHtml(data) : emptyHtml(),
		});
		bind($(page.main), page);
		setDirty($(page.main), state.dirty);
		refreshContinue($(page.main), !!(data && data.can_continue) && !state.dirty);
		if (state.dirty) {
			refreshContinue($(page.main), false);
		}
	}

	function saveEvaluationSetup($root, page, opts) {
		opts = opts || {};
		if (state.saving || !state.configurationId) {
			return;
		}
		state.saving = true;
		setDirty($root, state.dirty);
		refreshContinue($root);
		var payload = {
			criteria: persistableCriteria(),
			technical_marks_total: technicalMarksTotal(),
			minimum_technical_score: sharedMinimumTechnicalScore(opts.technicalPassMark),
			technical_pass_mark: sharedMinimumTechnicalScore(opts.technicalPassMark),
		};
		if (opts.importCriteria) {
			payload.import = 1;
		}
		frappe.call({
			method: SAVE_API,
			args: {
				configuration_id: state.configurationId,
				payload: payload,
			},
			callback: function (r) {
				state.saving = false;
				var data = r.message || null;
				if (!data) {
					remountWithPayload(page, state.payload || {}, { keepClientList: true });
					setDirty($(page.main), true);
					refreshContinue($(page.main), false);
					return;
				}
				var blockerCount = data.blocker_count || 0;
				if (opts.runCheck) {
					state.showIssuesPanel = blockerCount > 0;
					state.issuesExpanded = false;
				} else if (blockerCount > 0 && data.has_progress) {
					state.showIssuesPanel = true;
				} else if (!opts.importCriteria) {
					state.showIssuesPanel = false;
					state.issuesExpanded = false;
				}
				remountWithPayload(page, data);
				if (opts.runCheck) {
					var warnings = data.warning_count || 0;
					frappe.show_alert(
						{
							message:
								blockerCount === 0
									? __("Check complete: no blockers ({0} warnings).", [warnings])
									: __(
											"Check complete: {0} blocker(s), {1} warning(s).",
											[blockerCount, warnings]
									  ),
							indicator: blockerCount === 0 ? "green" : "orange",
						},
						6
					);
				} else if (opts.importCriteria) {
					frappe.show_alert(
						{
							message: __("Suggested criteria imported"),
							indicator: "green",
						},
						5
					);
				} else if (opts.fromDelete) {
					frappe.show_alert(
						{
							message: __("Evaluation criterion removed"),
							indicator: "green",
						},
						4
					);
				} else if (!opts.thenContinue && !opts.fromDrawer) {
					frappe.show_alert(
						{
							message: __("Evaluation Setup saved successfully"),
							indicator: "green",
						},
						5
					);
				} else if (opts.fromDrawer) {
					frappe.show_alert(
						{
							message: __("Evaluation criterion saved"),
							indicator: "green",
						},
						4
					);
				}
				if (opts.thenContinue && data.can_continue) {
					frappe.route_options = { configuration_id: state.configurationId };
					frappe.set_route(CONTINUE_ROUTE, state.configurationId);
				}
			},
			error: function () {
				state.saving = false;
				remountWithPayload(page, state.payload || {}, { keepClientList: true });
				setDirty($(page.main), true);
				refreshContinue($(page.main), false);
			},
		});
	}

	function bind($root, page) {
		$root.off(".cfg07");
		$root.on("click.cfg07", "[data-action='toggle-issues']", function (e) {
			e.preventDefault();
			state.issuesExpanded = !state.issuesExpanded;
			var $panel = $root.find('[data-testid="kt-cl-cfg07-blockers"]');
			var $list = $root.find('[data-testid="kt-cl-cfg07-issues-list"]');
			var $btn = $root.find('[data-testid="kt-cl-cfg07-issues"]');
			var $chev = $panel.find(".kt-cl-cfg06-issues-chevron");
			$panel.toggleClass("kt-cl-cfg06-issues--open", state.issuesExpanded);
			$panel.attr("data-expanded", state.issuesExpanded ? "true" : "false");
			$btn.attr("aria-expanded", state.issuesExpanded ? "true" : "false");
			$list.toggleClass("hidden", !state.issuesExpanded);
			if (state.issuesExpanded) {
				$list.removeAttr("hidden");
			} else {
				$list.attr("hidden", "hidden");
			}
			$chev.text(state.issuesExpanded ? "expand_less" : "expand_more");
		});
		$root.on("change.cfg07 input.cfg07", "[data-action='min-tech-score']", function () {
			state.minimumTechnicalScore = String($(this).val() || "").trim();
			setDirty($root, true);
			refreshContinue($root, false);
		});
		$root.on("blur.cfg07", "[data-action='min-tech-score']", function () {
			var next = String($(this).val() || "").trim();
			if (next === state.minimumTechnicalScore && !state.dirty) {
				return;
			}
			state.minimumTechnicalScore = next;
			if (state.dirty) {
				saveEvaluationSetup($root, page, { fromMinScore: true });
			}
		});
		$root.on("click.cfg07", "[data-action='set-tab']", function (e) {
			e.preventDefault();
			var key = String($(this).attr("data-tab") || TAB_ALL);
			state.tabFilter = key || TAB_ALL;
			remountWithPayload(page, state.payload || {}, { keepClientList: true });
		});
		$root.on("click.cfg07", "[data-action='add-criterion']", function (e) {
			e.preventDefault();
			openDrawer(-1);
		});
		$root.on("click.cfg07", "[data-action='import-criteria']", function (e) {
			e.preventDefault();
			if (state.saving) {
				return;
			}
			saveEvaluationSetup($root, page, { importCriteria: true });
		});
		$root.on("click.cfg07", "[data-action='edit-criterion']", function (e) {
			e.preventDefault();
			var idx = parseInt($(this).attr("data-index"), 10);
			if (!isNaN(idx)) {
				openDrawer(idx);
			}
		});
		$root.on("click.cfg07", "[data-action='delete-criterion']", function (e) {
			e.preventDefault();
			e.stopPropagation();
			var idx = parseInt($(this).attr("data-index"), 10);
			if (isNaN(idx) || idx < 0 || idx >= (state.criteria || []).length) {
				return;
			}
			var row = state.criteria[idx] || {};
			var label = row.criterion_name || row.criterion_id || __("this evaluation criterion");
			kentender_core.cl.confirm({
				title: __("Remove evaluation criterion?"),
				message: __("{0} will be removed from this configuration.", [label]),
				confirmLabel: __("Remove"),
				cancelLabel: __("Cancel"),
				tone: "danger",
				onConfirm: function () {
					state.criteria.splice(idx, 1);
					state.dirty = true;
					closeDrawer();
					if (state.page) {
						saveEvaluationSetup($(state.page.main), state.page, { fromDelete: true });
					}
				},
			});
		});
		$root.on("click.cfg07", "[data-action='back-home']", function (e) {
			e.preventDefault();
			closeDrawer();
			if (!state.configurationId) {
				frappe.set_route("it-tender-configuration-dashboard");
				return;
			}
			frappe.route_options = { configuration_id: state.configurationId };
			frappe.set_route(BACK_ROUTE, state.configurationId);
		});
		$root.on("click.cfg07", "[data-action='save']", function (e) {
			e.preventDefault();
			if (!state.dirty || state.saving) {
				return;
			}
			saveEvaluationSetup($root, page, {});
		});
		$root.on("click.cfg07", "[data-action='run-check']", function (e) {
			e.preventDefault();
			if (state.saving) {
				return;
			}
			saveEvaluationSetup($root, page, { runCheck: true });
		});
		$root.on("click.cfg07", "[data-action='continue']", function (e) {
			e.preventDefault();
			closeDrawer();
			if (state.dirty) {
				saveEvaluationSetup($root, page, { thenContinue: true });
				return;
			}
			if (state.payload && state.payload.can_continue && state.configurationId) {
				frappe.route_options = { configuration_id: state.configurationId };
				frappe.set_route(CONTINUE_ROUTE, state.configurationId);
			}
		});
	}

	function mount(page) {
		if (state.mounting) {
			return;
		}
		state.page = page;
		var sh = kentender_core.cl_shell;
		var surf = surface();
		if (!sh || typeof sh.mountContent !== "function") {
			page.main.html(
				'<div class="p-4 text-danger">' + __("Civic Ledger shell is not loaded.") + "</div>"
			);
			return;
		}
		var pageHeader = {
			title: __("Evaluation Setup"),
			subtitle: __(SUBTITLE),
			hideBreadcrumbs: true,
		};
		if (surf && surf.chrome && surf.chrome.toolbar) {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}

		var id = configurationId();
		state.configurationId = id;
		if (!id) {
			sh.mountContent(page.main, { pageHeader: pageHeader, mainHtml: emptyHtml() });
			bind($(page.main), page);
			return;
		}

		var route = frappe.get_route() || [];
		if (!(route[0] === PAGE_SLUG && route[1] === id)) {
			state.mounting = true;
			frappe.set_route(PAGE_SLUG, id);
			setTimeout(function () {
				state.mounting = false;
			}, 0);
			return;
		}

		try {
			window.sessionStorage.setItem(STORAGE_KEY, id);
		} catch (e) {
			/* ignore */
		}

		frappe.call({
			method: GET_API,
			args: { configuration_id: id },
			callback: function (r) {
				remountWithPayload(page, r.message || null);
			},
			error: function () {
				sh.mountContent(page.main, { pageHeader: pageHeader, mainHtml: emptyHtml() });
				bind($(page.main), page);
			},
		});
	}

	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Evaluation Setup"),
			single_column: true,
		});
		wrapper.page = page;
		frappe.pages[PAGE_SLUG].page = page;
		mount(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		if (wrapper && wrapper.page) {
			frappe.pages[PAGE_SLUG].page = wrapper.page;
			mount(wrapper.page);
		}
	};
})();
