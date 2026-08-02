// CFG-09 — Contract Values (C2-CFG9).
// Route contract: /desk/it-tender-configuration-scc/<configuration_id>
(function () {
	"use strict";

	var SURFACE_ID = "CFG-09";
	var PAGE_SLUG = "it-tender-configuration-scc";
	var GET_API =
		"kentender_procurement.tender_configurations.get_tender_configuration_contract_values";
	var SAVE_API =
		"kentender_procurement.tender_configurations.save_tender_configuration_contract_values";
	var STORAGE_KEY = "kt_cl_cfg09_configuration_id";
	var SUBTITLE =
		"Confirm the Special Conditions of Contract values and contract-facing obligations.";
	var DRAWER_HOST_ID = "kt-cl-cfg09-drawer-host";
	var BACK_ROUTE = "it-tender-configuration-overview";

	var SETUP_COMPLETE = "Complete";
	var SETUP_NEEDS_ATTENTION = "Needs attention";
	var SETUP_REVIEW = "Review before handoff";
	var SETUP_NOT_APPLICABLE = "Not applicable";

	var SOURCE_USER = "User entered";

	var CAT_SCC = "SCC Value";
	var CAT_DELIVERY = "Delivery Obligation";
	var CAT_SUPPORT = "Support & Warranty";
	var CAT_SECURITIES = "Securities & Guarantees";
	var CAT_SCHEDULE = "Contract Schedule";

	var TAB_ALL = "all_contract_values";
	var TAB_SCC = "scc_values";
	var TAB_DELIVERY = "delivery_obligations";
	var TAB_SUPPORT = "support_warranty";
	var TAB_SECURITIES = "securities_guarantees";
	var TAB_SCHEDULES = "contract_schedules";
	var TAB_NEEDS = "needs_attention";

	var TAB_OPTIONS = [
		{ key: TAB_ALL, label: "All Contract Values", testid: "kt-cl-cfg09-tab-all" },
		{
			key: TAB_SCC,
			label: "SCC Values",
			testid: "kt-cl-cfg09-tab-scc",
			category: CAT_SCC,
		},
		{
			key: TAB_DELIVERY,
			label: "Delivery Obligations",
			testid: "kt-cl-cfg09-tab-delivery",
			category: CAT_DELIVERY,
		},
		{
			key: TAB_SUPPORT,
			label: "Support & Warranty",
			testid: "kt-cl-cfg09-tab-support",
			category: CAT_SUPPORT,
		},
		{
			key: TAB_SECURITIES,
			label: "Securities & Guarantees",
			testid: "kt-cl-cfg09-tab-securities",
			category: CAT_SECURITIES,
		},
		{
			key: TAB_SCHEDULES,
			label: "Contract Schedules",
			testid: "kt-cl-cfg09-tab-schedules",
			category: CAT_SCHEDULE,
		},
		{
			key: TAB_NEEDS,
			label: "Needs Attention",
			testid: "kt-cl-cfg09-tab-needs",
		},
	];

	var state = {
		payload: null,
		configurationId: null,
		page: null,
		mounting: false,
		dirty: false,
		saving: false,
		items: [],
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

	function payloadItems(data) {
		if (!data) {
			return [];
		}
		return (data.contract_values || data.items || []).slice();
	}

	function rowStatus(row) {
		return String(
			(row && (row.setup_status_label || row.status_label || row.status)) || SETUP_NEEDS_ATTENTION
		);
	}

	function emptyHtml() {
		return (
			'<div class="rounded border border-outline-variant bg-surface-container-lowest p-6" data-testid="kt-cl-cfg09-empty">' +
			'<p class="text-body-md text-on-surface-variant">' +
			__("Select a tender configuration from Configuration Home.") +
			"</p>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary mt-4" data-action="back-home" data-testid="kt-cl-cfg09-back">' +
			__("Back to Configuration Home") +
			"</button></div>"
		);
	}

	function statusChip(label) {
		var display = String(label || SETUP_NEEDS_ATTENTION);
		var key = display.toLowerCase().replace(/\s+/g, "-");
		return (
			'<span class="kt-cl-cfg09-status kt-cl-cfg09-status--' +
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
				'<div class="kt-cl-cfg06-issues hidden" data-testid="kt-cl-cfg09-blockers" aria-hidden="true"></div>'
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
			'" data-testid="kt-cl-cfg09-blockers" data-expanded="' +
			(expanded ? "true" : "false") +
			'">' +
			'<button type="button" class="kt-cl-cfg06-issues-toggle" data-action="toggle-issues" data-testid="kt-cl-cfg09-issues" aria-expanded="' +
			(expanded ? "true" : "false") +
			'">' +
			'<span class="kt-cl-cfg06-issues-toggle-main">' +
			'<span class="material-symbols-outlined" aria-hidden="true">error</span>' +
			'<span data-testid="kt-cl-cfg09-issues-summary">' +
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
			'" data-testid="kt-cl-cfg09-issues-list"' +
			(expanded ? "" : " hidden") +
			"><ul>" +
			items +
			"</ul></div></div>"
		);
	}

	function itemMatchesTab(row, tabKey) {
		if (!tabKey || tabKey === TAB_ALL) {
			return true;
		}
		if (tabKey === TAB_NEEDS) {
			var status = rowStatus(row);
			return status === SETUP_NEEDS_ATTENTION || status === SETUP_REVIEW;
		}
		var opt = null;
		TAB_OPTIONS.forEach(function (o) {
			if (o.key === tabKey) {
				opt = o;
			}
		});
		if (!opt || !opt.category) {
			return true;
		}
		return String((row && row.category) || "") === opt.category;
	}

	function filteredItems() {
		var tabKey = state.tabFilter || TAB_ALL;
		var out = [];
		(state.items || []).forEach(function (row, idx) {
			if (itemMatchesTab(row, tabKey)) {
				out.push({ row: row, index: idx });
			}
		});
		return out;
	}

	function tableHeadHtml() {
		return (
			'<div class="kt-cl-cfg09-table-head" data-testid="kt-cl-cfg09-table-head">' +
			"<h3>" +
			__("Contract Values") +
			"</h3>" +
			'<div class="kt-cl-cfg09-table-actions" data-testid="kt-cl-cfg09-table-actions">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="add-item" data-testid="kt-cl-cfg09-add">' +
			'<span class="material-symbols-outlined" aria-hidden="true">add</span>' +
			__("Add Contract Value") +
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
			'<div class="kt-cl-cfg09-tabs-row" data-testid="kt-cl-cfg09-tabs-row">' +
			'<div class="kt-cl-cfg06-tabs" data-testid="kt-cl-cfg09-tabs" role="tablist" aria-label="' +
			esc(__("Contract value filters")) +
			'">' +
			tabs +
			"</div></div>"
		);
	}

	function tableHtml() {
		var comp = c();
		var cols = [
			{ label: __("Item") },
			{ label: __("Category") },
			{ label: __("Source") },
			{ label: __("Contract Location") },
			{ label: __("Value / Obligation") },
			{ label: __("Status") },
			{ label: __("Action") },
		];
		var visible = filteredItems();
		var rows = visible.map(function (entry) {
			var row = entry.row || {};
			var idx = entry.index;
			var action = row.action_label || "Edit";
			if (action === "Continue") {
				action = "Fix";
			}
			var setup = rowStatus(row);
			var valueText = row.value_or_obligation || "—";
			if (valueText.length > 80) {
				valueText = valueText.slice(0, 77) + "…";
			}
			return {
				id: row.contract_value_id || String(idx),
				cells: [
					{
						html:
							'<div class="kt-cl-cfg09-item-cell">' +
							'<span class="kt-cl-cfg09-item-name">' +
							esc(row.item_label || "—") +
							"</span>" +
							(row.contract_value_id
								? '<span class="kt-cl-cfg09-item-id">' +
									esc(row.contract_value_id) +
									"</span>"
								: "") +
							"</div>",
					},
					{ text: row.category || "—" },
					{ text: row.source_screen || "—" },
					{ text: row.contract_location || "—" },
					{ text: valueText },
					{ html: statusChip(setup) },
					{
						html:
							'<div class="kt-cl-cfg09-row-actions">' +
							'<button type="button" class="kt-cl-cfg09-row-action" data-action="edit-item" data-index="' +
							idx +
							'" data-testid="kt-cl-cfg09-row-action-' +
							esc(row.contract_value_id || String(idx)) +
							'">' +
							esc(action) +
							"</button></div>",
					},
				],
			};
		});
		var table = comp.queueTable({
			columns: cols,
			rows: rows,
			footerText: __("Total Items: {0}", [rows.length]),
			showPageSize: false,
			pagination: null,
		});
		return (
			'<section class="kt-cl-cfg09-table-card" data-testid="kt-cl-cfg09-table-card">' +
			tableHeadHtml() +
			tabsRowHtml() +
			'<div data-testid="kt-cl-cfg09-table">' +
			table +
			"</div></section>"
		);
	}

	function guidanceCountersHtml(data) {
		var summary = (data && data.summary) || null;
		if (!summary) {
			return "";
		}
		var parts = [];
		if (summary.total_values != null) {
			parts.push(
				"<div><dt>" +
					__("Total values") +
					"</dt><dd>" +
					esc(String(summary.total_values)) +
					"</dd></div>"
			);
		}
		if (summary.complete_values != null) {
			parts.push(
				"<div><dt>" +
					__("Complete values") +
					"</dt><dd>" +
					esc(String(summary.complete_values)) +
					"</dd></div>"
			);
		}
		if (summary.needs_attention != null) {
			parts.push(
				"<div><dt>" +
					__("Needs attention") +
					"</dt><dd>" +
					esc(String(summary.needs_attention)) +
					"</dd></div>"
			);
		}
		if (summary.review_before_handoff != null) {
			parts.push(
				"<div><dt>" +
					__("Review before handoff") +
					"</dt><dd>" +
					esc(String(summary.review_before_handoff)) +
					"</dd></div>"
			);
		}
		if (!parts.length) {
			return "";
		}
		return '<dl class="kt-cl-cfg09-guidance-counters">' + parts.join("") + "</dl>";
	}

	function guidanceHtml(data) {
		var g = (data && data.guidance) || {};
		return (
			'<aside class="kt-cl-cfg09-side" data-testid="kt-cl-cfg09-side">' +
			'<section class="kt-cl-cfg09-guidance" data-testid="kt-cl-cfg09-guidance">' +
			'<div class="kt-cl-cfg09-guidance-head">' +
			'<span class="material-symbols-outlined" aria-hidden="true">lightbulb</span>' +
			"<h3>" +
			esc(g.title || __("Contract Values Guidance")) +
			"</h3></div>" +
			'<p class="kt-cl-cfg09-guidance-body">' +
			esc(g.body || "") +
			"</p>" +
			guidanceCountersHtml(data) +
			"</section></aside>"
		);
	}

	function pageHtml(data) {
		var comp = c();
		var ctx = data.context || data;
		return (
			'<div data-testid="kt-cl-cfg09-root" data-configuration-id="' +
			esc(data.configuration_id || "") +
			'">' +
			comp.configurationContextStrip(ctx) +
			issuesHtml(data) +
			'<div class="kt-cl-cfg09-layout" data-testid="kt-cl-cfg09-layout">' +
			'<div class="kt-cl-cfg09-main" data-testid="kt-cl-cfg09-main">' +
			tableHtml() +
			"</div>" +
			guidanceHtml(data) +
			"</div>" +
			'<div class="kt-cl-cfg09-no-continue">' +
			comp.wizardStepFooter({
				testid: "kt-cl-cfg09-footer",
				backTestid: "kt-cl-cfg09-back",
				saveTestid: "kt-cl-cfg09-save",
				continueTestid: "kt-cl-cfg09-continue",
				backLabel: __("Back to Configuration Home"),
				saveLabel: __("Save Contract Values"),
				continueLabel: __("Continue"),
				saveDisabled: true,
				continueDisabled: true,
				extraEndActions: [
					{
						label: __("Run Check"),
						action: "run-check",
						testid: "kt-cl-cfg09-run-check",
						variant: "secondary",
					},
				],
			}) +
			"</div></div>"
		);
	}

	function optionsFor(key) {
		return (state.payload && state.payload.options && state.payload.options[key]) || [];
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

	function nextContractValueId() {
		var fromPayload = state.payload && state.payload.next_contract_value_id;
		var maxN = 0;
		(state.items || []).forEach(function (r) {
			var m = String((r && r.contract_value_id) || "").match(/^CV-(\d+)$/i);
			if (m) {
				maxN = Math.max(maxN, parseInt(m[1], 10));
			}
		});
		if (fromPayload) {
			var pm = String(fromPayload).match(/^CV-(\d+)$/i);
			if (pm) {
				maxN = Math.max(maxN, parseInt(pm[1], 10) - 1);
			}
		}
		var padded = String(maxN + 1);
		while (padded.length < 3) {
			padded = "0" + padded;
		}
		return "CV-" + padded;
	}

	function isEditableHere(row) {
		if (!row) {
			return true;
		}
		return !(row.editable_here === 0 || row.editable_here === "0" || row.editable_here === false);
	}

	function drawerHeaderTitle(isNew) {
		return isNew ? __("Add Contract Value") : __("Edit Contract Value");
	}

	function sourceScreenFieldHtml(row) {
		var source = row.source_screen || "";
		if (source === "Source not set") {
			source = "";
		}
		if (!isEditableHere(row)) {
			return fieldWrap(
				__("Source screen"),
				'<p class="kt-cl-cfg06-readonly" data-testid="kt-cl-cfg09-drawer-source-readonly">' +
					esc(source || "—") +
					"</p>",
				true
			);
		}
		return fieldWrap(
			__("Source screen"),
			'<select class="kt-cl-cfg06-select" data-drawer-field="source_screen" data-testid="kt-cl-cfg09-drawer-source">' +
				selectOpts(optionsFor("source_screen"), source) +
				"</select>",
			true
		);
	}

	function notApplicableSectionHtml(row) {
		var checked = row.not_applicable === 1 || row.not_applicable === "1" || row.not_applicable === true;
		return (
			fieldWrap(
				__("Not applicable"),
				'<label class="kt-cl-cfg09-checkbox-wrap">' +
					'<input type="checkbox" data-drawer-field="not_applicable" data-testid="kt-cl-cfg09-drawer-not-applicable"' +
					(checked ? " checked" : "") +
					" /> " +
					esc(__("Mark this contract value as not applicable for this tender")) +
					"</label>",
				false
			) +
			fieldWrap(
				__("Not applicable reason"),
				'<textarea class="kt-cl-cfg06-textarea" rows="2" data-drawer-field="not_applicable_reason" data-testid="kt-cl-cfg09-drawer-na-reason" placeholder="' +
					esc(__("Explain why this value does not apply")) +
					'">' +
					esc(row.not_applicable_reason || "") +
					"</textarea>",
				checked
			)
		);
	}

	function openSourceButtonHtml(row) {
		var route = String((row && row.source_route) || "").trim();
		if (!route) {
			return "";
		}
		return (
			'<div class="kt-cl-cfg09-drawer-source-action">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="open-source" data-route="' +
			esc(route) +
			'" data-testid="kt-cl-cfg09-drawer-open-source">' +
			esc(__("Open Source Step")) +
			"</button></div>"
		);
	}

	function drawerHtml(row, isNew) {
		row = row || {};
		var cvId = row.contract_value_id || (isNew ? nextContractValueId() : "");
		var saveLabel =
			rowStatus(row) === SETUP_NEEDS_ATTENTION ? __("Save Fix") : __("Save Contract Value");

		return (
			'<div class="kt-cl-cfg06-drawer-overlay" data-testid="kt-cl-cfg09-drawer-overlay" data-dismiss="explicit-only" role="dialog" aria-modal="true">' +
			'<aside class="kt-cl-cfg06-drawer" data-testid="kt-cl-cfg09-drawer">' +
			'<header class="kt-cl-cfg06-drawer-header">' +
			"<div>" +
			'<h2 data-testid="kt-cl-cfg09-drawer-title">' +
			esc(drawerHeaderTitle(isNew)) +
			"</h2>" +
			'<p class="kt-cl-cfg06-drawer-eyebrow">' +
			esc(__("CFG-09 CONTRACT VALUES")) +
			"</p></div>" +
			'<button type="button" class="kt-cl-cfg06-drawer-close" data-action="close-drawer" data-testid="kt-cl-cfg09-drawer-close" aria-label="' +
			__("Close") +
			'"><span class="material-symbols-outlined" aria-hidden="true">close</span></button></header>' +
			'<div class="kt-cl-cfg06-drawer-body" data-testid="kt-cl-cfg09-drawer-body">' +
			"<section>" +
			sectionTitle(1, __("Contract Value")) +
			fieldWrap(
				__("ID"),
				'<p class="kt-cl-cfg06-readonly" data-testid="kt-cl-cfg09-drawer-id" data-contract-value-id="' +
					esc(cvId) +
					'">' +
					esc(cvId || __("Assigned on save")) +
					"</p>",
				false
			) +
			fieldWrap(
				__("Item"),
				'<input type="text" class="kt-cl-cfg06-input" data-drawer-field="item_label" data-testid="kt-cl-cfg09-drawer-item" placeholder="' +
					esc(__("e.g. Delivery Period")) +
					'" value="' +
					esc(row.item_label || "") +
					'" />',
				true
			) +
			fieldWrap(
				__("Category"),
				'<select class="kt-cl-cfg06-select" data-drawer-field="category" data-testid="kt-cl-cfg09-drawer-category">' +
					selectOpts(optionsFor("category"), row.category || "") +
					"</select>",
				true
			) +
			sourceScreenFieldHtml(row) +
			fieldWrap(
				__("Contract location"),
				'<input type="text" class="kt-cl-cfg06-input" data-drawer-field="contract_location" data-testid="kt-cl-cfg09-drawer-location" placeholder="' +
					esc(__("e.g. SCC / Delivery Schedule")) +
					'" value="' +
					esc(row.contract_location || "") +
					'" />',
				true
			) +
			fieldWrap(
				__("Value / obligation"),
				'<textarea class="kt-cl-cfg06-textarea" rows="3" data-drawer-field="value_or_obligation" data-testid="kt-cl-cfg09-drawer-value" placeholder="' +
					esc(__("Contract-facing value or obligation text")) +
					'">' +
					esc(row.value_or_obligation || "") +
					"</textarea>",
				true
			) +
			notApplicableSectionHtml(row) +
			"</section>" +
			"<section>" +
			sectionTitle(2, __("Source")) +
			fieldWrap(
				__("Source item"),
				'<input type="text" class="kt-cl-cfg06-input" data-drawer-field="source_item_label" data-testid="kt-cl-cfg09-drawer-source-item" placeholder="' +
					esc(__("Optional upstream item label")) +
					'" value="' +
					esc(row.source_item_label || "") +
					'" />',
				false
			) +
			fieldWrap(
				__("Source value"),
				'<textarea class="kt-cl-cfg06-textarea" rows="2" data-drawer-field="source_value" data-testid="kt-cl-cfg09-drawer-source-value" placeholder="' +
					esc(__("Optional upstream value snapshot")) +
					'">' +
					esc(row.source_value || "") +
					"</textarea>",
				false
			) +
			openSourceButtonHtml(row) +
			"</section>" +
			"<section>" +
			sectionTitle(3, __("Review Notes")) +
			fieldWrap(
				__("Review note"),
				'<textarea class="kt-cl-cfg06-textarea" rows="2" data-drawer-field="review_note" data-testid="kt-cl-cfg09-drawer-review-note" placeholder="' +
					esc(__("Optional note for reviewers before handoff")) +
					'">' +
					esc(row.review_note || "") +
					"</textarea>",
				false
			) +
			"</section></div>" +
			'<footer class="kt-cl-cfg06-drawer-footer">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="save-item" data-testid="kt-cl-cfg09-drawer-save">' +
			esc(saveLabel) +
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
		$host.empty().off(".cfg09drawer");
	}

	function openDrawer(index) {
		state.drawerOpen = true;
		state.editingIndex = typeof index === "number" ? index : -1;
		var isNew = state.editingIndex < 0;
		var row = isNew
			? { source_screen: SOURCE_USER, editable_here: 1 }
			: state.items[state.editingIndex] || {};

		var $host = ensureDrawerHost();
		$host.html(drawerHtml(row, isNew));
		$host.off(".cfg09drawer");
		$host.on("click.cfg09drawer", "[data-action='close-drawer']", function (e) {
			e.preventDefault();
			closeDrawer();
		});
		// Explicit dismiss only (X / Cancel). Do not close on overlay/backdrop click —
		// that discards in-progress contract-value fields without confirmation.
		$host.on("click.cfg09drawer", "[data-action='save-item']", function (e) {
			e.preventDefault();
			saveDrawerItem($host);
		});
		$host.on("click.cfg09drawer", "[data-action='open-source']", function (e) {
			e.preventDefault();
			var route = String($(this).attr("data-route") || "").trim();
			if (route && state.configurationId) {
				frappe.route_options = { configuration_id: state.configurationId };
				frappe.set_route(route, state.configurationId);
			}
		});
	}

	function collectDrawer($host) {
		var row = {};
		$host.find("[data-drawer-field]").each(function () {
			var key = String($(this).attr("data-drawer-field") || "");
			if (key === "not_applicable") {
				row[key] = $(this).is(":checked") ? 1 : 0;
				return;
			}
			row[key] = String($(this).val() || "").trim();
		});
		var previewId = String(
			$host.find('[data-testid="kt-cl-cfg09-drawer-id"]').attr("data-contract-value-id") || ""
		).trim();
		if (state.editingIndex >= 0 && state.items[state.editingIndex]) {
			var existing = state.items[state.editingIndex];
			row.contract_value_id = existing.contract_value_id || previewId;
			row.editable_here = existing.editable_here;
			row.read_only_reason = existing.read_only_reason || "";
			row.source_route = existing.source_route || "";
			// Preserve STD binding — never drop structured keys on edit.
			row.parameter_code = existing.parameter_code || "";
			row.parameter_key = existing.parameter_key || "";
			row.readiness_parameter_id = existing.readiness_parameter_id || "";
			if (!isEditableHere(existing)) {
				row.source_screen = existing.source_screen || row.source_screen;
			}
		} else {
			row.contract_value_id = previewId || nextContractValueId();
			row.editable_here = 1;
			row.read_only_reason = "";
			row.source_route = "";
			if (!row.source_screen) {
				row.source_screen = SOURCE_USER;
			}
		}
		return row;
	}

	function persistableItems() {
		return (state.items || []).map(function (r) {
			return {
				contract_value_id: r.contract_value_id || "",
				item_label: r.item_label || "",
				category: r.category || "",
				source_screen: r.source_screen || "",
				source_item_label: r.source_item_label || "",
				source_value: r.source_value || "",
				contract_location: r.contract_location || "",
				value_or_obligation: r.value_or_obligation || "",
				not_applicable: r.not_applicable ? 1 : 0,
				not_applicable_reason: r.not_applicable_reason || "",
				review_note: r.review_note || "",
				editable_here: r.editable_here != null ? r.editable_here : 1,
				read_only_reason: r.read_only_reason || "",
				source_route: r.source_route || "",
				parameter_code: r.parameter_code || "",
				parameter_key: r.parameter_key || "",
				readiness_parameter_id: r.readiness_parameter_id || "",
			};
		});
	}

	function saveDrawerItem($host) {
		var row = collectDrawer($host);
		if (state.editingIndex >= 0) {
			state.items[state.editingIndex] = Object.assign({}, state.items[state.editingIndex], row);
		} else {
			state.items.push(row);
		}
		state.dirty = true;
		closeDrawer();
		if (state.page) {
			saveContractValues($(state.page.main), state.page, { fromDrawer: true });
		}
	}

	function setDirty($root, dirty) {
		state.dirty = !!dirty;
		$root.find('[data-testid="kt-cl-cfg09-save"]').prop("disabled", !state.dirty || state.saving);
	}

	function remountWithPayload(page, data, opts) {
		opts = opts || {};
		var sh = kentender_core.cl_shell;
		var surf = surface();
		var pageHeader = {
			title: __("Contract Values"),
			subtitle: __(SUBTITLE),
			hideBreadcrumbs: true,
		};
		if (surf && surf.chrome && surf.chrome.toolbar) {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}
		state.payload = data;
		if (!opts.keepClientList) {
			state.items = payloadItems(data);
			state.dirty = false;
		}
		sh.mountContent(page.main, {
			pageHeader: pageHeader,
			mainHtml: data ? pageHtml(data) : emptyHtml(),
		});
		bind($(page.main), page);
		setDirty($(page.main), state.dirty);
	}

	function saveContractValues($root, page, opts) {
		opts = opts || {};
		if (state.saving || !state.configurationId) {
			return;
		}
		state.saving = true;
		setDirty($root, state.dirty);
		var payload = { contract_values: persistableItems() };
		// Always merge STD-declared parameters on Run Check so blockers map to rows.
		if (opts.runCheck) {
			payload.hydrate = 1;
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
					return;
				}
				var blockerCount = data.blocker_count || 0;
				if (opts.runCheck) {
					state.showIssuesPanel = blockerCount > 0;
					state.issuesExpanded = false;
				} else if (blockerCount > 0 && data.has_progress) {
					state.showIssuesPanel = true;
				} else {
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
				} else if (opts.fromDrawer) {
					frappe.show_alert(
						{
							message: __("Contract value saved"),
							indicator: "green",
						},
						4
					);
				} else {
					frappe.show_alert(
						{
							message: __("Contract Values saved successfully"),
							indicator: "green",
						},
						5
					);
				}
			},
			error: function () {
				state.saving = false;
				remountWithPayload(page, state.payload || {}, { keepClientList: true });
				setDirty($(page.main), true);
			},
		});
	}

	function bind($root, page) {
		$root.off(".cfg09");
		$root.on("click.cfg09", "[data-action='toggle-issues']", function (e) {
			e.preventDefault();
			state.issuesExpanded = !state.issuesExpanded;
			var $panel = $root.find('[data-testid="kt-cl-cfg09-blockers"]');
			var $list = $root.find('[data-testid="kt-cl-cfg09-issues-list"]');
			var $btn = $root.find('[data-testid="kt-cl-cfg09-issues"]');
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
		$root.on("click.cfg09", "[data-action='set-tab']", function (e) {
			e.preventDefault();
			var key = String($(this).attr("data-tab") || TAB_ALL);
			state.tabFilter = key || TAB_ALL;
			remountWithPayload(page, state.payload || {}, { keepClientList: true });
		});
		$root.on("click.cfg09", "[data-action='add-item']", function (e) {
			e.preventDefault();
			openDrawer(-1);
		});
		$root.on("click.cfg09", "[data-action='edit-item']", function (e) {
			e.preventDefault();
			var idx = parseInt($(this).attr("data-index"), 10);
			if (!isNaN(idx)) {
				openDrawer(idx);
			}
		});
		$root.on("click.cfg09", "[data-action='back-home']", function (e) {
			e.preventDefault();
			closeDrawer();
			if (!state.configurationId) {
				frappe.set_route("it-tender-configuration-dashboard");
				return;
			}
			frappe.route_options = { configuration_id: state.configurationId };
			frappe.set_route(BACK_ROUTE, state.configurationId);
		});
		$root.on("click.cfg09", "[data-action='save']", function (e) {
			e.preventDefault();
			if (!state.dirty || state.saving) {
				return;
			}
			saveContractValues($root, page, {});
		});
		$root.on("click.cfg09", "[data-action='run-check']", function (e) {
			e.preventDefault();
			if (state.saving) {
				return;
			}
			saveContractValues($root, page, { runCheck: true });
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
			title: __("Contract Values"),
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
			title: __("Contract Values"),
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
