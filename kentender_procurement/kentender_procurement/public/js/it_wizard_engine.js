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

	function normalize_page_layout(doc) {
		if (!doc || !doc.body) {
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
			"Active now: Method and status checkboxes. Category, STD package, review track, and owner filters require ITW-02 backend fields and stay disabled until then.",
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

	function fetch_screen_data(ctx, filters) {
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
			fetch_screen_data(ctx, next).then(function (payload) {
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
				var root = window.parent && window.parent.frappe ? window.parent : window;
				root.frappe.route_options = { configuration_id: configuration_id };
				root.frappe.show_alert({
					message: __("IT Wizard step shell is not wired yet (ITW-02+)."),
					indicator: "blue",
				});
			},
			true,
		);
	}

	function hydrate_iframe(screen, iframe, ctx, page_title) {
		var doc = iframe.contentDocument;
		if (!doc) {
			return;
		}
		install_hydration_gate(doc);
		normalize_page_layout(doc);
		var filters = { page: 1, page_size: 25 };
		fetch_screen_data(ctx, filters)
			.then(function (payload) {
				if (HYDRATORS[screen]) {
					HYDRATORS[screen](doc, payload, ctx, filters);
				}
				mark_hydrated(doc);
				var handoffKey =
					(ctx.tender_id || "") + "|" + (ctx.std_version_id || "") + "|" + (ctx.plan_item_id || "");
				if (ctx.tender_id && ctx.std_version_id && !planningHandoffKeys[handoffKey]) {
					planningHandoffKeys[handoffKey] = true;
					open_create_dialog(ctx, function () {
						fetch_screen_data(ctx, filters).then(function (fresh) {
							HYDRATORS.dashboard(doc, fresh, ctx, filters);
						});
					});
				}
			})
			.catch(function (err) {
				mark_hydration_error(doc);
				frappe.show_alert({
					indicator: "red",
					message: (err && err.message) || __("Unable to load dashboard data."),
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
		var ctx = read_route_context();
		prepare_iframe_frame(iframe);
		function run_hydration() {
			hydrate_iframe(config.screen, iframe, ctx, config.title);
		}
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
			var fresh_ctx = read_route_context();
			hydrate_iframe(config.screen, iframe, fresh_ctx, config.title);
		};
		frappe.pages[config.page].on_page_hide = function () {
			document.body.classList.remove(config.shell_class);
		};
	}

	kentender.it_wizard.mount_page = mount_page;
	kentender.it_wizard.hydrate_iframe = hydrate_iframe;
	kentender.it_wizard.read_route_context = read_route_context;
	kentender.it_wizard.set_route_context = set_route_context;
	kentender.it_wizard.hydrate_dashboard_kpis = hydrate_dashboard_kpis;
	kentender.it_wizard.hydrate_dashboard_table = hydrate_dashboard_table;
	kentender.it_wizard.hydrate_dashboard_pager = hydrate_dashboard_pager;
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
