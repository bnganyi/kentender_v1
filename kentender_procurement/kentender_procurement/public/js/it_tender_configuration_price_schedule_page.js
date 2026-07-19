// CFG-06 — Price Schedule (C2-CFG6).
// Route contract: /desk/it-tender-configuration-price-schedule/<configuration_id>
(function () {
	"use strict";

	var SURFACE_ID = "CFG-06";
	var PAGE_SLUG = "it-tender-configuration-price-schedule";
	var GET_API =
		"kentender_procurement.tender_configurations.get_tender_configuration_price_schedule";
	var SAVE_API =
		"kentender_procurement.tender_configurations.save_tender_configuration_price_schedule";
	var STORAGE_KEY = "kt_cl_cfg06_configuration_id";
	var SUBTITLE = "Define how bidders must price the tender.";
	var DRAWER_HOST_ID = "kt-cl-cfg06-drawer-host";
	var CONTINUE_ROUTE = "it-tender-configuration-evaluation-setup";
	var BACK_ROUTE = "it-tender-configuration-overview";

	var GROUP_SUPPLY = "Supply & Installation";
	var GROUP_RECURRENT = "Recurrent Cost";
	var GROUP_OPTIONAL = "Optional / Provisional";
	var SETUP_COMPLETE = "Complete";

	var TAB_ALL = "all_price_items";
	var TAB_SUPPLY = "supply_installation";
	var TAB_RECURRENT = "recurrent_costs";
	var TAB_OPTIONAL = "optional_provisional";
	var TAB_NEEDS = "needs_attention";

	// Plain labels (avoid top-level __() — page script may evaluate before desk i18n).
	var TAB_OPTIONS = [
		{ key: TAB_ALL, label: "All Price Items", testid: "kt-cl-cfg06-tab-all" },
		{
			key: TAB_SUPPLY,
			label: "Supply & Installation",
			testid: "kt-cl-cfg06-tab-supply",
		},
		{
			key: TAB_RECURRENT,
			label: "Recurrent Costs",
			testid: "kt-cl-cfg06-tab-recurrent",
		},
		{
			key: TAB_OPTIONAL,
			label: "Optional / Provisional Items",
			testid: "kt-cl-cfg06-tab-optional",
		},
		{
			key: TAB_NEEDS,
			label: "Needs Attention",
			testid: "kt-cl-cfg06-tab-needs",
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
		return (data.price_items || data.items || []).slice();
	}

	function emptyHtml() {
		return (
			'<div class="rounded border border-outline-variant bg-surface-container-lowest p-6" data-testid="kt-cl-cfg06-empty">' +
			'<p class="text-body-md text-on-surface-variant">' +
			__("Select a tender configuration from Configuration Home.") +
			"</p>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary mt-4" data-action="back-home" data-testid="kt-cl-cfg06-back">' +
			__("Back to Configuration Home") +
			"</button></div>"
		);
	}

	function statusChip(label) {
		var key = String(label || "Draft")
			.toLowerCase()
			.replace(/\s+/g, "-");
		return (
			'<span class="kt-cl-cfg06-status kt-cl-cfg06-status--' +
			esc(key) +
			'">' +
			esc(label || "Draft") +
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
				'<div class="kt-cl-cfg06-issues hidden" data-testid="kt-cl-cfg06-blockers" aria-hidden="true"></div>'
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
			'" data-testid="kt-cl-cfg06-blockers" data-expanded="' +
			(expanded ? "true" : "false") +
			'">' +
			'<button type="button" class="kt-cl-cfg06-issues-toggle" data-action="toggle-issues" data-testid="kt-cl-cfg06-issues" aria-expanded="' +
			(expanded ? "true" : "false") +
			'">' +
			'<span class="kt-cl-cfg06-issues-toggle-main">' +
			'<span class="material-symbols-outlined" aria-hidden="true">error</span>' +
			'<span data-testid="kt-cl-cfg06-issues-summary">' +
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
			'" data-testid="kt-cl-cfg06-issues-list"' +
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
		var group = String((row && (row.price_group || row.price_group_label)) || "");
		var setup = String((row && row.setup_status_label) || "");
		if (tabKey === TAB_SUPPLY) {
			return group === GROUP_SUPPLY;
		}
		if (tabKey === TAB_RECURRENT) {
			return group === GROUP_RECURRENT;
		}
		if (tabKey === TAB_OPTIONAL) {
			return group === GROUP_OPTIONAL;
		}
		if (tabKey === TAB_NEEDS) {
			return setup !== SETUP_COMPLETE;
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
			'<div class="kt-cl-cfg06-tabs-row" data-testid="kt-cl-cfg06-tabs-row">' +
			'<div class="kt-cl-cfg06-tabs" data-testid="kt-cl-cfg06-tabs" role="tablist" aria-label="' +
			esc(__("Price schedule tabs")) +
			'">' +
			tabs +
			"</div>" +
			'<div class="kt-cl-cfg06-tabs-actions" data-testid="kt-cl-cfg06-tabs-actions">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="add-item" data-testid="kt-cl-cfg06-add">' +
			'<span class="material-symbols-outlined" aria-hidden="true">add</span>' +
			__("Add Price Item") +
			"</button>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="import-items" data-testid="kt-cl-cfg06-import">' +
			'<span class="material-symbols-outlined" aria-hidden="true">download</span>' +
			__("Import Price Items") +
			"</button></div></div>"
		);
	}

	function tableHtml() {
		var comp = c();
		var cols = [
			{ label: __("ID") },
			{ label: __("Price Item") },
			{ label: __("Price Group") },
			{ label: __("Pricing Basis") },
			{ label: __("Quantity / Duration") },
			{ label: __("Source") },
			{ label: __("Evaluated Price") },
			{ label: __("Setup Status") },
			{ label: __("Action") },
		];
		var visible = filteredItems();
		var rows = visible.map(function (entry) {
			var row = entry.row || {};
			var idx = entry.index;
			var action = row.action_label || "Edit";
			var setup = row.setup_status_label || row.status_label || "Draft";
			return {
				id: row.item_id || String(idx),
				cells: [
					{ text: row.item_id || "", cls: "kt-cl-cfg06-cell-mono" },
					{ text: row.item_name || "—" },
					{ text: row.price_group_label || row.price_group || "—" },
					{ text: row.pricing_basis_label || row.pricing_basis || "—" },
					{ text: row.quantity_display || "—" },
					{ text: row.source_label || row.source_type || "—" },
					{ text: row.evaluated_price_display || row.evaluated_price_treatment || "—" },
					{ html: statusChip(setup) },
					{
						html:
							'<div class="kt-cl-cfg06-row-actions">' +
							'<button type="button" class="kt-cl-cfg06-row-action" data-action="edit-item" data-index="' +
							idx +
							'" data-testid="kt-cl-cfg06-row-action-' +
							esc(row.item_id || String(idx)) +
							'">' +
							esc(action) +
							"</button>" +
							'<button type="button" class="kt-cl-cfg06-row-delete" data-action="delete-item" data-index="' +
							idx +
							'" data-testid="kt-cl-cfg06-row-delete-' +
							esc(row.item_id || String(idx)) +
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
			'<section class="kt-cl-cfg06-table-card" data-testid="kt-cl-cfg06-table-card">' +
			tabsRowHtml() +
			'<div data-testid="kt-cl-cfg06-table">' +
			table +
			"</div></section>"
		);
	}

	function pageHtml(data) {
		var comp = c();
		var ctx = data.context || data;
		return (
			'<div data-testid="kt-cl-cfg06-root" data-configuration-id="' +
			esc(data.configuration_id || "") +
			'">' +
			comp.configurationContextStrip(ctx) +
			issuesHtml(data) +
			'<div class="kt-cl-cfg06-main" data-testid="kt-cl-cfg06-main">' +
			tableHtml() +
			"</div>" +
			comp.wizardStepFooter({
				testid: "kt-cl-cfg06-footer",
				backTestid: "kt-cl-cfg06-back",
				saveTestid: "kt-cl-cfg06-save",
				continueTestid: "kt-cl-cfg06-continue",
				backLabel: __("Back to Configuration Home"),
				saveLabel: __("Save Price Schedule"),
				continueLabel: __("Continue to Evaluation Setup"),
				saveDisabled: true,
				continueDisabled: !data.can_continue,
				extraEndActions: [
					{
						label: __("Run Check"),
						action: "run-check",
						testid: "kt-cl-cfg06-run-check",
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
					return (
						'<option value="' +
						esc(o) +
						'"' +
						(selected === o ? " selected" : "") +
						">" +
						esc(o) +
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

	function nextItemId() {
		var fromPayload = state.payload && state.payload.next_item_id;
		var maxN = 0;
		(state.items || []).forEach(function (r) {
			var m = String((r && r.item_id) || "").match(/^PRI-(\d+)$/i);
			if (m) {
				maxN = Math.max(maxN, parseInt(m[1], 10));
			}
		});
		if (fromPayload) {
			var pm = String(fromPayload).match(/^PRI-(\d+)$/i);
			if (pm) {
				maxN = Math.max(maxN, parseInt(pm[1], 10) - 1);
			}
		}
		var padded = String(maxN + 1);
		while (padded.length < 3) {
			padded = "0" + padded;
		}
		return "PRI-" + padded;
	}

	function defaultCurrency() {
		return (
			(state.payload && state.payload.currency_default) ||
			"As specified in TDS"
		);
	}

	function drawerHeaderTitle(isNew) {
		return isNew ? __("Add Price Item") : __("Edit Price Item");
	}

	function drawerHtml(row, isNew) {
		row = row || {};
		var itemId = row.item_id || (isNew ? nextItemId() : "");
		var currency = row.currency || defaultCurrency();
		var reqRef = refDisplay(row.related_requirement_ref);
		var invRef = refDisplay(row.related_inventory_ref);
		var msRef = refDisplay(row.related_milestone_ref);

		return (
			'<div class="kt-cl-cfg06-drawer-overlay" data-testid="kt-cl-cfg06-drawer-overlay" role="dialog" aria-modal="true">' +
			'<aside class="kt-cl-cfg06-drawer" data-testid="kt-cl-cfg06-drawer">' +
			'<header class="kt-cl-cfg06-drawer-header">' +
			"<div>" +
			'<h2 data-testid="kt-cl-cfg06-drawer-title">' +
			esc(drawerHeaderTitle(isNew)) +
			"</h2>" +
			'<p class="kt-cl-cfg06-drawer-eyebrow">' +
			esc(__("CFG-06 PRICE SCHEDULE")) +
			"</p></div>" +
			'<button type="button" class="kt-cl-cfg06-drawer-close" data-action="close-drawer" data-testid="kt-cl-cfg06-drawer-close" aria-label="' +
			__("Close") +
			'"><span class="material-symbols-outlined" aria-hidden="true">close</span></button></header>' +
			'<div class="kt-cl-cfg06-drawer-body" data-testid="kt-cl-cfg06-drawer-body">' +
			"<section>" +
			sectionTitle(1, __("Price Item")) +
			fieldWrap(
				__("ID"),
				'<p class="kt-cl-cfg06-readonly" data-testid="kt-cl-cfg06-drawer-id" data-item-id="' +
					esc(itemId) +
					'">' +
					esc(itemId || __("Assigned on save")) +
					"</p>",
				false
			) +
			fieldWrap(
				__("Price Item Name"),
				'<input type="text" class="kt-cl-cfg06-input" data-drawer-field="item_name" data-testid="kt-cl-cfg06-drawer-name" placeholder="' +
					esc(__("e.g. Server compute nodes")) +
					'" value="' +
					esc(row.item_name || "") +
					'" />',
				true
			) +
			fieldWrap(
				__("Price Group"),
				'<select class="kt-cl-cfg06-select" data-drawer-field="price_group" data-testid="kt-cl-cfg06-drawer-group">' +
					selectOpts(optionsFor("price_group"), row.price_group || "") +
					"</select>",
				true
			) +
			fieldWrap(
				__("Bidder-facing Description"),
				'<textarea class="kt-cl-cfg06-textarea" rows="3" data-drawer-field="bidder_facing_description" data-testid="kt-cl-cfg06-drawer-description" placeholder="' +
					esc(__("Plain instruction shown to bidders")) +
					'">' +
					esc(row.bidder_facing_description || "") +
					"</textarea>",
				true
			) +
			fieldWrap(
				__("Source"),
				'<select class="kt-cl-cfg06-select" data-drawer-field="source_type" data-testid="kt-cl-cfg06-drawer-source">' +
					selectOpts(optionsFor("source_type"), row.source_type || "") +
					"</select>",
				true
			) +
			"</section>" +
			"<section>" +
			sectionTitle(2, __("Pricing Basis")) +
			fieldWrap(
				__("Pricing Basis"),
				'<select class="kt-cl-cfg06-select" data-drawer-field="pricing_basis" data-testid="kt-cl-cfg06-drawer-basis">' +
					selectOpts(optionsFor("pricing_basis"), row.pricing_basis || "") +
					"</select>",
				true
			) +
			'<div class="kt-cl-cfg06-grid-2">' +
			fieldWrap(
				__("Quantity / Duration"),
				'<input type="text" class="kt-cl-cfg06-input" data-drawer-field="quantity" data-testid="kt-cl-cfg06-drawer-quantity" placeholder="' +
					esc(__("e.g. 12 or 36")) +
					'" value="' +
					esc(row.quantity || row.duration || "") +
					'" />',
				false
			) +
			fieldWrap(
				__("Unit"),
				'<input type="text" class="kt-cl-cfg06-input" data-drawer-field="unit" data-testid="kt-cl-cfg06-drawer-unit" placeholder="' +
					esc(__("e.g. units, months, years")) +
					'" value="' +
					esc(row.unit || "") +
					'" />',
				false
			) +
			fieldWrap(
				__("Currency"),
				'<p class="kt-cl-cfg06-readonly" data-testid="kt-cl-cfg06-drawer-currency">' +
					esc(currency) +
					"</p>",
				false
			) +
			"</div>" +
			"</section>" +
			"<section>" +
			sectionTitle(3, __("Evaluated Price")) +
			fieldWrap(
				__("Evaluated Price Treatment"),
				'<select class="kt-cl-cfg06-select" data-drawer-field="evaluated_price_treatment" data-testid="kt-cl-cfg06-drawer-evaluated">' +
					selectOpts(
						optionsFor("evaluated_price_treatment"),
						row.evaluated_price_treatment || ""
					) +
					"</select>",
				true
			) +
			fieldWrap(
				__("Conditional Rule"),
				'<textarea class="kt-cl-cfg06-textarea" rows="2" data-drawer-field="conditional_rule" data-testid="kt-cl-cfg06-drawer-conditional" placeholder="' +
					esc(__("Required when treatment is Conditional")) +
					'">' +
					esc(row.conditional_rule || "") +
					"</textarea>",
				false
			) +
			fieldWrap(
				__("Bidder Pricing Instruction"),
				'<textarea class="kt-cl-cfg06-textarea" rows="3" data-drawer-field="bidder_pricing_instruction" data-testid="kt-cl-cfg06-drawer-instruction" placeholder="' +
					esc(__("Exact instruction bidders will see")) +
					'">' +
					esc(row.bidder_pricing_instruction || "") +
					"</textarea>",
				true
			) +
			"</section>" +
			'<section data-testid="kt-cl-cfg06-drawer-references">' +
			sectionTitle(4, __("References")) +
			'<dl class="kt-cl-cfg06-refs-readonly">' +
			"<div><dt>" +
			__("Related Requirement") +
			"</dt><dd>" +
			esc(reqRef) +
			"</dd></div>" +
			"<div><dt>" +
			__("Related Inventory Item") +
			"</dt><dd>" +
			esc(invRef) +
			"</dd></div>" +
			"<div><dt>" +
			__("Related Milestone") +
			"</dt><dd>" +
			esc(msRef) +
			"</dd></div>" +
			"<div><dt>" +
			__("Evaluation Setup") +
			"</dt><dd>" +
			esc(__("Financial evaluation is configured in Evaluation Setup.")) +
			"</dd></div></dl></section></div>" +
			'<footer class="kt-cl-cfg06-drawer-footer">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="save-item" data-testid="kt-cl-cfg06-drawer-save">' +
			__("Save Item") +
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
		$host.empty().off(".cfg06drawer");
	}

	function openDrawer(index) {
		state.drawerOpen = true;
		state.editingIndex = typeof index === "number" ? index : -1;
		var isNew = state.editingIndex < 0;
		var row = isNew ? {} : state.items[state.editingIndex] || {};

		var $host = ensureDrawerHost();
		$host.html(drawerHtml(row, isNew));
		$host.off(".cfg06drawer");
		$host.on("click.cfg06drawer", "[data-action='close-drawer']", function (e) {
			e.preventDefault();
			closeDrawer();
		});
		$host.on("click.cfg06drawer", "[data-testid='kt-cl-cfg06-drawer-overlay']", function (e) {
			if (e.target === this) {
				closeDrawer();
			}
		});
		$host.on("click.cfg06drawer", "[data-action='save-item']", function (e) {
			e.preventDefault();
			saveDrawerItem($host);
		});
	}

	function collectDrawer($host) {
		var row = {};
		$host.find("[data-drawer-field]").each(function () {
			var key = String($(this).attr("data-drawer-field") || "");
			row[key] = String($(this).val() || "").trim();
		});
		var previewId = String(
			$host.find('[data-testid="kt-cl-cfg06-drawer-id"]').attr("data-item-id") || ""
		).trim();
		if (state.editingIndex >= 0 && state.items[state.editingIndex]) {
			var existing = state.items[state.editingIndex];
			row.item_id = existing.item_id || previewId;
			row.related_requirement_id = existing.related_requirement_id || "";
			row.related_inventory_id = existing.related_inventory_id || "";
			row.related_milestone_id = existing.related_milestone_id || "";
			row.related_requirement_ref = existing.related_requirement_ref || null;
			row.related_inventory_ref = existing.related_inventory_ref || null;
			row.related_milestone_ref = existing.related_milestone_ref || null;
			row.currency = existing.currency || defaultCurrency();
		} else {
			row.item_id = previewId || nextItemId();
			row.related_requirement_id = "";
			row.related_inventory_id = "";
			row.related_milestone_id = "";
			row.currency = defaultCurrency();
		}
		return row;
	}

	function persistableItems() {
		return (state.items || []).map(function (r) {
			return {
				item_id: r.item_id || "",
				item_name: r.item_name || "",
				price_group: r.price_group || r.price_group_label || "",
				bidder_facing_description: r.bidder_facing_description || "",
				source_type: r.source_type || "",
				related_requirement_id: r.related_requirement_id || "",
				related_inventory_id: r.related_inventory_id || "",
				related_milestone_id: r.related_milestone_id || "",
				pricing_basis: r.pricing_basis || r.pricing_basis_label || "",
				quantity: r.quantity || r.duration || "",
				unit: r.unit || "",
				currency: r.currency || defaultCurrency(),
				evaluated_price_treatment:
					r.evaluated_price_treatment || r.evaluated_price_treatment_label || "",
				conditional_rule: r.conditional_rule || "",
				bidder_pricing_instruction: r.bidder_pricing_instruction || "",
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
			savePriceSchedule($(state.page.main), state.page, { fromDrawer: true });
		}
	}

	function setDirty($root, dirty) {
		state.dirty = !!dirty;
		$root.find('[data-testid="kt-cl-cfg06-save"]').prop("disabled", !state.dirty || state.saving);
	}

	function refreshContinue($root, canContinue) {
		var can =
			typeof canContinue === "boolean"
				? canContinue
				: !!(state.payload && state.payload.can_continue);
		$root.find('[data-testid="kt-cl-cfg06-continue"]').prop("disabled", !can || state.saving);
	}

	function remountWithPayload(page, data, opts) {
		opts = opts || {};
		var sh = kentender_core.cl_shell;
		var surf = surface();
		var pageHeader = {
			title: __("Price Schedule"),
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

	function savePriceSchedule($root, page, opts) {
		opts = opts || {};
		if (state.saving || !state.configurationId) {
			return;
		}
		state.saving = true;
		setDirty($root, state.dirty);
		refreshContinue($root);
		var payload = { items: persistableItems() };
		if (opts.importItems) {
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
				} else if (!opts.importItems) {
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
				} else if (opts.importItems) {
					frappe.show_alert(
						{
							message: __("Price items imported"),
							indicator: "green",
						},
						5
					);
				} else if (opts.fromDelete) {
					frappe.show_alert(
						{
							message: __("Price item removed"),
							indicator: "green",
						},
						4
					);
				} else if (!opts.thenContinue && !opts.fromDrawer) {
					frappe.show_alert(
						{
							message: __("Price Schedule saved successfully"),
							indicator: "green",
						},
						5
					);
				} else if (opts.fromDrawer) {
					frappe.show_alert(
						{
							message: __("Price item saved"),
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
		$root.off(".cfg06");
		$root.on("click.cfg06", "[data-action='toggle-issues']", function (e) {
			e.preventDefault();
			state.issuesExpanded = !state.issuesExpanded;
			var $panel = $root.find('[data-testid="kt-cl-cfg06-blockers"]');
			var $list = $root.find('[data-testid="kt-cl-cfg06-issues-list"]');
			var $btn = $root.find('[data-testid="kt-cl-cfg06-issues"]');
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
		$root.on("click.cfg06", "[data-action='set-tab']", function (e) {
			e.preventDefault();
			var key = String($(this).attr("data-tab") || TAB_ALL);
			state.tabFilter = key || TAB_ALL;
			remountWithPayload(page, state.payload || {}, { keepClientList: true });
		});
		$root.on("click.cfg06", "[data-action='add-item']", function (e) {
			e.preventDefault();
			openDrawer(-1);
		});
		$root.on("click.cfg06", "[data-action='import-items']", function (e) {
			e.preventDefault();
			if (state.saving) {
				return;
			}
			savePriceSchedule($root, page, { importItems: true });
		});
		$root.on("click.cfg06", "[data-action='edit-item']", function (e) {
			e.preventDefault();
			var idx = parseInt($(this).attr("data-index"), 10);
			if (!isNaN(idx)) {
				openDrawer(idx);
			}
		});
		$root.on("click.cfg06", "[data-action='delete-item']", function (e) {
			e.preventDefault();
			e.stopPropagation();
			var idx = parseInt($(this).attr("data-index"), 10);
			if (isNaN(idx) || idx < 0 || idx >= (state.items || []).length) {
				return;
			}
			var row = state.items[idx] || {};
			var label = row.item_name || row.item_id || __("this price item");
			kentender_core.cl.confirm({
				title: __("Remove price item?"),
				message: __("{0} will be removed from this configuration.", [label]),
				confirmLabel: __("Remove"),
				cancelLabel: __("Cancel"),
				tone: "danger",
				onConfirm: function () {
					state.items.splice(idx, 1);
					state.dirty = true;
					closeDrawer();
					if (state.page) {
						savePriceSchedule($(state.page.main), state.page, { fromDelete: true });
					}
				},
			});
		});
		$root.on("click.cfg06", "[data-action='back-home']", function (e) {
			e.preventDefault();
			closeDrawer();
			if (!state.configurationId) {
				frappe.set_route("it-tender-configuration-dashboard");
				return;
			}
			frappe.route_options = { configuration_id: state.configurationId };
			frappe.set_route(BACK_ROUTE, state.configurationId);
		});
		$root.on("click.cfg06", "[data-action='save']", function (e) {
			e.preventDefault();
			if (!state.dirty || state.saving) {
				return;
			}
			savePriceSchedule($root, page, {});
		});
		$root.on("click.cfg06", "[data-action='run-check']", function (e) {
			e.preventDefault();
			if (state.saving) {
				return;
			}
			savePriceSchedule($root, page, { runCheck: true });
		});
		$root.on("click.cfg06", "[data-action='continue']", function (e) {
			e.preventDefault();
			closeDrawer();
			if (state.dirty) {
				savePriceSchedule($root, page, { thenContinue: true });
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
			title: __("Price Schedule"),
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
			title: __("Price Schedule"),
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
