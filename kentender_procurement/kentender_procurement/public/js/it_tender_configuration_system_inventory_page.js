// CFG-05 — System Inventory & Bidder Background (C2-CFG5).
// Route contract: /desk/it-tender-configuration-system-inventory/<configuration_id>
(function () {
	"use strict";

	var SURFACE_ID = "CFG-05";
	var PAGE_SLUG = "it-tender-configuration-system-inventory";
	var GET_API =
		"kentender_procurement.tender_configurations.get_tender_configuration_system_inventory";
	var SAVE_API =
		"kentender_procurement.tender_configurations.save_tender_configuration_system_inventory";
	var STORAGE_KEY = "kt_cl_cfg05_configuration_id";
	var SUBTITLE =
		"Describe the systems, sites, integrations, data, and background context bidders need to understand the IT tender.";
	var DRAWER_HOST_ID = "kt-cl-cfg05-drawer-host";
	var CONTINUE_ROUTE = "it-tender-configuration-price-schedule";
	var CATEGORY_BACKGROUND = "Background Notes";
	var CATEGORY_OUT_OF_SCOPE = "Out of Scope";
	var SCOPE_OUT = "Out of scope";

	// Plain labels (avoid top-level __() — page script may evaluate before desk i18n).
	var FILTER_OPTIONS = [
		{ key: "All", label: "All", testid: "kt-cl-cfg05-filter-all" },
		{
			key: "Systems in Scope",
			label: "Systems in Scope",
			testid: "kt-cl-cfg05-filter-systems-in-scope",
		},
		{
			key: "Infrastructure Environment",
			label: "Infrastructure Environment",
			testid: "kt-cl-cfg05-filter-infrastructure-environment",
		},
		{
			key: "Sites & Users",
			label: "Sites & Users",
			testid: "kt-cl-cfg05-filter-sites-users",
		},
		{
			key: "Integrations",
			label: "Integrations",
			testid: "kt-cl-cfg05-filter-integrations",
		},
		{
			key: "Data Migration",
			label: "Data Migration",
			testid: "kt-cl-cfg05-filter-data-migration",
		},
		{
			key: "Licensing & Support",
			label: "Licensing & Support",
			testid: "kt-cl-cfg05-filter-licensing-support",
		},
		{
			key: "Background Notes",
			label: "Background Notes",
			testid: "kt-cl-cfg05-filter-background-notes",
		},
		{
			key: "Out of Scope",
			label: "Out of Scope",
			testid: "kt-cl-cfg05-filter-out-of-scope",
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
		categoryFilter: "All",
		editingIndex: -1,
		drawerOpen: false,
		drawerRelatedReqIds: [],
		drawerRelatedMsIds: [],
		showIssuesPanel: false,
		issuesExpanded: false,
		addMode: "inventory",
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

	function emptyHtml() {
		return (
			'<div class="rounded border border-outline-variant bg-surface-container-lowest p-6" data-testid="kt-cl-cfg05-empty">' +
			'<p class="text-body-md text-on-surface-variant">' +
			__("Select a tender configuration from Configuration Home.") +
			"</p>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary mt-4" data-action="back-home" data-testid="kt-cl-cfg05-back">' +
			__("Back to Configuration Home") +
			"</button></div>"
		);
	}

	function statusChip(label) {
		var key = String(label || "Not started")
			.toLowerCase()
			.replace(/\s+/g, "-");
		return (
			'<span class="kt-cl-cfg05-status kt-cl-cfg05-status--' +
			esc(key) +
			'">' +
			esc(label || "Not started") +
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
				'<div class="kt-cl-cfg05-issues hidden" data-testid="kt-cl-cfg05-blockers" aria-hidden="true"></div>'
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
			'<div class="kt-cl-cfg05-issues' +
			(expanded ? " kt-cl-cfg05-issues--open" : "") +
			'" data-testid="kt-cl-cfg05-blockers" data-expanded="' +
			(expanded ? "true" : "false") +
			'">' +
			'<button type="button" class="kt-cl-cfg05-issues-toggle" data-action="toggle-issues" data-testid="kt-cl-cfg05-issues-toggle" aria-expanded="' +
			(expanded ? "true" : "false") +
			'">' +
			'<span class="kt-cl-cfg05-issues-toggle-main">' +
			'<span class="material-symbols-outlined" aria-hidden="true">error</span>' +
			'<span data-testid="kt-cl-cfg05-issues-summary">' +
			esc(summary) +
			"</span>" +
			'<span class="kt-cl-cfg05-issues-hint">' +
			esc(__("Review details")) +
			"</span></span>" +
			'<span class="material-symbols-outlined kt-cl-cfg05-issues-chevron" aria-hidden="true">' +
			(expanded ? "expand_less" : "expand_more") +
			"</span></button>" +
			'<div class="kt-cl-cfg05-issues-body' +
			(expanded ? "" : " hidden") +
			'" data-testid="kt-cl-cfg05-issues-list"' +
			(expanded ? "" : " hidden") +
			"><ul>" +
			items +
			"</ul></div></div>"
		);
	}

	function disclosureBannerHtml(data) {
		var banner = (data && data.disclosure_banner) || {};
		var primary = banner.primary || "";
		var secondary = banner.secondary || "";
		if (!primary && !secondary) {
			return "";
		}
		return (
			'<div class="kt-cl-cfg05-banner" data-testid="kt-cl-cfg05-banner" role="note">' +
			'<span class="material-symbols-outlined" aria-hidden="true">shield</span>' +
			"<div>" +
			(primary
				? '<p class="kt-cl-cfg05-banner-primary">' + esc(primary) + "</p>"
				: "") +
			(secondary
				? '<p class="kt-cl-cfg05-banner-secondary">' + esc(secondary) + "</p>"
				: "") +
			"</div></div>"
		);
	}

	function itemMatchesFilter(row, filterKey) {
		if (!filterKey || filterKey === "All") {
			return true;
		}
		var cat = String((row && row.category_label) || "");
		var scope = String((row && row.scope_label) || "");
		if (filterKey === CATEGORY_OUT_OF_SCOPE) {
			return cat === CATEGORY_OUT_OF_SCOPE || scope === SCOPE_OUT;
		}
		return cat === filterKey;
	}

	function filteredItems() {
		var filterKey = state.categoryFilter || "All";
		var out = [];
		(state.items || []).forEach(function (row, idx) {
			if (itemMatchesFilter(row, filterKey)) {
				out.push({ row: row, index: idx });
			}
		});
		return out;
	}

	function filtersHtml() {
		var chips = FILTER_OPTIONS.map(function (opt) {
			var active = (state.categoryFilter || "All") === opt.key;
			return (
				'<button type="button" class="kt-cl-cfg05-filter-chip' +
				(active ? " kt-cl-cfg05-filter-chip--active" : "") +
				'" data-action="set-filter" data-filter="' +
				esc(opt.key) +
				'" data-testid="' +
				esc(opt.testid) +
				'" aria-pressed="' +
				(active ? "true" : "false") +
				'">' +
				esc(opt.label) +
				"</button>"
			);
		}).join("");
		return (
			'<div class="kt-cl-cfg05-filters" data-testid="kt-cl-cfg05-filters" role="toolbar" aria-label="' +
			esc(__("Category filters")) +
			'">' +
			chips +
			"</div>"
		);
	}

	function tableHtml() {
		var comp = c();
		var cols = [
			{ label: __("ID") },
			{ label: __("Item") },
			{ label: __("Category") },
			{ label: __("Scope") },
			{ label: __("Bidder Consideration") },
			{ label: __("Disclosure Status") },
			{ label: __("Price Link") },
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
					{ text: row.item_id || "", cls: "kt-cl-cfg05-cell-mono" },
					{ text: row.item_title || "—" },
					{ text: row.category_label || "—" },
					{ text: row.scope_label || "—" },
					{
						text:
							row.bidder_consideration_display ||
							row.bidder_consideration ||
							"—",
					},
					{
						text:
							row.disclosure_status_display ||
							row.disclosure_status_label ||
							"—",
					},
					{
						text: row.price_link_display || row.price_link_label || "—",
					},
					{ html: statusChip(setup) },
					{
						html:
							'<div class="kt-cl-cfg05-row-actions">' +
							'<button type="button" class="kt-cl-cfg05-row-action" data-action="edit-item" data-index="' +
							idx +
							'" data-testid="kt-cl-cfg05-row-action-' +
							esc(row.item_id || String(idx)) +
							'">' +
							esc(action) +
							"</button>" +
							'<button type="button" class="kt-cl-cfg05-row-delete" data-action="delete-item" data-index="' +
							idx +
							'" data-testid="kt-cl-cfg05-row-delete-' +
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
			'<section class="kt-cl-cfg05-table-card" data-testid="kt-cl-cfg05-table-card">' +
			'<div class="kt-cl-cfg05-table-head">' +
			"<h3>" +
			__("Inventory & Background") +
			"</h3>" +
			'<div class="kt-cl-cfg05-table-actions">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="add-inventory" data-testid="kt-cl-cfg05-add">' +
			'<span class="material-symbols-outlined" aria-hidden="true">add</span>' +
			__("Add Inventory Item") +
			"</button>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="add-background" data-testid="kt-cl-cfg05-add-background">' +
			'<span class="material-symbols-outlined" aria-hidden="true">note_add</span>' +
			__("Add Background Note") +
			"</button></div></div>" +
			'<div data-testid="kt-cl-cfg05-table">' +
			table +
			"</div></section>"
		);
	}

	function guidanceHtml(data) {
		var g = (data && data.guidance) || {};
		return (
			'<aside class="kt-cl-cfg05-side" data-testid="kt-cl-cfg05-side">' +
			'<section class="kt-cl-cfg05-guidance" data-testid="kt-cl-cfg05-guidance">' +
			'<div class="kt-cl-cfg05-guidance-head">' +
			'<span class="material-symbols-outlined" aria-hidden="true">lightbulb</span>' +
			"<h3>" +
			esc(g.title || __("Inventory & Background Guidance")) +
			"</h3></div>" +
			'<p class="kt-cl-cfg05-guidance-body">' +
			esc(g.body || "") +
			"</p>" +
			'<dl class="kt-cl-cfg05-guidance-list">' +
			"<div><dt>" +
			__("What this affects") +
			"</dt><dd>" +
			esc(g.what_this_affects || "") +
			"</dd></div>" +
			"<div><dt>" +
			__("Used later by") +
			"</dt><dd>" +
			esc(g.used_later_by || "") +
			"</dd></div>" +
			"<div><dt>" +
			__("Not configured here") +
			"</dt><dd>" +
			esc(g.not_configured_here || "") +
			"</dd></div></dl></section></aside>"
		);
	}

	function pageHtml(data) {
		var comp = c();
		var ctx = data.context || data;
		return (
			'<div data-testid="kt-cl-cfg05-root" data-configuration-id="' +
			esc(data.configuration_id || "") +
			'">' +
			comp.configurationContextStrip(ctx) +
			issuesHtml(data) +
			disclosureBannerHtml(data) +
			'<div class="kt-cl-cfg05-layout" data-testid="kt-cl-cfg05-layout">' +
			'<div class="kt-cl-cfg05-main" data-testid="kt-cl-cfg05-main">' +
			filtersHtml() +
			tableHtml() +
			"</div>" +
			guidanceHtml(data) +
			"</div>" +
			comp.wizardStepFooter({
				testid: "kt-cl-cfg05-footer",
				backTestid: "kt-cl-cfg05-back",
				saveTestid: "kt-cl-cfg05-save",
				continueTestid: "kt-cl-cfg05-continue",
				backLabel: __("Back to Configuration Home"),
				saveLabel: __("Save Inventory & Background"),
				continueLabel: __("Continue to Price Schedule"),
				saveDisabled: true,
				continueDisabled: !data.can_continue,
				extraEndActions: [
					{
						label: __("Run Check"),
						action: "run-check",
						testid: "kt-cl-cfg05-run-check",
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
			'<div class="kt-cl-cfg05-field">' +
			"<label>" +
			esc(label) +
			(required ? ' <span class="kt-cl-cfg05-req">*</span>' : "") +
			"</label>" +
			controlHtml +
			"</div>"
		);
	}

	function sectionTitle(n, label) {
		return (
			'<h3 class="kt-cl-cfg05-section-title">' +
			esc(String(n) + ". " + label) +
			"</h3>"
		);
	}

	function availableRequirements() {
		return (state.payload && state.payload.available_requirements) || [];
	}

	function availableMilestones() {
		return (state.payload && state.payload.available_milestones) || [];
	}

	function refById(list, id) {
		var rid = String(id || "");
		var found = null;
		(list || []).forEach(function (r) {
			if (String(r.id || "") === rid) {
				found = r;
			}
		});
		return found;
	}

	function relatedChipsHtml(kind, selectedIds) {
		var isReq = kind === "req";
		var available = isReq ? availableRequirements() : availableMilestones();
		var selected = selectedIds || [];
		var emptyHint = isReq
			? __("Optional — link configured IT Requirements")
			: __("Optional — link configured milestones");
		var pickEmpty = isReq
			? __("No IT Requirements configured")
			: __("No milestones configured");
		var pickAdd = __("+ Add Reference");
		var testidField = isReq
			? "kt-cl-cfg05-drawer-related-req"
			: "kt-cl-cfg05-drawer-related-ms";
		var testidChips = isReq
			? "kt-cl-cfg05-drawer-related-req-chips"
			: "kt-cl-cfg05-drawer-related-ms-chips";
		var testidPick = isReq
			? "kt-cl-cfg05-drawer-related-req-pick"
			: "kt-cl-cfg05-drawer-related-ms-pick";
		var removeAction = isReq ? "remove-related-req" : "remove-related-ms";

		var chips = selected
			.map(function (id) {
				var ref = refById(available, id) || { id: id, code: id, name: id };
				var label = ref.code || ref.id;
				var title =
					ref.name && ref.code
						? ref.name + " (" + ref.code + ")"
						: ref.name || ref.code || id;
				return (
					'<span class="kt-cl-cfg05-chip" data-related-id="' +
					esc(ref.id || id) +
					'" title="' +
					esc(title) +
					'">' +
					esc(label) +
					'<button type="button" class="kt-cl-cfg05-chip-remove" data-action="' +
					removeAction +
					'" data-related-id="' +
					esc(ref.id || id) +
					'" aria-label="' +
					esc(__("Remove")) +
					'"><span class="material-symbols-outlined" aria-hidden="true">close</span></button></span>'
				);
			})
			.join("");

		var remaining = available.filter(function (r) {
			return selected.indexOf(String(r.id || "")) < 0;
		});
		var pickOpts =
			'<option value="">' +
			esc(remaining.length ? pickAdd : pickEmpty) +
			"</option>";
		remaining.forEach(function (r) {
			var primary = r.name || r.code || r.id;
			var secondary = r.code && r.name ? r.code : "";
			pickOpts +=
				'<option value="' +
				esc(r.id) +
				'">' +
				esc(primary) +
				(secondary ? " (" + esc(secondary) + ")" : "") +
				"</option>";
		});

		return (
			'<div class="kt-cl-cfg05-chip-field" data-testid="' +
			testidField +
			'">' +
			'<div class="kt-cl-cfg05-chips" data-testid="' +
			testidChips +
			'">' +
			(chips ||
				'<span class="kt-cl-cfg05-chip-empty">' + esc(emptyHint) + "</span>") +
			"</div>" +
			'<select class="kt-cl-cfg05-select kt-cl-cfg05-related-pick" data-testid="' +
			testidPick +
			'"' +
			(remaining.length ? "" : " disabled") +
			">" +
			pickOpts +
			"</select></div>"
		);
	}

	function nextItemId(background) {
		var prefix = background ? "BG" : "INV";
		var fromPayload = background
			? state.payload && state.payload.next_background_id
			: state.payload && state.payload.next_inventory_id;
		var maxN = 0;
		(state.items || []).forEach(function (r) {
			var m = String((r && r.item_id) || "").match(
				new RegExp("^" + prefix + "-(\\d+)$", "i")
			);
			if (m) {
				maxN = Math.max(maxN, parseInt(m[1], 10));
			}
		});
		if (fromPayload) {
			var pm = String(fromPayload).match(new RegExp("^" + prefix + "-(\\d+)$", "i"));
			if (pm) {
				maxN = Math.max(maxN, parseInt(pm[1], 10) - 1);
			}
		}
		var padded = String(maxN + 1);
		while (padded.length < 3) {
			padded = "0" + padded;
		}
		return prefix + "-" + padded;
	}

	function drawerHeaderTitle(isNew) {
		if (!isNew) {
			return __("Edit Item");
		}
		return state.addMode === "background"
			? __("Add Background Note")
			: __("Add Inventory Item");
	}

	function drawerHtml(row, isNew) {
		row = row || {};
		var isBackground =
			state.addMode === "background" ||
			String(row.category_label || "") === CATEGORY_BACKGROUND;
		var itemId =
			row.item_id || (isNew ? nextItemId(isBackground) : "");
		var relatedReqIds = (state.drawerRelatedReqIds || []).slice();
		var relatedMsIds = (state.drawerRelatedMsIds || []).slice();
		var refs = row.references || {
			it_requirements: relatedReqIds.length
				? "Linked to IT Requirement"
				: "No requirement link selected",
			implementation_schedule: relatedMsIds.length
				? "Linked to milestone"
				: "No milestone link selected",
			price_schedule: row.price_link_label || "No price link expected",
			contract_values:
				row.scope_label === "In scope"
					? "May carry into contract values"
					: "No contract carry-forward expected",
		};
		var defaultCategory = isBackground
			? CATEGORY_BACKGROUND
			: row.category_label || "";

		return (
			'<div class="kt-cl-cfg05-drawer-overlay" data-testid="kt-cl-cfg05-drawer-overlay" data-dismiss="explicit-only" role="dialog" aria-modal="true">' +
			'<aside class="kt-cl-cfg05-drawer" data-testid="kt-cl-cfg05-drawer">' +
			'<header class="kt-cl-cfg05-drawer-header">' +
			"<div>" +
			'<h2 data-testid="kt-cl-cfg05-drawer-title">' +
			esc(drawerHeaderTitle(isNew)) +
			"</h2>" +
			'<p class="kt-cl-cfg05-drawer-eyebrow">' +
			esc(__("CFG-05 INVENTORY")) +
			"</p></div>" +
			'<button type="button" class="kt-cl-cfg05-drawer-close" data-action="close-drawer" data-testid="kt-cl-cfg05-drawer-close" aria-label="' +
			__("Close") +
			'"><span class="material-symbols-outlined" aria-hidden="true">close</span></button></header>' +
			'<div class="kt-cl-cfg05-drawer-body" data-testid="kt-cl-cfg05-drawer-body">' +
			"<section>" +
			sectionTitle(1, __("Item Core Identity")) +
			fieldWrap(
				__("ID"),
				'<p class="kt-cl-cfg05-readonly" data-testid="kt-cl-cfg05-drawer-id" data-item-id="' +
					esc(itemId) +
					'">' +
					esc(itemId || __("Assigned on save")) +
					"</p>",
				false
			) +
			fieldWrap(
				__("Item"),
				'<input type="text" class="kt-cl-cfg05-input" data-drawer-field="item_title" data-testid="kt-cl-cfg05-drawer-title-input" placeholder="' +
					esc(__("e.g. Existing HRIS at headquarters")) +
					'" value="' +
					esc(row.item_title || "") +
					'" />',
				true
			) +
			'<div class="kt-cl-cfg05-grid-2">' +
			fieldWrap(
				__("Category"),
				'<select class="kt-cl-cfg05-select" data-drawer-field="category_label" data-testid="kt-cl-cfg05-drawer-category">' +
					selectOpts(optionsFor("category_label"), defaultCategory) +
					"</select>",
				true
			) +
			fieldWrap(
				__("Scope"),
				'<select class="kt-cl-cfg05-select" data-drawer-field="scope_label" data-testid="kt-cl-cfg05-drawer-scope">' +
					selectOpts(optionsFor("scope_label"), row.scope_label || "") +
					"</select>",
				true
			) +
			"</div>" +
			fieldWrap(
				__("Description"),
				'<textarea class="kt-cl-cfg05-textarea" rows="3" data-drawer-field="item_description" data-testid="kt-cl-cfg05-drawer-description" placeholder="' +
					esc(__("Describe the inventory or background context for bidders")) +
					'">' +
					esc(row.item_description || "") +
					"</textarea>",
				true
			) +
			"</section>" +
			"<section>" +
			sectionTitle(2, __("Bidder Context")) +
			fieldWrap(
				__("Bidder Consideration"),
				'<textarea class="kt-cl-cfg05-textarea" rows="2" data-drawer-field="bidder_consideration" data-testid="kt-cl-cfg05-drawer-consideration" placeholder="' +
					esc(__("What bidders should understand or assume")) +
					'">' +
					esc(row.bidder_consideration || "") +
					"</textarea>",
				true
			) +
			fieldWrap(
				__("Related IT Requirements"),
				relatedChipsHtml("req", relatedReqIds),
				false
			) +
			fieldWrap(
				__("Related Milestones"),
				relatedChipsHtml("ms", relatedMsIds),
				false
			) +
			"</section>" +
			"<section>" +
			sectionTitle(3, __("Inventory / Background Details")) +
			'<div class="kt-cl-cfg05-grid-2">' +
			fieldWrap(
				__("Location / Site"),
				'<input type="text" class="kt-cl-cfg05-input" data-drawer-field="location_site" data-testid="kt-cl-cfg05-drawer-location" value="' +
					esc(row.location_site || "") +
					'" />',
				false
			) +
			fieldWrap(
				__("Existing System Name"),
				'<input type="text" class="kt-cl-cfg05-input" data-drawer-field="existing_system_name" data-testid="kt-cl-cfg05-drawer-existing-system" value="' +
					esc(row.existing_system_name || "") +
					'" />',
				false
			) +
			fieldWrap(
				__("Estimated Volume / Count"),
				'<input type="text" class="kt-cl-cfg05-input" data-drawer-field="estimated_volume_count" data-testid="kt-cl-cfg05-drawer-volume" value="' +
					esc(row.estimated_volume_count || "") +
					'" />',
				false
			) +
			fieldWrap(
				__("Integration Point"),
				'<input type="text" class="kt-cl-cfg05-input" data-drawer-field="integration_point" data-testid="kt-cl-cfg05-drawer-integration" value="' +
					esc(row.integration_point || "") +
					'" />',
				false
			) +
			fieldWrap(
				__("Data Source"),
				'<input type="text" class="kt-cl-cfg05-input" data-drawer-field="data_source" data-testid="kt-cl-cfg05-drawer-data-source" value="' +
					esc(row.data_source || "") +
					'" />',
				false
			) +
			fieldWrap(
				__("Support / Licence Context"),
				'<input type="text" class="kt-cl-cfg05-input" data-drawer-field="support_licence_context" data-testid="kt-cl-cfg05-drawer-support" value="' +
					esc(row.support_licence_context || "") +
					'" />',
				false
			) +
			"</div>" +
			fieldWrap(
				__("Out of Scope Note"),
				'<textarea class="kt-cl-cfg05-textarea" rows="2" data-drawer-field="out_of_scope_note" data-testid="kt-cl-cfg05-drawer-out-of-scope-note" placeholder="' +
					esc(__("Required when scope or category is Out of Scope")) +
					'">' +
					esc(row.out_of_scope_note || "") +
					"</textarea>",
				false
			) +
			"</section>" +
			"<section>" +
			sectionTitle(4, __("Disclosure")) +
			fieldWrap(
				__("Disclosure Status"),
				'<select class="kt-cl-cfg05-select" data-drawer-field="disclosure_status_label" data-testid="kt-cl-cfg05-drawer-disclosure">' +
					selectOpts(
						optionsFor("disclosure_status_label"),
						row.disclosure_status_label || ""
					) +
					"</select>",
				true
			) +
			fieldWrap(
				__("Disclosure Note"),
				'<textarea class="kt-cl-cfg05-textarea" rows="2" data-drawer-field="disclosure_note" data-testid="kt-cl-cfg05-drawer-disclosure-note" placeholder="' +
					esc(__("Required when status needs review or removal of sensitive detail")) +
					'">' +
					esc(row.disclosure_note || "") +
					"</textarea>",
				false
			) +
			fieldWrap(
				__("Price Link"),
				'<select class="kt-cl-cfg05-select" data-drawer-field="price_link_label" data-testid="kt-cl-cfg05-drawer-price-link">' +
					selectOpts(optionsFor("price_link_label"), row.price_link_label || "") +
					"</select>",
				false
			) +
			"</section>" +
			'<section data-testid="kt-cl-cfg05-drawer-references">' +
			sectionTitle(5, __("References Compact")) +
			'<ul class="kt-cl-cfg05-refs-compact">' +
			'<li><span class="material-symbols-outlined" aria-hidden="true">link</span>' +
			esc(refs.it_requirements || "") +
			"</li>" +
			'<li><span class="material-symbols-outlined" aria-hidden="true">event</span>' +
			esc(refs.implementation_schedule || "") +
			"</li>" +
			'<li><span class="material-symbols-outlined" aria-hidden="true">payments</span>' +
			esc(refs.price_schedule || "") +
			"</li>" +
			'<li><span class="material-symbols-outlined" aria-hidden="true">description</span>' +
			esc(refs.contract_values || "") +
			"</li></ul></section></div>" +
			'<footer class="kt-cl-cfg05-drawer-footer">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="save-item" data-testid="kt-cl-cfg05-drawer-save">' +
			__("Save Item") +
			"</button>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="close-drawer" data-testid="kt-cl-cfg05-drawer-cancel">' +
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
		state.drawerRelatedReqIds = [];
		state.drawerRelatedMsIds = [];
		state.addMode = "inventory";
		var $host = ensureDrawerHost();
		$host.empty().off(".cfg05drawer");
	}

	function refreshRelatedChips($host) {
		var $req = $host.find('[data-testid="kt-cl-cfg05-drawer-related-req"]');
		if ($req.length) {
			$req.replaceWith($(relatedChipsHtml("req", state.drawerRelatedReqIds)));
		}
		var $ms = $host.find('[data-testid="kt-cl-cfg05-drawer-related-ms"]');
		if ($ms.length) {
			$ms.replaceWith($(relatedChipsHtml("ms", state.drawerRelatedMsIds)));
		}
	}

	function openDrawer(index, mode) {
		state.drawerOpen = true;
		state.editingIndex = typeof index === "number" ? index : -1;
		var isNew = state.editingIndex < 0;
		if (isNew) {
			state.addMode = mode === "background" ? "background" : "inventory";
		} else {
			var existing = state.items[state.editingIndex] || {};
			state.addMode =
				String(existing.category_label || "") === CATEGORY_BACKGROUND
					? "background"
					: "inventory";
		}
		var row = isNew ? {} : state.items[state.editingIndex] || {};
		var relatedReqIds = (row.related_requirement_ids || []).slice();
		if (!relatedReqIds.length && row.related_requirement_refs) {
			relatedReqIds = row.related_requirement_refs.map(function (r) {
				return r.id || r.code;
			});
		}
		var relatedMsIds = (row.related_milestone_ids || []).slice();
		if (!relatedMsIds.length && row.related_milestone_refs) {
			relatedMsIds = row.related_milestone_refs.map(function (r) {
				return r.id || r.code;
			});
		}
		state.drawerRelatedReqIds = relatedReqIds.slice();
		state.drawerRelatedMsIds = relatedMsIds.slice();

		var $host = ensureDrawerHost();
		$host.html(drawerHtml(row, isNew));
		$host.off(".cfg05drawer");
		$host.on("click.cfg05drawer", "[data-action='close-drawer']", function (e) {
			e.preventDefault();
			closeDrawer();
		});
		// Explicit dismiss only (X / Cancel). Do not close on overlay/backdrop click —
		// that discards in-progress inventory fields without confirmation.
		$host.on("click.cfg05drawer", "[data-action='save-item']", function (e) {
			e.preventDefault();
			saveDrawerItem($host);
		});
		$host.on("click.cfg05drawer", "[data-action='remove-related-req']", function (e) {
			e.preventDefault();
			var rid = String($(this).attr("data-related-id") || "");
			state.drawerRelatedReqIds = (state.drawerRelatedReqIds || []).filter(function (id) {
				return id !== rid;
			});
			refreshRelatedChips($host);
		});
		$host.on("click.cfg05drawer", "[data-action='remove-related-ms']", function (e) {
			e.preventDefault();
			var mid = String($(this).attr("data-related-id") || "");
			state.drawerRelatedMsIds = (state.drawerRelatedMsIds || []).filter(function (id) {
				return id !== mid;
			});
			refreshRelatedChips($host);
		});
		$host.on(
			"change.cfg05drawer",
			"[data-testid='kt-cl-cfg05-drawer-related-req-pick']",
			function () {
				var rid = String($(this).val() || "");
				if (!rid) {
					return;
				}
				if ((state.drawerRelatedReqIds || []).indexOf(rid) < 0) {
					state.drawerRelatedReqIds = (state.drawerRelatedReqIds || []).concat([rid]);
				}
				refreshRelatedChips($host);
			}
		);
		$host.on(
			"change.cfg05drawer",
			"[data-testid='kt-cl-cfg05-drawer-related-ms-pick']",
			function () {
				var mid = String($(this).val() || "");
				if (!mid) {
					return;
				}
				if ((state.drawerRelatedMsIds || []).indexOf(mid) < 0) {
					state.drawerRelatedMsIds = (state.drawerRelatedMsIds || []).concat([mid]);
				}
				refreshRelatedChips($host);
			}
		);
		$host.on(
			"change.cfg05drawer",
			"[data-testid='kt-cl-cfg05-drawer-category']",
			function () {
				var cat = String($(this).val() || "");
				if (cat === CATEGORY_BACKGROUND) {
					state.addMode = "background";
				} else if (state.addMode === "background" && cat !== CATEGORY_BACKGROUND) {
					state.addMode = "inventory";
				}
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
			$host.find('[data-testid="kt-cl-cfg05-drawer-id"]').attr("data-item-id") || ""
		).trim();
		var isBackground =
			row.category_label === CATEGORY_BACKGROUND || state.addMode === "background";
		if (state.editingIndex >= 0 && state.items[state.editingIndex]) {
			row.item_id = state.items[state.editingIndex].item_id || previewId;
		} else {
			row.item_id = previewId || nextItemId(isBackground);
		}
		row.related_requirement_ids = (state.drawerRelatedReqIds || []).slice();
		row.related_milestone_ids = (state.drawerRelatedMsIds || []).slice();
		return row;
	}

	function persistableItems() {
		return (state.items || []).map(function (r) {
			return {
				item_id: r.item_id || "",
				item_title: r.item_title || "",
				category_label: r.category_label || "",
				scope_label: r.scope_label || "",
				item_description: r.item_description || "",
				bidder_consideration: r.bidder_consideration || "",
				related_requirement_ids: r.related_requirement_ids || [],
				related_milestone_ids: r.related_milestone_ids || [],
				location_site: r.location_site || "",
				existing_system_name: r.existing_system_name || "",
				estimated_volume_count: r.estimated_volume_count || "",
				integration_point: r.integration_point || "",
				data_source: r.data_source || "",
				support_licence_context: r.support_licence_context || "",
				out_of_scope_note: r.out_of_scope_note || "",
				disclosure_status_label: r.disclosure_status_label || "",
				disclosure_note: r.disclosure_note || "",
				price_link_label: r.price_link_label || "",
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
		// Persist immediately so Setup Status / issues / Continue refresh
		// without a second footer "Save Inventory & Background" click.
		if (state.page) {
			saveInventory($(state.page.main), state.page, { fromDrawer: true });
		}
	}

	function setDirty($root, dirty) {
		state.dirty = !!dirty;
		$root.find('[data-testid="kt-cl-cfg05-save"]').prop("disabled", !state.dirty || state.saving);
	}

	function refreshContinue($root, canContinue) {
		var can =
			typeof canContinue === "boolean"
				? canContinue
				: !!(state.payload && state.payload.can_continue);
		$root.find('[data-testid="kt-cl-cfg05-continue"]').prop("disabled", !can || state.saving);
	}

	function remountWithPayload(page, data, opts) {
		opts = opts || {};
		var sh = kentender_core.cl_shell;
		var surf = surface();
		var pageHeader = {
			title: __("System Inventory & Bidder Background"),
			subtitle: __(SUBTITLE),
			hideBreadcrumbs: true,
		};
		if (surf && surf.chrome && surf.chrome.toolbar) {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}
		state.payload = data;
		if (!opts.keepClientList) {
			state.items = (data && data.items ? data.items : []).slice();
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

	function saveInventory($root, page, opts) {
		opts = opts || {};
		if (state.saving || !state.configurationId) {
			return;
		}
		state.saving = true;
		setDirty($root, state.dirty);
		refreshContinue($root);
		frappe.call({
			method: SAVE_API,
			args: {
				configuration_id: state.configurationId,
				payload: { items: persistableItems() },
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
				} else if (opts.fromDelete) {
					frappe.show_alert(
						{
							message: __("Inventory item removed"),
							indicator: "green",
						},
						4
					);
				} else if (!opts.thenContinue) {
					frappe.show_alert(
						{
							message: __("Inventory & Background saved successfully"),
							indicator: "green",
						},
						5
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
		$root.off(".cfg05");
		$root.on("click.cfg05", "[data-action='toggle-issues']", function (e) {
			e.preventDefault();
			state.issuesExpanded = !state.issuesExpanded;
			var $panel = $root.find('[data-testid="kt-cl-cfg05-blockers"]');
			var $list = $root.find('[data-testid="kt-cl-cfg05-issues-list"]');
			var $btn = $root.find('[data-testid="kt-cl-cfg05-issues-toggle"]');
			var $chev = $panel.find(".kt-cl-cfg05-issues-chevron");
			$panel.toggleClass("kt-cl-cfg05-issues--open", state.issuesExpanded);
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
		$root.on("click.cfg05", "[data-action='set-filter']", function (e) {
			e.preventDefault();
			var key = String($(this).attr("data-filter") || "All");
			state.categoryFilter = key || "All";
			remountWithPayload(page, state.payload || {}, { keepClientList: true });
		});
		$root.on("click.cfg05", "[data-action='add-inventory']", function (e) {
			e.preventDefault();
			openDrawer(-1, "inventory");
		});
		$root.on("click.cfg05", "[data-action='add-background']", function (e) {
			e.preventDefault();
			openDrawer(-1, "background");
		});
		$root.on("click.cfg05", "[data-action='edit-item']", function (e) {
			e.preventDefault();
			var idx = parseInt($(this).attr("data-index"), 10);
			if (!isNaN(idx)) {
				openDrawer(idx);
			}
		});
		$root.on("click.cfg05", "[data-action='delete-item']", function (e) {
			e.preventDefault();
			e.stopPropagation();
			var idx = parseInt($(this).attr("data-index"), 10);
			if (isNaN(idx) || idx < 0 || idx >= (state.items || []).length) {
				return;
			}
			var row = state.items[idx] || {};
			var label = row.item_title || row.item_id || __("this item");
			kentender_core.cl.confirm({
				title: __("Remove inventory item?"),
				message: __("{0} will be removed from this configuration.", [label]),
				confirmLabel: __("Remove"),
				cancelLabel: __("Cancel"),
				tone: "danger",
				onConfirm: function () {
					state.items.splice(idx, 1);
					state.dirty = true;
					closeDrawer();
					if (state.page) {
						saveInventory($(state.page.main), state.page, { fromDelete: true });
					}
				},
			});
		});
		$root.on("click.cfg05", "[data-action='back-home']", function (e) {
			e.preventDefault();
			closeDrawer();
			if (!state.configurationId) {
				frappe.set_route("it-tender-configuration-dashboard");
				return;
			}
			frappe.route_options = { configuration_id: state.configurationId };
			frappe.set_route("it-tender-configuration-overview", state.configurationId);
		});
		$root.on("click.cfg05", "[data-action='save']", function (e) {
			e.preventDefault();
			if (!state.dirty || state.saving) {
				return;
			}
			saveInventory($root, page, {});
		});
		$root.on("click.cfg05", "[data-action='run-check']", function (e) {
			e.preventDefault();
			if (state.saving) {
				return;
			}
			saveInventory($root, page, { runCheck: true });
		});
		$root.on("click.cfg05", "[data-action='continue']", function (e) {
			e.preventDefault();
			closeDrawer();
			if (state.dirty) {
				saveInventory($root, page, { thenContinue: true });
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
			title: __("System Inventory & Bidder Background"),
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
			title: __("System Inventory & Bidder Background"),
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
