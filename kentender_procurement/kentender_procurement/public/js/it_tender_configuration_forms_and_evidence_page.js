// CFG-08 — Forms & Evidence (C2-CFG8).
// Route contract: /desk/it-tender-configuration-forms-and-evidence/<configuration_id>
(function () {
	"use strict";

	var SURFACE_ID = "CFG-08";
	var PAGE_SLUG = "it-tender-configuration-forms-and-evidence";
	var GET_API =
		"kentender_procurement.tender_configurations.get_tender_configuration_forms_and_evidence";
	var SAVE_API =
		"kentender_procurement.tender_configurations.save_tender_configuration_forms_and_evidence";
	var STORAGE_KEY = "kt_cl_cfg08_configuration_id";
	var SUBTITLE =
		"Define the forms, declarations, certificates, and evidence bidders must submit.";
	var DRAWER_HOST_ID = "kt-cl-cfg08-drawer-host";
	var CONTINUE_ROUTE = "it-tender-configuration-scc";
	var BACK_ROUTE = "it-tender-configuration-overview";

	var REQ_CONDITIONAL = "Conditional";
	var REQ_NA = "Not Applicable";
	var SOURCE_STD = "STD";
	var SOURCE_USER = "User Added";

	var CAT_STANDARD = "Standard Form";
	var CAT_DECLARATION = "Declaration";
	var CAT_QUAL = "Qualification Evidence";
	var CAT_TECH = "Technical Evidence";
	var CAT_SECURITY = "Tender Security";

	var TAB_ALL = "all_items";
	var TAB_STANDARD = "standard_forms";
	var TAB_DECL = "declarations";
	var TAB_QUAL = "qualification_evidence";
	var TAB_TECH = "technical_evidence";
	var TAB_SECURITY = "tender_security";
	var TAB_CONDITIONAL = "conditional_items";

	var TAB_OPTIONS = [
		{ key: TAB_ALL, label: "All Items", testid: "kt-cl-cfg08-tab-all" },
		{
			key: TAB_STANDARD,
			label: "Standard Forms",
			testid: "kt-cl-cfg08-tab-standard",
			category: CAT_STANDARD,
		},
		{
			key: TAB_DECL,
			label: "Declarations",
			testid: "kt-cl-cfg08-tab-decl",
			category: CAT_DECLARATION,
		},
		{
			key: TAB_QUAL,
			label: "Qualification Evidence",
			testid: "kt-cl-cfg08-tab-qual",
			category: CAT_QUAL,
		},
		{
			key: TAB_TECH,
			label: "Technical Evidence",
			testid: "kt-cl-cfg08-tab-tech",
			category: CAT_TECH,
		},
		{
			key: TAB_SECURITY,
			label: "Tender Security",
			testid: "kt-cl-cfg08-tab-security",
			category: CAT_SECURITY,
		},
		{
			key: TAB_CONDITIONAL,
			label: "Conditional Items",
			testid: "kt-cl-cfg08-tab-conditional",
			requirement: REQ_CONDITIONAL,
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
		return (data.submission_items || data.items || []).slice();
	}

	function emptyHtml() {
		return (
			'<div class="rounded border border-outline-variant bg-surface-container-lowest p-6" data-testid="kt-cl-cfg08-empty">' +
			'<p class="text-body-md text-on-surface-variant">' +
			__("Select a tender configuration from Configuration Home.") +
			"</p>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary mt-4" data-action="back-home" data-testid="kt-cl-cfg08-back">' +
			__("Back to Configuration Home") +
			"</button></div>"
		);
	}

	function statusChip(label) {
		var display = String(label || "Needs attention");
		var key = display.toLowerCase().replace(/\s+/g, "-");
		return (
			'<span class="kt-cl-cfg08-status kt-cl-cfg08-status--' +
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
				'<div class="kt-cl-cfg06-issues hidden" data-testid="kt-cl-cfg08-blockers" aria-hidden="true"></div>'
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
			'" data-testid="kt-cl-cfg08-blockers" data-expanded="' +
			(expanded ? "true" : "false") +
			'">' +
			'<button type="button" class="kt-cl-cfg06-issues-toggle" data-action="toggle-issues" data-testid="kt-cl-cfg08-issues" aria-expanded="' +
			(expanded ? "true" : "false") +
			'">' +
			'<span class="kt-cl-cfg06-issues-toggle-main">' +
			'<span class="material-symbols-outlined" aria-hidden="true">error</span>' +
			'<span data-testid="kt-cl-cfg08-issues-summary">' +
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
			'" data-testid="kt-cl-cfg08-issues-list"' +
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
		var opt = null;
		TAB_OPTIONS.forEach(function (o) {
			if (o.key === tabKey) {
				opt = o;
			}
		});
		if (!opt) {
			return true;
		}
		if (opt.requirement) {
			return String((row && row.requirement) || "") === opt.requirement;
		}
		if (opt.category) {
			return String((row && (row.category || row.category_label)) || "") === opt.category;
		}
		return true;
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
			'<div class="kt-cl-cfg08-table-head" data-testid="kt-cl-cfg08-table-head">' +
			"<h3>" +
			__("Submission Requirements") +
			"</h3>" +
			'<div class="kt-cl-cfg08-table-actions" data-testid="kt-cl-cfg08-table-actions">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="add-item" data-testid="kt-cl-cfg08-add">' +
			'<span class="material-symbols-outlined" aria-hidden="true">add</span>' +
			__("Add Submission Item") +
			"</button>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="import-forms" data-testid="kt-cl-cfg08-import">' +
			'<span class="material-symbols-outlined" aria-hidden="true">download</span>' +
			__("Import Standard Forms") +
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
			'<div class="kt-cl-cfg08-tabs-row" data-testid="kt-cl-cfg08-tabs-row">' +
			'<div class="kt-cl-cfg06-tabs" data-testid="kt-cl-cfg08-tabs" role="tablist" aria-label="' +
			esc(__("Submission item filters")) +
			'">' +
			tabs +
			"</div></div>"
		);
	}

	function tableHtml() {
		var comp = c();
		var cols = [
			{ label: __("Submission Item") },
			{ label: __("Category") },
			{ label: __("Source") },
			{ label: __("Requirement") },
			{ label: __("Bidder Instruction") },
			{ label: __("Status") },
			{ label: __("Actions") },
		];
		var visible = filteredItems();
		var rows = visible.map(function (entry) {
			var row = entry.row || {};
			var idx = entry.index;
			var action = row.action_label || "Edit";
			if (action === "Continue") {
				action = "Fix";
			}
			var setup = row.setup_status_label || row.status_label || "Needs attention";
			var instruction =
				row.bidder_instruction_display ||
				row.bidder_instruction ||
				"—";
			if (instruction.length > 80) {
				instruction = instruction.slice(0, 77) + "…";
			}
			var itemId = row.item_id || "";
			var itemLabel =
				'<div class="kt-cl-cfg08-item-cell">' +
				'<span class="kt-cl-cfg08-item-name">' +
				esc(row.item_name || "—") +
				"</span>" +
				(itemId
					? '<span class="kt-cl-cfg08-item-id" data-testid="kt-cl-cfg08-item-id-' +
						esc(itemId) +
						'">' +
						esc(itemId) +
						"</span>"
					: "") +
				"</div>";
			return {
				id: itemId || String(idx),
				cells: [
					{ html: itemLabel },
					{ text: row.category_label || row.category || "—" },
					{ text: row.source_label || row.source || "—" },
					{ text: row.requirement_label || row.requirement || "—" },
					{ text: instruction },
					{ html: statusChip(setup) },
					{
						html:
							'<div class="kt-cl-cfg08-row-actions">' +
							'<button type="button" class="kt-cl-cfg08-row-action" data-action="edit-item" data-index="' +
							idx +
							'" data-testid="kt-cl-cfg08-row-action-' +
							esc(itemId || String(idx)) +
							'">' +
							esc(action) +
							"</button>" +
							'<button type="button" class="kt-cl-cfg08-row-delete" data-action="delete-item" data-index="' +
							idx +
							'" data-testid="kt-cl-cfg08-row-delete-' +
							esc(itemId || String(idx)) +
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
			footerText: __("Total Items: {0}", [rows.length]),
			showPageSize: false,
			pagination: null,
		});
		return (
			'<section class="kt-cl-cfg08-table-card" data-testid="kt-cl-cfg08-table-card">' +
			tableHeadHtml() +
			tabsRowHtml() +
			'<div data-testid="kt-cl-cfg08-table">' +
			table +
			"</div></section>"
		);
	}

	function guidanceHtml(data) {
		var g = (data && data.guidance) || {};
		return (
			'<aside class="kt-cl-cfg08-side" data-testid="kt-cl-cfg08-side">' +
			'<section class="kt-cl-cfg08-guidance" data-testid="kt-cl-cfg08-guidance">' +
			'<div class="kt-cl-cfg08-guidance-head">' +
			'<span class="material-symbols-outlined" aria-hidden="true">lightbulb</span>' +
			"<h3>" +
			esc(g.title || __("Forms & Evidence Guidance")) +
			"</h3></div>" +
			'<p class="kt-cl-cfg08-guidance-body">' +
			esc(g.body || "") +
			"</p>" +
			'<dl class="kt-cl-cfg08-guidance-counters">' +
			"<div><dt>" +
			__("Mandatory items") +
			"</dt><dd>" +
			esc(String(g.mandatory_items != null ? g.mandatory_items : 0)) +
			"</dd></div>" +
			"<div><dt>" +
			__("Conditional items") +
			"</dt><dd>" +
			esc(String(g.conditional_items != null ? g.conditional_items : 0)) +
			"</dd></div>" +
			"<div><dt>" +
			__("Items needing attention") +
			"</dt><dd>" +
			esc(String(g.items_needing_attention != null ? g.items_needing_attention : 0)) +
			"</dd></div>" +
			"<div><dt>" +
			__("Not applicable items") +
			"</dt><dd>" +
			esc(String(g.not_applicable_items != null ? g.not_applicable_items : 0)) +
			"</dd></div></dl></section></aside>"
		);
	}

	function pageHtml(data) {
		var comp = c();
		var ctx = data.context || data;
		return (
			'<div data-testid="kt-cl-cfg08-root" data-configuration-id="' +
			esc(data.configuration_id || "") +
			'">' +
			comp.configurationContextStrip(ctx) +
			issuesHtml(data) +
			'<div class="kt-cl-cfg08-layout" data-testid="kt-cl-cfg08-layout">' +
			'<div class="kt-cl-cfg08-main" data-testid="kt-cl-cfg08-main">' +
			tableHtml() +
			"</div>" +
			guidanceHtml(data) +
			"</div>" +
			comp.wizardStepFooter({
				testid: "kt-cl-cfg08-footer",
				backTestid: "kt-cl-cfg08-back",
				saveTestid: "kt-cl-cfg08-save",
				continueTestid: "kt-cl-cfg08-continue",
				backLabel: __("Back to Configuration Home"),
				saveLabel: __("Save Forms & Evidence"),
				continueLabel: __("Continue to Contract Values"),
				saveDisabled: true,
				continueDisabled: !data.can_continue,
				extraEndActions: [
					{
						label: __("Run Check"),
						action: "run-check",
						testid: "kt-cl-cfg08-run-check",
						variant: "secondary",
					},
				],
			}) +
			"</div>"
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

	function nextItemId() {
		var fromPayload = state.payload && state.payload.next_item_id;
		var maxN = 0;
		(state.items || []).forEach(function (r) {
			var m = String((r && r.item_id) || "").match(/^FE-(\d+)$/i);
			if (m) {
				maxN = Math.max(maxN, parseInt(m[1], 10));
			}
		});
		if (fromPayload) {
			var pm = String(fromPayload).match(/^FE-(\d+)$/i);
			if (pm) {
				maxN = Math.max(maxN, parseInt(pm[1], 10) - 1);
			}
		}
		var padded = String(maxN + 1);
		while (padded.length < 3) {
			padded = "0" + padded;
		}
		return "FE-" + padded;
	}

	function isStdFixed(row) {
		return String((row && row.source) || "") === SOURCE_STD;
	}

	function refDisplay(val) {
		var text = String(val || "").trim();
		return text || __("None");
	}

	function drawerHeaderTitle(isNew) {
		return isNew ? __("Add Submission Item") : __("Edit Submission Item");
	}

	function categoryFieldHtml(row, readonly) {
		var cat = row.category || row.category_label || "";
		if (readonly) {
			return fieldWrap(
				__("Category"),
				'<p class="kt-cl-cfg06-readonly" data-testid="kt-cl-cfg08-drawer-category-readonly">' +
					esc(cat || "—") +
					"</p>",
				true
			);
		}
		return fieldWrap(
			__("Category"),
			'<select class="kt-cl-cfg06-select" data-drawer-field="category" data-testid="kt-cl-cfg08-drawer-category">' +
				selectOpts(optionsFor("category"), cat) +
				"</select>",
			true
		);
	}

	function requirementSectionsHtml(row) {
		var requirement = row.requirement || row.requirement_label || "";
		var parts = [];
		if (requirement === REQ_CONDITIONAL) {
			var condSource = row.condition_source || "";
			var condSourceReadonly =
				String(row.source || "") === SOURCE_STD ||
				String(row.source || "") === "TDS" ||
				String(row.source || "") === "Evaluation Setup";
			parts.push(
				"<section>" +
					sectionTitle(3, __("Condition")) +
					fieldWrap(
						__("Condition text"),
						'<textarea class="kt-cl-cfg06-textarea" rows="2" data-drawer-field="condition_text" data-testid="kt-cl-cfg08-drawer-condition-text" placeholder="' +
							esc(__("Plain-language condition for when this item applies")) +
							'">' +
							esc(row.condition_text || "") +
							"</textarea>",
						true
					) +
					fieldWrap(
						__("Condition source"),
						condSourceReadonly
							? '<p class="kt-cl-cfg06-readonly" data-testid="kt-cl-cfg08-drawer-condition-source">' +
									esc(condSource || "—") +
									"</p>"
							: '<select class="kt-cl-cfg06-select" data-drawer-field="condition_source" data-testid="kt-cl-cfg08-drawer-condition-source-select">' +
									selectOpts(
										["TDS", "IT Requirements", "Evaluation Setup", SOURCE_USER],
										condSource
									) +
									"</select>",
						false
					) +
					"</section>"
			);
		}
		if (requirement === REQ_NA) {
			parts.push(
				"<section>" +
					sectionTitle(5, __("Applicability decision")) +
					fieldWrap(
						__("Not applicable reason"),
						'<textarea class="kt-cl-cfg06-textarea" rows="2" data-drawer-field="not_applicable_reason" data-testid="kt-cl-cfg08-drawer-na-reason" placeholder="' +
							esc(__("Explain why this item is excluded from this tender")) +
							'">' +
							esc(row.not_applicable_reason || "") +
							"</textarea>",
						true
					) +
					"</section>"
			);
		}
		return parts.join("");
	}

	function drawerHtml(row, isNew) {
		row = row || {};
		var itemId = row.item_id || (isNew ? nextItemId() : "");
		var source = row.source || row.source_label || (isNew ? SOURCE_USER : "");
		var stdFixed = isStdFixed(row);
		var saveLabel =
			String(row.setup_status_label || row.status_label || "") === "Needs attention"
				? __("Save Fix")
				: __("Save Submission Item");

		return (
			'<div class="kt-cl-cfg06-drawer-overlay" data-testid="kt-cl-cfg08-drawer-overlay" role="dialog" aria-modal="true">' +
			'<aside class="kt-cl-cfg06-drawer" data-testid="kt-cl-cfg08-drawer">' +
			'<header class="kt-cl-cfg06-drawer-header">' +
			"<div>" +
			'<h2 data-testid="kt-cl-cfg08-drawer-title">' +
			esc(drawerHeaderTitle(isNew)) +
			"</h2>" +
			'<p class="kt-cl-cfg06-drawer-eyebrow">' +
			esc(__("CFG-08 FORMS & EVIDENCE")) +
			"</p></div>" +
			'<button type="button" class="kt-cl-cfg06-drawer-close" data-action="close-drawer" data-testid="kt-cl-cfg08-drawer-close" aria-label="' +
			__("Close") +
			'"><span class="material-symbols-outlined" aria-hidden="true">close</span></button></header>' +
			'<div class="kt-cl-cfg06-drawer-body" data-testid="kt-cl-cfg08-drawer-body">' +
			"<section>" +
			sectionTitle(1, __("Submission item")) +
			fieldWrap(
				__("ID"),
				'<p class="kt-cl-cfg06-readonly" data-testid="kt-cl-cfg08-drawer-id" data-item-id="' +
					esc(itemId) +
					'">' +
					esc(itemId || __("Assigned on save")) +
					"</p>",
				false
			) +
			fieldWrap(
				__("Submission item name"),
				'<input type="text" class="kt-cl-cfg06-input" data-drawer-field="item_name" data-testid="kt-cl-cfg08-drawer-name" placeholder="' +
					esc(__("e.g. Manufacturer Authorization for Servers")) +
					'" value="' +
					esc(row.item_name || "") +
					'" />',
				true
			) +
			categoryFieldHtml(row, stdFixed) +
			fieldWrap(
				__("Source"),
				'<p class="kt-cl-cfg06-readonly" data-testid="kt-cl-cfg08-drawer-source">' +
					esc(source || SOURCE_USER) +
					"</p>",
				false
			) +
			fieldWrap(
				__("Requirement"),
				'<select class="kt-cl-cfg06-select" data-drawer-field="requirement" data-testid="kt-cl-cfg08-drawer-requirement">' +
					selectOpts(optionsFor("requirement"), row.requirement || "") +
					"</select>",
				true
			) +
			"</section>" +
			"<section>" +
			sectionTitle(2, __("Bidder instruction")) +
			fieldWrap(
				__("Bidder instruction"),
				'<textarea class="kt-cl-cfg06-textarea" rows="3" data-drawer-field="bidder_instruction" data-testid="kt-cl-cfg08-drawer-instruction" placeholder="' +
					esc(__("Exact text shown to bidders")) +
					'">' +
					esc(row.bidder_instruction || "") +
					"</textarea>",
				true
			) +
			'<div class="kt-cl-cfg06-grid-2">' +
			fieldWrap(
				__("Accepted response format"),
				'<select class="kt-cl-cfg06-select" data-drawer-field="accepted_response_format" data-testid="kt-cl-cfg08-drawer-response-format">' +
					selectOpts(
						optionsFor("accepted_response_format"),
						row.accepted_response_format || ""
					) +
					"</select>",
				false
			) +
			fieldWrap(
				__("Accepted file type"),
				'<input type="text" class="kt-cl-cfg06-input" data-drawer-field="accepted_file_type" data-testid="kt-cl-cfg08-drawer-file-type" placeholder="' +
					esc(__("Optional — e.g. PDF")) +
					'" value="' +
					esc(row.accepted_file_type || "") +
					'" />',
				false
			) +
			"</div></section>" +
			'<div data-testid="kt-cl-cfg08-drawer-requirement-host">' +
			requirementSectionsHtml(row) +
			"</div>" +
			'<section data-testid="kt-cl-cfg08-drawer-references">' +
			sectionTitle(4, __("Related configuration")) +
			'<dl class="kt-cl-cfg06-refs-readonly">' +
			"<div><dt>" +
			__("Related IT Requirement") +
			"</dt><dd>" +
			esc(refDisplay(row.related_requirement_id)) +
			"</dd></div>" +
			"<div><dt>" +
			__("Related Evaluation Criterion") +
			"</dt><dd>" +
			esc(refDisplay(row.related_criterion_id)) +
			"</dd></div>" +
			"<div><dt>" +
			__("Related TDS value") +
			"</dt><dd>" +
			esc(refDisplay(row.related_tds_key)) +
			"</dd></div></dl></section></div>" +
			'<footer class="kt-cl-cfg06-drawer-footer">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="save-item" data-testid="kt-cl-cfg08-drawer-save">' +
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
		$host.empty().off(".cfg08drawer");
	}

	function refreshDrawerRequirementFields($host) {
		var draft = collectDrawer($host);
		var $reqHost = $host.find('[data-testid="kt-cl-cfg08-drawer-requirement-host"]');
		if (!$reqHost.length) {
			return;
		}
		$reqHost.html(requirementSectionsHtml(draft));
	}

	function openDrawer(index) {
		state.drawerOpen = true;
		state.editingIndex = typeof index === "number" ? index : -1;
		var isNew = state.editingIndex < 0;
		var row = isNew ? { source: SOURCE_USER } : state.items[state.editingIndex] || {};

		var $host = ensureDrawerHost();
		$host.html(drawerHtml(row, isNew));
		$host.off(".cfg08drawer");
		$host.on("click.cfg08drawer", "[data-action='close-drawer']", function (e) {
			e.preventDefault();
			closeDrawer();
		});
		$host.on("click.cfg08drawer", "[data-testid='kt-cl-cfg08-drawer-overlay']", function (e) {
			if (e.target === this) {
				closeDrawer();
			}
		});
		$host.on("click.cfg08drawer", "[data-action='save-item']", function (e) {
			e.preventDefault();
			saveDrawerItem($host);
		});
		$host.on(
			"change.cfg08drawer",
			'[data-testid="kt-cl-cfg08-drawer-requirement"]',
			function () {
				refreshDrawerRequirementFields($host);
			}
		);
	}

	function collectDrawer($host) {
		var row = {};
		$host.find("[data-drawer-field]").each(function () {
			var key = String($(this).attr("data-drawer-field") || "");
			row[key] = String($(this).val() || "").trim();
		});
		var previewId = String(
			$host.find('[data-testid="kt-cl-cfg08-drawer-id"]').attr("data-item-id") || ""
		).trim();
		var source = String(
			$host.find('[data-testid="kt-cl-cfg08-drawer-source"]').text() || SOURCE_USER
		).trim();
		row.source = source;
		if (isStdFixed({ source: source })) {
			if (state.editingIndex >= 0 && state.items[state.editingIndex]) {
				row.category =
					state.items[state.editingIndex].category ||
					state.items[state.editingIndex].category_label ||
					row.category;
			}
		}
		if (state.editingIndex >= 0 && state.items[state.editingIndex]) {
			var existing = state.items[state.editingIndex];
			row.item_id = existing.item_id || previewId;
			row.related_requirement_id = existing.related_requirement_id || "";
			row.related_criterion_id = existing.related_criterion_id || "";
			row.related_tds_key = existing.related_tds_key || "";
			if (!row.condition_source && existing.condition_source) {
				row.condition_source = existing.condition_source;
			}
		} else {
			row.item_id = previewId || nextItemId();
			row.related_requirement_id = "";
			row.related_criterion_id = "";
			row.related_tds_key = "";
		}
		return row;
	}

	function persistableItems() {
		return (state.items || []).map(function (r) {
			return {
				item_id: r.item_id || "",
				item_name: r.item_name || "",
				category: r.category || r.category_label || "",
				source: r.source || r.source_label || "",
				requirement: r.requirement || r.requirement_label || "",
				bidder_instruction: r.bidder_instruction || "",
				accepted_response_format: r.accepted_response_format || "",
				accepted_file_type: r.accepted_file_type || "",
				condition_text: r.condition_text || "",
				condition_source: r.condition_source || "",
				related_requirement_id: r.related_requirement_id || "",
				related_criterion_id: r.related_criterion_id || "",
				related_tds_key: r.related_tds_key || "",
				not_applicable_reason: r.not_applicable_reason || "",
			};
		});
	}

	function saveDrawerItem($host) {
		var row = collectDrawer($host);
		if (state.editingIndex >= 0) {
			state.items[state.editingIndex] = Object.assign(
				{},
				state.items[state.editingIndex],
				row
			);
		} else {
			state.items.push(row);
		}
		state.dirty = true;
		closeDrawer();
		if (state.page) {
			saveFormsAndEvidence($(state.page.main), state.page, { fromDrawer: true });
		}
	}

	function setDirty($root, dirty) {
		state.dirty = !!dirty;
		$root.find('[data-testid="kt-cl-cfg08-save"]').prop("disabled", !state.dirty || state.saving);
	}

	function refreshContinue($root, canContinue) {
		var can =
			typeof canContinue === "boolean"
				? canContinue
				: !!(state.payload && state.payload.can_continue);
		$root.find('[data-testid="kt-cl-cfg08-continue"]').prop("disabled", !can || state.saving);
	}

	function remountWithPayload(page, data, opts) {
		opts = opts || {};
		var sh = kentender_core.cl_shell;
		var surf = surface();
		var pageHeader = {
			title: __("Forms & Evidence"),
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
		refreshContinue($(page.main), !!(data && data.can_continue) && !state.dirty);
		if (state.dirty) {
			refreshContinue($(page.main), false);
		}
	}

	function saveFormsAndEvidence($root, page, opts) {
		opts = opts || {};
		if (state.saving || !state.configurationId) {
			return;
		}
		state.saving = true;
		setDirty($root, state.dirty);
		refreshContinue($root);
		var payload = { submission_items: persistableItems() };
		if (opts.importForms) {
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
				} else if (!opts.importForms) {
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
				} else if (opts.importForms) {
					frappe.show_alert(
						{
							message: __("Standard forms imported"),
							indicator: "green",
						},
						5
					);
				} else if (opts.fromDelete) {
					frappe.show_alert(
						{
							message: __("Submission item removed"),
							indicator: "green",
						},
						4
					);
				} else if (!opts.thenContinue && !opts.fromDrawer) {
					frappe.show_alert(
						{
							message: __("Forms & Evidence saved successfully"),
							indicator: "green",
						},
						5
					);
				} else if (opts.fromDrawer) {
					frappe.show_alert(
						{
							message: __("Submission item saved"),
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
		$root.off(".cfg08");
		$root.on("click.cfg08", "[data-action='toggle-issues']", function (e) {
			e.preventDefault();
			state.issuesExpanded = !state.issuesExpanded;
			var $panel = $root.find('[data-testid="kt-cl-cfg08-blockers"]');
			var $list = $root.find('[data-testid="kt-cl-cfg08-issues-list"]');
			var $btn = $root.find('[data-testid="kt-cl-cfg08-issues"]');
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
		$root.on("click.cfg08", "[data-action='set-tab']", function (e) {
			e.preventDefault();
			var key = String($(this).attr("data-tab") || TAB_ALL);
			state.tabFilter = key || TAB_ALL;
			remountWithPayload(page, state.payload || {}, { keepClientList: true });
		});
		$root.on("click.cfg08", "[data-action='add-item']", function (e) {
			e.preventDefault();
			openDrawer(-1);
		});
		$root.on("click.cfg08", "[data-action='import-forms']", function (e) {
			e.preventDefault();
			if (state.saving) {
				return;
			}
			saveFormsAndEvidence($root, page, { importForms: true });
		});
		$root.on("click.cfg08", "[data-action='edit-item']", function (e) {
			e.preventDefault();
			var idx = parseInt($(this).attr("data-index"), 10);
			if (!isNaN(idx)) {
				openDrawer(idx);
			}
		});
		$root.on("click.cfg08", "[data-action='delete-item']", function (e) {
			e.preventDefault();
			e.stopPropagation();
			var idx = parseInt($(this).attr("data-index"), 10);
			if (isNaN(idx) || idx < 0 || idx >= (state.items || []).length) {
				return;
			}
			var row = state.items[idx] || {};
			var label = row.item_name || row.item_id || __("this submission item");
			kentender_core.cl.confirm({
				title: __("Remove submission item?"),
				message: __("{0} will be removed from this configuration.", [label]),
				confirmLabel: __("Remove"),
				cancelLabel: __("Cancel"),
				tone: "danger",
				onConfirm: function () {
					state.items.splice(idx, 1);
					state.dirty = true;
					closeDrawer();
					if (state.page) {
						saveFormsAndEvidence($(state.page.main), state.page, { fromDelete: true });
					}
				},
			});
		});
		$root.on("click.cfg08", "[data-action='back-home']", function (e) {
			e.preventDefault();
			closeDrawer();
			if (!state.configurationId) {
				frappe.set_route("it-tender-configuration-dashboard");
				return;
			}
			frappe.route_options = { configuration_id: state.configurationId };
			frappe.set_route(BACK_ROUTE, state.configurationId);
		});
		$root.on("click.cfg08", "[data-action='save']", function (e) {
			e.preventDefault();
			if (!state.dirty || state.saving) {
				return;
			}
			saveFormsAndEvidence($root, page, {});
		});
		$root.on("click.cfg08", "[data-action='run-check']", function (e) {
			e.preventDefault();
			if (state.saving) {
				return;
			}
			saveFormsAndEvidence($root, page, { runCheck: true });
		});
		$root.on("click.cfg08", "[data-action='continue']", function (e) {
			e.preventDefault();
			closeDrawer();
			if (state.dirty) {
				saveFormsAndEvidence($root, page, { thenContinue: true });
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
			title: __("Forms & Evidence"),
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
			title: __("Forms & Evidence"),
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
