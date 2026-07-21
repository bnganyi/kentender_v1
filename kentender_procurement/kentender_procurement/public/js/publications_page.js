// PUB-A2 — Publications queue (v7).
(function () {
	"use strict";

	var SURFACE_ID = "PUB-A2";
	var PAGE_SLUG = "publications";
	var API = "kentender_procurement.tender_configurations.list_publications";

	var TAB_DEFS = [
		{ key: "awaiting_setup", label: __("Awaiting Setup"), countKey: "awaiting_setup_count" },
		{ key: "ready_to_publish", label: __("Ready to Publish"), countKey: "ready_to_publish_count" },
		{ key: "scheduled", label: __("Scheduled"), countKey: "scheduled_count" },
		{ key: "published", label: __("Published"), countKey: "published_count" },
		{ key: "returned", label: __("Returned"), countKey: "returned_count" },
		{ key: "all", label: __("All"), countKey: "all_count" },
	];

	var state = {
		tab: "awaiting_setup",
		search: "",
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

	function enterSurface() {
		var sh = kentender_core.cl_shell;
		var surf = surface();
		if (!sh || typeof sh.enterNative !== "function" || !surf) {
			return;
		}
		sh.enterNative({
			sidebarWorkspaceKey: surf.sidebarWorkspaceKey || "procurement",
			toolbar: (surf.chrome && surf.chrome.toolbar) || {},
			chrome: surf.chrome,
		});
	}

	function summaryHtml(summary) {
		var c = comp();
		var s = summary || {};
		var cards =
			c.queueSummaryCard({
				key: "awaiting",
				layout: "bento",
				label: __("Awaiting Setup"),
				value: String(s.awaiting_setup_count != null ? s.awaiting_setup_count : "—"),
				icon: "pending_actions",
				accentBorderClass: "border-l-primary",
				iconClass: "kt-cl-queue-summary-watermark text-primary",
			}) +
			c.queueSummaryCard({
				key: "ready",
				layout: "bento",
				label: __("Ready to Publish"),
				value: String(s.ready_to_publish_count != null ? s.ready_to_publish_count : "—"),
				icon: "publish",
				accentBorderClass: "border-l-emerald-available",
				iconClass: "kt-cl-queue-summary-watermark text-emerald-available",
			}) +
			c.queueSummaryCard({
				key: "scheduled",
				layout: "bento",
				label: __("Scheduled"),
				value: String(s.scheduled_count != null ? s.scheduled_count : "—"),
				icon: "schedule",
				accentBorderClass: "border-l-secondary",
				iconClass: "kt-cl-queue-summary-watermark text-secondary",
			}) +
			c.queueSummaryCard({
				key: "returned",
				layout: "bento",
				label: __("Returned"),
				value: String(s.returned_count != null ? s.returned_count : "—"),
				icon: "assignment_return",
				accentBorderClass: "border-l-error",
				iconClass: "kt-cl-queue-summary-watermark text-error",
			});
		return c.queueSummaryGrid(cards);
	}

	function filterDefs() {
		return [
			{
				key: "search",
				type: "search",
				label: __("Search"),
				placeholder: __("Publication / configuration ref..."),
				value: state.search,
			},
		];
	}

	function statusTone(status) {
		var s = String(status || "").toLowerCase();
		if (s.indexOf("published") >= 0 || s.indexOf("ready") >= 0) {
			return "approved";
		}
		if (s.indexOf("returned") >= 0) {
			return "rejected";
		}
		if (s.indexOf("scheduled") >= 0 || s.indexOf("awaiting") >= 0) {
			return "review";
		}
		return "draft";
	}

	function stdChip(label) {
		var text = String(label || "").trim() || "—";
		var short =
			text.length > 28
				? text.replace(/Standard Tender Document/gi, "STD").slice(0, 28)
				: text;
		return (
			'<span class="kt-cl-pub-a2-std-chip" title="' +
			frappe.utils.escape_html(text) +
			'">' +
			frappe.utils.escape_html(short) +
			"</span>"
		);
	}

	function mutedOrValue(value) {
		if (!value) {
			return '<span class="kt-cl-pub-a2-not-set">' + __("Not set") + "</span>";
		}
		return frappe.utils.escape_html(String(value));
	}

	function tabsWithCounts(summary) {
		var s = summary || {};
		var awaiting = Number(s.awaiting_setup_count || 0);
		var ready = Number(s.ready_to_publish_count || 0);
		var scheduled = Number(s.scheduled_count || 0);
		var published = Number(s.published_count || 0);
		var returned = Number(s.returned_count || 0);
		var all =
			s.all_count != null
				? Number(s.all_count)
				: awaiting + ready + scheduled + published + returned;
		var counts = {
			awaiting_setup_count: awaiting,
			ready_to_publish_count: ready,
			scheduled_count: scheduled,
			published_count: published,
			returned_count: returned,
			all_count: all,
		};
		return TAB_DEFS.map(function (tab) {
			var n = counts[tab.countKey];
			return {
				key: tab.key,
				label: tab.label + (n != null ? " (" + n + ")" : ""),
			};
		});
	}

	function columns() {
		var qs = q();
		var c = comp();
		return {
			columns: [
				{ label: __("Publication Ref") },
				{ label: __("Tender Title") },
				{ label: __("Procuring Entity") },
				{ label: __("Standard Tender Document") },
				{ label: __("Status") },
				{ label: __("Publication Date/Time") },
				{ label: __("Submission Deadline") },
				{ label: __("Opening Date/Time") },
				{ label: __("Issues") },
				{ label: __("Next Action") },
			],
			mapRow: function (row) {
				return {
					id: row.publication_id,
					cells: [
						{ cls: qs.tdRef, text: row.publication_ref || row.publication_id },
						{ cls: qs.tdTitle, text: row.tender_title },
						{ cls: qs.tdText, text: row.procuring_entity },
						{ cls: qs.tdText, html: stdChip(row.standard_tender_document) },
						{
							cls: qs.tdText,
							html: c.statusChip({ tone: statusTone(row.status), label: row.status }),
						},
						{ cls: qs.tdMuted, html: mutedOrValue(row.publication_datetime) },
						{ cls: qs.tdMuted, html: mutedOrValue(row.submission_deadline) },
						{ cls: qs.tdMuted, html: mutedOrValue(row.opening_datetime) },
						{ cls: qs.tdMuted, text: row.issues != null ? String(row.issues) : "0" },
						{
							cls: qs.tdAction,
							html:
								'<button type="button" class="kt-cl-pub-a2-cta" data-action="open-setup" data-publication-id="' +
								frappe.utils.escape_html(row.publication_id || "") +
								'" data-testid="kt-cl-pub-a2-next-action">' +
								frappe.utils.escape_html(row.next_action || __("Open")) +
								"</button>",
						},
					],
				};
			},
		};
	}

	function emptyHtml() {
		return (
			'<div class="p-10 text-center" data-testid="kt-cl-pub-a2-empty">' +
			'<p class="text-headline-md font-semibold text-primary mb-2">' +
			__("No publications in this tab") +
			"</p>" +
			'<p class="text-body-md text-on-surface-variant">' +
			__("Confirm a tender package to create a publication setup record.") +
			"</p></div>"
		);
	}

	function tableHtml(payload) {
		var c = comp();
		var model = columns();
		var raw = (payload && payload.rows) || [];
		if (!raw.length) {
			return emptyHtml();
		}
		var rows = raw.map(model.mapRow);
		var total = payload.total != null ? payload.total : rows.length;
		var page = payload.page || state.page;
		var pageSize = payload.page_size || state.page_size;
		var totalPages = Math.max(1, Math.ceil(total / pageSize));
		return (
			'<div data-testid="kt-cl-pub-a2-table">' +
			c.queueTable({
				columns: model.columns,
				rows: rows,
				footerText: __("Showing {0} of {1}", [rows.length, total]),
				pagination: {
					page: page,
					page_size: pageSize,
					total: total,
					total_pages: totalPages,
				},
				pageSize: state.page_size,
				pageSizeOptions: [10, 20, 50, 100],
			}) +
			"</div>"
		);
	}

	function bodyHtml(payload) {
		var c = comp();
		var qs = q();
		return (
			'<div data-testid="kt-cl-pub-a2-root">' +
			summaryHtml(payload.summary) +
			'<div class="' +
			(qs.canvas || "") +
			'">' +
			'<div data-testid="kt-cl-pub-a2-tabs">' +
			c.tabBar({ tabs: tabsWithCounts(payload.summary), active: state.tab }) +
			"</div>" +
			c.filterBar({ filters: filterDefs() }) +
			tableHtml(payload) +
			"</div></div>"
		);
	}

	function bind($root) {
		var c = comp();
		$root.off(".puba2");
		$root.on("click.puba2", "[data-tab]", function (e) {
			e.preventDefault();
			state.tab = $(this).attr("data-tab");
			state.page = 1;
			reload();
		});
		if (c && typeof c.bindFilterBar === "function") {
			c.bindFilterBar($root, {
				namespace: ".puba2filter",
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
		$root.on("click.puba2", '[data-action="open-setup"]', function (e) {
			e.preventDefault();
			var id = $(this).attr("data-publication-id");
			if (id) {
				frappe.set_route("publication-setup", id);
			}
		});
		$root.on("click.puba2", "[data-page]", function (e) {
			e.preventDefault();
			var p = $(this).attr("data-page");
			var pag = state.payload || {};
			var cur = pag.page || 1;
			var total = Math.max(
				1,
				Math.ceil((pag.total || 0) / (pag.page_size || state.page_size || 20))
			);
			if (p === "prev") {
				state.page = Math.max(1, cur - 1);
			} else if (p === "next") {
				state.page = Math.min(total, cur + 1);
			} else {
				state.page = parseInt(p, 10) || 1;
			}
			reload();
		});
		$root.on("change.puba2", "[data-page-size]", function () {
			state.page_size = parseInt($(this).val(), 10) || 20;
			state.page = 1;
			reload();
		});
	}

	function paint(page, payload) {
		var sh = kentender_core.cl_shell;
		var surf = surface();
		enterSurface();
		var pageHeader =
			(surf && surf.chrome && surf.chrome.pageHeader) || {
				title: __("Publications"),
				hideBreadcrumbs: true,
			};
		if (surf && surf.chrome && surf.chrome.toolbar && typeof sh.updateChrome === "function") {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}
		sh.mountContent(page.main, {
			pageHeader: pageHeader,
			mainHtml: bodyHtml(payload || { summary: {}, rows: [], total: 0 }),
		});
		bind($(page.main).find('[data-testid="kt-cl-pub-a2-root"]'));
	}

	function reload() {
		var page = frappe.pages[PAGE_SLUG].page;
		if (!page) {
			return;
		}
		var token = ++state.token;
		frappe.call({
			method: API,
			args: {
				tab: state.tab,
				search: state.search || null,
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
		frappe.pages[PAGE_SLUG].page = page;
		paint(page, {
			summary: {},
			rows: [],
			total: 0,
			page: 1,
			page_size: 20,
		});
		reload();
	}

	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Publications"),
			single_column: true,
		});
		wrapper.page = page;
		mount(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		if (wrapper && wrapper.page) {
			mount(wrapper.page);
		}
	};
})();
