(function () {
	"use strict";

	frappe.provide("kentender.std_prod");

	var API = "kentender_procurement.std_engine.api.read";
	var DEFAULT_FAMILY = "KE-PPRA-IT";
	var DEFAULT_PACKAGE = "KE-PPRA-IT-2022-04";

	function call_read(method, args) {
		return frappe.call({
			method: API + "." + method,
			type: "GET",
			args: args || {},
		});
	}

	var MODULE_ROW_ROUTES = {
		"Sections & Containers": "std-section-clauses",
		"Standard Clauses": "std-section-clauses",
		"Parameters & Rules": "std-parameter-dictionary",
		"Requirements Schema": "std-requirement-schema-manager",
		"Price Schedule Schema": "std-price-schedule-schema",
	};

	var SCHEMA_CROSS_LINKS = {
		"Parameter Dictionary": "std-parameter-dictionary",
		"Rule Dictionary": "std-rule-dictionary",
		"Form Schema Manager": "std-form-schema-manager",
		"Evaluation Schema": "std-evaluation-schema",
		"Render Blocks": "std-render-blocks",
	};

	// Frappe router registers DocType slugs before custom Pages; these collide.
	var PROCUREMENT_SIDEBAR_KEY = "Procurement";

	function preserve_procurement_sidebar() {
		if (frappe.app && frappe.app.sidebar && typeof frappe.app.sidebar.setup === "function") {
			frappe.app.sidebar.setup(PROCUREMENT_SIDEBAR_KEY);
		}
	}

	var DOCTYPE_ROUTE_CONFLICT_PAGES = [
		"std-price-schedule-schema",
		"std-evaluation-schema",
	];

	function claim_page_routes_over_doctype_conflicts() {
		if (!frappe.router || !frappe.router.routes) {
			return;
		}
		DOCTYPE_ROUTE_CONFLICT_PAGES.forEach(function (slug) {
			if (frappe.router.routes[slug]) {
				delete frappe.router.routes[slug];
			}
		});
	}

	function install_route_conflict_guard() {
		if (!frappe.router || frappe.router.__std_prod_route_guard) {
			return;
		}
		frappe.router.__std_prod_route_guard = true;
		var originalSetup = frappe.router.setup.bind(frappe.router);
		frappe.router.setup = function () {
			originalSetup();
			claim_page_routes_over_doctype_conflicts();
		};
		var originalParse = frappe.router.parse.bind(frappe.router);
		frappe.router.parse = async function (route) {
			claim_page_routes_over_doctype_conflicts();
			return originalParse(route);
		};
		claim_page_routes_over_doctype_conflicts();
	}

	function get_context() {
		var root = window.parent && window.parent.frappe ? window.parent : window;
		var opts = root.frappe.route_options || {};
		return {
			family_code: opts.family_code || DEFAULT_FAMILY,
			package_id: opts.package_id || DEFAULT_PACKAGE,
			clause_key: opts.clause_key || "",
			parameter_key: opts.parameter_key || "",
			rule_key: opts.rule_key || "",
			form_key: opts.form_key || "",
			import_run_key: opts.import_run_key || "",
		};
	}

	function set_context(ctx) {
		var root = window.parent && window.parent.frappe ? window.parent : window;
		root.frappe.route_options = Object.assign({}, root.frappe.route_options || {}, ctx || {});
	}

	function navigate(route, ctx) {
		var root = window.parent && window.parent.frappe ? window.parent : window;
		if (ctx) {
			set_context(ctx);
		}
		root.frappe.set_route(route);
	}

	function reveal_iframe_frame(doc) {
		var frame = doc && doc.defaultView && doc.defaultView.frameElement;
		if (frame) {
			frame.style.opacity = "1";
		}
	}

	function prepare_iframe_frame(iframe) {
		if (!iframe) {
			return;
		}
		iframe.style.opacity = "0";
		iframe.style.transition = "opacity 120ms ease-in";
	}

	function mark_hydrated(doc, ctx) {
		if (!doc || !doc.body) {
			return;
		}
		doc.body.setAttribute("data-std-prod-hydrated", "1");
		doc.body.setAttribute("data-std-package-id", ctx.package_id || "");
		doc.body.setAttribute("data-std-family-code", ctx.family_code || "");
		reveal_iframe_frame(doc);
	}

	function install_hydration_gate(doc) {
		if (!doc || !doc.head || doc.getElementById("std-prod-hydration-gate")) {
			return;
		}
		var style = doc.createElement("style");
		style.id = "std-prod-hydration-gate";
		style.textContent =
			'body:not([data-std-prod-hydrated="1"]):not([data-std-prod-hydrated="error"]) > main,' +
			'body:not([data-std-prod-hydrated="1"]):not([data-std-prod-hydrated="error"]) main {' +
			"visibility: hidden !important;" +
			"}" +
			"body.std-prod-header-harmonized > main," +
			"body.std-prod-header-harmonized main.mt-16," +
			"body.std-prod-header-harmonized main.mt-14," +
			"body.std-prod-header-harmonized main.pt-20 {" +
			"margin-top: 0 !important;" +
			"padding-top: 0 !important;" +
			"}";
		doc.head.appendChild(style);
	}

	function mark_hydration_failed(doc) {
		if (!doc || !doc.body) {
			return;
		}
		doc.body.setAttribute("data-std-prod-hydrated", "error");
		reveal_iframe_frame(doc);
	}

	var STD_PROD_BRAND_LABEL = "STD Engine";
	var STD_PROD_DEFAULT_UTILITY_HTML =
		'<button class="p-2 rounded-full hover:bg-surface-container transition-colors text-on-surface-variant" type="button">' +
		'<span class="material-symbols-outlined">notifications</span></button>' +
		'<button class="p-2 rounded-full hover:bg-surface-container transition-colors text-on-surface-variant" type="button">' +
		'<span class="material-symbols-outlined">help</span></button>' +
		'<button class="p-2 rounded-full hover:bg-surface-container transition-colors text-on-surface-variant" type="button">' +
		'<span class="material-symbols-outlined">settings</span></button>' +
		'<div class="h-8 w-8 rounded-full bg-primary-container flex items-center justify-center text-on-primary-container font-bold text-xs">AD</div>';

	function find_top_app_bar(doc) {
		var selectors = [
			"body > header",
			"body > nav",
			"header.sticky",
			"header.fixed",
			"nav.fixed",
			"header",
			"nav",
		];
		for (var i = 0; i < selectors.length; i++) {
			var node = doc.querySelector(selectors[i]);
			if (node && !node.closest("main, aside, footer")) {
				return node;
			}
		}
		return null;
	}

	function extract_utility_cluster(bar) {
		if (!bar) {
			return null;
		}
		var children = Array.from(bar.children);
		for (var i = children.length - 1; i >= 0; i--) {
			var child = children[i];
			if (child.querySelector("button, .material-symbols-outlined, input")) {
				return child;
			}
		}
		return null;
	}

	function hydrate_page_header(doc, page_title) {
		if (!doc || !doc.body) {
			return;
		}
		var title = String(page_title || "").trim();
		if (!title) {
			return;
		}
		var bar = find_top_app_bar(doc);
		if (!bar || !bar.parentNode) {
			return;
		}
		var utility = extract_utility_cluster(bar);
		var utility_html = utility ? utility.innerHTML : STD_PROD_DEFAULT_UTILITY_HTML;
		var header = doc.createElement("header");
		header.className =
			"std-prod-page-header bg-surface-bright dark:bg-surface-dim border-b border-outline-variant flex justify-between items-center w-full px-6 h-16 sticky top-0 z-50";
		header.setAttribute("data-testid", "std-prod-page-header");
		header.innerHTML =
			'<div class="flex items-center gap-4">' +
			'<span class="std-prod-brand font-headline-sm text-headline-sm font-extrabold text-primary">' +
			frappe.utils.escape_html(STD_PROD_BRAND_LABEL) +
			"</span>" +
			'<div class="w-px h-6 bg-outline-variant"></div>' +
			'<h1 class="std-prod-page-title font-headline-sm text-headline-sm text-primary">' +
			frappe.utils.escape_html(title) +
			"</h1>" +
			"</div>" +
			'<div class="flex items-center gap-3 std-prod-page-header-utility">' +
			utility_html +
			"</div>";
		bar.parentNode.replaceChild(header, bar);
		doc.body.classList.add("std-prod-header-harmonized");
		doc.querySelectorAll("main").forEach(function (main) {
			main.classList.remove("mt-16", "mt-14", "pt-20");
		});
		doc.title = title + " | " + STD_PROD_BRAND_LABEL;
	}

	function replace_mock_identities(doc, ctx) {
		var html = doc.body.innerHTML;
		var patterns = [
			/KE-PPRA-IT-2024-\d{2}(-[A-Z])?/g,
			/KE-PPRA-IT-2024-04/g,
			/KE-PPRA-IT-2024-01/g,
			/KE-PPRA-IT-2024-02-B/g,
		];
		patterns.forEach(function (pattern) {
			html = html.replace(pattern, ctx.package_id);
		});
		html = html.replace(/>\s*2024-04\s*</g, ">" + ctx.package_id + "<");
		html = html.replace(/v2024-04/g, "v" + ctx.package_id);
		doc.body.innerHTML = html;
	}

	function apply_read_only_banner(doc, ctx) {
		var banner_text =
			"DRAFT VERSION — READ ONLY INSPECTION. Editing, approval, and activation are disabled in Milestone 1.";
		doc.querySelectorAll("main *, header *").forEach(function (node) {
			if (!node.childNodes || node.childNodes.length !== 1) {
				return;
			}
			var text = (node.textContent || "").trim();
			if (text.indexOf("ACTIVE VERSION — READ ONLY") === 0) {
				node.textContent = banner_text;
			}
		});
		var lifecycle_nodes = doc.querySelectorAll("span, p, div");
		lifecycle_nodes.forEach(function (node) {
			var text = (node.textContent || "").trim();
			if (text === "ACTIVE" && node.children.length === 0) {
				node.textContent = "DRAFT";
			}
		});
	}

	function hide_extra_rows(tbody, keep) {
		if (!tbody) {
			return null;
		}
		var rows = Array.from(tbody.querySelectorAll("tr"));
		rows.forEach(function (row, index) {
			row.style.display = index < keep ? "" : "none";
		});
		return rows[0] || null;
	}

	function detect_table_page_size(doc, fallback) {
		var select = doc.querySelector(
			".border-t select, .bg-surface-container-low select, .bg-surface-container-high select, table + div select, table ~ div select"
		);
		if (select && select.options && select.options.length) {
			var parsed = parseInt(
				select.options[select.selectedIndex].textContent ||
					select.options[0].textContent ||
					"",
				10
			);
			if (!isNaN(parsed) && parsed > 0) {
				return parsed;
			}
		}
		return fallback || 10;
	}

	function update_showing_label(node, start, end, total) {
		if (!node) {
			return false;
		}
		var spans = Array.from(node.querySelectorAll(":scope > span"));
		if (
			spans.length >= 4 &&
			(spans[0].textContent || "").trim() === "Showing" &&
			(spans[2].textContent || "").trim() === "of"
		) {
			spans[1].textContent = start + "-" + end;
			spans[3].textContent = String(total);
			return true;
		}
		var raw = (node.textContent || "").trim();
		if (raw.indexOf("Showing") !== 0) {
			return false;
		}
		var suffix_match = raw.match(/of\s+[\d,]+\s*(.*)$/i);
		var suffix = suffix_match ? suffix_match[1].trim() : "";
		if (node.querySelector("span.font-bold, span.text-primary.font-bold")) {
			var bold_class = "font-bold";
			if (node.querySelector("span.text-primary.font-bold")) {
				bold_class = "font-bold text-primary";
			}
			var html =
				"Showing <span class='" +
				bold_class +
				"'>" +
				start +
				"-" +
				end +
				"</span> of <span class='" +
				bold_class +
				"'>" +
				total +
				"</span>";
			if (suffix) {
				html += " " + suffix;
			}
			node.innerHTML = html;
			return true;
		}
		var plain = "Showing " + start + "-" + end + " of " + total;
		if (suffix) {
			plain += " " + suffix;
		}
		node.textContent = plain;
		return true;
	}

	function sync_page_of_labels(doc, total_pages) {
		doc.querySelectorAll("span, div").forEach(function (node) {
			var text = (node.textContent || "").trim();
			if (/^PAGE\s+\d+\s+OF\s+\d+/i.test(text)) {
				node.textContent = "PAGE 1 OF " + total_pages;
				return;
			}
			if (/^\d+\s+OF\s+\d+$/i.test(text)) {
				node.textContent = "1 OF " + total_pages;
			}
		});
		doc.querySelectorAll("div.flex.items-center.px-2, div.flex.items-center.gap-4").forEach(function (node) {
			var text = (node.textContent || "").trim();
			if (text.indexOf("PAGE") === 0 && text.indexOf("OF") > 0) {
				var page_spans = node.querySelectorAll("span");
				if (page_spans.length >= 2) {
					page_spans[page_spans.length - 1].textContent = String(total_pages);
				}
			}
		});
	}

	function sync_numbered_page_buttons(doc, total_pages) {
		doc.querySelectorAll("button").forEach(function (btn) {
			var label = (btn.textContent || "").trim();
			if (!/^\d+$/.test(label)) {
				return;
			}
			var page_num = parseInt(label, 10);
			if (page_num <= total_pages) {
				btn.style.display = "";
				btn.disabled = false;
				btn.removeAttribute("disabled");
				if (page_num === 1) {
					btn.classList.add("bg-primary", "text-white");
				} else {
					btn.classList.remove("bg-primary", "text-white");
				}
			} else {
				btn.style.display = "none";
			}
		});
	}

	function sync_pager_ellipsis(doc, total_pages) {
		doc.querySelectorAll("nav span, .flex.items-center.px-4 span, .flex.items-center.gap-1 span").forEach(
			function (node) {
				if ((node.textContent || "").trim() !== "...") {
					return;
				}
				node.style.display = total_pages > 1 ? "" : "none";
			}
		);
	}

	function widen_table_footer_page_size_select(doc) {
		doc.querySelectorAll(
			"div.border-t select, .border-t.border-outline-variant select, table + div select, table ~ div select"
		).forEach(function (select) {
			select.classList.add("min-w-12", "w-12", "shrink-0", "pr-1");
		});
	}

	function sync_pager_nav_buttons(doc, total_pages) {
		var nav_icons = {
			first_page: true,
			chevron_left: true,
			chevron_right: true,
			last_page: true,
		};
		doc.querySelectorAll("button").forEach(function (btn) {
			var icon = btn.querySelector(".material-symbols-outlined");
			if (!icon) {
				return;
			}
			var icon_name = (icon.textContent || "").trim();
			if (!nav_icons[icon_name]) {
				return;
			}
			var disable =
				total_pages <= 1 ||
				icon_name === "first_page" ||
				icon_name === "chevron_left";
			btn.disabled = disable;
			if (disable) {
				btn.setAttribute("disabled", "");
				btn.style.opacity = "0.3";
				btn.classList.add("disabled:opacity-30");
			} else {
				btn.removeAttribute("disabled");
				btn.style.opacity = "";
			}
		});
	}

	function is_table_footer_showing_node(node) {
		if (!node || node.querySelector("button, select, .material-symbols-outlined")) {
			return false;
		}
		var text = (node.textContent || "").trim();
		if (text.indexOf("Showing") !== 0) {
			return false;
		}
		var tag = (node.tagName || "").toUpperCase();
		return tag === "SPAN" || tag === "P" || tag === "DIV";
	}

	function hydrate_table_footer(doc, total, page_size) {
		var count = total || 0;
		var pageSize = page_size || detect_table_page_size(doc, 10);
		var start = count > 0 ? 1 : 0;
		var end = count > 0 ? Math.min(pageSize, count) : 0;
		var total_pages = count > 0 ? Math.ceil(count / pageSize) : 0;

		var showing_nodes = [];
		doc.querySelectorAll("span, p, div").forEach(function (node) {
			if (!is_table_footer_showing_node(node)) {
				return;
			}
			var dominated = showing_nodes.some(function (seen) {
				return seen !== node && seen.contains(node);
			});
			if (!dominated) {
				showing_nodes.push(node);
			}
		});
		showing_nodes.forEach(function (node) {
			var has_child_showing = showing_nodes.some(function (other) {
				return other !== node && node.contains(other);
			});
			if (!has_child_showing) {
				update_showing_label(node, start, end, count);
			}
		});

		sync_page_of_labels(doc, Math.max(total_pages, 1));
		sync_numbered_page_buttons(doc, total_pages);
		sync_pager_ellipsis(doc, total_pages);
		sync_pager_nav_buttons(doc, total_pages);
		widen_table_footer_page_size_select(doc);
	}

	function disable_governance_actions(doc) {
		doc.querySelectorAll("button").forEach(function (btn) {
			var text = (btn.textContent || "").trim();
			if (
				text === "Suspend" ||
				text === "Supersede" ||
				text.indexOf("Approve") === 0 ||
				text === "Commit Import" ||
				text === "Reject Import" ||
				text === "Activate Version"
			) {
				btn.style.pointerEvents = "none";
				btn.style.opacity = "0.55";
				btn.setAttribute("aria-disabled", "true");
			}
		});
	}

	function update_headline_counters(doc, label, value) {
		doc.querySelectorAll(".text-headline-md, .font-headline-md").forEach(function (node) {
			var parent_text = node.parentElement ? node.parentElement.textContent || "" : "";
			if (parent_text.indexOf(label) >= 0) {
				node.textContent = String(value);
			}
		});
	}

	function render_identity_rows(items, row_class, data_attr) {
		return items
			.map(function (item) {
				return (
					"<tr class='" +
					row_class +
					" cursor-pointer hover:bg-surface-container-low transition-colors' " +
					data_attr +
					"='" +
					frappe.utils.escape_html(item.id) +
					"'><td class='px-4 py-3 font-data-mono text-primary'>" +
					frappe.utils.escape_html(item.code || item.id) +
					"</td><td class='px-4 py-3'>" +
					frappe.utils.escape_html(item.name || "") +
					"</td><td class='px-4 py-3'>" +
					frappe.utils.escape_html(item.validationStatus || "—") +
					"</td><td class='px-4 py-3 font-data-mono text-[11px]'>" +
					frappe.utils.escape_html(item.sourceAnchorId || "—") +
					"</td></tr>"
				);
			})
			.join("");
	}

	function hydrate_parameters(doc, payload, ctx) {
		var data = payload.data || {};
		var params = data.parameters || [];
		update_headline_counters(doc, "Total Parameters", data.count || params.length);
		var tbody = doc.querySelector("table tbody");
		if (tbody && params.length) {
			tbody.innerHTML = params
				.slice(0, 60)
				.map(function (item) {
					return (
						"<tr class='bureau-table-row transition-colors std-prod-param-row cursor-pointer' data-parameter-key='" +
						frappe.utils.escape_html(item.id) +
						"'><td class='px-4 py-4 parameter-key text-primary font-medium'>" +
						frappe.utils.escape_html(item.code || item.id) +
						"</td><td class='px-4 py-4'>" +
						frappe.utils.escape_html(item.name || "") +
						"</td><td class='px-4 py-4'>—</td><td class='px-4 py-4'>—</td><td class='px-4 py-4'>—</td><td class='px-4 py-4'>—</td><td class='px-4 py-4'>—</td><td class='px-4 py-4'>" +
						frappe.utils.escape_html(item.validationStatus || "—") +
						"</td><td class='px-4 py-4'>—</td><td class='px-4 py-4'>—</td><td class='px-4 py-4 font-mono text-[10px]'>—</td></tr>"
					);
				})
				.join("");
		}
		hydrate_table_footer(doc, data.count || params.length);
	}

	function set_labeled_field(doc, label, value, options) {
		options = options || {};
		var target_label = String(label || "").trim().toLowerCase();
		var nodes = doc.querySelectorAll("section.bento-item p.text-on-surface-variant");
		for (var i = 0; i < nodes.length; i += 1) {
			var node = nodes[i];
			if ((node.textContent || "").trim().toLowerCase() !== target_label) {
				continue;
			}
			var value_node = node.nextElementSibling;
			if (!value_node) {
				continue;
			}
			if (options.html) {
				value_node.innerHTML = value;
			} else {
				value_node.textContent = value == null || value === "" ? "—" : String(value);
			}
			return true;
		}
		return false;
	}

	function find_bento_section(doc, heading) {
		var sections = doc.querySelectorAll("section.bento-item");
		for (var i = 0; i < sections.length; i += 1) {
			var header = sections[i].querySelector("h3");
			if (header && (header.textContent || "").trim() === heading) {
				return sections[i];
			}
		}
		return null;
	}

	function business_code_from_key(key, marker) {
		if (!key) {
			return "";
		}
		var marker_index = String(key).indexOf(marker);
		if (marker_index >= 0) {
			return String(key).slice(marker_index + marker.length);
		}
		var parts = String(key).split(".");
		return parts[parts.length - 1] || String(key);
	}

	function set_detail_label_value(doc, label, value, options) {
		options = options || {};
		var target_label = String(label || "").trim().toLowerCase();
		var labels = doc.querySelectorAll("label");
		for (var i = 0; i < labels.length; i += 1) {
			var node = labels[i];
			if ((node.textContent || "").trim().toLowerCase() !== target_label) {
				continue;
			}
			var value_node = node.nextElementSibling;
			if (!value_node) {
				continue;
			}
			if (options.html) {
				value_node.innerHTML = value;
			} else {
				value_node.textContent = value == null || value === "" ? "—" : String(value);
			}
			return true;
		}
		return false;
	}

	function find_card_section(doc, heading) {
		var headers = doc.querySelectorAll("h3");
		for (var i = 0; i < headers.length; i += 1) {
			if ((headers[i].textContent || "").trim() !== heading) {
				continue;
			}
			var section = headers[i].closest(".bg-white, section");
			if (section) {
				return section;
			}
		}
		return null;
	}

	function hydrate_parameter(doc, payload, ctx) {
		var data = payload.data || {};
		var metadata = data.metadata || {};
		var package_context = payload.packageContext || {};
		var business_code = data.code || metadata.parameter_key || "";
		var display_name = data.name || metadata.display_label || business_code || "Parameter";
		var lifecycle = package_context.lifecycleState || "DRAFT";

		var breadcrumb = doc.querySelector("nav span.text-primary.font-medium");
		if (breadcrumb) {
			breadcrumb.textContent = business_code;
			breadcrumb.setAttribute("data-testid", "std-prod-parameter-breadcrumb");
		}
		var title = doc.querySelector("h1.font-headline-lg");
		if (title) {
			title.innerHTML =
				frappe.utils.escape_html(display_name) +
				' <span class="text-on-surface-variant font-normal"> (' +
				frappe.utils.escape_html(business_code) +
				")</span>";
			title.setAttribute("data-testid", "std-prod-parameter-title");
		}

		var badges = doc.querySelector(".flex.items-center.gap-3.mt-2");
		if (badges) {
			var badge_bits = [];
			if (data.groupLabel) {
				badge_bits.push(
					'<span class="bg-surface-container-high text-on-surface-variant px-3 py-1 rounded-full text-[12px] font-semibold">Group: ' +
						frappe.utils.escape_html(data.groupLabel) +
						"</span>",
				);
			}
			if (data.sectionTitle) {
				badge_bits.push(
					'<span class="bg-surface-container-high text-on-surface-variant px-3 py-1 rounded-full text-[12px] font-semibold">Section: ' +
						frappe.utils.escape_html(data.sectionTitle) +
						"</span>",
				);
			}
			if (data.fieldType) {
				badge_bits.push(
					'<span class="bg-surface-container-high text-on-surface-variant px-3 py-1 rounded-full text-[12px] font-semibold">Type: ' +
						frappe.utils.escape_html(data.fieldType) +
						"</span>",
				);
			}
			badges.innerHTML = badge_bits.join(
				'<span class="w-1 h-1 rounded-full bg-outline-variant"></span>',
			);
		}

		set_labeled_field(doc, "STD Version", ctx.package_id);
		set_labeled_field(doc, "Lifecycle State", lifecycle);
		set_labeled_field(doc, "Package ID", ctx.package_id);
		set_labeled_field(
			doc,
			"Parameter Status",
			data.validationStatus || data.extractionStatus || "—",
		);
		set_labeled_field(doc, "Data Type", data.fieldType || "—");
		set_labeled_field(doc, "Requiredness", data.required ? "MANDATORY" : "OPTIONAL");
		set_labeled_field(
			doc,
			"Allowed Values",
			data.optionSetKey
				? "Option set: " + data.optionSetKey
				: "No predefined list. Value entered according to field type constraints.",
		);
		set_labeled_field(
			doc,
			"Conditional Display Rules",
			data.sectionTitle ? "Visible in " + data.sectionTitle : "Always visible in configured sections.",
		);
		set_labeled_field(
			doc,
			"Render Binding",
			(data.renderBindings || []).length ? (data.renderBindings || []).join(", ") : "None",
		);
		set_labeled_field(
			doc,
			"Rule Binding",
			(data.validationRuleKeys || []).length
				? (data.validationRuleKeys || []).join(", ")
				: "None",
		);

		var usage_section = find_bento_section(doc, "USAGE MAP");
		var usage_container = usage_section && usage_section.querySelector(".divide-y");
		if (usage_container) {
			var usage_items = [];
			(data.renderBindings || []).forEach(function (binding_key) {
				usage_items.push({
					icon: "layers",
					title: binding_key,
					subtitle: "Render binding",
				});
			});
			(data.validationRuleKeys || []).forEach(function (rule_key) {
				usage_items.push({
					icon: "rule",
					title: rule_key,
					subtitle: "Validation rule",
				});
			});
			if (!usage_items.length) {
				usage_container.innerHTML =
					'<div class="p-card-padding text-on-surface-variant italic text-[13px]">No render blocks or validation rules are bound to this parameter yet.</div>';
			} else {
				usage_container.innerHTML = usage_items
					.map(function (item) {
						return (
							'<div class="p-card-padding flex items-center justify-between hover:bg-surface-container-low transition-colors">' +
							'<div class="flex items-center gap-4"><span class="material-symbols-outlined text-primary">' +
							item.icon +
							'</span><div><p class="font-semibold text-[13px]">' +
							frappe.utils.escape_html(item.title) +
							'</p><p class="text-[11px] text-on-surface-variant uppercase">' +
							frappe.utils.escape_html(item.subtitle) +
							"</p></div></div></div>"
						);
					})
					.join("");
			}
		}

		var validation_section = find_bento_section(doc, "VALIDATION RULES");
		var validation_body = validation_section && validation_section.querySelector("tbody");
		if (validation_body) {
			var rule_keys = data.validationRuleKeys || [];
			if (!rule_keys.length) {
				validation_body.innerHTML =
					'<tr><td class="px-card-padding py-4 text-on-surface-variant italic" colspan="5">No validation rules are bound to this parameter.</td></tr>';
			} else {
				validation_body.innerHTML = rule_keys
					.map(function (rule_key) {
						return (
							"<tr><td class='px-card-padding py-4 font-semibold text-[13px]'>" +
							frappe.utils.escape_html(rule_key) +
							"</td><td class='px-card-padding py-4 font-data-mono text-[12px]'>—</td><td class='px-card-padding py-4 text-[13px]'>VALIDATION_RUN</td><td class='px-card-padding py-4'>—</td><td class='px-card-padding py-4 text-right'>—</td></tr>"
						);
					})
					.join("");
			}
		}

		var options_section = find_bento_section(doc, "OPTIONS & DEFAULTS");
		if (options_section) {
			var default_node = options_section.querySelector(".font-data-mono.text-\\[13px\\]");
			if (default_node) {
				default_node.textContent =
					data.defaultValue == null || data.defaultValue === ""
						? "NULL (Input Required)"
						: String(data.defaultValue);
			}
			options_section.querySelectorAll("p.text-on-surface-variant.italic").forEach(function (node) {
				if ((node.textContent || "").indexOf("No predefined list") >= 0) {
					node.textContent = data.optionSetKey
						? "Controlled by option set " + data.optionSetKey + "."
						: "No predefined list. Value entered according to field type constraints.";
				}
			});
		}

		var trace_section = find_bento_section(doc, "SOURCE TRACEABILITY");
		if (trace_section) {
			set_labeled_field(
				doc,
				"Source STD Section/Page/Anchor",
				data.sectionTitle || data.sourceAnchorKey || data.sourceAnchorId || "—",
			);
			var hash_panel = trace_section.querySelector(".font-data-mono.text-\\[12px\\].text-tertiary");
			if (hash_panel) {
				hash_panel.textContent =
					data.description ||
					"Source text hash and verbatim extraction are pending for this parameter in Milestone 1.";
			}
		}

		var audit_section = find_bento_section(doc, "AUDIT HISTORY");
		if (audit_section) {
			var audit_body = audit_section.querySelector(".space-y-8");
			if (audit_body) {
				audit_body.innerHTML =
					'<div class="text-on-surface-variant italic text-[13px]">Parameter-level audit events are not exposed in the Milestone 1 read model.</div>';
			}
		}

		if (doc.body) {
			doc.body.setAttribute("data-std-parameter-key", data.id || ctx.parameter_key || "");
		}
	}

	function hydrate_rules(doc, payload, ctx) {
		var data = payload.data || {};
		var rules = data.rules || [];
		update_headline_counters(doc, "Total Rules", data.count || rules.length);
		var tbody = doc.querySelector("table tbody");
		if (tbody && rules.length) {
			tbody.innerHTML = render_identity_rows(rules.slice(0, 60), "std-prod-rule-row", "data-rule-key");
		}
		hydrate_table_footer(doc, data.count || rules.length);
	}

	function hydrate_rule(doc, payload, ctx) {
		var data = payload.data || {};
		var metadata = data.metadata || {};
		var package_context = payload.packageContext || {};
		var business_code = data.code || metadata.rule_key || "";
		var display_name = data.name || business_code || "Rule";
		var lifecycle = package_context.lifecycleState || "DRAFT";

		var breadcrumb = doc.querySelector("nav span.font-semibold.text-on-surface");
		if (breadcrumb) {
			breadcrumb.textContent = business_code;
			breadcrumb.setAttribute("data-testid", "std-prod-rule-breadcrumb");
		}
		var title = doc.querySelector("h1.text-headline-lg.font-headline-lg");
		if (title) {
			title.innerHTML =
				frappe.utils.escape_html(display_name) +
				' <span class="text-on-surface-variant font-normal">(' +
				frappe.utils.escape_html(business_code) +
				")</span>";
			title.setAttribute("data-testid", "std-prod-rule-title");
		}

		doc.querySelectorAll("span.text-body-md.font-semibold").forEach(function (node) {
			var label = node.previousElementSibling;
			if (!label) {
				return;
			}
			var label_text = (label.textContent || "").trim().toUpperCase();
			if (label_text === "FAMILY") {
				node.textContent = ctx.family_code || package_context.familyCode || "—";
			} else if (label_text === "VERSION") {
				node.textContent = ctx.package_id || package_context.packageId || "—";
			} else if (label_text === "PACKAGE ID") {
				node.textContent = ctx.package_id || package_context.packageId || "—";
			} else if (label_text === "LIFECYCLE") {
				node.textContent = lifecycle;
			}
		});

		doc.querySelectorAll("span.flex.items-center.gap-1\\.5").forEach(function (badge) {
			var text = (badge.textContent || "").trim();
			if (text.indexOf("Rule Type:") >= 0) {
				badge.innerHTML =
					'<span class="material-symbols-outlined text-[14px]">rule</span> Rule Type: ' +
					frappe.utils.escape_html(data.ruleType || "—");
				badge.setAttribute("data-testid", "std-prod-rule-type");
			} else if (text.indexOf("Severity:") >= 0) {
				badge.innerHTML =
					'<span class="material-symbols-outlined text-[14px]">block</span> Severity: ' +
					frappe.utils.escape_html(data.severity || "—");
				badge.setAttribute("data-testid", "std-prod-rule-severity");
			} else if (text.indexOf("Status:") >= 0) {
				badge.innerHTML =
					'<span class="material-symbols-outlined text-[14px]" style=\'font-variation-settings: "FILL" 1;\'>check_circle</span> Status: ' +
					frappe.utils.escape_html(data.validationStatus || "—");
			}
		});

		set_detail_label_value(doc, "Rule Name", display_name);
		set_detail_label_value(doc, "Key identifier", business_code);
		set_detail_label_value(
			doc,
			"Description",
			data.description || data.message || "No description recorded for this rule.",
		);
		var expression_node = doc.querySelector(
			".bg-primary-container\\/10.p-4.rounded.border.font-data-mono, .bg-primary-container\\/10.p-4.rounded.border"
		);
		if (expression_node) {
			expression_node.textContent = data.expression
				? String(data.expression)
				: "Expression is evaluated by service rule logic in Milestone 1 (no inline expression stored).";
		}
		set_detail_label_value(doc, "Error Message", data.message || "—");
		set_detail_label_value(
			doc,
			"Plain-Language Explanation",
			data.description || data.message || "—",
		);
		set_detail_label_value(
			doc,
			"Suggested Fix",
			data.message
				? "Resolve the validation issue described in the error message before publication."
				: "—",
			{ html: true },
		);

		var trigger_scope = find_card_section(doc, "Trigger & Scope");
		if (trigger_scope) {
			var stage_badge = trigger_scope.querySelector("span.uppercase.tracking-wider");
			if (stage_badge) {
				stage_badge.textContent = data.lifecycleStage || "VALIDATION_RUN";
			}
			var scope_badges = trigger_scope.querySelectorAll("span.uppercase.tracking-wider");
			if (scope_badges.length > 1) {
				scope_badges[1].textContent = metadata.version_code || ctx.package_id || "—";
			}
			var affected_container = trigger_scope.querySelector(".space-y-2");
			if (affected_container) {
				var affected_keys = data.affectedParameterKeys || [];
				if (!affected_keys.length) {
					affected_container.innerHTML =
						'<div class="text-on-surface-variant italic text-[13px]">No affected parameters are linked to this rule yet.</div>';
				} else {
					affected_container.innerHTML = affected_keys
						.map(function (parameter_key) {
							var parameter_code = business_code_from_key(parameter_key, ".parameter.");
							return (
								'<div class="flex justify-between items-center p-2 bg-surface-container-low rounded">' +
								'<span class="text-[11px] font-label-caps text-outline">Parameter</span>' +
								'<span class="font-data-mono text-xs text-secondary">' +
								frappe.utils.escape_html(parameter_code) +
								"</span></div>"
							);
						})
						.join("");
				}
			}
			set_detail_label_value(
				doc,
				"Execution Context",
				data.blockingOnPublish ? "Blocking on publish" : "Advisory validation",
			);
		}

		var trace_section = find_card_section(doc, "Source Traceability");
		if (trace_section) {
			set_detail_label_value(
				doc,
				"Source Document",
				(ctx.package_id || "—") + " / Official IT STD Source PDF",
			);
			set_detail_label_value(doc, "Legal Basis", data.sourceAnchorKey || data.sourceAnchorId || "—");
			set_detail_label_value(doc, "Paragraph/Anchor", data.sourceAnchorId || "—");
			var hash_panel = trace_section.querySelector(".font-data-mono.text-\\[11px\\]");
			if (hash_panel) {
				hash_panel.textContent =
					"Source text hash is not exposed in the Milestone 1 read model.";
			}
		}

		var test_section = find_card_section(doc, "Verification & Test Cases");
		if (test_section) {
			var test_body = test_section.querySelector("tbody");
			if (test_body) {
				test_body.innerHTML =
					'<tr><td class="px-container-padding py-3 text-on-surface-variant italic" colspan="5">Automated verification cases are not exposed in the Milestone 1 read model.</td></tr>';
			}
			var test_footer = test_section.querySelector(".text-label-caps.font-label-caps.text-on-surface-variant");
			if (test_footer) {
				test_footer.textContent = "Showing 0 of 0 Test Cases";
			}
		}

		var history_section = find_card_section(doc, "Execution History");
		if (history_section) {
			var history_body = history_section.querySelector("tbody");
			if (history_body) {
				history_body.innerHTML =
					'<tr><td class="px-container-padding py-3 text-on-surface-variant italic" colspan="5">Rule execution history is not exposed in the Milestone 1 read model.</td></tr>';
			}
		}

		if (doc.body) {
			doc.body.setAttribute("data-std-rule-key", data.id || ctx.rule_key || "");
		}
	}

	function hydrate_forms(doc, payload, ctx) {
		var data = payload.data || {};
		var forms = data.forms || [];
		update_headline_counters(doc, "Total Forms", data.count || forms.length);
		var tbody = doc.querySelector("table tbody");
		if (tbody && forms.length) {
			tbody.innerHTML = forms
				.slice(0, 40)
				.map(function (item) {
					return (
						"<tr class='hover:bg-surface-container-low transition-colors std-prod-form-row cursor-pointer' data-form-key='" +
						frappe.utils.escape_html(item.id) +
						"'><td class='p-4 font-data-mono text-primary'>" +
						frappe.utils.escape_html(item.code || item.id) +
						"</td><td class='p-4 font-medium'>" +
						frappe.utils.escape_html(item.name || "") +
						"</td><td class='p-4'>—</td><td class='p-4'>—</td><td class='p-4 text-center'>—</td><td class='p-4 text-center'>—</td><td class='p-4 text-center'>—</td><td class='p-4'>—</td><td class='p-4'>—</td><td class='p-4'>—</td><td class='p-4 text-right'>—</td></tr>"
					);
				})
				.join("");
		}
		hydrate_table_footer(doc, data.count || forms.length);
	}

	function hydrate_form(doc, payload, ctx) {
		var data = payload.data || {};
		var metadata = data.metadata || {};
		var package_context = payload.packageContext || {};
		var business_code = data.code || metadata.form_code || "";
		var display_name = data.name || metadata.display_title || business_code || "Form";
		var fields = data.formFields || [];
		var lifecycle = package_context.lifecycleState || "DRAFT";

		var header_title = doc.querySelector("header h1");
		if (header_title) {
			header_title.textContent = display_name;
			header_title.setAttribute("data-testid", "std-prod-form-title");
		}

		doc.querySelectorAll("div.flex.gap-1").forEach(function (row) {
			var label_node = row.querySelector("span.opacity-60");
			var value_node = label_node && label_node.nextElementSibling;
			if (!label_node || !value_node) {
				return;
			}
			var label_text = (label_node.textContent || "").trim();
			if (label_text === "Family:") {
				value_node.textContent = ctx.family_code || package_context.familyCode || "—";
			} else if (label_text === "Version:") {
				value_node.textContent = ctx.package_id || package_context.packageId || "—";
			} else if (label_text === "Package:") {
				value_node.textContent = ctx.package_id || package_context.packageId || "—";
			}
		});

		doc.querySelectorAll("label.text-label-caps").forEach(function (label) {
			var value_node = label.nextElementSibling;
			if (!value_node) {
				return;
			}
			var label_text = (label.textContent || "").trim();
			if (label_text === "Form Code") {
				value_node.textContent = business_code;
				value_node.setAttribute("data-testid", "std-prod-form-code");
			} else if (label_text === "Title") {
				value_node.textContent = display_name;
			} else if (label_text === "Respondent") {
				value_node.textContent = data.respondentType || metadata.respondent_type || "—";
			} else if (label_text === "Workflow Stage") {
				value_node.textContent = data.stage || metadata.stage || "—";
			} else if (label_text === "Requirement Level") {
				value_node.textContent = data.validationStatus || "—";
			} else if (label_text === "Source File") {
				value_node.textContent = (ctx.package_id || "—") + " / Official IT STD Source PDF";
			} else if (label_text === "Section/Page/Para") {
				value_node.textContent = data.sourceAnchorId || data.sourceAnchorKey || "—";
			} else if (label_text === "Source Anchor") {
				value_node.textContent = data.sourceAnchorKey || data.sourceAnchorId || "—";
			}
		});

		doc.querySelectorAll("span.text-label-caps.font-label-caps.text-outline").forEach(function (label) {
			var stat_card = label.closest(".bg-white");
			if (!stat_card) {
				return;
			}
			var count_node = stat_card.querySelector("span.text-3xl");
			if (!count_node) {
				return;
			}
			var label_text = (label.textContent || "").trim();
			if (label_text === "Total Fields") {
				count_node.textContent = String(fields.length);
			} else if (label_text === "Evidence Reqs") {
				count_node.textContent = "0";
			} else if (label_text === "Activation Rules") {
				count_node.textContent = String((metadata.activation_rule_keys || []).length);
			} else if (label_text === "Carry-Forward") {
				count_node.textContent = "0";
			}
		});

		var tbody = doc.querySelector("table tbody");
		if (tbody) {
			if (!fields.length) {
				tbody.innerHTML =
					'<tr><td class="px-4 py-3 text-on-surface-variant italic" colspan="10">No fields are defined for this form yet.</td></tr>';
			} else {
				tbody.innerHTML = fields
					.map(function (field) {
						var schema = field.schema || {};
						var validation_rules = schema.validation_rule_keys || [];
						return (
							"<tr class='hover:bg-surface-container-low transition-colors group'>" +
							"<td class='px-4 py-3 data-cell-mono text-primary font-semibold'>" +
							frappe.utils.escape_html(field.code || field.id) +
							"</td><td class='px-4 py-3 text-body-md'>" +
							frappe.utils.escape_html(field.name || "") +
							"</td><td class='px-4 py-3'><span class='px-2 py-0.5 bg-surface-container-highest rounded text-[11px] font-bold'>" +
							frappe.utils.escape_html(field.fieldType || "") +
							"</span></td><td class='px-4 py-3'>" +
							(field.isRequired ? "Required" : "Optional") +
							"</td><td class='px-4 py-3 text-body-md text-on-surface-variant max-w-xs truncate'>" +
							frappe.utils.escape_html(schema.display_label || field.name || "—") +
							"</td><td class='px-4 py-3 data-cell-mono text-xs text-secondary'>" +
							frappe.utils.escape_html(
								validation_rules.length ? validation_rules.join(", ") : "—",
							) +
							"</td><td class='px-4 py-3 text-outline'>—</td><td class='px-4 py-3 text-outline'>—</td><td class='px-4 py-3 text-outline'>" +
							frappe.utils.escape_html(schema.source_anchor_key || data.sourceAnchorId || "—") +
							"</td><td class='px-4 py-3 text-right'>—</td></tr>"
						);
					})
					.join("");
			}
		}
		hydrate_table_footer(doc, fields.length);

		if (doc.body) {
			doc.body.setAttribute("data-std-form-key", data.id || ctx.form_key || "");
		}
	}

	function hydrate_requirements(doc, payload, ctx) {
		var data = payload.data || {};
		var items = data.requirements || [];
		update_headline_counters(doc, "Requirement", data.count || items.length);
		var tbody = doc.querySelector("table tbody");
		if (tbody && items.length) {
			tbody.innerHTML = render_identity_rows(items, "std-prod-req-row", "data-requirement-key");
		}
		hydrate_table_footer(doc, data.count || items.length);
	}

	function hydrate_price_schedules(doc, payload, ctx) {
		var data = payload.data || {};
		var items = data.priceSchedules || [];
		update_headline_counters(doc, "Price Schedule", data.count || items.length);
		var tbody = doc.querySelector("table tbody");
		if (tbody && items.length) {
			tbody.innerHTML = render_identity_rows(items, "std-prod-price-row", "data-price-key");
		}
		hydrate_table_footer(doc, data.count || items.length);
	}

	function hydrate_evaluation(doc, payload, ctx) {
		var data = payload.data || {};
		var schemas = data.schemas || [];
		var schema = schemas[0] || {};
		doc.querySelectorAll("h1, .font-headline-sm").forEach(function (node) {
			if ((node.textContent || "").indexOf("Evaluation Schema") >= 0 && schema.name) {
				node.textContent = schema.name;
			}
		});
		update_headline_counters(doc, "Criteria", data.count || schemas.length);
		hydrate_table_footer(doc, data.count || schemas.length);
	}

	function hydrate_render_blocks(doc, payload, ctx) {
		var data = payload.data || {};
		var blocks = data.renderBlocks || [];
		update_headline_counters(doc, "Render Block", data.count || blocks.length);
		var tbody = doc.querySelector("table tbody");
		if (tbody && blocks.length) {
			tbody.innerHTML = blocks
				.slice(0, 40)
				.map(function (item) {
					return (
						"<tr class='hover:bg-surface-container-low transition-colors'><td class='px-4 py-3 font-data-mono text-primary'>" +
						frappe.utils.escape_html(item.code || item.id) +
						"</td><td class='px-4 py-3'>" +
						frappe.utils.escape_html(item.name || "") +
						"</td><td class='px-4 py-3'>—</td><td class='px-4 py-3'>—</td><td class='px-4 py-3'>—</td><td class='px-4 py-3'>—</td><td class='px-4 py-3'>" +
						frappe.utils.escape_html(item.validationStatus || "—") +
						"</td><td class='px-4 py-3'>—</td><td class='px-4 py-3'>—</td></tr>"
					);
				})
				.join("");
		}
		hydrate_table_footer(doc, data.count || blocks.length);
	}

	function hydrate_usage_kpis(doc, kpis) {
		if (!kpis) {
			return;
		}
		function set_usage_kpi_card(label, value, options) {
			doc.querySelectorAll(".font-label-caps, .text-label-caps").forEach(function (node) {
				if ((node.textContent || "").trim() !== label) {
					return;
				}
				var card = node.closest(".bg-white");
				if (!card) {
					return;
				}
				var headline = card.querySelector(".font-headline-lg, .text-headline-lg");
				if (headline) {
					headline.textContent = String(value);
					if (label === "OPEN ADDENDA") {
						headline.classList.toggle("text-status-exhausted", Number(value) > 0);
						headline.classList.toggle("text-primary", Number(value) <= 0);
					}
				}
				var value_row = card.querySelector(".flex.items-baseline.gap-2");
				if (value_row) {
					var badge = value_row.querySelector("span.text-xs.font-bold");
					if (badge) {
						if (options && options.badge) {
							badge.textContent = options.badge;
							badge.style.display = "";
						} else {
							badge.style.display = "none";
						}
					}
				}
			});
		}
		set_usage_kpi_card("TOTAL TENDERS BOUND (ALL VERSIONS)", kpis.totalTendersBoundAllVersions || 0, {
			badge: kpis.trendPercent != null ? "+" + kpis.trendPercent + "%" : null,
		});
		set_usage_kpi_card("ACTIVE TENDERS (THIS VERSION)", kpis.activeTendersThisVersion || 0, {
			badge:
				kpis.activeTendersThisVersion > 0 && kpis.activeStabilityBadge
					? kpis.activeStabilityBadge
					: null,
		});
		set_usage_kpi_card("HISTORICAL RECORDS", kpis.historicalRecords || 0);
		set_usage_kpi_card("OPEN ADDENDA", kpis.openAddenda || 0, {
			badge: kpis.openAddendaActionRequired ? "Action Req" : null,
		});
	}

	function hydrate_usage(doc, payload, ctx) {
		var data = payload.data || {};
		var bindings = data.bindings || [];
		hydrate_usage_kpis(doc, data.usageKpis);
		var tbody = doc.querySelector("table tbody");
		if (!tbody) {
			hydrate_table_footer(doc, data.count || 0);
			return;
		}
		if (!bindings.length) {
			tbody.innerHTML =
				"<tr><td colspan='8' class='px-4 py-6 text-on-surface-variant'>No usage bindings for this package.</td></tr>";
			hydrate_table_footer(doc, data.count || 0);
			return;
		}
		tbody.innerHTML = bindings
			.map(function (binding) {
				return (
					"<tr><td class='px-4 py-3 font-data-mono text-primary'>" +
					frappe.utils.escape_html(binding.code || binding.id) +
					"</td><td class='px-4 py-3'>" +
					frappe.utils.escape_html(binding.name || "") +
					"</td><td class='px-4 py-3'>" +
					frappe.utils.escape_html(binding.tenderRef || "—") +
					"</td><td class='px-4 py-3'>" +
					frappe.utils.escape_html(binding.bindingStatus || "—") +
					"</td><td class='px-4 py-3 font-data-mono text-[11px]'>" +
					frappe.utils.escape_html(binding.fixtureSource || "—") +
					"</td><td class='px-4 py-3'>—</td><td class='px-4 py-3'>—</td><td class='px-4 py-3'>—</td></tr>"
				);
			})
			.join("");
		hydrate_table_footer(doc, data.count || bindings.length);
	}

	function hydrate_import_review(doc, payload, ctx) {
		var run = (payload.data && payload.data.importRun) || {};
		doc.querySelectorAll("h1").forEach(function (node) {
			if ((node.textContent || "").indexOf("Import Package Review") >= 0) {
				node.textContent = "Import Package Review — " + (run.import_run_key || ctx.package_id);
			}
		});
		var tbody = doc.querySelectorAll("table tbody")[0];
		if (tbody) {
			tbody.innerHTML =
				"<tr><td class='px-4 py-3 font-body-md text-[13px] font-semibold'>manifest.json</td><td class='px-4 py-3 font-data-mono text-[11px]'>" +
				frappe.utils.escape_html(run.manifest_hash || "—") +
				"</td><td class='px-4 py-3'>" +
				frappe.utils.escape_html(run.status || "—") +
				"</td><td class='px-4 py-3 font-data-mono text-[11px]'>" +
				frappe.utils.escape_html(run.package_sha256 || "—") +
				"</td></tr>";
		}
		hydrate_table_footer(doc, 1);
	}

	function hydrate_version_diff(doc, payload, ctx) {
		var data = payload.data || {};
		var panel = doc.querySelector("main");
		if (!panel) {
			return;
		}
		if (!data.compareAvailable) {
			var notice =
				"<div class='std-prod-diff-stub mx-container-padding my-6 p-6 border border-outline-variant rounded-lg bg-surface-container-low text-on-surface-variant'>" +
				frappe.utils.escape_html(data.message || "Version comparison unavailable.") +
				" <span class='font-data-mono text-primary'>" +
				frappe.utils.escape_html(data.reason || "SINGLE_VERSION_ONLY") +
				"</span></div>";
			var existing = doc.querySelector(".std-prod-diff-stub");
			if (existing) {
				existing.outerHTML = notice;
			} else {
				panel.insertAdjacentHTML("afterbegin", notice);
			}
		}
		var diff_count = (data.changes && data.changes.length) || (data.compareAvailable ? 1 : 0);
		hydrate_table_footer(doc, diff_count);
	}

	function hydrate_review(doc, results, ctx) {
		var version = (results.version && results.version.data) || {};
		var validation = (results.validation && results.validation.data) || {};
		var summary = validation.summary || {};
		doc.querySelectorAll("h1").forEach(function (node) {
			if ((node.textContent || "").indexOf("Review and Approval") >= 0) {
				node.textContent = "Review and Approval — " + (version.packageId || ctx.package_id);
			}
		});
		doc.querySelectorAll(".font-headline-lg, .font-headline-md").forEach(function (node) {
			var label = node.previousElementSibling ? node.previousElementSibling.textContent || "" : "";
			if (label.indexOf("Blockers") >= 0) {
				node.textContent = String(summary.blockers || 0);
			}
			if (label.indexOf("Warnings") >= 0) {
				node.textContent = String(summary.warnings || 0);
			}
		});
		disable_governance_actions(doc);
	}

	function resolve_module_route(row_label) {
		return MODULE_ROW_ROUTES[row_label] || null;
	}

	function hydrate_library_kpis(doc, kpis, health) {
		if (!kpis) {
			return;
		}
		function set_kpi_card(label, value, delta) {
			doc.querySelectorAll(".font-label-caps").forEach(function (node) {
				if ((node.textContent || "").trim() !== label) {
					return;
				}
				var card = node.parentElement;
				if (!card) {
					return;
				}
				var headline = card.querySelector(".font-headline-md");
				if (headline) {
					headline.textContent = String(value);
				}
				if (label === "STD FAMILIES") {
					var delta_node = card.querySelector(".text-status-available");
					if (delta_node) {
						if (delta > 0) {
							delta_node.textContent = "+" + delta + " New";
							delta_node.style.display = "";
						} else {
							delta_node.style.display = "none";
						}
					}
				}
			});
		}
		set_kpi_card("STD FAMILIES", kpis.stdFamilies || 0, kpis.newFamilies || 0);
		set_kpi_card("ACTIVE VERSIONS", kpis.activeVersions || 0);
		set_kpi_card("IN REVIEW", kpis.inReview || 0);
		set_kpi_card("DUE / OVERDUE", kpis.dueOverdue || 0);
		set_kpi_card("BLOCKERS", kpis.blockers || 0);

		if (!health) {
			return;
		}
		var health_rows = {
			"Unauthorized active versions": health.unauthorizedActiveVersions,
			"Pending approvals": health.pendingApprovals,
			"Due for review (30d)": health.dueForReview30d,
			"Superseded in active tenders": health.supersededInActiveTenders,
			"Blocked drafts": health.blockedDrafts,
		};
		doc.querySelectorAll(".space-y-2 > div").forEach(function (row) {
			var label_span = row.querySelector(".text-on-surface-variant");
			var value_span = row.querySelector(".font-bold");
			if (!label_span || !value_span) {
				return;
			}
			var label = (label_span.textContent || "").trim();
			if (Object.prototype.hasOwnProperty.call(health_rows, label)) {
				value_span.textContent = String(health_rows[label]);
			}
		});
	}

	function hydrate_library(doc, payload, ctx) {
		var data = payload.data || {};
		var families = data.families || [];
		var kpis = data.libraryKpis || {};
		var total_families = kpis.stdFamilies || families.length;
		hydrate_library_kpis(doc, kpis, data.libraryHealth);
		hydrate_table_footer(doc, total_families);
		var family = families[0];
		if (!family) {
			return;
		}
		var tbody = doc.querySelector("table tbody");
		var row = hide_extra_rows(tbody, 1);
		if (!row) {
			return;
		}
		var cells = row.querySelectorAll("td");
		if (cells[0]) {
			cells[0].innerHTML =
				'<div class="font-bold text-body-md text-primary">' +
				frappe.utils.escape_html(family.familyName || family.familyCode) +
				'</div><div class="text-[11px] text-on-surface-variant font-body-md">' +
				frappe.utils.escape_html(family.familyCode) +
				"</div>";
		}
		if (cells[1]) {
			cells[1].textContent = family.familyCode;
		}
		if (cells[2]) {
			cells[2].innerHTML =
				'<span class="bg-surface-container-highest text-secondary text-[10px] px-2 py-0.5 font-bold rounded">' +
				frappe.utils.escape_html(family.latestPackageId || ctx.package_id) +
				" (DRAFT)</span>";
		}
		if (cells[6]) {
			cells[6].innerHTML =
				'<span class="bg-surface-container-highest text-secondary text-[10px] px-2 py-0.5 font-bold border border-outline-variant rounded">DRAFT</span>';
		}
		var summary = payload.validationSummary || {};
		if (cells[10]) {
			var blockers = summary.blockers || 0;
			var warnings = summary.warnings || 0;
			if (blockers > 0) {
				cells[10].innerHTML =
					'<div class="flex items-center gap-1 text-error text-[10px] font-bold"><span class="material-symbols-outlined text-[14px]">error</span> ' +
					blockers +
					" BLOCKERS</div>";
			} else if (warnings > 0) {
				cells[10].innerHTML =
					'<div class="flex items-center gap-1 text-status-reserved text-[10px] font-bold"><span class="material-symbols-outlined text-[14px]">warning</span> ' +
					warnings +
					" WARNINGS</div>";
			}
		}
	}

	function hydrate_family_kpis(doc, kpis, usage) {
		if (!kpis) {
			return;
		}
		function set_family_kpi_card(label, value, options) {
			doc.querySelectorAll(".font-label-caps, .text-label-caps").forEach(function (node) {
				if ((node.textContent || "").trim() !== label) {
					return;
				}
				var card = node.parentElement;
				if (!card) {
					return;
				}
				var headline = card.querySelector(".font-headline-md, .text-headline-md");
				if (headline) {
					headline.textContent = String(value);
				}
				if (options && options.badge) {
					var badge = card.querySelector(".bg-primary-fixed, .text-primary-container");
					if (badge) {
						badge.textContent = options.badge;
					}
				}
				if (options && options.subtext) {
					var subtext = card.querySelector(".font-body-sm, .text-body-sm");
					if (subtext) {
						subtext.textContent = options.subtext;
					}
				}
				if (label === "TENDERS USING FAMILY") {
					var trend_wrap = card.querySelector(
						".flex.items-end.justify-between > .flex.items-center, .flex.items-end.justify-between > div.gap-1"
					);
					if (trend_wrap) {
						if (options && options.trendPercent != null) {
							var trend_label = trend_wrap.querySelector(".font-label-caps, .text-label-caps");
							if (trend_label) {
								trend_label.textContent = "+" + options.trendPercent + "%";
							}
							trend_wrap.style.display = "";
						} else {
							trend_wrap.style.display = "none";
						}
					}
				}
				if (label === "PENDING REVIEW" && headline) {
					headline.classList.toggle("text-error", Number(value) > 0);
				}
			});
		}
		set_family_kpi_card("ACTIVE VERSION", kpis.activeVersionLabel || "—", {
			badge: kpis.activeVersionBadge || "DRAFT",
		});
		set_family_kpi_card("TOTAL VERSIONS", kpis.totalVersions || 0, {
			subtext: "Across " + (kpis.releaseCycles || 0) + " cycles",
		});
		set_family_kpi_card("TENDERS USING FAMILY", kpis.tendersUsingFamily || 0, {
			trendPercent: kpis.trendPercent,
		});
		set_family_kpi_card("PENDING REVIEW", kpis.pendingReview || 0);

		if (!usage) {
			return;
		}
		var usage_rows = {
			"Active Tenders": usage.activeTenders,
			"Binding Rate":
				usage.bindingRatePercent != null ? String(usage.bindingRatePercent) + "%" : "—",
			"Avg. Cycle": usage.avgCycleDays != null ? String(usage.avgCycleDays) + " Days" : "—",
		};
		doc.querySelectorAll("h4").forEach(function (heading) {
			if ((heading.textContent || "").trim() !== "USAGE INSIGHTS") {
				return;
			}
			var panel = heading.parentElement;
			if (!panel) {
				return;
			}
			panel.querySelectorAll(".space-y-4 > div, .space-y-4 > .flex").forEach(function (row) {
				var label_span = row.querySelector("span.text-body-sm, span");
				var value_span = row.querySelector(".font-bold");
				if (!label_span || !value_span) {
					return;
				}
				var label = (label_span.textContent || "").trim();
				if (Object.prototype.hasOwnProperty.call(usage_rows, label)) {
					value_span.textContent = String(usage_rows[label]);
				}
			});
		});
	}

	function hydrate_family(doc, payload, ctx) {
		var data = payload.data || {};
		var versions = data.versions || [];
		hydrate_family_kpis(doc, data.familyKpis, data.usageInsights);
		var version = versions[0];
		doc.querySelectorAll("h1, h2, .font-display-lg").forEach(function (node) {
			if ((node.textContent || "").indexOf("KE-PPRA-IT") >= 0) {
				node.textContent = data.familyName || data.familyCode || ctx.family_code;
			}
		});
		var tbody = doc.querySelector("table tbody");
		var row = hide_extra_rows(tbody, versions.length || 1);
		if (!row || !version) {
			hydrate_table_footer(doc, versions.length);
			return;
		}
		var cells = row.querySelectorAll("td");
		if (cells[0]) {
			cells[0].textContent = version.packageId;
		}
		if (cells[1]) {
			cells[1].textContent = version.versionCode || version.packageId;
		}
		if (cells[2]) {
			cells[2].innerHTML =
				'<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-surface-container-highest text-secondary border border-outline-variant/20">' +
				frappe.utils.escape_html(version.lifecycleState || "DRAFT") +
				"</span>";
		}
		if (cells[4]) {
			var blockers = (payload.validationSummary && payload.validationSummary.blockers) || 0;
			if (blockers > 0) {
				cells[4].innerHTML =
					'<div class="flex items-center gap-1.5 text-error"><span class="material-symbols-outlined text-[16px]">error</span><span class="text-body-sm">' +
					blockers +
					" Blockers</span></div>";
			}
		}
		hydrate_table_footer(doc, versions.length);
	}

	function hydrate_version(doc, version_payload, ctx) {
		var data = version_payload.data || {};
		var ctx_data = version_payload.packageContext || {};
		doc.querySelectorAll("h1.font-display-lg, nav span.text-primary.font-bold").forEach(function (node) {
			node.textContent = data.packageId || ctx.package_id;
		});
		var blockers = (version_payload.validationSummary && version_payload.validationSummary.blockers) || 0;
		var warnings = (version_payload.validationSummary && version_payload.validationSummary.warnings) || 0;
		doc.querySelectorAll(".font-label-caps").forEach(function (node) {
			if ((node.textContent || "").indexOf("Blockers /") >= 0) {
				node.textContent = blockers + " Blockers / " + warnings + " Warnings";
			}
		});
		var integrity = doc.querySelector(".bg-status-available\\/5");
		if (integrity) {
			integrity.classList.remove("bg-status-available/5", "border-status-available/20");
			integrity.classList.add("bg-surface-container-low", "border-outline-variant");
		}
	}

	function hydrate_source_doc(doc, payload, ctx) {
		var docs = (payload.data && payload.data.sourceDocuments) || [];
		var doc_row = docs[0];
		if (doc_row) {
			doc.querySelectorAll("h1").forEach(function (node) {
				node.textContent = ctx.package_id + " — Source Documents & Traceability";
			});
			doc.querySelectorAll("span.font-bold, .font-bold").forEach(function (node) {
				if ((node.textContent || "").indexOf(".pdf") >= 0) {
					node.textContent = doc_row.name;
				}
			});
			doc.querySelectorAll("code").forEach(function (node) {
				if ((node.textContent || "").indexOf("...") >= 0 && doc_row.hash) {
					node.textContent = doc_row.hash.slice(0, 8) + "..." + doc_row.hash.slice(-4);
					node.title = doc_row.hash;
				}
			});
		}
		var anchors = (payload.data && payload.data.anchors) || [];
		var anchor_panel = doc.querySelector("table tbody");
		if (anchor_panel && anchors.length) {
			anchor_panel.innerHTML = anchors
				.slice(0, 10)
				.map(function (anchor) {
					return (
						"<tr><td class='px-4 py-3 font-data-mono'>" +
						frappe.utils.escape_html(anchor.code || anchor.id) +
						"</td><td class='px-4 py-3'>" +
						frappe.utils.escape_html(anchor.name || anchor.id) +
						"</td><td class='px-4 py-3'>" +
						frappe.utils.escape_html(String(anchor.pageFrom || "")) +
						"</td></tr>"
					);
				})
				.join("");
		}
		hydrate_table_footer(doc, anchors.length);
	}

	function hydrate_sections(doc, payload, ctx) {
		var sections = (payload.data && payload.data.sections) || [];
		var clauses = (payload.data && payload.data.clauses) || [];
		doc.querySelectorAll(".font-headline-sm.text-primary").forEach(function (node) {
			if ((node.textContent || "").trim() === "4") {
				node.textContent = String(sections.length);
			}
			if ((node.textContent || "").trim() === "28") {
				node.textContent = String(sections.length);
			}
			if ((node.textContent || "").trim() === "142") {
				node.textContent = String(clauses.length);
			}
		});

		function section_row_classes(selected) {
			return (
				"p-2 rounded " +
				(selected
					? "bg-primary/5 text-primary border-l-2 border-primary"
					: "hover:bg-surface-container-low text-on-surface-variant") +
				" text-body-md flex items-center gap-2 cursor-pointer std-prod-section-row"
			);
		}

		function find_section(section_id) {
			for (var i = 0; i < sections.length; i += 1) {
				if (sections[i].id === section_id) {
					return sections[i];
				}
			}
			return sections[0] || null;
		}

		function section_clauses(section_id) {
			return clauses.filter(function (clause) {
				return clause.sectionId === section_id;
			});
		}

		function update_clause_header(section) {
			var header_wrap = doc.querySelector(".flex-1 .bg-surface-container-low .flex.items-center.gap-4");
			if (!header_wrap || !section) {
				return;
			}
			var title_node = header_wrap.querySelector("h4");
			var subtitle_node = header_wrap.querySelector("span.text-body-md");
			if (title_node) {
				title_node.setAttribute("data-testid", "std-prod-clause-map-header");
				title_node.textContent = "Clause Map: " + (section.name || section.code || section.id);
			}
			if (subtitle_node) {
				subtitle_node.setAttribute("data-testid", "std-prod-clause-map-subtitle");
				subtitle_node.textContent =
					(section.code || "") +
					(section.clauseCount != null ? " · " + String(section.clauseCount) + " clauses" : "");
			}
		}

		function render_clause_rows(section_id) {
			var clause_panel = doc.querySelector("table.w-full tbody");
			if (!clause_panel) {
				return;
			}
			var rows = section_clauses(section_id);
			if (!rows.length) {
				clause_panel.innerHTML =
					"<tr><td class='px-4 py-6 text-on-surface-variant' colspan='11'>No clauses mapped for this section.</td></tr>";
				hydrate_table_footer(doc, 0);
				return;
			}
			clause_panel.innerHTML = rows
				.map(function (clause) {
					return (
						"<tr class='std-prod-clause-row zebra-stripe border-b border-outline-variant/30 hover:bg-secondary/5 transition-colors group cursor-pointer' data-clause-id='" +
						frappe.utils.escape_html(clause.id) +
						"'><td class='px-4 py-3 font-data-mono'>" +
						frappe.utils.escape_html(clause.code || clause.id) +
						"</td><td class='px-4 py-3 font-semibold'>" +
						frappe.utils.escape_html(clause.name || clause.id) +
						"</td><td class='px-4 py-3 text-on-surface-variant'>—</td><td class='px-4 py-3 text-on-surface-variant'>—</td><td class='px-4 py-3 text-on-surface-variant'>" +
						frappe.utils.escape_html(clause.sourceAnchorId || "—") +
						"</td><td class='px-4 py-3 text-on-surface-variant'>—</td><td class='px-4 py-3 text-on-surface-variant'>—</td><td class='px-4 py-3 text-on-surface-variant'>—</td><td class='px-4 py-3 text-on-surface-variant'>—</td><td class='px-4 py-3 text-on-surface-variant'>—</td><td class='px-4 py-3 text-right'><button class='text-primary font-bold hover:underline std-prod-clause-open'>Open</button></td></tr>"
					);
				})
				.join("");
			clause_panel.querySelectorAll(".std-prod-clause-row").forEach(function (row) {
				row.addEventListener("click", function () {
					kentender.std_prod.navigate("std-clause-detail", {
						package_id: ctx.package_id,
						family_code: ctx.family_code,
						clause_key: row.getAttribute("data-clause-id"),
					});
				});
			});
			hydrate_table_footer(doc, rows.length);
		}

		function render_section_tree(selected_section_id) {
			var tree = doc.querySelector(".tree-container");
			if (!tree) {
				return;
			}
			tree.innerHTML = sections
				.map(function (section) {
					var selected = section.id === selected_section_id;
					return (
						'<div class="' +
						section_row_classes(selected) +
						'" data-testid="std-prod-section-row" data-section-id="' +
						frappe.utils.escape_html(section.id) +
						'"><span class="material-symbols-outlined text-[16px]">description</span>' +
						frappe.utils.escape_html(section.name || section.code) +
						"</div>"
					);
				})
				.join("");
			tree.querySelectorAll(".std-prod-section-row").forEach(function (row) {
				row.addEventListener("click", function (event) {
					event.preventDefault();
					event.stopPropagation();
					select_section(row.getAttribute("data-section-id"));
				});
			});
		}

		function select_section(section_id) {
			var section = find_section(section_id);
			if (!section) {
				return;
			}
			doc.__stdProdSelectedSectionId = section.id;
			render_section_tree(section.id);
			update_clause_header(section);
			render_clause_rows(section.id);
		}

		doc.__stdProdSectionsState = {
			sections: sections,
			clauses: clauses,
			selectSection: select_section,
		};

		var initial_section_id = sections.length ? sections[0].id : "";
		if (initial_section_id) {
			select_section(initial_section_id);
		}
	}

	function hydrate_clause(doc, payload, ctx) {
		var data = payload.data || {};
		var metadata = data.metadata || {};
		var business_code = data.code || metadata.clause_code || "";
		var clause_name = data.name || metadata.display_title || business_code || "Clause Detail";
		var section_label = data.sectionTitle || "";

		var identity_section = doc.querySelector("section.bg-white.border.border-border-subtle.rounded-lg.p-6");
		var badge = identity_section && identity_section.querySelector("span.bg-primary.text-on-primary");
		if (badge) {
			badge.textContent = business_code;
			badge.setAttribute("data-testid", "std-prod-clause-code");
		}
		var section_node =
			identity_section &&
			identity_section.querySelector("span.text-on-surface-variant.font-label-caps");
		if (section_node) {
			section_node.textContent = section_label;
			section_node.setAttribute("data-testid", "std-prod-clause-section");
		}
		var title = identity_section && identity_section.querySelector("h1.font-headline-lg");
		if (title) {
			title.textContent = clause_name;
			title.setAttribute("data-testid", "std-prod-clause-title");
		}
		var desc = identity_section && identity_section.querySelector("p.text-on-surface-variant.font-body-md");
		if (desc) {
			desc.textContent =
				data.description ||
				data.textStatus ||
				data.validationStatus ||
				"Clause metadata loaded from STD package.";
		}

		doc.querySelectorAll("span.font-data-mono").forEach(function (node) {
			var label = (node.textContent || "").trim();
			if (label.indexOf("UUID:") === 0) {
				node.textContent = business_code ? "Clause: " + business_code : "Clause";
				node.setAttribute("data-testid", "std-prod-clause-ref");
			}
		});

		var legal_panel = doc.querySelector("section .p-6.bg-slate-50");
		if (legal_panel) {
			legal_panel.setAttribute("data-testid", "std-prod-clause-legal-text");
			var clause_text = (data.clauseText || "").trim();
			if (clause_text) {
				legal_panel.innerHTML =
					"<p class='mb-4 whitespace-pre-wrap'>" + frappe.utils.escape_html(clause_text) + "</p>";
			} else {
				legal_panel.innerHTML =
					"<p class='text-on-surface-variant italic'>" +
					frappe.utils.escape_html(
						"Full legal text is not yet extracted for this clause in Milestone 1. Showing title and traceability metadata only.",
					) +
					"</p><p class='mt-4 font-semibold text-on-surface'>" +
					frappe.utils.escape_html(clause_name) +
					"</p>";
			}
		}

		var traceability_panel = doc.querySelector("section .bg-primary-container.text-on-primary-container");
		if (traceability_panel) {
			var trace_root = traceability_panel.parentElement;
			if (trace_root) {
				trace_root.querySelectorAll("div.flex.items-center.justify-between").forEach(function (row) {
					var label_node = row.querySelector("span.text-xs.text-on-surface-variant");
					var value_node = row.querySelector("span.text-xs.font-bold, span.text-xs.font-data-mono");
					if (!label_node || !value_node) {
						return;
					}
					var label = (label_node.textContent || "").trim();
					if (label === "Source Anchor") {
						value_node.textContent = business_code || data.sourceAnchorId || "—";
					}
					if (label === "Source Document") {
						value_node.textContent =
							(ctx.package_id || "") + " / Official IT STD Source PDF";
					}
					if (label === "Verification Level") {
						value_node.textContent = data.mutabilityType
							? String(data.mutabilityType).replace(/_/g, " ")
							: value_node.textContent;
					}
				});
			}
		}

		var render_preview_body = doc.querySelector("section .p-8.bg-white.m-4.border");
		if (render_preview_body) {
			render_preview_body.innerHTML =
				"<div class='max-w-[650px] mx-auto text-on-surface-variant italic text-sm'>" +
				frappe.utils.escape_html(
					"Render preview is not available until full clause text and render blocks are wired for this clause.",
				) +
				"</div>";
		}
		if (doc.body) {
			doc.body.setAttribute("data-std-clause-key", data.id || ctx.clause_key || "");
		}
	}

	function hydrate_validation(doc, payload, ctx) {
		var data = payload.data || {};
		var summary = data.summary || payload.validationSummary || {};
		doc.querySelectorAll(".font-headline-lg.text-primary").forEach(function (node) {
			var label = (node.previousElementSibling && node.previousElementSibling.textContent) || "";
			if (label.indexOf("Total Findings") >= 0) {
				node.textContent = String(data.count || 0);
			}
			if (label.indexOf("Blockers") >= 0) {
				node.textContent = String(summary.blockers || 0);
			}
			if (label.indexOf("Warnings") >= 0) {
				node.textContent = String(summary.warnings || 0);
			}
		});
		var run = data.validationRun || {};
		doc.querySelectorAll(".font-data-mono").forEach(function (node) {
			if ((node.textContent || "").indexOf("VR-") === 0 && run.runKey) {
				node.textContent = run.runKey;
			}
		});
		var tbody = doc.querySelector("table tbody");
		var findings = data.findings || [];
		if (tbody && findings.length) {
			tbody.innerHTML = findings
				.map(function (finding) {
					return (
						"<tr><td class='px-4 py-3 font-data-mono'>" +
						frappe.utils.escape_html(finding.code || finding.id) +
						"</td><td class='px-4 py-3'>" +
						frappe.utils.escape_html(finding.severity || "") +
						"</td><td class='px-4 py-3'>" +
						frappe.utils.escape_html(finding.name || "") +
						"</td><td class='px-4 py-3 font-data-mono'>" +
						frappe.utils.escape_html(finding.objectId || "") +
						"</td></tr>"
					);
				})
				.join("");
		}
		hydrate_table_footer(doc, data.count || findings.length);
	}

	function hydrate_audit(doc, payload, ctx) {
		var events = (payload.data && payload.data.events) || [];
		var tbody = doc.querySelector("table tbody");
		if (!tbody) {
			return;
		}
		if (!events.length) {
			tbody.innerHTML =
				"<tr><td colspan='10' class='px-4 py-6 text-on-surface-variant'>No audit events recorded for this package.</td></tr>";
			hydrate_table_footer(doc, (payload.pagination && payload.pagination.total) || 0);
			return;
		}
		tbody.innerHTML = events
			.map(function (event) {
				return (
					"<tr><td class='px-4 py-3 font-data-mono whitespace-nowrap'>" +
					frappe.utils.escape_html(event.occurredAt || "") +
					"</td><td class='px-4 py-3'>" +
					frappe.utils.escape_html(event.actor || "system") +
					"</td><td class='px-4 py-3'>" +
					frappe.utils.escape_html(event.eventType || "") +
					"</td><td class='px-4 py-3'>" +
					frappe.utils.escape_html(event.objectType || "") +
					"</td><td class='px-4 py-3 font-data-mono text-primary'>" +
					frappe.utils.escape_html(event.objectId || "") +
					"</td><td class='px-4 py-3'>—</td><td class='px-4 py-3'>—</td><td class='px-4 py-3'>—</td><td class='px-4 py-3 font-data-mono'>—</td><td class='px-4 py-3 text-center'>—</td></tr>"
				);
			})
			.join("");
		hydrate_table_footer(doc, (payload.pagination && payload.pagination.total) || events.length);
	}

	var HYDRATORS = {
		library: function (doc, results, ctx) {
			hydrate_library(doc, results.families, ctx);
		},
		family: function (doc, results, ctx) {
			hydrate_family(doc, results.family, ctx);
		},
		version: function (doc, results, ctx) {
			hydrate_version(doc, results.version, ctx);
			var events = (results.audit && results.audit.data && results.audit.data.events) || [];
			var audit_tbody = doc.querySelectorAll("table tbody")[1];
			if (audit_tbody && events.length) {
				audit_tbody.innerHTML = events
					.slice(0, 3)
					.map(function (event) {
						return (
							"<tr class='text-body-sm'><td class='px-4 py-4 font-semibold text-on-surface'>" +
							frappe.utils.escape_html(event.eventType || "") +
							"</td><td class='px-4 py-4 text-on-surface-variant'>" +
							frappe.utils.escape_html(event.actor || "system") +
							"</td><td class='px-4 py-4 font-data-mono text-secondary'>" +
							frappe.utils.escape_html(event.occurredAt || "") +
							"</td><td class='px-4 py-4 font-data-mono text-[11px] text-secondary'>" +
							frappe.utils.escape_html(event.objectId || "") +
							"</td></tr>"
						);
					})
					.join("");
			}
		},
		source: function (doc, results, ctx) {
			hydrate_source_doc(doc, results.source, ctx);
		},
		sections: function (doc, results, ctx) {
			hydrate_sections(doc, results.sections, ctx);
		},
		clause: function (doc, results, ctx) {
			hydrate_clause(doc, results.clause, ctx);
		},
		validation: function (doc, results, ctx) {
			hydrate_validation(doc, results.validation, ctx);
		},
		audit: function (doc, results, ctx) {
			hydrate_audit(doc, results.audit, ctx);
		},
		parameters: function (doc, results, ctx) {
			hydrate_parameters(doc, results.parameters, ctx);
		},
		parameter: function (doc, results, ctx) {
			hydrate_parameter(doc, results.parameter, ctx);
		},
		rules: function (doc, results, ctx) {
			hydrate_rules(doc, results.rules, ctx);
		},
		rule: function (doc, results, ctx) {
			hydrate_rule(doc, results.rule, ctx);
		},
		forms: function (doc, results, ctx) {
			hydrate_forms(doc, results.forms, ctx);
		},
		form: function (doc, results, ctx) {
			hydrate_form(doc, results.form, ctx);
		},
		requirements: function (doc, results, ctx) {
			hydrate_requirements(doc, results.requirements, ctx);
		},
		priceSchedules: function (doc, results, ctx) {
			hydrate_price_schedules(doc, results.priceSchedules, ctx);
		},
		evaluation: function (doc, results, ctx) {
			hydrate_evaluation(doc, results.evaluation, ctx);
		},
		renderBlocks: function (doc, results, ctx) {
			hydrate_render_blocks(doc, results.renderBlocks, ctx);
		},
		usage: function (doc, results, ctx) {
			hydrate_usage(doc, results.usage, ctx);
		},
		importReview: function (doc, results, ctx) {
			hydrate_import_review(doc, results.importReview, ctx);
			disable_governance_actions(doc);
		},
		versionDiff: function (doc, results, ctx) {
			hydrate_version_diff(doc, results.versionDiff, ctx);
			disable_governance_actions(doc);
		},
		review: function (doc, results, ctx) {
			hydrate_review(doc, results, ctx);
		},
	};

	function fetch_screen_data(screen, ctx) {
		var package_id = ctx.package_id;
		if (screen === "library") {
			return call_read("get_std_families").then(function (r) {
				return { families: r.message };
			});
		}
		if (screen === "family") {
			return call_read("get_std_family", { family_code: ctx.family_code }).then(function (r) {
				return { family: r.message };
			});
		}
		if (screen === "version") {
			return Promise.all([
				call_read("get_std_version", { package_id: package_id }),
				call_read("get_std_version_audit_log", { package_id: package_id, limit: 3 }),
			]).then(function (responses) {
				return { version: responses[0].message, audit: responses[1].message };
			});
		}
		if (screen === "source") {
			return call_read("get_std_version_source_traceability", { package_id: package_id }).then(function (r) {
				return { source: r.message };
			});
		}
		if (screen === "sections") {
			return call_read("get_std_version_sections", { package_id: package_id }).then(function (r) {
				return { sections: r.message };
			});
		}
		if (screen === "clause") {
			var clause_key = ctx.clause_key;
			return call_read("get_std_version_sections", { package_id: package_id }).then(function (r) {
				var clauses = (r.message.data && r.message.data.clauses) || [];
				if (!clause_key && clauses.length) {
					clause_key = clauses[0].id;
				}
				if (!clause_key) {
					return { clause: { data: {}, packageContext: r.message.packageContext } };
				}
				return call_read("get_std_clause", { clause_key: clause_key }).then(function (cr) {
					return { clause: cr.message };
				});
			});
		}
		if (screen === "validation") {
			return call_read("get_std_version_validation_report", { package_id: package_id }).then(function (r) {
				return { validation: r.message };
			});
		}
		if (screen === "audit") {
			return call_read("get_std_version_audit_log", { package_id: package_id }).then(function (r) {
				return { audit: r.message };
			});
		}
		if (screen === "parameters") {
			return call_read("get_std_version_parameters", { package_id: package_id }).then(function (r) {
				return { parameters: r.message };
			});
		}
		if (screen === "parameter") {
			return call_read("get_std_version_parameters", { package_id: package_id }).then(function (r) {
				var params = (r.message.data && r.message.data.parameters) || [];
				var key = ctx.parameter_key || (params[0] && params[0].id);
				if (!key) {
					return { parameter: { data: {}, packageContext: r.message.packageContext } };
				}
				return call_read("get_std_parameter", { parameter_key: key }).then(function (pr) {
					return { parameter: pr.message };
				});
			});
		}
		if (screen === "rules") {
			return call_read("get_std_version_rules", { package_id: package_id }).then(function (r) {
				return { rules: r.message };
			});
		}
		if (screen === "rule") {
			return call_read("get_std_version_rules", { package_id: package_id }).then(function (r) {
				var rules = (r.message.data && r.message.data.rules) || [];
				var key = ctx.rule_key || (rules[0] && rules[0].id);
				if (!key) {
					return { rule: { data: {}, packageContext: r.message.packageContext } };
				}
				return call_read("get_std_rule", { rule_key: key }).then(function (rr) {
					return { rule: rr.message };
				});
			});
		}
		if (screen === "forms") {
			return call_read("get_std_version_forms", { package_id: package_id }).then(function (r) {
				return { forms: r.message };
			});
		}
		if (screen === "form") {
			return call_read("get_std_version_forms", { package_id: package_id }).then(function (r) {
				var forms = (r.message.data && r.message.data.forms) || [];
				var key = ctx.form_key || (forms[0] && forms[0].id);
				if (!key) {
					return { form: { data: {}, packageContext: r.message.packageContext } };
				}
				return call_read("get_std_form", { form_key: key }).then(function (fr) {
					return { form: fr.message };
				});
			});
		}
		if (screen === "requirements") {
			return call_read("get_std_version_requirements", { package_id: package_id }).then(function (r) {
				return { requirements: r.message };
			});
		}
		if (screen === "priceSchedules") {
			return call_read("get_std_version_price_schedules", { package_id: package_id }).then(function (r) {
				return { priceSchedules: r.message };
			});
		}
		if (screen === "evaluation") {
			return call_read("get_std_version_evaluation_schema", { package_id: package_id }).then(function (r) {
				return { evaluation: r.message };
			});
		}
		if (screen === "renderBlocks") {
			return call_read("get_std_version_render_blocks", { package_id: package_id }).then(function (r) {
				return { renderBlocks: r.message };
			});
		}
		if (screen === "usage") {
			return call_read("get_std_version_usage_bindings", { package_id: package_id }).then(function (r) {
				return { usage: r.message };
			});
		}
		if (screen === "importReview") {
			if (ctx.import_run_key) {
				return call_read("get_std_import_run", { import_run_key: ctx.import_run_key }).then(function (r) {
					return { importReview: r.message };
				});
			}
			return call_read("get_std_version_import_runs", { package_id: package_id }).then(function (r) {
				var runs = (r.message.data && r.message.data.importRuns) || [];
				var latest = runs[0];
				if (!latest || !latest.id) {
					return { importReview: { data: { importRun: {} }, packageContext: r.message.packageContext } };
				}
				return call_read("get_std_import_run", { import_run_key: latest.id }).then(function (ir) {
					return { importReview: ir.message };
				});
			});
		}
		if (screen === "versionDiff") {
			return call_read("get_std_version_diff", { package_id: package_id }).then(function (r) {
				return { versionDiff: r.message };
			});
		}
		if (screen === "review") {
			return Promise.all([
				call_read("get_std_version", { package_id: package_id }),
				call_read("get_std_version_validation_report", { package_id: package_id }),
				call_read("get_std_version_audit_log", { package_id: package_id, limit: 5 }),
			]).then(function (responses) {
				return {
					version: responses[0].message,
					validation: responses[1].message,
					audit: responses[2].message,
				};
			});
		}
		return Promise.resolve({});
	}

	function wire_navigation(screen, iframe, ctx) {
		function apply() {
			var doc = iframe.contentDocument;
			if (!doc) {
				return;
			}
			wire_navigation_doc(screen, doc, ctx);
		}
		iframe.addEventListener("load", apply);
		try {
			if (iframe.contentDocument && iframe.contentDocument.readyState === "complete") {
				apply();
			}
		} catch (err) {
			// Ignore until load event fires.
		}
	}

	function normalize_control_text(value) {
		return String(value || "").replace(/\s+/g, " ").trim();
	}

	function closest_button_text(target) {
		var btn = target && target.closest ? target.closest("button") : null;
		return btn ? normalize_control_text(btn.textContent) : "";
	}

	function button_contains_label(target, label) {
		var needle = normalize_control_text(label);
		if (!needle) {
			return false;
		}
		return closest_button_text(target).indexOf(needle) >= 0;
	}

	function wire_navigation_doc(screen, doc, ctx) {
		if (!doc || !doc.body || doc.body.dataset.stdProdNavScreen === screen) {
			return;
		}
		doc.body.dataset.stdProdNavScreen = screen;
		doc.body.addEventListener(
			"click",
			function (event) {
				var target = event.target && event.target.closest ? event.target.closest("button, a, tr, span") : null;
				if (!target) {
					return;
				}
				var text = (target.textContent || "").trim();

				if (screen === "library") {
					var open_btn = target.closest("button");
					if (open_btn && text === "Open") {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-family-detail", ctx);
					}
					return;
				}

				if (screen === "family") {
					var family_btn = target.closest("button");
					if (!family_btn) {
						return;
					}
					var icon = family_btn.querySelector(".material-symbols-outlined");
					if (icon) {
						var icon_name = (icon.textContent || "").trim();
						if (["open_in_new", "edit", "visibility"].indexOf(icon_name) !== -1) {
							event.preventDefault();
							event.stopPropagation();
							navigate("std-version-detail", ctx);
						}
					}
					return;
				}

				if (screen === "version") {
					if (
						button_contains_label(target, "View Audit Trail") ||
						button_contains_label(target, "Full Audit Log")
					) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-audit-log", ctx);
						return;
					}
					if (button_contains_label(target, "View Usage")) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-usage-and-tender-bindings", ctx);
						return;
					}
					if (button_contains_label(target, "Validation")) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-validation-report", ctx);
						return;
					}
					if (button_contains_label(target, "Traceability")) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-source-doc", ctx);
						return;
					}
					if (button_contains_label(target, "Supersede")) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-version-diff-and-supersession", ctx);
						return;
					}
					var version_row = target.closest("tr");
					if (version_row) {
						var label = version_row.querySelector(".font-semibold, .font-body-md.font-semibold");
						var name = label ? (label.textContent || "").trim() : "";
						var route = resolve_module_route(name);
						if (route) {
							event.preventDefault();
							event.stopPropagation();
							navigate(route, ctx);
							return;
						}
						if (name === "Sections & Containers" || name === "Standard Clauses") {
							event.preventDefault();
							event.stopPropagation();
							navigate("std-section-clauses", ctx);
						}
					}
					return;
				}

				if (screen === "parameters") {
					var param_row = target.closest(".std-prod-param-row");
					if (param_row) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-parameter-detail", {
							package_id: ctx.package_id,
							family_code: ctx.family_code,
							parameter_key: param_row.getAttribute("data-parameter-key"),
						});
						return;
					}
					var open_btn = target.closest("button");
					if (open_btn && (text === "Open" || open_btn.querySelector(".material-symbols-outlined"))) {
						var row = open_btn.closest(".std-prod-param-row");
						if (row) {
							event.preventDefault();
							event.stopPropagation();
							navigate("std-parameter-detail", {
								package_id: ctx.package_id,
								family_code: ctx.family_code,
								parameter_key: row.getAttribute("data-parameter-key"),
							});
						}
						return;
					}
					if (text.indexOf("Rule Dictionary") >= 0 || target.closest('[title="View Rules"]')) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-rule-dictionary", ctx);
					}
					return;
				}

				if (screen === "rules") {
					var rule_row = target.closest(".std-prod-rule-row");
					if (rule_row) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-rule-detail", {
							package_id: ctx.package_id,
							family_code: ctx.family_code,
							rule_key: rule_row.getAttribute("data-rule-key"),
						});
					}
					return;
				}

				if (screen === "forms") {
					var form_row = target.closest(".std-prod-form-row");
					if (form_row) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-form-detail-field-builder", {
							package_id: ctx.package_id,
							family_code: ctx.family_code,
							form_key: form_row.getAttribute("data-form-key"),
						});
					}
					return;
				}

				var cross_route = SCHEMA_CROSS_LINKS[text];
				if (cross_route && ["parameters", "rules", "forms", "requirements", "priceSchedules", "evaluation", "renderBlocks", "versionDiff", "importReview", "usage", "review"].indexOf(screen) !== -1) {
					event.preventDefault();
					event.stopPropagation();
					navigate(cross_route, ctx);
					return;
				}

				if (screen === "sections") {
					var section_row =
						event.target && event.target.closest
							? event.target.closest(".std-prod-section-row")
							: null;
					if (section_row && doc.__stdProdSectionsState) {
						event.preventDefault();
						event.stopPropagation();
						doc.__stdProdSectionsState.selectSection(section_row.getAttribute("data-section-id"));
						return;
					}
					var sections_btn = target.closest("button");
					if (!sections_btn) {
						return;
					}
					var sections_text = normalize_control_text(sections_btn.textContent);
					if (sections_text.indexOf("SOURCE TRACEABILITY") >= 0) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-source-doc", ctx);
					} else if (sections_text.indexOf("VIEW VALIDATION") >= 0) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-validation-report", ctx);
					} else if (sections_text.indexOf("AUDIT TRAIL") >= 0) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-audit-log", ctx);
					}
				}
			},
			true,
		);
	}

	function should_refresh_on_show(screen, iframe, fresh_ctx) {
		if (!iframe || ["clause", "parameter", "rule", "form"].indexOf(screen) === -1) {
			return false;
		}
		var doc = iframe.contentDocument;
		if (!doc || !doc.body || doc.body.getAttribute("data-std-prod-hydrated") !== "1") {
			return false;
		}
		if (screen === "clause") {
			var last_clause_key = doc.body.getAttribute("data-std-clause-key") || "";
			var next_clause_key = fresh_ctx.clause_key || "";
			return Boolean(next_clause_key) && last_clause_key !== next_clause_key;
		}
		if (screen === "parameter") {
			var last_parameter_key = doc.body.getAttribute("data-std-parameter-key") || "";
			var next_parameter_key = fresh_ctx.parameter_key || "";
			return Boolean(next_parameter_key) && last_parameter_key !== next_parameter_key;
		}
		if (screen === "rule") {
			var last_rule_key = doc.body.getAttribute("data-std-rule-key") || "";
			var next_rule_key = fresh_ctx.rule_key || "";
			return Boolean(next_rule_key) && last_rule_key !== next_rule_key;
		}
		var last_form_key = doc.body.getAttribute("data-std-form-key") || "";
		var next_form_key = fresh_ctx.form_key || "";
		return Boolean(next_form_key) && last_form_key !== next_form_key;
	}

	function hydrate_iframe(screen, iframe, ctx, page_title) {
		var doc = iframe.contentDocument;
		if (!doc) {
			return;
		}
		install_hydration_gate(doc);
		fetch_screen_data(screen, ctx)
			.then(function (results) {
				replace_mock_identities(doc, ctx);
				hydrate_page_header(doc, page_title);
				apply_read_only_banner(doc, ctx);
				disable_governance_actions(doc);
				var hydrator = HYDRATORS[screen];
				if (hydrator) {
					hydrator(doc, results, ctx);
				}
				wire_navigation_doc(screen, doc, ctx);
				mark_hydrated(doc, ctx);
			})
			.catch(function (err) {
				hydrate_page_header(doc, page_title);
				mark_hydration_failed(doc);
				frappe.msgprint({
					title: __("STD read API failed"),
					indicator: "red",
					message: (err && err.message) || __("Unable to load STD data."),
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
		var shell_class = config.shell_class;
		document.body.classList.add(shell_class);

		var root = page.main.get(0);
		if (!root) {
			return;
		}
		var testid = config.testid;
		root.className = config.root_class;
		root.setAttribute("data-testid", testid + "-root");
		root.innerHTML =
			'<section class="' +
			shell_class +
			'" data-testid="' +
			testid +
			'-shell">' +
			'<iframe class="' +
			config.iframe_class +
			'" data-testid="' +
			testid +
			'-iframe" src="' +
			config.asset +
			'" title="' +
			frappe.utils.escape_html(config.title) +
			'"></iframe></section>';

		var iframe = root.querySelector("iframe");
		var ctx = get_context();
		prepare_iframe_frame(iframe);
		wire_navigation(config.screen, iframe, ctx);
		function run_hydration() {
			hydrate_iframe(config.screen, iframe, ctx, config.title);
		}
		iframe.addEventListener("load", run_hydration);
		try {
			if (iframe.contentDocument && iframe.contentDocument.readyState === "complete") {
				run_hydration();
			}
		} catch (err) {
			// Cross-origin guard — load event will hydrate when ready.
		}

		frappe.pages[config.page].on_page_show = function () {
			document.body.classList.add(shell_class);
			preserve_procurement_sidebar();
			var fresh_ctx = get_context();
			if (should_refresh_on_show(config.screen, iframe, fresh_ctx)) {
				hydrate_iframe(config.screen, iframe, fresh_ctx, config.title);
			}
		};
		frappe.pages[config.page].on_page_hide = function () {
			document.body.classList.remove(shell_class);
		};
	}

	kentender.std_prod.DEFAULT_FAMILY_CODE = DEFAULT_FAMILY;
	kentender.std_prod.DEFAULT_PACKAGE_ID = DEFAULT_PACKAGE;
	kentender.std_prod.get_context = get_context;
	kentender.std_prod.set_context = set_context;
	kentender.std_prod.navigate = navigate;
	kentender.std_prod.mount_page = mount_page;
	kentender.std_prod.hydrate_iframe = hydrate_iframe;
	kentender.std_prod.claim_page_routes_over_doctype_conflicts =
		claim_page_routes_over_doctype_conflicts;
	kentender.std_prod.install_route_conflict_guard = install_route_conflict_guard;
	kentender.std_prod.preserve_procurement_sidebar = preserve_procurement_sidebar;
	kentender.std_prod.hydrate_table_footer = hydrate_table_footer;
	kentender.std_prod.install_hydration_gate = install_hydration_gate;
	kentender.std_prod.hydrate_page_header = hydrate_page_header;

	install_route_conflict_guard();
	$(document).on("app_ready", claim_page_routes_over_doctype_conflicts);
})();
