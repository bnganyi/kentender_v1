(function () {
	"use strict";

	frappe.provide("kentender.it_wizard");

	var API = "kentender_procurement.it_tender_wizard.api.instance_api";
	var PROCUREMENT_SIDEBAR_KEY = "Procurement";
	var planningHandoffKeys = {};

	var STATE_FILTER_MAP = {
		"In Configuration": "IN_CONFIGURATION",
		"Ready for Review": "READY_FOR_REVIEW",
		"Validation Failed": "VALIDATION_FAILED",
		Returned: "RETURNED_FOR_CORRECTION",
	};

	var STATUS_FILTER_OPTIONS = [
		{ value: "IN_CONFIGURATION", label: "In Configuration" },
		{ value: "VALIDATION_FAILED", label: "Validation Failed" },
		{ value: "READY_FOR_REVIEW", label: "Ready for Review" },
		{ value: "RETURNED_FOR_CORRECTION", label: "Returned" },
	];

	var ENTITY_FILTER_MAP = {
		"Ministry of ICT": "PE-MIN-ICT",
		Treasury: "PE-NATIONAL-TREASURY",
	};

	var METHOD_FILTER_MAP = {
		"Open Tender": "OPEN_NATIONAL",
		RFP: "RFP",
	};

	var DRAWER_METHOD_MAP = {
		"All Methods": "",
		"Open Tender": "OPEN_NATIONAL",
		RFP: "RFP",
	};

	var DRAWER_STATE_MAP = {
		validation_failed: "VALIDATION_FAILED",
		returned: "RETURNED_FOR_CORRECTION",
	};

	var KPI_LABELS = {
		in_configuration: "In Configuration",
		validation_failed: "Validation Failed",
		ready_for_review: "Ready for Review",
		returned: "Returned",
		publication_ready: "Publication Ready",
		overdue_actions: "Overdue Actions",
	};

	function call_api(method, args) {
		return frappe.call({
			method: API + "." + method,
			args: args || {},
		});
	}

	function preserve_procurement_sidebar() {
		if (frappe.app && frappe.app.sidebar && typeof frappe.app.sidebar.setup === "function") {
			frappe.app.sidebar.setup(PROCUREMENT_SIDEBAR_KEY);
		}
	}

	function read_route_context() {
		var root = window.parent && window.parent.frappe ? window.parent : window;
		var opts = root.frappe.route_options || {};
		var params = new URLSearchParams(root.location && root.location.search ? root.location.search : "");
		function pick(key) {
			return (opts[key] || params.get(key) || "").trim();
		}
		return {
			configuration_id: pick("configuration_id"),
			tender_id: pick("tender_id"),
			std_version_id: pick("std_version_id"),
			plan_item_id: pick("plan_item_id"),
			procurement_entity_id: pick("procurement_entity_id"),
		};
	}

	function set_route_context(ctx) {
		var root = window.parent && window.parent.frappe ? window.parent : window;
		root.frappe.route_options = Object.assign({}, root.frappe.route_options || {}, ctx || {});
	}

	var ITW_REGISTERED_ROUTES = [
		"it-tender-configuration-dashboard",
		"it-tender-configuration-overview",
		"it-tender-configuration-tender-profile",
		"it-tender-configuration-tds",
	];

	var STEP_ROUTE_MAP = {
		TENDER_PROFILE: "it-tender-configuration-tender-profile",
		TDS: "it-tender-configuration-tds",
	};

	var CONFIGURATION_CONTEXT_ROUTES = {
		"it-tender-configuration-overview": 1,
		"it-tender-configuration-tender-profile": 1,
		"it-tender-configuration-tds": 1,
	};

	var configRedirectInFlight = false;

	function desk_root_window() {
		return window.parent && window.parent.frappe ? window.parent : window;
	}

	function sync_configuration_id_to_url(configuration_id) {
		var root = desk_root_window();
		if (!configuration_id || !root.location) {
			return;
		}
		var url = new URL(root.location.href);
		if (url.searchParams.get("configuration_id") === configuration_id) {
			return;
		}
		url.searchParams.set("configuration_id", configuration_id);
		root.history.replaceState({}, "", url.toString());
	}

	function clear_configuration_id_from_url() {
		var root = desk_root_window();
		if (!root.location) {
			return;
		}
		var url = new URL(root.location.href);
		if (!url.searchParams.has("configuration_id")) {
			return;
		}
		url.searchParams.delete("configuration_id");
		var next = url.pathname + url.search + url.hash;
		root.history.replaceState({}, "", next);
	}

	function navigate(route, ctx) {
		var normalized = String(route || "").trim();
		if (ITW_REGISTERED_ROUTES.indexOf(normalized) === -1) {
			frappe.msgprint({
				title: __("Navigation failed"),
				indicator: "red",
				message: __("Unknown IT Wizard page route: {0}", [route || ""]),
			});
			return;
		}
		var root = desk_root_window();
		if (ctx) {
			set_route_context(ctx);
		}
		if (normalized === "it-tender-configuration-dashboard") {
			configRedirectInFlight = false;
			clear_configuration_id_from_url();
		}
		root.frappe.set_route(normalized);
		if (CONFIGURATION_CONTEXT_ROUTES[normalized] && ctx && ctx.configuration_id) {
			setTimeout(function () {
				sync_configuration_id_to_url(ctx.configuration_id);
			}, 0);
		}
	}

	function prepare_iframe_frame(iframe) {
		if (!iframe) {
			return;
		}
		iframe.style.opacity = "0";
		iframe.style.transition = "opacity 120ms ease-in";
	}

	function reveal_iframe_frame(doc) {
		var frame = doc && doc.defaultView && doc.defaultView.frameElement;
		if (frame) {
			frame.style.opacity = "1";
		}
	}

	function unfix_layout_chrome(node) {
		if (!node || !node.classList) {
			return;
		}
		node.classList.remove(
			"fixed",
			"sticky",
			"top-0",
			"top-14",
			"top-16",
			"left-0",
			"right-0",
			"z-40",
			"z-50",
		);
		node.classList.add("relative", "w-full");
	}

	function install_hydration_gate(doc) {
		if (!doc || !doc.head || doc.getElementById("it-wizard-hydration-gate")) {
			return;
		}
		var style = doc.createElement("style");
		style.id = "it-wizard-hydration-gate";
		style.textContent =
			'body:not([data-it-wizard-hydrated="1"]):not([data-it-wizard-hydrated="error"]) > main,' +
			'body:not([data-it-wizard-hydrated="1"]):not([data-it-wizard-hydrated="error"]) main {' +
			"visibility: hidden !important;" +
			"}" +
			"body.it-wizard-header-harmonized {" +
			"display: flex;" +
			"flex-direction: column;" +
			"min-height: 100%;" +
			"background: #f7f9fb;" +
			"}" +
			"body.it-wizard-header-harmonized > header {" +
			"position: relative !important;" +
			"top: auto !important;" +
			"flex-shrink: 0;" +
			"}" +
			"body.it-wizard-header-harmonized > main {" +
			"flex: 1 1 auto;" +
			"margin-top: 0 !important;" +
			"padding-top: 1rem !important;" +
			"padding-bottom: 1.5rem !important;" +
			"padding-left: 1rem !important;" +
			"padding-right: 1rem !important;" +
			"max-width: 1600px !important;" +
			"width: 100% !important;" +
			"margin-left: auto !important;" +
			"margin-right: auto !important;" +
			"box-sizing: border-box;" +
			"}" +
			"@media (min-width: 768px) {" +
			"body.it-wizard-header-harmonized > main {" +
			"padding-left: 2rem !important;" +
			"padding-right: 2rem !important;" +
			"}" +
			"}" +
			"body.it-wizard-header-harmonized > main > section + section {" +
			"margin-top: 24px;" +
			"}" +
			"[data-itw-kpi-grid] {" +
			"display: grid !important;" +
			"grid-template-columns: repeat(6, minmax(0, 1fr)) !important;" +
			"gap: 12px !important;" +
			"width: 100%;" +
			"}" +
			"[data-itw-kpi-grid] > div {" +
			"box-sizing: border-box;" +
			"min-height: 118px;" +
			"padding: 20px !important;" +
			"background: #ffffff;" +
			"border: 1px solid #E2E8F0;" +
			"border-radius: 0.5rem;" +
			"box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);" +
			"display: flex;" +
			"flex-direction: column;" +
			"justify-content: space-between;" +
			"}" +
			"[data-itw-kpi-grid] .font-label-caps," +
			"[data-itw-kpi-grid] .text-label-caps {" +
			'font-family: Inter, system-ui, sans-serif;' +
			"font-size: 12px !important;" +
			"line-height: 16px !important;" +
			"letter-spacing: 0.05em !important;" +
			"font-weight: 700 !important;" +
			"text-transform: uppercase;" +
			"margin-bottom: 8px !important;" +
			"}" +
			"[data-itw-kpi-grid] .font-data-mono-lg," +
			"[data-itw-kpi-grid] .text-data-mono-lg {" +
			'font-family: "JetBrains Mono", ui-monospace, monospace;' +
			"font-size: 18px !important;" +
			"line-height: 24px !important;" +
			"font-weight: 600 !important;" +
			"}" +
			"[data-itw-kpi-grid] .font-body-md," +
			"[data-itw-kpi-grid] .text-body-md {" +
			'font-family: Inter, system-ui, sans-serif;' +
			"font-size: 14px !important;" +
			"line-height: 20px !important;" +
			"}" +
			"[data-itw-kpi-grid] .flex.items-baseline.gap-2 {" +
			"display: flex;" +
			"align-items: baseline;" +
			"gap: 8px;" +
			"flex-wrap: wrap;" +
			"}" +
			"[data-itw-kpi-grid] .mt-4.h-1 {" +
			"margin-top: 16px !important;" +
			"height: 4px !important;" +
			"width: 100%;" +
			"border-radius: 9999px;" +
			"overflow: hidden;" +
			"background: #e6e8ea;" +
			"}" +
			"body.it-wizard-header-harmonized > nav {" +
			"position: relative !important;" +
			"top: auto !important;" +
			"z-index: auto !important;" +
			"flex-shrink: 0;" +
			"margin-top: 0 !important;" +
			"}" +
			".it-wizard-table-surface {" +
			"display: flex;" +
			"flex-direction: column;" +
			"overflow: hidden;" +
			"max-width: 100%;" +
			"}" +
			".it-wizard-table-scroll-host {" +
			"display: block;" +
			"width: 100%;" +
			"max-width: 100%;" +
			"max-height: 600px;" +
			"overflow-x: auto !important;" +
			"overflow-y: auto !important;" +
			"position: relative;" +
			"-webkit-overflow-scrolling: touch;" +
			"}" +
			".it-wizard-table-footer {" +
			"position: relative !important;" +
			"z-index: 2;" +
			"flex-shrink: 0;" +
			"background: #f2f4f6;" +
			"}" +
			"[data-itw-page-size-wrap] .material-symbols-outlined {" +
			"display: none !important;" +
			"}" +
			"[data-itw-page-size] {" +
			"min-width: 4.5rem;" +
			"height: 2rem;" +
			"padding: 0.25rem 2rem 0.25rem 0.75rem;" +
			"font-size: 0.875rem;" +
			"line-height: 1.25rem;" +
			"appearance: auto !important;" +
			"-webkit-appearance: menulist !important;" +
			"background-image: none !important;" +
			"cursor: pointer;" +
			"}" +
			"[data-itw-filter-drawer]:not(.hidden) {" +
			"display: block !important;" +
			"}" +
			"[data-itw-drawer-stub-surface] {" +
			"opacity: 0.55;" +
			"pointer-events: none;" +
			"}" +
			"[data-itw-drawer-capability-note] {" +
			"font-size: 12px;" +
			"line-height: 18px;" +
			"color: #5f6368;" +
			"background: #f2f4f6;" +
			"border: 1px solid #e2e8f0;" +
			"border-radius: 0.5rem;" +
			"padding: 0.75rem 1rem;" +
			"margin-bottom: 1.5rem;" +
			"}";
		doc.head.appendChild(style);
	}

	function normalize_page_layout(doc, screen) {
		if (!doc || !doc.body) {
			return;
		}
		if (screen === "std_config_overview") {
			harmonize_overview_page_layout(doc);
			return;
		}
		if (screen === "tender_profile") {
			harmonize_tender_profile_page_layout(doc);
			return;
		}
		if (screen === "tds") {
			harmonize_tds_page_layout(doc);
			return;
		}
		doc.body.classList.add("it-wizard-header-harmonized");
		doc.querySelectorAll("main").forEach(function (main) {
			["pt-24", "pt-20", "pt-16", "pb-24"].forEach(function (token) {
				main.classList.remove(token);
			});
		});
		doc.querySelectorAll("header.fixed, header.sticky").forEach(unfix_layout_chrome);
		doc.querySelectorAll("body > nav").forEach(unfix_layout_chrome);
		enhance_dashboard_kpi_layout(doc);
		enhance_dashboard_filter_layout(doc);
		enhance_dashboard_filter_drawer(doc);
		enhance_dashboard_table_layout(doc);
	}

	function enhance_dashboard_filter_layout(doc) {
		var searchInput = doc.querySelector('input[placeholder*="Search Tender"]');
		if (!searchInput) {
			return;
		}
		searchInput.setAttribute("data-itw-search", "1");
		var bar = searchInput.closest("section");
		if (!bar) {
			return;
		}
		bar.setAttribute("data-itw-filter-bar", "1");
		var filterKeys = ["status", "entity", "method"];
		bar.querySelectorAll("select").forEach(function (sel, index) {
			if (filterKeys[index]) {
				sel.setAttribute("data-itw-filter", filterKeys[index]);
			}
		});
		bar.querySelectorAll("button").forEach(function (btn) {
			if ((btn.textContent || "").indexOf("More Filters") >= 0) {
				btn.setAttribute("data-itw-open-filter-drawer", "1");
			}
		});
	}

	function enhance_dashboard_filter_drawer(doc) {
		var drawer = doc.getElementById("filters-drawer");
		if (!drawer) {
			return;
		}
		drawer.setAttribute("data-itw-filter-drawer", "1");
		drawer.querySelectorAll("select").forEach(function (sel) {
			var first = sel.options.length ? (sel.options[0].textContent || "").trim() : "";
			if (first === "All Methods") {
				sel.setAttribute("data-itw-drawer-filter", "method");
			} else if (first === "All Packages") {
				sel.setAttribute("data-itw-drawer-stub", "1");
			}
		});
		drawer.querySelectorAll('input[type="checkbox"]').forEach(function (input) {
			var label = input.closest("label");
			var text = label ? (label.textContent || "").trim() : "";
			if (text.indexOf("Due This Week") >= 0) {
				input.setAttribute("data-itw-drawer-filter", "due_this_week");
			} else if (text.indexOf("Returned") >= 0) {
				input.setAttribute("data-itw-drawer-filter", "returned");
			} else if (text.indexOf("Validation Failed") >= 0) {
				input.setAttribute("data-itw-drawer-filter", "validation_failed");
			} else {
				input.setAttribute("data-itw-drawer-stub", "1");
			}
		});
		drawer.querySelectorAll("input[type='text']").forEach(function (input) {
			input.setAttribute("data-itw-drawer-stub", "1");
		});
		drawer.querySelectorAll(".flex.flex-wrap.gap-2 span").forEach(function (pill) {
			pill.setAttribute("data-itw-drawer-stub", "1");
		});
		drawer.querySelectorAll("button").forEach(function (btn) {
			var text = (btn.textContent || "").trim();
			if (text === "Clear All") {
				btn.setAttribute("data-itw-drawer-action", "clear");
			} else if (text === "Apply Filters") {
				btn.setAttribute("data-itw-drawer-action", "apply");
			} else if ((btn.textContent || "").indexOf("close") >= 0 || btn.querySelector(".material-symbols-outlined")) {
				var icon = btn.querySelector(".material-symbols-outlined");
				if (icon && (icon.textContent || "").trim() === "close") {
					btn.setAttribute("data-itw-drawer-action", "close");
				}
			}
		});
		var backdrop = drawer.firstElementChild;
		if (backdrop) {
			backdrop.setAttribute("data-itw-drawer-action", "close");
		}
		inject_drawer_capability_note(doc);
		apply_drawer_stub_state(doc);
	}

	function inject_drawer_capability_note(doc) {
		var drawer = doc.querySelector("[data-itw-filter-drawer]");
		if (!drawer) {
			return;
		}
		var scrollBody = drawer.querySelector(".flex-grow.overflow-y-auto");
		if (!scrollBody || scrollBody.querySelector("[data-itw-drawer-capability-note]")) {
			return;
		}
		var note = doc.createElement("p");
		note.setAttribute("data-itw-drawer-capability-note", "1");
		note.textContent = __(
			"Active now: Method and status checkboxes. Category, STD package, review track, and owner filters require ITW-03+ step editors and stay disabled until then.",
		);
		scrollBody.insertBefore(note, scrollBody.firstChild);
	}

	function apply_drawer_stub_state(doc) {
		var drawer = doc.querySelector("[data-itw-filter-drawer]");
		if (!drawer) {
			return;
		}
		drawer.querySelectorAll("[data-itw-drawer-stub]").forEach(function (node) {
			var surface = node.closest("label") || node.closest(".space-y-1") || node;
			surface.setAttribute("data-itw-drawer-stub-surface", "1");
			if (node.matches && node.matches("input, select, textarea")) {
				node.disabled = true;
				node.setAttribute("aria-disabled", "true");
				if (node.type === "checkbox") {
					node.checked = false;
				}
			}
		});
	}

	function enhance_dashboard_kpi_layout(doc) {
		var main = doc.querySelector("main");
		if (!main) {
			return;
		}
		var kpiSection = main.querySelector("section");
		if (!kpiSection) {
			return;
		}
		kpiSection.classList.add("it-wizard-kpi-grid");
		kpiSection.setAttribute("data-itw-kpi-grid", "1");
	}

	function enhance_dashboard_table_layout(doc) {
		var table = doc.querySelector("table");
		if (!table) {
			return;
		}
		var section = table.closest("section");
		if (section) {
			section.classList.remove("overflow-visible");
			section.classList.add("it-wizard-table-surface");
			section.setAttribute("data-itw-table-surface", "1");
		}
		var scrollHost =
			table.parentElement && table.parentElement.classList.contains("custom-scrollbar")
				? table.parentElement
				: table.parentElement;
		if (scrollHost) {
			scrollHost.classList.remove("overflow-visible");
			scrollHost.classList.add("it-wizard-table-scroll-host");
			scrollHost.setAttribute("data-itw-table-scroll-host", "1");
		}
		var footer = section ? section.querySelector(".bg-surface-container-low.px-4.py-3") : null;
		if (footer) {
			footer.classList.add("it-wizard-table-footer");
			footer.setAttribute("data-itw-table-footer", "1");
			var pageSizeSelect = footer.querySelector("select");
			if (pageSizeSelect) {
				normalize_page_size_select(pageSizeSelect);
				var wrap = pageSizeSelect.parentElement;
				if (wrap) {
					wrap.setAttribute("data-itw-page-size-wrap", "1");
				}
			}
			var pagerPagesHost = find_pager_pages_host(footer);
			if (pagerPagesHost) {
				pagerPagesHost.setAttribute("data-itw-pager-pages", "1");
			}
		}
	}

	function find_pager_pages_host(footer) {
		if (!footer) {
			return null;
		}
		var blocks = footer.querySelectorAll(".flex.items-center.gap-6");
		for (var i = 0; i < blocks.length; i++) {
			var outer = blocks[i].querySelector(".flex.items-center.gap-1");
			if (!outer) {
				continue;
			}
			var children = outer.children;
			for (var j = 0; j < children.length; j++) {
				var child = children[j];
				if (child.tagName === "DIV" && child.classList.contains("flex")) {
					return child;
				}
			}
		}
		return null;
	}

	function normalize_page_size_select(select) {
		if (!select) {
			return;
		}
		select.setAttribute("data-itw-page-size", "1");
		select.classList.remove("appearance-none", "pr-8");
		Array.from(select.options || []).forEach(function (option) {
			if (!option.value) {
				option.value = (option.textContent || "").trim();
			}
		});
		var wrap = select.parentElement;
		if (wrap) {
			wrap.querySelectorAll(".material-symbols-outlined").forEach(function (icon) {
				icon.remove();
			});
		}
	}

	function mark_hydrated(doc) {
		if (!doc || !doc.body) {
			return;
		}
		doc.body.setAttribute("data-it-wizard-hydrated", "1");
		reveal_iframe_frame(doc);
	}

	function mark_hydration_error(doc) {
		if (!doc || !doc.body) {
			return;
		}
		doc.body.setAttribute("data-it-wizard-hydrated", "error");
		reveal_iframe_frame(doc);
	}

	function set_kpi_card(doc, label, value, todayDelta) {
		doc.querySelectorAll(".font-label-caps").forEach(function (node) {
			if ((node.textContent || "").trim().toUpperCase() !== String(label).toUpperCase()) {
				return;
			}
			var card = node.closest("div.bg-surface-white") || node.parentElement;
			if (!card) {
				return;
			}
			var headline = card.querySelector(".font-data-mono-lg");
			if (headline) {
				headline.textContent = String(value);
			}
			var subtext = card.querySelector(".flex.items-baseline.gap-2 > .font-body-md");
			if (subtext) {
				var delta = parseInt(todayDelta, 10) || 0;
				if (delta > 0) {
					subtext.textContent = "+" + delta + " " + __("today");
					subtext.style.display = "";
				} else {
					subtext.textContent = "";
					subtext.style.display = "none";
				}
			}
			var progress = card.querySelector(".mt-4.h-1");
			if (progress) {
				progress.style.display = "none";
			}
		});
	}

	function hydrate_dashboard_kpis(doc, kpis, todayDeltas) {
		if (!kpis) {
			return;
		}
		Object.keys(KPI_LABELS).forEach(function (key) {
			set_kpi_card(
				doc,
				KPI_LABELS[key],
				kpis[key] || 0,
				(todayDeltas && todayDeltas[key]) || 0,
			);
		});
	}

	function format_entity_reference(entity) {
		if (!entity) {
			return __("—");
		}
		var name = (entity.name || "").trim();
		var code = (entity.code || "").trim();
		if (!name && !code) {
			return __("—");
		}
		if (name && code && name !== code) {
			return frappe.utils.escape_html(name) + " (" + frappe.utils.escape_html(code) + ")";
		}
		return frappe.utils.escape_html(name || code);
	}

	function format_method_reference(entity) {
		if (!entity) {
			return __("—");
		}
		return frappe.utils.escape_html((entity.name || "").trim() || __("—"));
	}

	function rebuild_filter_select_options(select, placeholder, options, valueKey, labelKey) {
		if (!select) {
			return;
		}
		var previous = select.value || "";
		var html = '<option value="">' + frappe.utils.escape_html(placeholder) + "</option>";
		(options || []).forEach(function (row) {
			var value = row[valueKey] || "";
			var label = row[labelKey] || value;
			if (!value || !label) {
				return;
			}
			html +=
				'<option value="' +
				frappe.utils.escape_html(value) +
				'">' +
				frappe.utils.escape_html(label) +
				"</option>";
		});
		select.innerHTML = html;
		if (previous) {
			select.value = previous;
			if (select.value !== previous) {
				select.selectedIndex = 0;
			}
		}
	}

	function hydrate_drawer_method_select(doc, methods) {
		var drawer = doc.querySelector("[data-itw-filter-drawer]");
		if (!drawer) {
			return;
		}
		var select = drawer.querySelector('[data-itw-drawer-filter="method"]');
		if (!select) {
			return;
		}
		var rows = [{ id: "", name: "All Methods" }].concat(methods || []);
		rebuild_filter_select_options(select, "All Methods", rows, "id", "name");
		select.options[0].textContent = "All Methods";
		select.options[0].value = "";
	}

	function hydrate_filter_selects(doc, filterOptions) {
		var options = filterOptions || {};
		var bar = doc.querySelector("[data-itw-filter-bar]");
		if (!bar) {
			return;
		}
		var statusOptions = (options.statuses || []).map(function (row) {
			return { value: row.value, label: row.label };
		});
		if (!statusOptions.length) {
			statusOptions = STATUS_FILTER_OPTIONS;
		}
		rebuild_filter_select_options(
			bar.querySelector('[data-itw-filter="status"]'),
			"Status: All",
			statusOptions,
			"value",
			"label",
		);
		rebuild_filter_select_options(
			bar.querySelector('[data-itw-filter="entity"]'),
			"Entity: All",
			options.entities || [],
			"id",
			"name",
		);
		rebuild_filter_select_options(
			bar.querySelector('[data-itw-filter="method"]'),
			"Method: All",
			options.methods || [],
			"id",
			"name",
		);
		hydrate_drawer_method_select(doc, options.methods || []);
	}

	function state_badge_class(state) {
		if (state === "VALIDATION_FAILED") {
			return "bg-rose-exhausted bg-opacity-10 text-rose-exhausted";
		}
		if (state === "READY_FOR_REVIEW" || state === "APPROVED_FOR_TENDER_CREATION" || state === "BOUND_TO_TENDER") {
			return "bg-emerald-available bg-opacity-10 text-emerald-available";
		}
		if (state === "RETURNED_FOR_CORRECTION") {
			return "bg-amber-reserved bg-opacity-10 text-amber-reserved";
		}
		return "bg-indigo-committed bg-opacity-10 text-indigo-committed";
	}

	function build_row_html(item) {
		var planning = item.planning_package || {};
		var pe = item.procuring_entity || {};
		var method = item.method || {};
		var step = item.current_step || {};
		var validation = item.validation || {};
		var owner = item.owner || {};
		var blockers = validation.blockers || 0;
		var warnings = validation.warnings || 0;
		var validationLine =
			blockers > 0
				? blockers + " " + __("Blockers")
				: blockers + " " + __("Blockers") + " / " + warnings + " " + __("Warnings");
		var validationClass =
			blockers > 0 ? "text-rose-exhausted" : warnings > 0 ? "text-amber-reserved" : "text-emerald-available";
		var dueClass = item.overdue ? "text-rose-exhausted" : "text-on-surface-variant";
		var borderClass =
			item.state === "VALIDATION_FAILED"
				? "border-l-4 border-rose-exhausted"
				: item.state === "RETURNED_FOR_CORRECTION"
					? "border-l-4 border-amber-reserved"
					: "";
		var continueLabel = item.state === "VALIDATION_FAILED" ? __("View Findings") : __("Continue");
		return (
			'<tr class="' +
			borderClass +
			'" data-configuration-id="' +
			frappe.utils.escape_html(item.code || "") +
			'">' +
			'<td class="px-4 py-4"><div class="font-data-mono text-data-mono text-primary mb-1">' +
			frappe.utils.escape_html(item.code || "") +
			'</div><div class="font-body-md text-body-md font-medium text-on-surface mb-1">' +
			frappe.utils.escape_html(item.name || "") +
			'</div><div class="font-data-mono text-[12px] text-on-surface-variant">' +
			__("Planning Package") +
			": " +
			frappe.utils.escape_html(planning.code || planning.name || __("—")) +
			"</div></td>" +
			'<td class="px-4 py-4 font-body-md text-body-md text-on-surface-variant">' +
			format_entity_reference(pe) +
			"</td>" +
			'<td class="px-4 py-4 font-body-md text-body-md text-on-surface-variant">' +
			format_method_reference(method) +
			"</td>" +
			'<td class="px-4 py-4"><div class="mb-2"><span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ' +
			state_badge_class(item.state) +
			'">' +
			frappe.utils.escape_html(item.state_label || item.state || "") +
			'</span></div><div class="text-xs font-medium ' +
			validationClass +
			'">' +
			frappe.utils.escape_html(validationLine) +
			"</div></td>" +
			'<td class="px-4 py-4"><div class="flex items-center gap-3 mb-1"><span class="font-data-mono text-[12px] text-on-surface-variant">' +
			String(item.completion_percent || 0) +
			'%</span></div><div class="font-body-md text-body-md text-on-surface-variant">' +
			__("Current Step") +
			": " +
			frappe.utils.escape_html(step.name || step.code || __("—")) +
			"</div></td>" +
			'<td class="px-4 py-4"><div class="font-body-md text-body-md mb-1">' +
			frappe.utils.escape_html(owner.name || __("—")) +
			'</div><div class="font-body-md text-body-md text-on-surface-variant">' +
			__("Technical Review") +
			"</div></td>" +
			'<td class="px-4 py-4 font-data-mono text-data-mono ' +
			dueClass +
			'">' +
			frappe.utils.escape_html(item.last_updated || __("—")) +
			(item.overdue ? ' <span class="material-symbols-outlined text-[14px] align-middle">warning</span>' : "") +
			"</td>" +
			'<td class="px-4 py-4 text-right"><div class="flex items-center justify-end gap-2">' +
			'<button type="button" class="px-3 py-1 bg-primary text-on-primary rounded text-xs font-medium hover:opacity-90" data-itw-action="continue">' +
			frappe.utils.escape_html(continueLabel) +
			"</button></div></td></tr>"
		);
	}

	function hydrate_dashboard_table(doc, items, highlight_id) {
		var tbody = doc.querySelector("table tbody");
		if (!tbody) {
			return;
		}
		if (!items || !items.length) {
			tbody.innerHTML =
				'<tr><td colspan="8" class="px-4 py-8 text-center text-on-surface-variant">' +
				__("No tender configurations found.") +
				"</td></tr>";
			return;
		}
		tbody.innerHTML = items.map(build_row_html).join("");
		if (highlight_id) {
			var row = tbody.querySelector('[data-configuration-id="' + highlight_id + '"]');
			if (row) {
				row.classList.add("ring-2", "ring-primary");
			}
		}
	}

	function get_visible_page_numbers(totalPages, currentPage) {
		var total = Math.max(1, parseInt(totalPages, 10) || 1);
		var page = Math.max(1, Math.min(total, parseInt(currentPage, 10) || 1));
		if (total <= 7) {
			var all = [];
			for (var i = 1; i <= total; i++) {
				all.push(i);
			}
			return all;
		}
		var items = [1];
		var windowStart = Math.max(2, page - 1);
		var windowEnd = Math.min(total - 1, page + 1);
		if (windowStart > 2) {
			items.push("ellipsis");
		}
		for (var p = windowStart; p <= windowEnd; p++) {
			items.push(p);
		}
		if (windowEnd < total - 1) {
			items.push("ellipsis");
		}
		items.push(total);
		return items;
	}

	function render_pager_page_buttons(host, totalPages, currentPage) {
		if (!host) {
			return;
		}
		var items = get_visible_page_numbers(totalPages, currentPage);
		host.innerHTML = items
			.map(function (item) {
				if (item === "ellipsis") {
					return '<span class="px-1 text-outline" data-itw-pager-ellipsis="1">...</span>';
				}
				var active = item === currentPage;
				return (
					'<button type="button" class="w-8 h-8 flex items-center justify-center rounded text-sm ' +
					(active
						? "bg-primary text-on-primary font-bold"
						: "hover:bg-surface-container font-medium") +
					'" data-itw-pager-page="' +
					item +
					'">' +
					item +
					"</button>"
				);
			})
			.join("");
	}

	function hydrate_dashboard_pager(doc, page, page_size, total) {
		var footer = doc.querySelector("[data-itw-table-footer]");
		if (!footer) {
			footer = doc.querySelector(".bg-surface-container-low.px-4.py-3");
		}
		if (!footer) {
			return;
		}
		var pageSize = page_size || 25;
		var currentPage = page || 1;
		var count = total || 0;
		var totalPages = count > 0 ? Math.max(1, Math.ceil(count / pageSize)) : 1;
		if (currentPage > totalPages) {
			currentPage = totalPages;
		}
		var start = count > 0 ? (currentPage - 1) * pageSize + 1 : 0;
		var end = count > 0 ? Math.min(currentPage * pageSize, count) : 0;
		footer.setAttribute("data-itw-total", String(count));
		footer.setAttribute("data-itw-current-page", String(currentPage));
		footer.setAttribute("data-itw-page-size-active", String(pageSize));
		var summary =
			footer.querySelector(".font-body-md.text-body-md.text-on-surface-variant") ||
			footer.querySelector(".font-body-md.text-on-surface-variant");
		if (summary) {
			summary.setAttribute("data-itw-pager-showing", "1");
			summary.innerHTML =
				__("Showing") +
				' <span class="font-bold text-on-surface">' +
				start +
				"-" +
				end +
				'</span> ' +
				__("of") +
				' <span class="font-bold text-on-surface">' +
				count +
				"</span>";
		}
		var pageSizeSelect = footer.querySelector("[data-itw-page-size]");
		if (pageSizeSelect) {
			normalize_page_size_select(pageSizeSelect);
			pageSizeSelect.value = String(pageSize);
		}
		var pagesHost = footer.querySelector("[data-itw-pager-pages]") || find_pager_pages_host(footer);
		if (pagesHost) {
			pagesHost.setAttribute("data-itw-pager-pages", "1");
			render_pager_page_buttons(pagesHost, totalPages, currentPage);
		}
		footer.querySelectorAll("button").forEach(function (btn) {
			var icon = btn.querySelector(".material-symbols-outlined");
			if (!icon) {
				return;
			}
			var iconText = (icon.textContent || "").trim();
			if (iconText !== "chevron_left" && iconText !== "chevron_right") {
				return;
			}
			var disable =
				totalPages <= 1 ||
				(iconText === "chevron_left" && currentPage <= 1) ||
				(iconText === "chevron_right" && currentPage >= totalPages);
			btn.disabled = disable;
			if (disable) {
				btn.setAttribute("disabled", "");
				btn.style.opacity = "0.3";
			} else {
				btn.removeAttribute("disabled");
				btn.style.opacity = "";
			}
		});
	}

	function get_page_size(doc) {
		var footer = doc.querySelector("[data-itw-table-footer]");
		if (!footer) {
			return 25;
		}
		var select = footer.querySelector("select");
		if (!select) {
			return 25;
		}
		var parsed = parseInt(select.value || "", 10);
		return !isNaN(parsed) && parsed > 0 ? parsed : 25;
	}

	function wire_dashboard_pagination(doc, ctx, filters, reload) {
		var footer = doc.querySelector("[data-itw-table-footer]");
		if (!footer || footer.getAttribute("data-itw-pager-wired") === "1") {
			return;
		}
		footer.setAttribute("data-itw-pager-wired", "1");
		var pageSizeSelect = footer.querySelector("select");
		if (pageSizeSelect) {
			pageSizeSelect.addEventListener("change", function () {
				reload({ page: 1, page_size: get_page_size(doc) });
			});
		}
		footer.addEventListener("click", function (event) {
			var btn = event.target.closest("button");
			if (!btn || btn.disabled) {
				return;
			}
			var icon = btn.querySelector(".material-symbols-outlined");
			var iconText = icon ? (icon.textContent || "").trim() : "";
			var page = parseInt(footer.getAttribute("data-itw-current-page") || "1", 10);
			var pageSize = parseInt(
				footer.getAttribute("data-itw-page-size-active") || String(get_page_size(doc)),
				10,
			);
			var total = parseInt(footer.getAttribute("data-itw-total") || "0", 10);
			var totalPages = Math.max(1, Math.ceil(total / pageSize));
			if (iconText === "chevron_left") {
				if (page > 1) {
					reload({ page: page - 1, page_size: pageSize });
				}
				return;
			}
			if (iconText === "chevron_right") {
				if (page < totalPages) {
					reload({ page: page + 1, page_size: pageSize });
				}
				return;
			}
			var pageAttr = btn.getAttribute("data-itw-pager-page");
			var pageNum = pageAttr ? parseInt(pageAttr, 10) : parseInt((btn.textContent || "").trim(), 10);
			if (!isNaN(pageNum) && pageNum >= 1 && pageNum <= totalPages) {
				reload({ page: pageNum, page_size: pageSize });
			}
		});
	}

	function disable_stub_actions(doc) {
		doc.querySelectorAll("button").forEach(function (btn) {
			var text = (btn.textContent || "").trim();
			if (text.indexOf("Export Dashboard Report") >= 0 || text.indexOf("View Audit Logs") >= 0) {
				btn.disabled = true;
				btn.style.opacity = "0.55";
				btn.style.pointerEvents = "none";
				btn.setAttribute("aria-disabled", "true");
			}
		});
	}

	function get_active_filters(doc) {
		try {
			var raw = doc.body.getAttribute("data-itw-active-filters");
			return raw ? JSON.parse(raw) : null;
		} catch (e) {
			return null;
		}
	}

	function set_active_filters(doc, nextFilters) {
		doc.body.setAttribute("data-itw-active-filters", JSON.stringify(nextFilters || {}));
	}

	function normalize_filter_args(filters) {
		var next = Object.assign({}, filters || {});
		if (next.state) {
			next.states = next.state;
			delete next.state;
		}
		["states", "q", "procurement_entity_id", "procurement_method_code"].forEach(function (key) {
			if (!next[key]) {
				delete next[key];
			}
		});
		if (!next.overdue_only) {
			delete next.overdue_only;
		}
		return next;
	}

	function read_drawer_filters(doc) {
		var result = {
			procurement_method_code: "",
			states: "",
			overdue_only: false,
		};
		var drawer = doc.querySelector("[data-itw-filter-drawer]");
		if (!drawer) {
			return result;
		}
		var methodSelect = drawer.querySelector('[data-itw-drawer-filter="method"]');
		if (methodSelect) {
			result.procurement_method_code = (methodSelect.value || "").trim();
		}
		var stateKeys = [];
		drawer.querySelectorAll("[data-itw-drawer-filter]").forEach(function (node) {
			var key = node.getAttribute("data-itw-drawer-filter");
			if (key === "due_this_week" && node.checked) {
				result.overdue_only = true;
				return;
			}
			if ((key === "validation_failed" || key === "returned") && node.checked) {
				stateKeys.push(DRAWER_STATE_MAP[key]);
			}
		});
		result.states = stateKeys.join(",");
		return result;
	}

	function reset_drawer_status_filters(doc) {
		var drawer = doc.querySelector("[data-itw-filter-drawer]");
		if (!drawer) {
			return;
		}
		drawer.querySelectorAll('input[type="checkbox"][data-itw-drawer-filter]').forEach(function (input) {
			input.checked = false;
		});
	}

	function sync_toolbar_method_filter(doc, methodCode) {
		var bar = doc.querySelector("[data-itw-filter-bar]");
		if (!bar) {
			return;
		}
		var methodSelect = bar.querySelector('[data-itw-filter="method"]');
		if (!methodSelect) {
			return;
		}
		if (!methodCode) {
			methodSelect.selectedIndex = 0;
			return;
		}
		methodSelect.value = methodCode;
		if (methodSelect.value !== methodCode) {
			Array.from(methodSelect.options || []).forEach(function (option, index) {
				if (option.value === methodCode) {
					methodSelect.selectedIndex = index;
				}
			});
		}
	}

	function reset_dashboard_filter_ui(doc) {
		var searchInput = doc.querySelector("[data-itw-search]");
		if (searchInput) {
			searchInput.value = "";
		}
		var bar = doc.querySelector("[data-itw-filter-bar]");
		if (bar) {
			bar.querySelectorAll("select[data-itw-filter]").forEach(function (sel) {
				sel.selectedIndex = 0;
			});
		}
		var drawer = doc.querySelector("[data-itw-filter-drawer]");
		if (drawer) {
			drawer.querySelectorAll("select[data-itw-drawer-filter]").forEach(function (sel) {
				sel.selectedIndex = 0;
			});
			drawer.querySelectorAll('input[type="checkbox"][data-itw-drawer-filter]').forEach(function (input) {
				input.checked = false;
			});
		}
	}

	function open_filter_drawer(doc) {
		var drawer = doc.getElementById("filters-drawer");
		if (drawer) {
			drawer.classList.remove("hidden");
		}
	}

	function close_filter_drawer(doc) {
		var drawer = doc.getElementById("filters-drawer");
		if (drawer) {
			drawer.classList.add("hidden");
		}
	}

	function wire_filter_drawer(doc, reload) {
		doc.querySelectorAll("[data-itw-open-filter-drawer]").forEach(function (btn) {
			btn.addEventListener("click", function (event) {
				event.preventDefault();
				open_filter_drawer(doc);
			});
		});
		doc.addEventListener("keydown", function (event) {
			if (event.key === "Escape") {
				close_filter_drawer(doc);
			}
		});
		doc.addEventListener("click", function (event) {
			var actionNode = event.target.closest("[data-itw-drawer-action]");
			if (!actionNode) {
				return;
			}
			var action = actionNode.getAttribute("data-itw-drawer-action");
			if (action === "close") {
				event.preventDefault();
				close_filter_drawer(doc);
				return;
			}
			if (action === "clear") {
				event.preventDefault();
				reset_dashboard_filter_ui(doc);
				close_filter_drawer(doc);
				reload({
					page: 1,
					q: "",
					state: "",
					states: "",
					procurement_entity_id: "",
					procurement_method_code: "",
					overdue_only: false,
				});
				return;
			}
			if (action === "apply") {
				event.preventDefault();
				var drawerFilters = read_drawer_filters(doc);
				sync_toolbar_method_filter(doc, drawerFilters.procurement_method_code);
				var bar = doc.querySelector("[data-itw-filter-bar]");
				if (bar) {
					var statusSelect = bar.querySelector('[data-itw-filter="status"]');
					if (statusSelect) {
						statusSelect.selectedIndex = 0;
					}
				}
				close_filter_drawer(doc);
				reload(
					Object.assign(
						{
							page: 1,
							state: "",
							overdue_only: false,
						},
						drawerFilters,
					),
				);
			}
		});
	}

	function read_dashboard_filters(doc) {
		var result = {
			q: get_search_query(doc),
			state: "",
			states: "",
			procurement_entity_id: "",
			procurement_method_code: "",
			overdue_only: false,
		};
		var bar = doc.querySelector("[data-itw-filter-bar]");
		if (!bar) {
			return result;
		}
		bar.querySelectorAll("select[data-itw-filter]").forEach(function (sel) {
			var key = sel.getAttribute("data-itw-filter");
			var val = (sel.value || "").trim();
			if (!val || val === "All") {
				return;
			}
			if (key === "status") {
				result.states = "";
				result.overdue_only = false;
				if (val && val.indexOf("Status:") !== 0) {
					result.state = val;
				} else if (STATE_FILTER_MAP[val]) {
					result.state = STATE_FILTER_MAP[val];
				} else if (val.indexOf("Status:") === 0) {
					var statusLabel = val.replace("Status:", "").trim();
					if (statusLabel && statusLabel !== "All") {
						result.state = STATE_FILTER_MAP[statusLabel] || "";
					}
				}
			} else if (key === "entity") {
				if (val && val.indexOf("Entity:") !== 0) {
					result.procurement_entity_id = val;
				} else if (ENTITY_FILTER_MAP[val]) {
					result.procurement_entity_id = ENTITY_FILTER_MAP[val];
				} else if (val.indexOf("Entity:") === 0) {
					var entityLabel = val.replace("Entity:", "").trim();
					if (entityLabel && entityLabel !== "All") {
						result.procurement_entity_id = ENTITY_FILTER_MAP[entityLabel] || "";
					}
				}
			} else if (key === "method") {
				if (val && val.indexOf("Method:") !== 0) {
					result.procurement_method_code = val;
				} else if (METHOD_FILTER_MAP[val]) {
					result.procurement_method_code = METHOD_FILTER_MAP[val];
				} else if (val.indexOf("Method:") === 0) {
					var methodLabel = val.replace("Method:", "").trim();
					if (methodLabel && methodLabel !== "All") {
						result.procurement_method_code = METHOD_FILTER_MAP[methodLabel] || "";
					}
				}
			}
		});
		return result;
	}

	function get_search_query(doc) {
		var input = doc.querySelector('input[placeholder*="Search Tender"]');
		return input ? (input.value || "").trim() : "";
	}

	function install_overview_layout_styles(doc) {
		if (!doc || !doc.head || doc.getElementById("it-wizard-overview-layout-styles")) {
			return;
		}
		var style = doc.createElement("style");
		style.id = "it-wizard-overview-layout-styles";
		style.textContent =
			"html.it-wizard-overview-root," +
			"html.it-wizard-overview-root body.it-wizard-overview-layout {" +
			"height: 100% !important;" +
			"}" +
			"body.it-wizard-overview-layout {" +
			"display: flex !important;" +
			"flex-direction: column !important;" +
			"height: 100% !important;" +
			"min-height: 100% !important;" +
			"overflow: hidden !important;" +
			"}" +
			"body.it-wizard-overview-layout > div {" +
			"display: flex !important;" +
			"flex-direction: column !important;" +
			"flex: 1 1 auto !important;" +
			"min-height: 0 !important;" +
			"height: 100% !important;" +
			"}" +
			"body.it-wizard-overview-layout header {" +
			"position: relative !important;" +
			"top: auto !important;" +
			"flex-shrink: 0 !important;" +
			"}" +
			"body.it-wizard-overview-layout main," +
			"body.it-wizard-overview-layout [data-itw-overview-main] {" +
			"flex: 1 1 auto !important;" +
			"min-height: 0 !important;" +
			"margin-top: 0 !important;" +
			"display: flex !important;" +
			"overflow: hidden !important;" +
			"max-width: none !important;" +
			"padding: 0 !important;" +
			"}" +
			"body.it-wizard-overview-layout [data-itw-overview-scroll-host] {" +
			"flex: 1 1 auto !important;" +
			"min-height: 0 !important;" +
			"height: 100% !important;" +
			"overflow-y: auto !important;" +
			"overflow-x: hidden !important;" +
			"-webkit-overflow-scrolling: touch;" +
			"scrollbar-gutter: stable;" +
			"}" +
			"body.it-wizard-overview-layout [data-itw-overview-scroll-host]::-webkit-scrollbar {" +
			"width: 10px;" +
			"}" +
			"body.it-wizard-overview-layout [data-itw-overview-scroll-host]::-webkit-scrollbar-thumb {" +
			"background: #c2c6d3;" +
			"border-radius: 9999px;" +
			"}" +
			"body.it-wizard-overview-layout [data-itw-overview-actions] {" +
			"position: relative !important;" +
			"bottom: auto !important;" +
			"flex-shrink: 0 !important;" +
			"width: 100% !important;" +
			"z-index: 10 !important;" +
			"}";
		doc.head.appendChild(style);
	}

	function harmonize_overview_page_layout(doc) {
		if (!doc || !doc.body) {
			return;
		}
		install_overview_layout_styles(doc);
		if (doc.documentElement) {
			doc.documentElement.classList.add("it-wizard-overview-root");
		}
		doc.body.classList.add("it-wizard-overview-layout");
		doc.body.classList.remove("overflow-hidden", "h-screen");
		doc.querySelectorAll("header.fixed, header.sticky").forEach(unfix_layout_chrome);
		doc.querySelectorAll("main").forEach(function (main) {
			main.classList.remove("mt-16", "overflow-hidden");
			main.setAttribute("data-itw-overview-main", "1");
		});
		var scrollHost = doc.querySelector("main .overflow-y-auto");
		if (scrollHost) {
			scrollHost.classList.remove("scroll-hidden");
			scrollHost.setAttribute("data-itw-overview-scroll-host", "1");
		}
		var bottomBar = doc.querySelector("div.fixed.bottom-0");
		if (bottomBar) {
			unfix_layout_chrome(bottomBar);
			bottomBar.classList.remove("bottom-0", "fixed", "w-full");
			bottomBar.setAttribute("data-itw-overview-actions", "1");
		}
		enhance_overview_layout(doc);
	}

	function enhance_overview_layout(doc) {
		var title = doc.querySelector("h1.font-headline-lg");
		if (title) {
			var header = title.closest(".bg-surface-container-lowest");
			if (header) {
				header.setAttribute("data-itw-overview-header", "1");
			}
		}
		doc.querySelectorAll("h2").forEach(function (heading) {
			if ((heading.textContent || "").indexOf("Configuration Steps") >= 0 && heading.nextElementSibling) {
				heading.nextElementSibling.setAttribute("data-itw-overview-step-grid", "1");
			}
		});
		var aside = doc.querySelector("aside.w-80");
		if (aside) {
			aside.setAttribute("data-itw-overview-governance", "1");
		}
		var bottomBar = doc.querySelector("[data-itw-overview-actions]");
		if (!bottomBar) {
			bottomBar = doc.querySelector("div.fixed.bottom-0");
		}
		if (bottomBar) {
			bottomBar.setAttribute("data-itw-overview-actions", "1");
		}
	}

	var LOTTING_STRATEGY_OPTIONS = {
		SINGLE_LOT: "Single Lot (Unsplit)",
		MULTIPLE_LOTS: "Multiple Lots (Phased)",
		BULK: "Bulk Procurement",
	};

	var RESERVATION_OPTIONS = {
		AGPO: "Youth, Women & PWD (AGPO)",
		NONE: "None (Open for All)",
	};

	var TENDER_SECURITY_OPTIONS = {
		TENDER_SECURING_DECLARATION: "Tender Securing Declaration (AGPO)",
		BANK_GUARANTEE: "Bank Guarantee",
		CASH_DEPOSIT: "Cash Deposit",
		NONE: "None Required",
	};

	function install_tender_profile_layout_styles(doc) {
		if (!doc || doc.getElementById("itw-profile-layout-style")) {
			return;
		}
		var style = doc.createElement("style");
		style.id = "itw-profile-layout-style";
		style.textContent =
			"html.it-wizard-profile-root, body.it-wizard-profile-layout {" +
			"height: 100%; margin: 0; overflow: hidden;" +
			"}" +
			"body.it-wizard-profile-layout {" +
			"display: flex; flex-direction: column; min-height: 100vh;" +
			"}" +
			"body.it-wizard-profile-layout > header {" +
			"flex: 0 0 auto; position: static !important;" +
			"}" +
			"body.it-wizard-profile-layout [data-itw-profile-main] {" +
			"flex: 1 1 auto; min-height: 0; overflow-y: auto; margin-top: 0 !important;" +
			"padding-bottom: 0 !important;" +
			"}" +
			"body.it-wizard-profile-layout [data-itw-profile-actions] {" +
			"flex: 0 0 auto; position: static !important;" +
			"}";
		(doc.head || doc.documentElement).appendChild(style);
	}

	function harmonize_tender_profile_page_layout(doc) {
		if (!doc || !doc.body) {
			return;
		}
		install_tender_profile_layout_styles(doc);
		if (doc.documentElement) {
			doc.documentElement.classList.add("it-wizard-profile-root");
		}
		doc.body.classList.add("it-wizard-profile-layout");
		doc.body.classList.remove("overflow-x-hidden");
		doc.querySelectorAll("header.fixed, header.sticky").forEach(unfix_layout_chrome);
		doc.querySelectorAll("main").forEach(function (main) {
			main.classList.remove("mt-16", "pb-24");
			main.setAttribute("data-itw-profile-main", "1");
		});
		var footer = doc.querySelector("footer.fixed");
		if (footer) {
			unfix_layout_chrome(footer);
			footer.classList.remove("fixed", "bottom-0", "left-0", "right-0");
			footer.setAttribute("data-itw-profile-actions", "1");
		}
		enhance_tender_profile_layout(doc);
	}

	function enhance_tender_profile_layout(doc) {
		var context = doc.querySelector("main > section.bg-surface-container");
		if (context) {
			context.setAttribute("data-itw-profile-context", "1");
		}
		doc.querySelectorAll("h3").forEach(function (heading) {
			var text = (heading.textContent || "").trim();
			if (text.indexOf("Main Tender Profile") >= 0) {
				var card = heading.closest(".bg-surface-container-lowest");
				if (card) {
					card.setAttribute("data-itw-profile-form", "1");
				}
			}
		});
		var aside = doc.querySelector("aside");
		if (aside) {
			aside.setAttribute("data-itw-profile-sidebar", "1");
		}
		var footer = doc.querySelector("[data-itw-profile-actions]");
		if (!footer) {
			footer = doc.querySelector("footer");
		}
		if (footer) {
			footer.setAttribute("data-itw-profile-actions", "1");
		}
		tag_profile_field(
			doc,
			"Tender Display Title",
			"input",
			"tender_name",
		);
		tag_profile_field(
			doc,
			"Tender Description",
			"textarea",
			"contract_description",
		);
		tag_profile_field(doc, "Lot Structure", "select", "lotting_strategy");
		tag_profile_field(doc, "Reserved Procurement", "select", "reservation_setting");
		tag_profile_field(doc, "Tender Security", "select", "tender_security_applicability");
		tag_profile_field(doc, "Clarification Contact Email", "input", "clarification_contact_email");
		tag_profile_field(doc, "Submission Language", "input", "language_code");
		tag_profile_field(doc, "Currency", "input", "currency_code");
		strip_profile_fixture_scripts(doc);
		var toggleWrap = doc.querySelector("[data-itw-profile-form] .grid.grid-cols-1.md\\:grid-cols-3");
		if (toggleWrap) {
			var toggles = toggleWrap.querySelectorAll('[role="switch"]');
			var toggleKeys = [
				"alternative_tenders_allowed",
				"jv_allowed",
				"pre_tender_meeting_required",
			];
			toggles.forEach(function (toggle, index) {
				toggle = reset_profile_toggle_node(toggle);
				if (toggleKeys[index]) {
					toggle.setAttribute("data-itw-field", toggleKeys[index]);
					toggle.setAttribute("data-itw-toggle", "1");
				}
			});
		}
	}

	function reset_profile_toggle_node(toggle) {
		if (!toggle || toggle.getAttribute("data-itw-toggle-reset") === "1") {
			return toggle;
		}
		var clone = toggle.cloneNode(true);
		if (toggle.parentNode) {
			toggle.parentNode.replaceChild(clone, toggle);
		}
		clone.setAttribute("data-itw-toggle-reset", "1");
		return clone;
	}

	function strip_profile_fixture_scripts(doc) {
		if (!doc || !doc.body || doc.body.getAttribute("data-itw-profile-scripts-stripped") === "1") {
			return;
		}
		doc.querySelectorAll("body > script").forEach(function (script) {
			if ((script.textContent || "").indexOf('[role="switch"]') >= 0) {
				script.remove();
			}
		});
		doc.body.setAttribute("data-itw-profile-scripts-stripped", "1");
	}

	function tag_profile_field(doc, labelText, selector, fieldKey) {
		doc.querySelectorAll("label").forEach(function (label) {
			if ((label.textContent || "").indexOf(labelText) < 0) {
				return;
			}
			var control = label.parentElement && label.parentElement.querySelector(selector);
			if (control) {
				control.setAttribute("data-itw-field", fieldKey);
			}
		});
	}

	function set_select_option_by_value(select, value, labelMap) {
		if (!select) {
			return;
		}
		var targetLabel = labelMap[value] || value || "";
		var matched = false;
		Array.prototype.forEach.call(select.options || [], function (option) {
			if (
				option.value === value ||
				(option.textContent || "").trim() === targetLabel
			) {
				select.value = option.value;
				matched = true;
			}
		});
		if (!matched && targetLabel) {
			Array.prototype.forEach.call(select.options || [], function (option) {
				if ((option.textContent || "").indexOf(targetLabel) >= 0) {
					select.value = option.value;
				}
			});
		}
	}

	function set_toggle_state(toggle, enabled) {
		if (!toggle) {
			return;
		}
		var dot = toggle.querySelector("span");
		if (!dot) {
			return;
		}
		if (enabled) {
			dot.classList.remove("translate-x-0");
			dot.classList.add("translate-x-5");
			toggle.classList.remove("bg-surface-container-highest");
			toggle.classList.add("bg-secondary");
		} else {
			dot.classList.remove("translate-x-5");
			dot.classList.add("translate-x-0");
			toggle.classList.remove("bg-secondary");
			toggle.classList.add("bg-surface-container-highest");
		}
		toggle.setAttribute("aria-checked", enabled ? "true" : "false");
	}

	function read_toggle_state(toggle) {
		if (!toggle) {
			return false;
		}
		var dot = toggle.querySelector("span");
		return !!(dot && dot.classList.contains("translate-x-5"));
	}

	function read_reservation_setting(select) {
		var label = "";
		if (select && select.selectedIndex >= 0) {
			label = (select.options[select.selectedIndex].textContent || "").trim();
		}
		if (label.indexOf("AGPO") >= 0) {
			return { reservation_applies: 1, reserved_group_code: "AGPO" };
		}
		return { reservation_applies: 0, reserved_group_code: "NONE" };
	}

	function read_lotting_strategy(select) {
		if (!select || select.selectedIndex < 0) {
			return "";
		}
		var label = (select.options[select.selectedIndex].textContent || "").trim();
		if (label.indexOf("Multiple") >= 0) {
			return "MULTIPLE_LOTS";
		}
		if (label.indexOf("Bulk") >= 0) {
			return "BULK";
		}
		return "SINGLE_LOT";
	}

	function read_tender_security(select) {
		if (!select || select.selectedIndex < 0) {
			return "";
		}
		var label = (select.options[select.selectedIndex].textContent || "").trim();
		if (label.indexOf("Bank Guarantee") >= 0) {
			return "BANK_GUARANTEE";
		}
		if (label.indexOf("Cash Deposit") >= 0) {
			return "CASH_DEPOSIT";
		}
		if (label.indexOf("None Required") >= 0) {
			return "NONE";
		}
		if (label.indexOf("Declaration") >= 0) {
			return "TENDER_SECURING_DECLARATION";
		}
		return "";
	}

	function collect_profile_form_values(doc) {
		var values = {};
		doc.querySelectorAll("[data-itw-field]").forEach(function (node) {
			var key = node.getAttribute("data-itw-field");
			if (!key) {
				return;
			}
			if (node.getAttribute("data-itw-toggle") === "1") {
				values[key] = read_toggle_state(node) ? 1 : 0;
				return;
			}
			if (node.tagName === "SELECT") {
				if (key === "reservation_setting") {
					Object.assign(values, read_reservation_setting(node));
					return;
				}
				if (key === "lotting_strategy") {
					values[key] = read_lotting_strategy(node);
					return;
				}
				if (key === "tender_security_applicability") {
					values[key] = read_tender_security(node);
					return;
				}
				values[key] = (node.value || "").trim();
				return;
			}
			values[key] = (node.value || "").trim();
		});
		return values;
	}

	function unwrap_envelope_data(source) {
		var envelope = (source && source.message) || source || {};
		if (envelope.data !== undefined) {
			return envelope.data || {};
		}
		return envelope || {};
	}

	function profile_payload_data(source) {
		return unwrap_envelope_data(source);
	}

	function apply_profile_payload(doc, data) {
		data = data || {};
		hydrate_profile_context(doc, data);
		hydrate_profile_form(doc, data.profile || {});
		hydrate_profile_sidebar(doc, data);
		hydrate_profile_std_panel(doc, data);
	}

	function next_hydration_token(iframe) {
		if (!iframe) {
			return 0;
		}
		var token = (iframe.__itwHydrationToken || 0) + 1;
		iframe.__itwHydrationToken = token;
		return token;
	}

	function hydration_token_active(iframe, token) {
		return !!(iframe && token === iframe.__itwHydrationToken);
	}

	function live_iframe_document(iframe) {
		return iframe && iframe.contentDocument ? iframe.contentDocument : null;
	}

	function hydrate_profile_context(doc, data) {
		var panel = doc.querySelector("[data-itw-profile-context]");
		if (!panel) {
			return;
		}
		var planning = data.planning_package || {};
		var entity = data.procuring_entity || {};
		var method = data.method || {};
		var validation = data.validation || {};
		var cells = panel.querySelectorAll(":scope > div");
		var values = [
			data.configuration_id || "—",
			data.title || "—",
			planning.code || planning.name || "—",
			(entity.name || "").trim() || "—",
			format_method_reference(method),
			data.state_label || "—",
			String(validation.blockers || 0) +
				" " +
				(validation.blockers === 1 ? __("Blocker") : __("Blockers")) +
				" / " +
				String(validation.warnings || 0) +
				" " +
				(validation.warnings === 1 ? __("Warning") : __("Warnings")),
		];
		cells.forEach(function (cell, index) {
			var valueNode = cell.querySelector(".font-bold");
			if (valueNode) {
				valueNode.textContent = values[index] || "—";
			}
		});
	}

	function hydrate_profile_form(doc, profile) {
		profile = profile || {};
		set_control_value(doc, "tender_name", profile.tender_name || "");
		set_control_value(doc, "contract_description", profile.contract_description || "");
		set_select_option_by_value(
			find_profile_control(doc, "lotting_strategy"),
			profile.lotting_strategy || "",
			LOTTING_STRATEGY_OPTIONS,
		);
		var reservationSelect = find_profile_control(doc, "reservation_setting");
		if (profile.reservation_applies) {
			set_select_option_by_value(reservationSelect, "AGPO", RESERVATION_OPTIONS);
		} else {
			set_select_option_by_value(reservationSelect, "NONE", RESERVATION_OPTIONS);
		}
		set_select_option_by_value(
			find_profile_control(doc, "tender_security_applicability"),
			profile.tender_security_applicability || "",
			TENDER_SECURITY_OPTIONS,
		);
		set_control_value(
			doc,
			"clarification_contact_email",
			profile.clarification_contact_email || "",
		);
		set_toggle_state(
			find_profile_control(doc, "alternative_tenders_allowed"),
			!!profile.alternative_tenders_allowed,
		);
		set_toggle_state(find_profile_control(doc, "jv_allowed"), !!profile.jv_allowed);
		set_toggle_state(
			find_profile_control(doc, "pre_tender_meeting_required"),
			!!profile.pre_tender_meeting_required,
		);
		set_control_value(doc, "language_code", profile.language_code === "en" ? "English" : profile.language_code || "English");
		set_control_value(doc, "currency_code", profile.currency_code || "KES");
	}

	function find_profile_control(doc, fieldKey) {
		return doc.querySelector('[data-itw-field="' + fieldKey + '"]');
	}

	function set_control_value(doc, fieldKey, value) {
		var control = find_profile_control(doc, fieldKey);
		if (!control) {
			return;
		}
		if (control.getAttribute("data-itw-toggle") === "1") {
			set_toggle_state(control, !!value);
			return;
		}
		control.value = value;
	}

	function hydrate_profile_sidebar(doc, data) {
		var panel = doc.querySelector("[data-itw-profile-sidebar]");
		if (!panel) {
			return;
		}
		var completion = data.completion || {};
		var validation = data.validation || {};
		var countNode = panel.querySelector(".font-data-mono.font-bold.text-primary");
		if (countNode) {
			countNode.textContent =
				String(completion.completed || 0) + "/" + String(completion.total || 11);
		}
		var progress = panel.querySelector(".bg-primary.h-full");
		if (progress) {
			progress.style.width = String(completion.percent || 0) + "%";
		}
		var missingList = panel.querySelector("ul.space-y-2");
		if (missingList) {
			var missing = completion.missing_fields || [];
			if (!missing.length) {
				missingList.innerHTML =
					'<li class="flex items-center gap-2 text-body-md text-on-surface-variant">' +
					'<span class="w-1.5 h-1.5 rounded-full bg-status-available"></span>' +
					frappe.utils.escape_html(__("All required fields complete")) +
					"</li>";
			} else {
				missingList.innerHTML = missing
					.map(function (label) {
						return (
							'<li class="flex items-center gap-2 text-body-md text-on-surface-variant">' +
							'<span class="w-1.5 h-1.5 rounded-full bg-status-reserved"></span>' +
							frappe.utils.escape_html(label) +
							"</li>"
						);
					})
					.join("");
			}
		}
		panel.querySelectorAll(".flex.items-center.justify-between.p-3").forEach(function (row) {
			var text = (row.textContent || "").trim();
			var valueNode = row.querySelector(".font-bold");
			if (!valueNode) {
				return;
			}
			if (text.indexOf("Blocker") >= 0) {
				valueNode.textContent = String(validation.blockers || 0);
			}
			if (text.indexOf("Warning") >= 0) {
				valueNode.textContent = String(validation.warnings || 0);
			}
		});
	}

	function hydrate_profile_std_panel(doc, data) {
		doc.querySelectorAll("h4").forEach(function (heading) {
			if ((heading.textContent || "").indexOf("Standard Tender Document Binding") < 0) {
				return;
			}
			var panel = heading.closest(".bg-secondary-fixed");
			if (!panel) {
				return;
			}
			panel.querySelectorAll("p").forEach(function (node) {
				var text = node.textContent || "";
				if (text.indexOf("STD Package") >= 0) {
					node.innerHTML =
						"<strong>STD Package:</strong> " +
						frappe.utils.escape_html(
							data.std_template_version_label || data.std_template_version_id || "—",
						);
				}
			});
		});
	}

	function disable_profile_stub_actions(doc) {
		var actionBar = doc.querySelector("[data-itw-profile-actions]");
		if (!actionBar) {
			return;
		}
		actionBar.querySelectorAll("button").forEach(function (btn) {
			var text = (btn.textContent || "").trim();
			if (
				text.indexOf("Run Validation") >= 0 ||
				text.indexOf("Proceed Now") >= 0 ||
				text.indexOf("View Audit") >= 0
			) {
				btn.disabled = true;
				btn.style.opacity = "0.55";
				btn.style.pointerEvents = "none";
				btn.setAttribute("aria-disabled", "true");
			}
		});
	}

	function wire_profile_interactions(doc, ctx) {
		if (!doc || !doc.body) {
			return;
		}
		if (doc.body.getAttribute("data-itw-profile-wired") === "1") {
			return;
		}
		doc.body.setAttribute("data-itw-profile-wired", "1");

		doc.querySelectorAll('[data-itw-toggle="1"]').forEach(function (toggle) {
			toggle.addEventListener("click", function (event) {
				event.preventDefault();
				event.stopImmediatePropagation();
				set_toggle_state(toggle, !read_toggle_state(toggle));
			});
		});

		doc.addEventListener(
			"click",
			function (event) {
				var btn = event.target && event.target.closest ? event.target.closest("button") : null;
				if (!btn) {
					return;
				}
				var text = (btn.textContent || "").trim();
				if (text.indexOf("Save Profile") >= 0) {
					event.preventDefault();
					var values = collect_profile_form_values(doc);
					call_api("save_tender_profile_api", {
						configuration_id: ctx.configuration_id,
						profile_json: JSON.stringify(values),
					})
						.then(function (result) {
							frappe.show_alert({
								message: __("Profile saved"),
								indicator: "green",
							});
							apply_profile_payload(doc, profile_payload_data(result));
						})
						.catch(function (err) {
							frappe.show_alert({
								indicator: "red",
								message: (err && err.message) || __("Unable to save profile."),
							});
						});
					return;
				}
				if (
					text.indexOf("Continue to Tender Data Sheet") >= 0 ||
					text.indexOf("Proceed Now") >= 0
				) {
					event.preventDefault();
					navigate("it-tender-configuration-tds", {
						configuration_id: ctx.configuration_id,
					});
				}
			},
			true,
		);
	}

	function fetch_tender_profile_data(ctx) {
		return call_api("get_tender_profile_api", {
			configuration_id: ctx.configuration_id,
		}).then(function (result) {
			return {
				profile: (result && result.message) || {},
			};
		});
	}

	var LOCAL_SOURCING_OPTIONS = {
		MARGIN_15: "Apply 15% Margin of Preference",
		NONE: "No Local Preference",
	};

	var ISSUER_TYPE_OPTIONS = {
		COMMERCIAL_BANK: "Commercial Bank",
		INSURANCE_COMPANY: "Insurance Company",
		SACCO_SOCIETY: "Sacco Society",
	};

	function install_tds_layout_styles(doc) {
		if (!doc || doc.getElementById("itw-tds-layout-style")) {
			return;
		}
		var style = doc.createElement("style");
		style.id = "itw-tds-layout-style";
		style.textContent =
			"html.it-wizard-tds-root, body.it-wizard-tds-layout {" +
			"height: 100%; margin: 0; overflow: hidden;" +
			"}" +
			"body.it-wizard-tds-layout {" +
			"display: flex; flex-direction: column; min-height: 100vh;" +
			"}" +
			"body.it-wizard-tds-layout > header {" +
			"flex-shrink: 0; position: relative !important; top: auto !important;" +
			"}" +
			"body.it-wizard-tds-layout [data-itw-tds-main] {" +
			"flex: 1 1 auto; overflow-y: auto; min-height: 0;" +
			"max-width: none !important;" +
			"width: 100% !important;" +
			"margin-left: 0 !important;" +
			"margin-right: 0 !important;" +
			"padding: 0 !important;" +
			"}" +
			"body.it-wizard-tds-layout [data-itw-tds-shell] {" +
			"max-width: 1600px;" +
			"margin-left: auto;" +
			"margin-right: auto;" +
			"width: 100%;" +
			"box-sizing: border-box;" +
			"}" +
			"body.it-wizard-tds-layout [data-itw-tds-actions] {" +
			"flex-shrink: 0; position: relative !important; bottom: auto !important;" +
			"}";
		doc.head.appendChild(style);
	}

	function wrap_tds_content_shell(doc) {
		var main = doc.querySelector("[data-itw-tds-main]");
		if (!main || main.getAttribute("data-itw-tds-shell-wrapped") === "1") {
			return;
		}
		var formColumn = main.querySelector(":scope > .flex-grow");
		var aside = main.querySelector(":scope > aside");
		if (!formColumn) {
			return;
		}
		var shell = doc.createElement("div");
		shell.setAttribute("data-itw-tds-shell", "1");
		shell.className =
			"p-6 grid grid-cols-12 gap-section-gap max-w-[1600px] mx-auto w-full box-border";
		formColumn.classList.remove("flex-grow", "pr-gutter", "py-section-gap");
		formColumn.classList.add("col-span-12", "lg:col-span-9");
		if (aside) {
			aside.classList.remove(
				"w-80",
				"flex-shrink-0",
				"border-l",
				"border-border-subtle",
				"pl-gutter",
				"py-section-gap",
				"hidden",
				"lg:block",
			);
			aside.classList.add("col-span-12", "lg:col-span-3", "space-y-6");
		}
		main.classList.remove(
			"max-w-7xl",
			"mx-auto",
			"px-container-padding",
			"pb-24",
			"min-h-[calc(100vh-120px)]",
		);
		shell.appendChild(formColumn);
		if (aside) {
			shell.appendChild(aside);
		}
		main.appendChild(shell);
		main.setAttribute("data-itw-tds-shell-wrapped", "1");
	}

	function harmonize_tds_page_layout(doc) {
		if (!doc || !doc.body) {
			return;
		}
		install_tds_layout_styles(doc);
		if (doc.documentElement) {
			doc.documentElement.classList.add("it-wizard-tds-root");
		}
		doc.body.classList.add("it-wizard-tds-layout");
		doc.querySelectorAll("header.fixed, header.sticky").forEach(unfix_layout_chrome);
		var main = doc.querySelector("main");
		if (main) {
			main.classList.remove("pb-24");
			main.setAttribute("data-itw-tds-main", "1");
		}
		var footer = doc.querySelector("footer");
		if (footer) {
			footer.classList.remove("fixed");
			footer.setAttribute("data-itw-tds-actions", "1");
		}
		wrap_tds_content_shell(doc);
		enhance_tds_layout(doc);
	}

	function enhance_tds_layout(doc) {
		var context = doc.querySelector("header section.bg-surface-container");
		if (context) {
			context.setAttribute("data-itw-tds-context", "1");
		}
		var main = doc.querySelector("[data-itw-tds-main]");
		if (main) {
			var formWrap = main.querySelector(".space-y-6");
			if (formWrap) {
				formWrap.setAttribute("data-itw-tds-form", "1");
			}
		}
		var aside = doc.querySelector("aside");
		if (aside) {
			aside.setAttribute("data-itw-tds-sidebar", "1");
		}
		var footer = doc.querySelector("[data-itw-tds-actions]");
		if (footer) {
			footer.setAttribute("data-itw-tds-actions", "1");
		}
		tag_tds_field(doc, "Procuring Entity Address", "input", "procuring_entity_address");
		tag_tds_field(doc, "Tender Ref", "input", "tender_number");
		tag_tds_field(doc, "Tender Name", "input", "tender_name");
		tag_tds_field(doc, "JV Members Cap", "input", "jv_max_members");
		tag_tds_field(doc, "Local Sourcing Preference", "select", "local_sourcing_preference");
		tag_tds_field(doc, "Submission Deadline", "input", "submission_deadline_at");
		tag_tds_field(doc, "Opening Date/Time", "input", "opening_at");
		tag_tds_field(doc, "Clarification Contact", "input", "clarification_contact_email");
		tag_tds_field(doc, "Envelope Marking", "input", "envelope_marking");
		tag_tds_field(doc, "Security Amount", "input", "tender_security_amount");
		tag_tds_field(doc, "Validity", "input", "tender_validity_days");
		tag_tds_field(doc, "Issuer Type", "select", "security_issuer_type");
		var altSelect = doc.querySelector("[data-itw-tds-form] select");
		if (altSelect && !altSelect.getAttribute("data-itw-field")) {
			altSelect.setAttribute("data-itw-field", "alternative_tenders_allowed");
		}
		var electronicCheckbox = doc.querySelector(
			'[data-itw-tds-form] input[type="checkbox"]:not([disabled])',
		);
		if (electronicCheckbox) {
			electronicCheckbox.setAttribute("data-itw-field", "electronic_tenders_allowed");
		}
		strip_tds_fixture_scripts(doc);
		normalize_tds_fixture_field_styles(doc);
	}

	function strip_tds_fixture_scripts(doc) {
		if (!doc || !doc.body || doc.body.getAttribute("data-itw-tds-scripts-stripped") === "1") {
			return;
		}
		doc.querySelectorAll("body > script").forEach(function (node) {
			node.parentNode.removeChild(node);
		});
		doc.body.setAttribute("data-itw-tds-scripts-stripped", "1");
	}

	function tag_tds_field(doc, labelText, selector, fieldKey) {
		var labels = doc.querySelectorAll("label");
		labels.forEach(function (label) {
			if ((label.textContent || "").indexOf(labelText) < 0) {
				return;
			}
			var container = label.closest(".space-y-1") || label.parentElement;
			if (!container) {
				return;
			}
			var control = container.querySelector(selector);
			if (control) {
				control.setAttribute("data-itw-field", fieldKey);
			}
		});
	}

	function format_datetime_local(value) {
		if (!value) {
			return "";
		}
		return String(value).replace(" ", "T").slice(0, 16);
	}

	function parse_datetime_local(value) {
		if (!value) {
			return "";
		}
		if (value.indexOf("T") >= 0) {
			return value.replace("T", " ") + ":00";
		}
		return value;
	}

	function find_tds_control(doc, fieldKey) {
		return doc.querySelector('[data-itw-field="' + fieldKey + '"]');
	}

	function collect_tds_form_values(doc) {
		var values = {};
		doc.querySelectorAll("[data-itw-field]").forEach(function (node) {
			var key = node.getAttribute("data-itw-field");
			if (!key) {
				return;
			}
			if (node.type === "checkbox") {
				values[key] = node.checked ? 1 : 0;
				return;
			}
			if (node.type === "datetime-local") {
				values[key] = parse_datetime_local(node.value || "");
				return;
			}
			if (node.tagName === "SELECT") {
				var raw = (node.value || "").trim();
				if (key === "alternative_tenders_allowed") {
					values[key] = raw.toLowerCase() === "yes" ? "YES" : "NO";
					return;
				}
				if (key === "local_sourcing_preference") {
					Object.keys(LOCAL_SOURCING_OPTIONS).forEach(function (code) {
						if (LOCAL_SOURCING_OPTIONS[code] === raw) {
							values[key] = code;
						}
					});
					if (!values[key]) {
						values[key] = raw;
					}
					return;
				}
				if (key === "security_issuer_type") {
					Object.keys(ISSUER_TYPE_OPTIONS).forEach(function (code) {
						if (ISSUER_TYPE_OPTIONS[code] === raw) {
							values[key] = code;
						}
					});
					if (!values[key]) {
						values[key] = raw;
					}
					return;
				}
				values[key] = raw;
				return;
			}
			if (key === "jv_max_members" || key === "tender_validity_days") {
				var numeric = (node.value || "").trim();
				values[key] = numeric === "" ? null : parseInt(numeric, 10);
				return;
			}
			if (key === "tender_security_amount") {
				var amount = (node.value || "").replace(/,/g, "").trim();
				values[key] = amount === "" ? null : parseFloat(amount);
				return;
			}
			values[key] = (node.value || "").trim();
		});
		return values;
	}

	function tds_payload_data(source) {
		return unwrap_envelope_data(source);
	}

	function apply_tds_payload(doc, data) {
		data = data || {};
		hydrate_tds_context(doc, data);
		hydrate_tds_form(doc, data.values || {});
		hydrate_tds_sidebar(doc, data);
	}

	function hydrate_tds_context(doc, data) {
		var panel = doc.querySelector("[data-itw-tds-context]");
		if (!panel) {
			return;
		}
		var values = data.values || {};
		var planning = data.planning_package || {};
		var entity = data.procuring_entity || {};
		var method = data.method || {};
		var validation = data.validation || {};
		var cells = panel.querySelectorAll(":scope > div");
		var contextValues = [
			values.tender_number || data.configuration_id || "—",
			data.title || values.tender_name || "—",
			planning.code || planning.name || "—",
			(entity.name || "").trim() || "—",
			format_method_reference(method),
			data.state_label || "—",
			String(validation.blockers || 0) +
				" " +
				(validation.blockers === 1 ? __("Blocker") : __("Blockers")) +
				" / " +
				String(validation.warnings || 0) +
				" " +
				(validation.warnings === 1 ? __("Warning") : __("Warnings")),
		];
		cells.forEach(function (cell, index) {
			var valueNode = cell.querySelector(".font-bold");
			if (valueNode) {
				valueNode.textContent = contextValues[index] || "—";
			}
		});
	}

	function normalize_tds_fixture_field_styles(doc) {
		var standardDatetimeClasses =
			"w-full bg-surface-container-lowest border-outline-variant rounded-md p-2 font-data-mono text-data-mono form-input-focus";
		var submission = find_tds_control(doc, "submission_deadline_at");
		if (submission) {
			submission.className = standardDatetimeClasses;
		}
	}

	function hydrate_tds_form(doc, values) {
		values = values || {};
		set_control_value(doc, "procuring_entity_address", values.procuring_entity_address || "");
		set_control_value(doc, "tender_number", values.tender_number || "");
		set_control_value(doc, "tender_name", values.tender_name || "");
		var altSelect = find_tds_control(doc, "alternative_tenders_allowed");
		if (altSelect) {
			altSelect.value = values.alternative_tenders_allowed === "YES" ? "Yes" : "No";
		}
		set_control_value(doc, "jv_max_members", values.jv_max_members == null ? "" : String(values.jv_max_members));
		set_select_option_by_value(
			find_tds_control(doc, "local_sourcing_preference"),
			values.local_sourcing_preference || "",
			LOCAL_SOURCING_OPTIONS,
		);
		set_control_value(doc, "submission_deadline_at", format_datetime_local(values.submission_deadline_at));
		set_control_value(doc, "opening_at", format_datetime_local(values.opening_at));
		set_control_value(doc, "clarification_contact_email", values.clarification_contact_email || "");
		var electronic = find_tds_control(doc, "electronic_tenders_allowed");
		if (electronic) {
			electronic.checked = !!values.electronic_tenders_allowed;
		}
		set_control_value(doc, "envelope_marking", values.envelope_marking || "ELECTRONIC_ONLY");
		set_control_value(
			doc,
			"tender_security_amount",
			values.tender_security_amount == null ? "" : String(values.tender_security_amount),
		);
		set_control_value(
			doc,
			"tender_validity_days",
			values.tender_validity_days == null ? "" : String(values.tender_validity_days),
		);
		set_select_option_by_value(
			find_tds_control(doc, "security_issuer_type"),
			values.security_issuer_type || "",
			ISSUER_TYPE_OPTIONS,
		);
		normalize_tds_fixture_field_styles(doc);
	}

	function hydrate_tds_sidebar(doc, data) {
		var panel = doc.querySelector("[data-itw-tds-sidebar]");
		if (!panel) {
			return;
		}
		var completion = data.completion || {};
		var completed = completion.completed || 0;
		var total = completion.total || 15;
		var percent = completion.percent || 0;
		var progress = panel.querySelector(".bg-primary.h-2\\.5, .bg-primary.h-2_5, .bg-primary");
		if (progress) {
			progress.style.width = String(percent) + "%";
		}
		panel.querySelectorAll("p").forEach(function (node) {
			if ((node.textContent || "").indexOf("/") >= 0 && (node.textContent || "").indexOf("fields complete") >= 0) {
				node.textContent = completed + "/" + total + " fields complete";
			}
		});
		var list = panel.querySelector("ul");
		if (list) {
			list.innerHTML = "";
			(completion.missing_fields || []).forEach(function (label) {
				var li = doc.createElement("li");
				li.className = "flex items-start gap-2";
				li.innerHTML =
					'<span class="material-symbols-outlined text-[16px] text-error mt-0.5">error</span>' +
					"<span>" +
					frappe.utils.escape_html(label) +
					"</span>";
				list.appendChild(li);
			});
			if (!(completion.missing_fields || []).length) {
				var empty = doc.createElement("li");
				empty.className = "text-on-surface-variant";
				empty.textContent = __("All required fields complete.");
				list.appendChild(empty);
			}
		}
	}

	function disable_tds_stub_actions(doc) {
		var actionBar = doc.querySelector("[data-itw-tds-actions]");
		if (actionBar) {
			actionBar.querySelectorAll("button").forEach(function (btn) {
				var text = (btn.textContent || "").trim();
				if (
					text.indexOf("Run Validation") >= 0 ||
					text.indexOf("Continue to IT Requirements") >= 0 ||
					text.indexOf("View Details") >= 0
				) {
					btn.disabled = true;
					btn.style.opacity = "0.55";
					btn.style.pointerEvents = "none";
					btn.setAttribute("aria-disabled", "true");
				}
			});
		}
		doc.querySelectorAll("[data-itw-tds-sidebar] button, [data-itw-tds-form] button.group").forEach(
			function (btn) {
				btn.disabled = true;
				btn.style.opacity = "0.55";
				btn.style.pointerEvents = "none";
				btn.setAttribute("aria-disabled", "true");
			},
		);
	}

	function wire_tds_interactions(doc, ctx) {
		if (!doc || !doc.body) {
			return;
		}
		if (doc.body.getAttribute("data-itw-tds-wired") === "1") {
			return;
		}
		doc.body.setAttribute("data-itw-tds-wired", "1");

		var electronic = find_tds_control(doc, "electronic_tenders_allowed");
		if (electronic) {
			electronic.addEventListener("click", function (event) {
				event.stopImmediatePropagation();
			});
		}

		doc.addEventListener(
			"click",
			function (event) {
				var btn = event.target && event.target.closest ? event.target.closest("button") : null;
				if (!btn) {
					return;
				}
				var text = (btn.textContent || "").trim();
				if (text.indexOf("Save TDS") >= 0) {
					event.preventDefault();
					var values = collect_tds_form_values(doc);
					call_api("save_tds_api", {
						configuration_id: ctx.configuration_id,
						tds_json: JSON.stringify(values),
					})
						.then(function (result) {
							frappe.show_alert({
								message: __("TDS saved"),
								indicator: "green",
							});
							apply_tds_payload(doc, tds_payload_data(result));
						})
						.catch(function (err) {
							frappe.show_alert({
								indicator: "red",
								message: (err && err.message) || __("Unable to save TDS."),
							});
						});
				}
			},
			true,
		);
	}

	function fetch_tds_data(ctx) {
		return call_api("get_tds_api", {
			configuration_id: ctx.configuration_id,
		}).then(function (result) {
			return {
				tds: (result && result.message) || {},
			};
		});
	}

	var OVERVIEW_RAIL_BORDER = {
		COMPLETE: "border-l-status-available",
		HAS_WARNINGS: "border-l-status-available",
		IN_PROGRESS: "border-l-status-committed",
		HAS_BLOCKERS: "border-l-status-exhausted",
		NOT_STARTED: "border-l-4 border-l-outline-variant",
		LOCKED: "border-l-outline-variant",
	};

	var OVERVIEW_RAIL_ICON = {
		COMPLETE: { name: "check_circle", className: "text-status-available" },
		HAS_WARNINGS: { name: "check_circle", className: "text-status-available" },
		IN_PROGRESS: { name: "pending", className: "text-status-committed" },
		HAS_BLOCKERS: { name: "error", className: "text-status-exhausted" },
		NOT_STARTED: { name: "radio_button_unchecked", className: "text-outline-variant" },
		LOCKED: { name: "lock", className: "text-outline-variant" },
	};

	var OVERVIEW_RAIL_LABELS = {
		NOT_STARTED: __("Not started"),
		IN_PROGRESS: __("In progress"),
		COMPLETE: __("Complete"),
		HAS_WARNINGS: __("Complete with warnings"),
		HAS_BLOCKERS: __("Has blockers"),
		LOCKED: __("Locked"),
	};

	function overview_status_line(step) {
		if (step.rail_status === "LOCKED") {
			return __("Requires previous steps");
		}
		if (step.blockers > 0) {
			return (
				'<div class="flex items-center gap-1 text-xs text-error bg-error-container px-2 py-0.5 rounded-full w-fit mb-4 font-medium">' +
				'<span class="material-symbols-outlined text-[14px]">block</span> ' +
				step.blockers +
				" " +
				__("Blocker") +
				(step.blockers === 1 ? "" : "s") +
				"</div>"
			);
		}
		if (step.warnings > 0) {
			return (
				'<div class="flex items-center gap-1 text-xs text-status-reserved bg-status-reserved/10 px-2 py-0.5 rounded-full w-fit mb-4">' +
				'<span class="material-symbols-outlined text-[14px]">warning</span> ' +
				step.warnings +
				" " +
				__("Warning") +
				(step.warnings === 1 ? "" : "s") +
				"</div>"
			);
		}
		return (
			'<div class="font-body-md text-xs text-outline mb-4">' +
			__("0 Blockers, 0 Warnings") +
			"</div>"
		);
	}

	function build_overview_step_card_html(step) {
		var rail = step.rail_status || "NOT_STARTED";
		var icon = OVERVIEW_RAIL_ICON[rail] || OVERVIEW_RAIL_ICON.NOT_STARTED;
		var borderClass = OVERVIEW_RAIL_BORDER[rail] || OVERVIEW_RAIL_BORDER.NOT_STARTED;
		var locked = rail === "LOCKED";
		var currentRing = step.is_current && !locked ? " ring-2 ring-status-committed ring-offset-2" : "";
		var titleClass = locked ? "text-outline" : "text-on-surface";
		var cardClass =
			"bg-surface-container-lowest rounded-lg border border-border-subtle p-4 flex flex-col h-full border-l-4 " +
			borderClass +
			currentRing;
		if (locked) {
			cardClass += " opacity-75 grayscale cursor-not-allowed";
		} else {
			cardClass += " hover:shadow-md transition-shadow cursor-pointer";
		}
		var actionClass =
			rail === "HAS_BLOCKERS"
				? "text-error font-label-caps text-label-caps hover:underline uppercase"
				: rail === "IN_PROGRESS" || step.is_current
					? "bg-primary text-on-primary px-3 py-1 rounded font-label-caps text-label-caps hover:bg-primary-container transition-colors uppercase"
					: locked
						? "text-outline font-label-caps text-[10px]"
						: "text-primary font-label-caps text-label-caps hover:underline uppercase";
		var statusSubtitle =
			locked
				? '<div class="font-body-md text-xs text-outline mb-4">' + __("Requires previous steps") + "</div>"
				: '<div class="font-data-mono text-xs text-on-surface-variant mb-2 bg-surface-container-low inline-block px-2 py-1 rounded w-fit">' +
					frappe.utils.escape_html(OVERVIEW_RAIL_LABELS[rail] || rail) +
					"</div>" +
					overview_status_line(step);
		var footerOwner =
			locked
				? '<span class="font-label-caps text-[10px] text-outline">' +
					frappe.utils.escape_html(step.owner_role_label || "") +
					"</span>"
				: '<div class="flex items-center gap-1.5"><span class="font-label-caps text-[10px] text-outline">' +
					frappe.utils.escape_html(step.owner_role_label || "") +
					"</span></div>";
		var actionBtn = locked
			? ""
			: '<button type="button" class="' +
				actionClass +
				'" data-itw-step-action="1" data-itw-step-code="' +
				frappe.utils.escape_html(step.step_code || "") +
				'">' +
				frappe.utils.escape_html(step.action_label || __("Start")) +
				"</button>";
		return (
			'<div class="' +
			cardClass +
			'" data-itw-step-card="1" data-itw-step-code="' +
			frappe.utils.escape_html(step.step_code || "") +
			'" data-itw-step-current="' +
			(step.is_current ? "1" : "0") +
			'">' +
			'<div class="flex justify-between items-start mb-3">' +
			'<h3 class="font-headline-sm text-[16px] font-semibold ' +
			titleClass +
			'">' +
			frappe.utils.escape_html(step.step_title || "") +
			'</h3><span class="material-symbols-outlined ' +
			icon.className +
			'">' +
			icon.name +
			"</span></div>" +
			statusSubtitle +
			'<div class="mt-auto pt-4 flex justify-between items-center border-t border-border-subtle">' +
			footerOwner +
			actionBtn +
			"</div></div>"
		);
	}

	function hydrate_overview_header(doc, data) {
		var header = doc.querySelector("[data-itw-overview-header]");
		if (!header || !data) {
			return;
		}
		var title = header.querySelector("h1");
		if (title) {
			title.textContent = data.title || "";
		}
		var codeRow = header.querySelector(".font-data-mono.text-data-mono");
		if (codeRow) {
			codeRow.innerHTML =
				'<span class="bg-surface-container px-2 py-1 rounded text-primary-container font-semibold">' +
				frappe.utils.escape_html(data.configuration_id || "") +
				"</span>";
		}
		header.querySelectorAll(".inline-flex.items-center.gap-1\\.5.px-3.py-1.rounded-full").forEach(function (pill) {
			var text = (pill.textContent || "").trim();
			if (text.indexOf("Blocker") >= 0) {
				var blockers = (data.validation && data.validation.blockers) || 0;
				pill.style.display = blockers > 0 ? "" : "none";
				if (blockers > 0) {
					pill.innerHTML =
						'<span class="material-symbols-outlined text-sm">block</span> ' +
						blockers +
						" " +
						(blockers === 1 ? __("Blocker") : __("Blockers"));
				}
			}
			if (text.indexOf("Warning") >= 0) {
				var warnings = (data.validation && data.validation.warnings) || 0;
				pill.style.display = warnings > 0 ? "" : "none";
				if (warnings > 0) {
					pill.innerHTML =
						'<span class="material-symbols-outlined text-sm">warning</span> ' +
						warnings +
						" " +
						(warnings === 1 ? __("Warning") : __("Warnings"));
				}
			}
		});
		var statePill = header.querySelector(".rounded-full.bg-tertiary-fixed");
		if (statePill) {
			statePill.innerHTML =
				'<span class="material-symbols-outlined text-sm">edit_note</span> ' +
				frappe.utils.escape_html(data.state_label || data.state || "");
		}
		var progressBar = header.querySelector(".progress-bar-fill");
		if (progressBar) {
			progressBar.style.width = String(data.completion_percent || 0) + "%";
		}
		var progressLabel = header.querySelector(".font-data-mono.text-status-committed.font-bold");
		if (progressLabel) {
			progressLabel.textContent = String(data.completion_percent || 0) + "%";
		}
		var metaCells = header.querySelectorAll(".grid.grid-cols-4 > div");
		if (metaCells.length >= 4) {
			var planning = data.planning_package || {};
			var entity = data.procuring_entity || {};
			var method = data.method || {};
			var valueNodes = [
				planning.code || planning.name || "—",
				(entity.name || "").trim() || "—",
				format_method_reference(method),
				data.std_template_version_label || data.std_template_version_id || "—",
			];
			metaCells.forEach(function (cell, index) {
				var valueNode = cell.querySelector(".font-data-mono, .font-body-md.font-medium, .font-body-md.text-on-surface.font-medium");
				if (valueNode) {
					valueNode.textContent = valueNodes[index] || "—";
				}
			});
		}
	}

	function hydrate_overview_step_grid(doc, steps) {
		var grid = doc.querySelector("[data-itw-overview-step-grid]");
		if (!grid) {
			return;
		}
		if (!steps || !steps.length) {
			grid.innerHTML =
				'<div class="col-span-3 text-center text-on-surface-variant py-8">' +
				__("No configuration steps found.") +
				"</div>";
			return;
		}
		grid.innerHTML = steps.map(build_overview_step_card_html).join("");
	}

	function hydrate_overview_governance(doc, data) {
		var panel = doc.querySelector("[data-itw-overview-governance]");
		if (!panel || !data) {
			return;
		}
		var nextAction = data.next_required_action || {};
		var nextTitle = panel.querySelector(".bg-primary\\/5 .font-body-md.font-semibold");
		if (nextTitle) {
			nextTitle.textContent = nextAction.step_title
				? __("Complete {0}", [nextAction.step_title])
				: __("Review configuration progress");
		}
		var ownerName = panel.querySelector(".border-t + div .font-body-md.font-medium, .border-t.border-border-subtle.pt-4 .font-body-md.font-medium");
		panel.querySelectorAll(".border-t.border-border-subtle.pt-4").forEach(function (section) {
			var heading = section.querySelector("h4");
			if (!heading) {
				return;
			}
			var label = (heading.textContent || "").trim();
			if (label.indexOf("Current Ownership") >= 0) {
				var nameNode = section.querySelector(".font-body-md.font-medium.text-on-surface");
				var roleNode = section.querySelector(".font-data-mono.text-xs");
				if (nameNode && data.owner) {
					nameNode.textContent = data.owner.name || "—";
				}
				if (roleNode && data.owner) {
					roleNode.textContent = data.owner.role_label || "—";
				}
			}
			if (label.indexOf("Compliance Context") >= 0) {
				section.querySelectorAll("li").forEach(function (row) {
					var key = (row.querySelector("span") && row.querySelector("span").textContent) || "";
					if (key.indexOf("Review Track") >= 0) {
						var value = row.querySelector(".font-medium");
						if (value && data.governance) {
							value.textContent = data.governance.review_track || "—";
						}
					}
					if (key.indexOf("STD Binding") >= 0) {
						var binding = row.querySelector(".font-data-mono");
						if (binding && data.governance) {
							binding.textContent = data.governance.std_binding_code || "—";
						}
					}
					if (key.indexOf("Package Hash") >= 0) {
						var hashNode = row.querySelector(".font-data-mono.text-xs");
						if (hashNode && data.governance) {
							hashNode.textContent = data.governance.package_hash || "—";
						}
					}
				});
			}
			if (label.indexOf("Validation Status") >= 0) {
				section.querySelectorAll(".flex.items-center.justify-between.p-2.rounded").forEach(function (row) {
					var text = (row.textContent || "").trim();
					if (text.indexOf("Blocker") >= 0) {
						var blockers = (data.validation && data.validation.blockers) || 0;
						row.style.display = blockers > 0 ? "" : "none";
						if (blockers > 0) {
							row.querySelector(".font-medium").textContent =
								blockers + " " + (blockers === 1 ? __("Blocker") : __("Blockers"));
						}
					}
					if (text.indexOf("Warning") >= 0) {
						var warnings = (data.validation && data.validation.warnings) || 0;
						row.style.display = warnings > 0 ? "" : "none";
						if (warnings > 0) {
							row.querySelector(".font-medium").textContent =
								warnings + " " + (warnings === 1 ? __("Warning") : __("Warnings"));
						}
					}
				});
				var lastRun = section.querySelector(".font-data-mono.text-\\[11px\\]");
				if (lastRun && data.validation) {
					lastRun.textContent = data.validation.last_run_at
						? __("Last Run: {0}", [data.validation.last_run_at])
						: "";
				}
			}
			if (label.indexOf("Audit Snapshot") >= 0) {
				var countNode = section.querySelector(".font-data-mono.font-medium");
				if (countNode && data.governance) {
					countNode.textContent = String(data.governance.audit_event_count || 0);
				}
				var lastEvent = section.querySelector(".font-data-mono.text-\\[10px\\]");
				if (lastEvent && data.governance && data.governance.last_audit_event_type) {
					lastEvent.textContent = __("Last event: {0}", [data.governance.last_audit_event_type]);
				}
			}
		});
	}

	function disable_overview_stub_actions(doc) {
		var actionBar = doc.querySelector("[data-itw-overview-actions]");
		if (!actionBar) {
			return;
		}
		actionBar.querySelectorAll("button").forEach(function (btn) {
			var text = (btn.textContent || "").trim();
			if (
				text.indexOf("Save Draft") >= 0 ||
				text.indexOf("Preview Tender") >= 0 ||
				text.indexOf("Run Validation") >= 0 ||
				text.indexOf("Submit for Review") >= 0 ||
				text.indexOf("View Audit Trail") >= 0
			) {
				btn.disabled = true;
				btn.style.opacity = "0.55";
				btn.style.pointerEvents = "none";
				btn.setAttribute("aria-disabled", "true");
			}
		});
	}

	function wire_overview_interactions(doc, ctx) {
		if (!doc || !doc.body) {
			return;
		}
		if (doc.body.getAttribute("data-itw-overview-wired") === "1") {
			return;
		}
		doc.body.setAttribute("data-itw-overview-wired", "1");

		doc.addEventListener(
			"click",
			function (event) {
				var stepBtn = event.target.closest("[data-itw-step-action]");
				var stepCard = event.target.closest("[data-itw-step-card]");
				var target = stepBtn || stepCard;
				if (!target || !stepCard) {
					return;
				}
				if (stepCard.classList.contains("cursor-not-allowed")) {
					return;
				}
				var stepCode = stepCard.getAttribute("data-itw-step-code") || "";
				var route = STEP_ROUTE_MAP[stepCode];
				if (!route) {
					frappe.show_alert({
						message: __("Configuration step screens are not wired yet (ITW-04+)."),
						indicator: "blue",
					});
					return;
				}
				event.preventDefault();
				navigate(route, { configuration_id: ctx.configuration_id });
			},
			true,
		);
	}

	function fetch_overview_data(ctx) {
		return call_api("get_configuration_summary_api", {
			configuration_id: ctx.configuration_id,
		}).then(function (result) {
			return {
				overview: (result && result.message) || {},
			};
		});
	}

	function fetch_screen_data(screen, ctx, filters) {
		if (screen === "std_config_overview") {
			return fetch_overview_data(ctx);
		}
		if (screen === "tender_profile") {
			return fetch_tender_profile_data(ctx);
		}
		if (screen === "tds") {
			return fetch_tds_data(ctx);
		}
		var args = {
			page: filters.page || 1,
			page_size: filters.page_size || 25,
			q: filters.q || undefined,
			state: filters.state || undefined,
			states: filters.states || undefined,
			procurement_entity_id: filters.procurement_entity_id || ctx.procurement_entity_id || undefined,
			procurement_method_code: filters.procurement_method_code || undefined,
			overdue_only: filters.overdue_only ? 1 : undefined,
		};
		return Promise.all([
			call_api("get_dashboard_summary", {
				procurement_entity_id: ctx.procurement_entity_id || undefined,
			}),
			call_api("list_configurations_api", args),
		]).then(function (results) {
			return {
				summary: (results[0] && results[0].message) || {},
				list: (results[1] && results[1].message) || {},
			};
		});
	}

	var HYDRATORS = {
		dashboard: function (doc, payload, ctx, filters) {
			var summary = (payload.summary && payload.summary.data) || {};
			var list = (payload.list && payload.list.data) || {};
			var items = list.items || [];
			hydrate_filter_selects(doc, summary.filter_options || {});
			hydrate_dashboard_kpis(doc, summary.kpis || {}, summary.today_deltas || {});
			hydrate_dashboard_table(doc, items, ctx.configuration_id || "");
			hydrate_dashboard_pager(doc, list.page || 1, list.page_size || 25, list.total || 0);
			disable_stub_actions(doc);
			wire_dashboard_interactions(doc, ctx, filters || { page: 1, page_size: 25 });
		},
		std_config_overview: function (doc, payload, ctx) {
			var data = (payload.overview && payload.overview.data) || {};
			hydrate_overview_header(doc, data);
			hydrate_overview_step_grid(doc, data.wizard_steps || []);
			hydrate_overview_governance(doc, data);
			disable_overview_stub_actions(doc);
			wire_overview_interactions(doc, ctx);
		},
		tender_profile: function (doc, payload, ctx) {
			apply_profile_payload(doc, profile_payload_data(payload.profile || {}));
			disable_profile_stub_actions(doc);
			wire_profile_interactions(doc, ctx);
		},
		tds: function (doc, payload, ctx) {
			apply_tds_payload(doc, tds_payload_data(payload.tds || {}));
			disable_tds_stub_actions(doc);
			wire_tds_interactions(doc, ctx);
		},
	};

	function open_create_dialog(ctx, on_success) {
		var fields = [
			{
				fieldname: "title",
				label: __("Configuration title"),
				fieldtype: "Data",
				reqd: 1,
				default: ctx.tender_id ? __("IT Tender Configuration for {0}", [ctx.tender_id]) : "",
			},
			{
				fieldname: "std_template_version_id",
				label: __("STD template version"),
				fieldtype: "Data",
				reqd: 1,
				default: ctx.std_version_id || "",
			},
			{
				fieldname: "procuring_entity_id",
				label: __("Procuring entity"),
				fieldtype: "Data",
			},
		];
		var dialog = new frappe.ui.Dialog({
			title: __("Create Tender Configuration"),
			fields: fields,
			primary_action_label: __("Create"),
			primary_action: function () {
				var values = dialog.get_values();
				if (!values) {
					return;
				}
				dialog.hide();
				frappe.call({
					method: API + ".create_configuration_api",
					args: Object.assign({}, values, {
						tender_id: ctx.tender_id || undefined,
						procurement_plan_item_id: ctx.plan_item_id || undefined,
					}),
					callback: function (r) {
						if (r.exc) {
							return;
						}
						frappe.show_alert({
							message: __("Configuration created"),
							indicator: "green",
						});
						if (typeof on_success === "function") {
							on_success(r.message || {});
						}
					},
				});
			},
		});
		dialog.show();
	}

	function wire_dashboard_interactions(doc, ctx, filters) {
		if (!doc || !doc.body) {
			return;
		}
		if (doc.body.getAttribute("data-itw-wired") === "1") {
			return;
		}
		doc.body.setAttribute("data-itw-wired", "1");

		function reload(extra) {
			var base = get_active_filters(doc) || filters || { page: 1, page_size: 25 };
			var next = normalize_filter_args(
				Object.assign({}, base, read_dashboard_filters(doc), extra || {}),
			);
			set_active_filters(doc, next);
			fetch_screen_data("dashboard", ctx, next).then(function (payload) {
				HYDRATORS.dashboard(doc, payload, ctx, next);
			});
		}

		var searchInput = doc.querySelector("[data-itw-search]");
		if (!searchInput) {
			searchInput = doc.querySelector('input[placeholder*="Search Tender"]');
		}
		if (searchInput) {
			var timer = null;
			searchInput.addEventListener("input", function () {
				clearTimeout(timer);
				timer = setTimeout(function () {
					reload({ page: 1 });
				}, 300);
			});
		}

		var filterBar = doc.querySelector("[data-itw-filter-bar]");
		if (filterBar) {
			filterBar.querySelectorAll("select[data-itw-filter]").forEach(function (sel) {
				sel.addEventListener("change", function () {
					if (sel.getAttribute("data-itw-filter") === "status") {
						reset_drawer_status_filters(doc);
					}
					reload({ page: 1 });
				});
			});
		}

		doc.querySelectorAll("button").forEach(function (btn) {
			var text = (btn.textContent || "").trim();
			if (text.indexOf("Create Tender Configuration") >= 0) {
				btn.addEventListener("click", function (event) {
					event.preventDefault();
					open_create_dialog(ctx, function () {
						reload({ page: 1 });
					});
				});
			}
		});

		wire_dashboard_pagination(doc, ctx, filters, reload);
		wire_filter_drawer(doc, reload);

		doc.addEventListener(
			"click",
			function (event) {
				var target = event.target.closest("[data-itw-action='continue']");
				if (!target) {
					return;
				}
				event.preventDefault();
				var row = target.closest("tr[data-configuration-id]");
				var configuration_id = row ? row.getAttribute("data-configuration-id") : "";
				if (!configuration_id) {
					return;
				}
				navigate("it-tender-configuration-overview", { configuration_id: configuration_id });
			},
			true,
		);
	}

	function hydrate_iframe(screen, iframe, ctx, page_title) {
		if (!iframe) {
			return;
		}
		var doc = live_iframe_document(iframe);
		if (!doc || !doc.body) {
			return;
		}
		var hydrationToken = next_hydration_token(iframe);
		install_hydration_gate(doc);
		if (
			(screen === "std_config_overview" || screen === "tender_profile" || screen === "tds") &&
			!(ctx.configuration_id || "").trim()
		) {
			mark_hydration_error(doc);
			if (!configRedirectInFlight) {
				configRedirectInFlight = true;
				frappe.show_alert({
					message: __("Open a tender configuration from the dashboard to view this screen."),
					indicator: "orange",
				});
			}
			navigate("it-tender-configuration-dashboard");
			return;
		}
		normalize_page_layout(doc, screen);
		var filters = { page: 1, page_size: 25 };
		fetch_screen_data(screen, ctx, filters)
			.then(function (payload) {
				if (!hydration_token_active(iframe, hydrationToken)) {
					return;
				}
				doc = live_iframe_document(iframe);
				if (!doc || !doc.body) {
					return;
				}
				if (HYDRATORS[screen]) {
					HYDRATORS[screen](doc, payload, ctx, filters);
				}
				mark_hydrated(doc);
				if (screen !== "dashboard") {
					return;
				}
				var handoffKey =
					(ctx.tender_id || "") + "|" + (ctx.std_version_id || "") + "|" + (ctx.plan_item_id || "");
				if (ctx.tender_id && ctx.std_version_id && !planningHandoffKeys[handoffKey]) {
					planningHandoffKeys[handoffKey] = true;
					open_create_dialog(ctx, function () {
						fetch_screen_data("dashboard", ctx, filters).then(function (fresh) {
							if (!hydration_token_active(iframe, hydrationToken)) {
								return;
							}
							var liveDoc = live_iframe_document(iframe);
							if (!liveDoc || !liveDoc.body) {
								return;
							}
							HYDRATORS.dashboard(liveDoc, fresh, ctx, filters);
						});
					});
				}
			})
			.catch(function (err) {
				if (!hydration_token_active(iframe, hydrationToken)) {
					return;
				}
				doc = live_iframe_document(iframe);
				if (!doc || !doc.body) {
					return;
				}
				mark_hydration_error(doc);
				frappe.show_alert({
					indicator: "red",
					message:
						(err && err.message) ||
						(screen === "std_config_overview"
							? __("Unable to load configuration overview.")
							: screen === "tender_profile"
								? __("Unable to load tender profile.")
								: screen === "tds"
									? __("Unable to load tender data sheet.")
									: __("Unable to load dashboard data.")),
				});
			});
	}

	function mount_page(wrapper, config) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: config.title,
			single_column: true,
		});
		preserve_procurement_sidebar();
		document.body.classList.add(config.shell_class);

		var root = page.main.get(0);
		if (!root) {
			return;
		}
		root.className = config.root_class;
		root.setAttribute("data-testid", config.testid + "-root");
		root.innerHTML =
			'<section class="' +
			config.shell_class +
			'" data-testid="' +
			config.testid +
			'-shell">' +
			'<iframe class="' +
			config.iframe_class +
			'" data-testid="' +
			config.testid +
			'-iframe" src="' +
			config.asset +
			'" title="' +
			frappe.utils.escape_html(config.title) +
			'"></iframe></section>';

		var iframe = root.querySelector("iframe");
		var hydrationRunId = 0;
		function run_hydration() {
			hydrationRunId += 1;
			var runId = hydrationRunId;
			setTimeout(function () {
				if (runId !== hydrationRunId) {
					return;
				}
				var fresh_ctx = read_route_context();
				hydrate_iframe(config.screen, iframe, fresh_ctx, config.title);
			}, 0);
		}
		prepare_iframe_frame(iframe);
		iframe.addEventListener("load", run_hydration);
		try {
			if (iframe.contentDocument && iframe.contentDocument.readyState === "complete") {
				run_hydration();
			}
		} catch (err) {
			// load event will hydrate when ready
		}

		frappe.pages[config.page].on_page_show = function () {
			document.body.classList.add(config.shell_class);
			preserve_procurement_sidebar();
			if (CONFIGURATION_CONTEXT_ROUTES[config.page]) {
				var ctx = read_route_context();
				if (ctx.configuration_id) {
					sync_configuration_id_to_url(ctx.configuration_id);
				}
			}
			run_hydration();
		};
		frappe.pages[config.page].on_page_hide = function () {
			document.body.classList.remove(config.shell_class);
		};
	}

	kentender.it_wizard.mount_page = mount_page;
	kentender.it_wizard.navigate = navigate;
	kentender.it_wizard.hydrate_iframe = hydrate_iframe;
	kentender.it_wizard.read_route_context = read_route_context;
	kentender.it_wizard.set_route_context = set_route_context;
	kentender.it_wizard.hydrate_dashboard_kpis = hydrate_dashboard_kpis;
	kentender.it_wizard.hydrate_dashboard_table = hydrate_dashboard_table;
	kentender.it_wizard.hydrate_dashboard_pager = hydrate_dashboard_pager;
	kentender.it_wizard.hydrate_overview_header = hydrate_overview_header;
	kentender.it_wizard.hydrate_overview_step_grid = hydrate_overview_step_grid;
	kentender.it_wizard.hydrate_overview_governance = hydrate_overview_governance;
	kentender.it_wizard.enhance_overview_layout = enhance_overview_layout;
	kentender.it_wizard.harmonize_overview_page_layout = harmonize_overview_page_layout;
	kentender.it_wizard.harmonize_tender_profile_page_layout = harmonize_tender_profile_page_layout;
	kentender.it_wizard.hydrate_profile_context = hydrate_profile_context;
	kentender.it_wizard.hydrate_profile_form = hydrate_profile_form;
	kentender.it_wizard.hydrate_profile_sidebar = hydrate_profile_sidebar;
	kentender.it_wizard.unwrap_envelope_data = unwrap_envelope_data;
	kentender.it_wizard.harmonize_tds_page_layout = harmonize_tds_page_layout;
	kentender.it_wizard.hydrate_tds_context = hydrate_tds_context;
	kentender.it_wizard.hydrate_tds_form = hydrate_tds_form;
	kentender.it_wizard.hydrate_tds_sidebar = hydrate_tds_sidebar;
	kentender.it_wizard.strip_tds_fixture_scripts = strip_tds_fixture_scripts;
	kentender.it_wizard.enhance_dashboard_table_layout = enhance_dashboard_table_layout;
	kentender.it_wizard.enhance_dashboard_kpi_layout = enhance_dashboard_kpi_layout;
	kentender.it_wizard.enhance_dashboard_filter_layout = enhance_dashboard_filter_layout;
	kentender.it_wizard.enhance_dashboard_filter_drawer = enhance_dashboard_filter_drawer;
	kentender.it_wizard.read_dashboard_filters = read_dashboard_filters;
	kentender.it_wizard.hydrate_filter_selects = hydrate_filter_selects;
	kentender.it_wizard.format_entity_reference = format_entity_reference;
	kentender.it_wizard.format_method_reference = format_method_reference;
	kentender.it_wizard.render_pager_page_buttons = render_pager_page_buttons;
	kentender.it_wizard.HYDRATORS = HYDRATORS;
	kentender.it_wizard.preserve_procurement_sidebar = preserve_procurement_sidebar;
})();
