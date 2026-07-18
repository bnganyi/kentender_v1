// UI-00 — Tender Configurations Dashboard (C1-M1 + live APIs).
(function () {
	"use strict";

	var SURFACE_ID = "UI-00";
	var API =
		"kentender_procurement.tender_configurations.get_tender_configurations_dashboard";

	var TABS = [
		{ key: "ready_to_configure", label: __("Ready to Configure") },
		{ key: "in_progress", label: __("In Progress") },
		{ key: "needs_attention", label: __("Needs Attention") },
		{ key: "ready_for_review", label: __("Ready for Review") },
		{ key: "ready_for_publication", label: __("Ready for Publication") },
		{ key: "completed", label: __("Completed") },
	];

	var state = {
		tab: "ready_to_configure",
		search: "",
		std_family: "",
		procuring_entity: "",
		procurement_method: "",
		issue_status: "",
		page: 1,
		page_size: 20,
		payload: null,
		token: 0,
		keepSearchFocus: false,
	};

	function surface() {
		var reg = kentender_core.cl_surface_registry;
		return reg && typeof reg.get === "function" ? reg.get(SURFACE_ID) : null;
	}

	function comp() {
		return kentender_core.cl_components;
	}

	function q() {
		return (kentender_core.cl_code_spec && kentender_core.cl_code_spec.QUEUE) || {};
	}

	function openCreate(packageId) {
		var mod = kentender_procurement.tender_configurations;
		if (mod && typeof mod.openCreateModal === "function") {
			mod.openCreateModal({ package_id: packageId || null });
		} else {
			frappe.msgprint(__("Create modal is not loaded."));
		}
	}

	function summaryHtml(summary) {
		var c = comp();
		var s = summary || {};
		var cards =
			c.queueSummaryCard({
				key: "ready",
				label: __("Ready to Configure"),
				value: String(s.ready_to_configure_count != null ? s.ready_to_configure_count : "—"),
				icon: "pending_actions",
				accentClass: "bg-primary",
			}) +
			c.queueSummaryCard({
				key: "in_progress",
				label: __("In Progress"),
				value: String(s.in_progress_count != null ? s.in_progress_count : "—"),
				icon: "sync",
				accentClass: "bg-secondary",
				iconWrapClass:
					"w-10 h-10 rounded bg-secondary-container flex items-center justify-center shrink-0",
				iconClass: "text-on-secondary-container",
			}) +
			c.queueSummaryCard({
				key: "needs_attention",
				label: __("Needs Attention"),
				value: String(s.needs_attention_count != null ? s.needs_attention_count : "—"),
				icon: "report",
				accentClass: "bg-error",
				iconWrapClass:
					"w-10 h-10 rounded bg-error-container flex items-center justify-center shrink-0",
				iconClass: "text-on-error-container",
			}) +
			c.queueSummaryCard({
				key: "ready_for_review",
				label: __("Ready for Review"),
				value: String(s.ready_for_review_count != null ? s.ready_for_review_count : "—"),
				icon: "rule",
				accentClass: "bg-surface-tint",
				iconWrapClass:
					"w-10 h-10 rounded bg-surface-container-highest flex items-center justify-center shrink-0",
			});
		return c.queueSummaryGrid(cards);
	}

	function filterDefs(filters) {
		var f = filters || {};
		var familyOpts = [{ value: "", label: __("All Families") }].concat(
			(f.std_families || []).map(function (x) {
				return { value: x, label: x };
			})
		);
		var entityOpts = [{ value: "", label: __("All Entities") }].concat(
			(f.procuring_entities || []).map(function (x) {
				return { value: x, label: x };
			})
		);
		var methodOpts = [{ value: "", label: __("All Methods") }].concat(
			(f.procurement_methods || []).map(function (x) {
				return { value: x, label: x };
			})
		);
		var issueOpts = [
			{ value: "", label: __("All Issues") },
			{ value: "Has Blockers", label: __("Has Blockers") },
			{ value: "Has Warnings", label: __("Has Warnings") },
			{ value: "No Issues", label: __("No Issues") },
		];
		var issueHidden = state.tab === "ready_to_configure";
		return [
			{
				key: "search",
				type: "search",
				label: __("Search"),
				placeholder: __("Package ref / title..."),
				value: state.search,
			},
			{
				key: "std_family",
				label: __("STD Family"),
				options: familyOpts,
				value: state.std_family,
			},
			{
				key: "procuring_entity",
				label: __("Procuring Entity"),
				options: entityOpts,
				value: state.procuring_entity,
			},
			{
				key: "procurement_method",
				label: __("Method"),
				options: methodOpts,
				value: state.procurement_method,
			},
			{
				key: "issue_status",
				label: __("Issue Status"),
				options: issueOpts,
				value: state.issue_status,
				hidden: issueHidden,
			},
		];
	}

	function packageColumns() {
		var qs = q();
		return {
			columns: [
				{ label: __("Procurement Package Ref") },
				{ label: __("Package Title") },
				{ label: __("STD Family") },
				{ label: __("Procuring Entity") },
				{ label: __("Procurement Method") },
				{ label: __("Approval Date") },
				{ label: __("Action") },
			],
			mapRow: function (row) {
				return {
					id: row.package_id || row.procurement_package_ref,
					cells: [
						{ cls: qs.tdRef, text: row.procurement_package_ref },
						{ cls: qs.tdTitle, text: row.package_title },
						{ cls: qs.tdText, text: row.std_family },
						{ cls: qs.tdText, text: row.procuring_entity_name },
						{ cls: qs.tdText, text: row.procurement_method_label },
						{ cls: qs.tdMuted, text: row.approval_date || "" },
						{
							cls: qs.tdAction,
							html:
								'<button type="button" class="' +
								qs.rowBtn +
								'" data-action="create" data-package-id="' +
								frappe.utils.escape_html(row.package_id || "") +
								'" data-testid="kt-cl-ui00-create-row">' +
								__("Create Configuration") +
								"</button>",
						},
					],
				};
			},
		};
	}

	function configColumns() {
		var qs = q();
		var c = comp();
		return {
			columns: [
				{ label: __("Configuration Ref") },
				{ label: __("Procurement Package Ref") },
				{ label: __("Tender Title") },
				{ label: __("STD Family") },
				{ label: __("Procuring Entity") },
				{ label: __("Status") },
				{ label: __("Issues") },
				{ label: __("Last Updated") },
				{ label: __("Next Action") },
			],
			mapRow: function (row) {
				var tone = "draft";
				if (row.status_label === "In Progress") {
					tone = "review";
				} else if (row.status_label === "Needs Attention") {
					tone = "rejected";
				} else if (
					row.status_label === "Ready for Review" ||
					row.status_label === "Ready for Publication" ||
					row.status_label === "Completed"
				) {
					tone = "approved";
				}
				return {
					id: row.configuration_id || row.configuration_ref,
					cells: [
						{ cls: qs.tdRef, text: row.configuration_ref },
						{ cls: qs.tdText, text: row.procurement_package_ref },
						{ cls: qs.tdTitle, text: row.tender_title },
						{ cls: qs.tdText, text: row.std_family },
						{ cls: qs.tdText, text: row.procuring_entity_name },
						{
							cls: qs.tdText,
							html: c.statusChip({ tone: tone, label: row.status_label }),
						},
						{ cls: qs.tdMuted, text: row.issues_label },
						{ cls: qs.tdMuted, text: row.last_updated_label },
						{
							cls: qs.tdAction,
							html:
								'<button type="button" class="' +
								qs.rowBtn +
								'" data-action="open-config" data-configuration-id="' +
								frappe.utils.escape_html(row.configuration_id || "") +
								'" data-testid="kt-cl-ui00-next-action">' +
								frappe.utils.escape_html(row.next_action_label || __("Open")) +
								"</button>",
						},
					],
				};
			},
		};
	}

	function emptyHtml() {
		var ready = state.tab === "ready_to_configure";
		return (
			'<div class="p-10 text-center" data-testid="kt-cl-ui00-empty">' +
			'<p class="text-headline-md font-semibold text-primary mb-2">' +
			(ready
				? __("No approved procurement packages ready to configure")
				: __("No tender configurations found")) +
			"</p>" +
			'<p class="text-body-md text-on-surface-variant mb-4">' +
			(ready
				? __(
						"Tender configurations can only be created from approved procurement packages that have not already been configured."
					)
				: __("No tender configurations match the selected tab and filters.")) +
			"</p>" +
			'<button type="button" class="kt-cl-ui00-empty-action h-8 px-4 rounded bg-primary text-on-primary text-label-sm" data-action="' +
			(ready ? "refresh" : "clear-filters") +
			'" data-testid="kt-cl-ui00-empty-action">' +
			(ready ? __("Refresh") : __("Clear Filters")) +
			"</button></div>"
		);
	}

	function tableHtml(payload) {
		var c = comp();
		var ready = state.tab === "ready_to_configure";
		var model = ready ? packageColumns() : configColumns();
		var raw = ready
			? payload.ready_to_configure_packages || []
			: payload.configurations || [];
		if (!raw.length) {
			return emptyHtml();
		}
		var rows = raw.map(model.mapRow);
		var pag = payload.pagination || {};
		var shown = rows.length;
		var total = pag.total != null ? pag.total : shown;
		return c.queueTable({
			columns: model.columns,
			rows: rows,
			footerText: __("Showing {0} of {1}", [shown, total]),
			pagination: pag,
			pageSize: state.page_size,
			pageSizeOptions: [10, 20, 50, 100],
		});
	}

	function bodyHtml(payload) {
		var c = comp();
		var qs = q();
		return (
			'<div data-testid="kt-cl-ui00-root">' +
			summaryHtml(payload.summary) +
			'<div class="' +
			(qs.canvas || "") +
			'">' +
			c.tabBar({ tabs: TABS, active: state.tab }) +
			c.filterBar({ filters: filterDefs(payload.filters) }) +
			tableHtml(payload) +
			"</div></div>"
		);
	}

	function bind($root) {
		var c = comp();
		$root.off(".ui00");
		$root.on("click.ui00", "[data-tab]", function (e) {
			e.preventDefault();
			state.tab = $(this).attr("data-tab");
			state.page = 1;
			if (state.tab === "ready_to_configure") {
				state.issue_status = "";
			}
			reload();
		});
		if (c && typeof c.bindFilterBar === "function") {
			c.bindFilterBar($root, {
				namespace: ".ui00filter",
				onChange: function (key, value) {
					state[key] = value || "";
					state.page = 1;
					if (key === "search") {
						state.keepSearchFocus = true;
					}
					reload();
				},
			});
		}
		if (state.keepSearchFocus) {
			state.keepSearchFocus = false;
			var searchEl = $root.find('[data-filter="search"]').get(0);
			if (searchEl) {
				searchEl.focus();
				var len = (searchEl.value || "").length;
				try {
					searchEl.setSelectionRange(len, len);
				} catch (err) {
					/* ignore */
				}
			}
		}
		$root.on("click.ui00", '[data-action="create"]', function (e) {
			e.preventDefault();
			openCreate($(this).attr("data-package-id"));
		});
		$root.on("click.ui00", '[data-action="open-config"]', function (e) {
			e.preventDefault();
			var id = $(this).attr("data-configuration-id");
			frappe.route_options = { configuration_id: id };
			frappe.set_route("it-tender-configuration-overview");
		});
		$root.on("click.ui00", '[data-action="refresh"]', function (e) {
			e.preventDefault();
			reload();
		});
		$root.on("click.ui00", '[data-action="clear-filters"]', function (e) {
			e.preventDefault();
			state.search = "";
			state.std_family = "";
			state.procuring_entity = "";
			state.procurement_method = "";
			state.issue_status = "";
			state.page = 1;
			reload();
		});
		$root.on("click.ui00", "[data-page]", function (e) {
			e.preventDefault();
			var p = $(this).attr("data-page");
			var pag = (state.payload && state.payload.pagination) || {};
			var cur = pag.page || 1;
			var total = pag.total_pages || 1;
			if (p === "prev") {
				state.page = Math.max(1, cur - 1);
			} else if (p === "next") {
				state.page = Math.min(total, cur + 1);
			} else {
				state.page = parseInt(p, 10) || 1;
			}
			reload();
		});
		$root.on("change.ui00", "[data-page-size]", function () {
			var next = parseInt($(this).val(), 10) || 20;
			state.page_size = next;
			state.page = 1;
			reload();
		});
	}

	function paint(page, payload) {
		var sh = kentender_core.cl_shell;
		var surf = surface();
		var pageHeader =
			(surf && surf.chrome && surf.chrome.pageHeader) || {
				title: __("Tender Configurations"),
				subtitle: __(
					"Create configurations from approved procurement packages and manage configurations already in progress."
				),
				hideBreadcrumbs: true,
			};
		if (surf && surf.chrome && surf.chrome.toolbar && typeof sh.updateChrome === "function") {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		} else if (typeof sh.updateChrome === "function") {
			sh.updateChrome({
				toolbar: {
					breadcrumbs: [
						{ label: __("Dashboard"), route: ["Workspaces", "Procurement Home"] },
						{ label: __("Tender Management"), route: ["tender-management-v2"] },
					],
					showSearch: false,
					showUserMeta: true,
				},
			});
		}
		sh.mountContent(page.main, {
			pageHeader: pageHeader,
			mainHtml: bodyHtml(payload || { summary: {}, filters: {}, ready_to_configure_packages: [], configurations: [], pagination: {} }),
		});
		var $root = $(page.main).find('[data-testid="kt-cl-ui00-root"]');
		bind($root);
		// Header create action
		$(document)
			.off("click.ui00create", '[data-testid="kt-cl-action-create-tender-config"]')
			.on("click.ui00create", '[data-testid="kt-cl-action-create-tender-config"]', function (e) {
				e.preventDefault();
				openCreate(null);
			});
	}

	function reload() {
		var page = frappe.pages["it-tender-configuration-dashboard"].page;
		if (!page) {
			return;
		}
		var token = ++state.token;
		frappe.call({
			method: API,
			args: {
				tab: state.tab,
				search: state.search || null,
				std_family: state.std_family || null,
				procuring_entity: state.procuring_entity || null,
				procurement_method: state.procurement_method || null,
				issue_status: state.issue_status || null,
				page: state.page,
				page_size: state.page_size,
			},
			callback: function (r) {
				if (token !== state.token) {
					return;
				}
				state.payload = r.message || {};
				paint(page, state.payload);
			},
		});
	}

	function mount(page) {
		var sh = kentender_core.cl_shell;
		if (!sh || typeof sh.mountContent !== "function") {
			page.main.html(
				'<div class="p-4 text-danger">' + __("Civic Ledger shell is not loaded.") + "</div>"
			);
			return;
		}
		frappe.pages["it-tender-configuration-dashboard"].page = page;
		paint(page, {
			summary: {},
			filters: { std_families: [], procuring_entities: [], procurement_methods: [] },
			ready_to_configure_packages: [],
			configurations: [],
			pagination: { page: 1, page_size: 20, total: 0, total_pages: 1 },
		});
		reload();
	}

	frappe.pages["it-tender-configuration-dashboard"].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Tender Configurations"),
			single_column: true,
		});
		wrapper.page = page;
		mount(page);
	};

	frappe.pages["it-tender-configuration-dashboard"].on_page_show = function (wrapper) {
		if (wrapper && wrapper.page) {
			mount(wrapper.page);
		}
	};
})();
