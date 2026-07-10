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
		"Parameter Dictionary": "std-parameter-dictionary",
		"Rule Dictionary": "std-rule-dictionary",
		"Requirements Schema": "std-requirement-schema-manager",
		"Price Schedule Schema": "std-price-schedule-schema",
		"Form Schema Manager": "std-form-schema-manager",
		"Evaluation Schema": "std-evaluation-schema",
		"Render Blocks": "std-render-blocks",
	};

	var MODULE_ROW_MAP_FOCUS = {
		"Sections & Containers": "sections",
		"Standard Clauses": "clauses",
	};

	// Canonical Desk page slugs for STD prod navigation (must match hooks.page_js + Page records).
	var STD_PROD_REGISTERED_ROUTES = [
		"std-library",
		"std-family-detail",
		"std-version-detail",
		"std-source-doc",
		"std-section-clauses",
		"std-clause-detail",
		"std-validation-report",
		"std-audit-log",
		"std-parameter-dictionary",
		"std-parameter-detail",
		"std-rule-dictionary",
		"std-rule-detail",
		"std-form-schema-manager",
		"std-form-detail-field-builder",
		"std-requirement-schema-manager",
		"std-price-schedule-schema",
		"std-evaluation-schema",
		"std-render-blocks",
		"std-review-and-approval",
		"std-usage-and-tender-bindings",
		"std-import-package-review",
		"std-version-diff-and-supersession",
	];

	var STD_PROD_ROUTE_ALIASES = {
		"std-section-clause-map": "std-section-clauses",
	};

	var SCHEMA_ACTION_TITLE_ROUTES = {
		"View Source": "std-source-doc",
		"View Source Section": "std-source-doc",
		"View Usage": "std-usage-and-tender-bindings",
		"View Rules": "std-rule-dictionary",
		"View Data Bindings": "std-parameter-dictionary",
		"View Render Test": "std-validation-report",
		"View Affected Objects": "std-parameter-dictionary",
		"View Test Coverage": "std-validation-report",
		"View Line Schema": "std-source-doc",
		"View Formula": "std-source-doc",
		"Preview Price Form": "std-source-doc",
		"Compare Previous Version": "std-version-diff-and-supersession",
		"Preview Output": "std-section-clauses",
		"Preview Form": "std-form-detail-field-builder",
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
			version_code: opts.version_code || "",
			lifecycle_state: opts.lifecycle_state || "",
			clause_key: opts.clause_key || "",
			parameter_key: opts.parameter_key || "",
			filter_parameter_key: opts.filter_parameter_key || "",
			rule_key: opts.rule_key || "",
			form_key: opts.form_key || "",
			import_run_key: opts.import_run_key || "",
			map_focus: opts.map_focus || "",
		};
	}

	function sync_context_from_package_context(package_context, ctx) {
		if (!package_context) {
			return ctx;
		}
		var next = Object.assign({}, ctx || get_context());
		if (package_context.familyCode) {
			next.family_code = package_context.familyCode;
		}
		if (package_context.packageId) {
			next.package_id = package_context.packageId;
		}
		if (package_context.versionCode) {
			next.version_code = package_context.versionCode;
		}
		if (package_context.lifecycleState) {
			next.lifecycle_state = package_context.lifecycleState;
		}
		set_context(next);
		return next;
	}

	var STD_PROD_BREADCRUMB_CLASS =
		"bg-surface-container-low px-section-gap py-2 border-b border-outline-variant flex items-center gap-2 text-[11px] font-label-caps text-on-surface-variant";

	function is_top_chrome_nav(node) {
		if (!node || node.tagName !== "NAV") {
			return false;
		}
		var cls = node.className || "";
		return cls.indexOf("fixed") >= 0 || cls.indexOf("sticky") >= 0 || cls.indexOf("top-0") >= 0;
	}

	function find_legacy_breadcrumb_nav(doc) {
		var candidates = doc.querySelectorAll("main nav, body > nav");
		for (var i = 0; i < candidates.length; i++) {
			var node = candidates[i];
			if (node.getAttribute("data-std-prod-breadcrumb") === "1" || is_top_chrome_nav(node)) {
				continue;
			}
			var text = (node.textContent || "").trim();
			if (
				text.indexOf("chevron_right") >= 0 ||
				/STD Library|Dictionary|Schema Manager|Clause Map|Traceability|Validation Report|Audit Log/i.test(text)
			) {
				return node;
			}
		}
		return null;
	}

	function ensure_breadcrumb_nav(doc) {
		if (!doc || !doc.body) {
			return null;
		}
		var nav = doc.querySelector("nav[data-std-prod-breadcrumb='1']");
		if (!nav) {
			nav = find_legacy_breadcrumb_nav(doc);
		}
		if (!nav) {
			nav = doc.createElement("nav");
		}
		nav.setAttribute("data-std-prod-breadcrumb", "1");
		nav.setAttribute("data-testid", "std-prod-breadcrumb");
		nav.className = STD_PROD_BREADCRUMB_CLASS;
		var insert_before =
			doc.querySelector("body > header") ||
			doc.querySelector("body > nav.fixed") ||
			doc.querySelector("body > nav.sticky") ||
			doc.body.firstChild;
		if (insert_before && insert_before !== nav) {
			doc.body.insertBefore(nav, insert_before);
		} else if (doc.body.firstChild !== nav) {
			doc.body.insertBefore(nav, doc.body.firstChild);
		}
		return nav;
	}

	function remove_inline_breadcrumb_navs(doc, keep_nav) {
		doc.querySelectorAll("main nav, body > main nav").forEach(function (node) {
			if (node === keep_nav) {
				return;
			}
			var text = (node.textContent || "").trim();
			if (text.indexOf("chevron_right") >= 0 || /Dictionary|STD Library|Clause Map/i.test(text)) {
				node.remove();
			}
		});
	}

	function version_scope_segments(ctx, options) {
		options = options || {};
		var family = ctx.family_code || DEFAULT_FAMILY;
		var package_id = ctx.package_id || DEFAULT_PACKAGE;
		var segments = [
			{ label: "STD Library", route: "std-library" },
			{ label: family, route: "std-family-detail", family_code: family },
		];
		if (options.include_version !== false) {
			var version_segment = {
				label: package_id,
				family_code: family,
				package_id: package_id,
			};
			if (!options.version_as_leaf) {
				version_segment.route = "std-version-detail";
			}
			segments.push(version_segment);
		}
		return segments;
	}

	function breadcrumb_segment_attrs(segment, ctx) {
		var family = segment.family_code || ctx.family_code || DEFAULT_FAMILY;
		var package_id = segment.package_id || ctx.package_id || DEFAULT_PACKAGE;
		var attrs =
			'class="hover:text-primary transition-colors std-prod-breadcrumb-link" href="#" data-std-breadcrumb-target="' +
			frappe.utils.escape_html(segment.route) +
			'"';
		if (segment.route !== "std-library") {
			attrs += ' data-std-breadcrumb-family="' + frappe.utils.escape_html(family) + '"';
		}
		if (
			[
				"std-version-detail",
				"std-parameter-dictionary",
				"std-parameter-detail",
				"std-rule-dictionary",
				"std-rule-detail",
				"std-form-schema-manager",
				"std-form-detail-field-builder",
				"std-requirement-schema-manager",
				"std-price-schedule-schema",
				"std-evaluation-schema",
				"std-render-blocks",
				"std-section-clauses",
				"std-clause-detail",
				"std-source-doc",
				"std-validation-report",
				"std-audit-log",
				"std-usage-and-tender-bindings",
				"std-import-package-review",
				"std-version-diff-and-supersession",
				"std-review-and-approval",
			].indexOf(segment.route) >= 0
		) {
			attrs += ' data-std-breadcrumb-package="' + frappe.utils.escape_html(package_id) + '"';
		}
		if (segment.map_focus) {
			attrs += ' data-std-breadcrumb-map-focus="' + frappe.utils.escape_html(segment.map_focus) + '"';
		}
		return attrs;
	}

	function render_breadcrumb_trail(doc, ctx, segments) {
		var nav = ensure_breadcrumb_nav(doc);
		if (!nav || !segments || !segments.length) {
			return;
		}
		var parts = [];
		segments.forEach(function (segment, index) {
			if (index > 0) {
				parts.push('<span class="material-symbols-outlined text-[14px]">chevron_right</span>');
			}
			if (segment.route) {
				parts.push(
					"<a " +
						breadcrumb_segment_attrs(segment, ctx) +
						">" +
						frappe.utils.escape_html(segment.label || "") +
						"</a>",
				);
			} else {
				var leaf_attrs = segment.testid
					? ' data-testid="' + frappe.utils.escape_html(segment.testid) + '"'
					: "";
				parts.push(
					'<span class="text-primary"' +
						leaf_attrs +
						">" +
						frappe.utils.escape_html(segment.label || "") +
						"</span>",
				);
			}
		});
		nav.innerHTML = parts.join("");
		remove_inline_breadcrumb_navs(doc, nav);
	}

	function hydrate_breadcrumb_trail(doc, ctx, leaf, parentTrail) {
		var leaf_label = typeof leaf === "string" ? leaf : leaf && leaf.label;
		var leaf_testid = leaf && typeof leaf === "object" ? leaf.testid : null;
		var segments = version_scope_segments(ctx);
		if (Array.isArray(parentTrail)) {
			parentTrail.forEach(function (parent) {
				segments.push({
					label: parent.label,
					route: parent.route,
					map_focus: parent.map_focus,
				});
			});
		}
		if (leaf_label) {
			segments.push({ label: leaf_label, testid: leaf_testid });
		}
		render_breadcrumb_trail(doc, ctx, segments);
	}

	function hydrate_library_breadcrumb(doc, ctx) {
		render_breadcrumb_trail(doc, ctx, [{ label: "STD Library" }]);
	}

	function hydrate_family_breadcrumb(doc, ctx) {
		render_breadcrumb_trail(doc, ctx, [
			{ label: "STD Library", route: "std-library" },
			{ label: ctx.family_code || DEFAULT_FAMILY },
		]);
	}

	function hydrate_version_breadcrumb(doc, ctx) {
		render_breadcrumb_trail(doc, ctx, version_scope_segments(ctx, { version_as_leaf: true }));
	}

	function resolve_breadcrumb_navigation(target, ctx) {
		if (!target) {
			return null;
		}
		var route = target.getAttribute("data-std-breadcrumb-target");
		if (!route) {
			return null;
		}
		var family_code = target.getAttribute("data-std-breadcrumb-family") || ctx.family_code || DEFAULT_FAMILY;
		var package_id = target.getAttribute("data-std-breadcrumb-package") || ctx.package_id || DEFAULT_PACKAGE;
		var next_ctx = {
			family_code: family_code,
			package_id: package_id,
			version_code: ctx.version_code || "",
			lifecycle_state: ctx.lifecycle_state || "",
			parameter_key: "",
			rule_key: "",
			form_key: "",
			clause_key: "",
			filter_parameter_key: "",
			map_focus: target.getAttribute("data-std-breadcrumb-map-focus") || "",
			import_run_key: "",
		};
		if (route === "std-library") {
			next_ctx.family_code = DEFAULT_FAMILY;
			next_ctx.package_id = DEFAULT_PACKAGE;
		} else if (route === "std-family-detail") {
			next_ctx.package_id = "";
		}
		return { route: route, ctx: next_ctx };
	}

	function set_context(ctx) {
		var root = window.parent && window.parent.frappe ? window.parent : window;
		root.frappe.route_options = Object.assign({}, root.frappe.route_options || {}, ctx || {});
	}

	function resolve_std_route(route) {
		var normalized = String(route || "").trim();
		if (!normalized) {
			return "";
		}
		return STD_PROD_ROUTE_ALIASES[normalized] || normalized;
	}

	function is_registered_std_route(route) {
		var resolved = resolve_std_route(route);
		return STD_PROD_REGISTERED_ROUTES.indexOf(resolved) !== -1;
	}

	function navigate(route, ctx) {
		var resolved = resolve_std_route(route);
		if (!is_registered_std_route(resolved)) {
			frappe.msgprint({
				title: __("Navigation failed"),
				indicator: "red",
				message: __("Unknown STD page route: {0}", [route || ""]),
			});
			return;
		}
		var root = window.parent && window.parent.frappe ? window.parent : window;
		if (ctx) {
			set_context(ctx);
		}
		root.frappe.set_route(resolved);
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

	var LAYOUT_OFFSET_CLASSES = [
		"mt-16",
		"mt-14",
		"pt-16",
		"pt-20",
		"pt-24",
		"pt-32",
		"pt-section-gap",
	];

	function normalize_page_layout(doc) {
		if (!doc || !doc.body) {
			return;
		}
		doc.body.classList.add("std-prod-header-harmonized");
		doc.querySelectorAll("main").forEach(function (main) {
			LAYOUT_OFFSET_CLASSES.forEach(function (token) {
				main.classList.remove(token);
			});
		});
		doc.querySelectorAll("body > header + div, body > header + section").forEach(function (node) {
			if (!node || node.tagName === "MAIN") {
				return;
			}
			unfix_layout_chrome(node);
		});
		doc.querySelectorAll("div.fixed, section.fixed").forEach(function (node) {
			if (!node || node.closest("main, #clause-detail-drawer")) {
				return;
			}
			var cls = node.className || "";
			if (cls.indexOf("top-16") >= 0 || cls.indexOf("top-14") >= 0) {
				unfix_layout_chrome(node);
			}
		});
		doc.querySelectorAll(".sticky.top-16, .sticky.top-14").forEach(function (node) {
			if (node.closest("main, #clause-detail-drawer")) {
				return;
			}
			unfix_layout_chrome(node);
		});
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
		node.classList.add("w-full");
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
			"body.std-prod-header-harmonized main {" +
			"margin-top: 0 !important;" +
			"padding-top: 0 !important;" +
			"}" +
			"body.std-prod-header-harmonized nav[data-std-prod-breadcrumb='1'] {" +
			"padding-top: 0.375rem !important;" +
			"padding-bottom: 0.375rem !important;" +
			"}" +
			"body.std-prod-header-harmonized header.std-prod-page-header {" +
			"margin-bottom: 0 !important;" +
			"}" +
			"body.std-prod-header-harmonized header.std-prod-page-header + div," +
			"body.std-prod-header-harmonized header.std-prod-page-header + section {" +
			"position: static !important;" +
			"top: auto !important;" +
			"margin-top: 0 !important;" +
			"}" +
			"body.std-prod-header-harmonized.std-prod-schema-list > main," +
			"body.std-prod-header-harmonized.std-prod-schema-list main {" +
			"padding-top: 0.75rem !important;" +
			"}" +
			"body.std-prod-header-harmonized.std-prod-schema-list main > section:first-of-type {" +
			"margin-top: 0 !important;" +
			"}" +
			".std-prod-schema-actions {" +
			"opacity: 1 !important;" +
			"visibility: visible !important;" +
			"}" +
			".std-prod-schema-actions-cell {" +
			"min-width: 7.5rem;" +
			"}" +
			".std-prod-table-scroll-host {" +
			"overflow-x: auto;" +
			"-webkit-overflow-scrolling: touch;" +
			"scrollbar-gutter: stable;" +
			"overscroll-behavior-x: contain;" +
			"}" +
			"main section .std-prod-table-scroll-host {" +
			"position: sticky;" +
			"bottom: 0;" +
			"z-index: 15;" +
			"background: #ffffff;" +
			"box-shadow: 0 -1px 0 #e2e8f0;" +
			"}" +
			"[data-std-prod-page-size] {" +
			"min-width: 4.5rem;" +
			"width: auto;" +
			"padding-left: 0.5rem;" +
			"padding-right: 1.75rem;" +
			"font-size: 0.875rem;" +
			"font-weight: 600;" +
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
		normalize_page_layout(doc);
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

	function get_table_pagination_state(doc) {
		if (!doc.__stdProdTablePagination) {
			doc.__stdProdTablePagination = {
				page: 1,
				pageSize: 10,
			};
		}
		return doc.__stdProdTablePagination;
	}

	function is_pagination_footer_node(node) {
		if (!node || node.nodeType !== 1) {
			return false;
		}
		if (node.getAttribute && node.getAttribute("data-std-prod-table-footer") === "1") {
			return true;
		}
		var tag = (node.tagName || "").toUpperCase();
		if (tag === "FOOTER") {
			var text = (node.textContent || "").trim();
			return text.indexOf("Rows per page") >= 0 || /^Showing\s/i.test(text);
		}
		var body_text = (node.textContent || "").trim();
		if (body_text.indexOf("Rows per page") >= 0) {
			return true;
		}
		return /^Showing\s/i.test(body_text) && !!node.querySelector("select, button .material-symbols-outlined");
	}

	function resolve_table_surface(doc, tbody) {
		tbody = tbody || doc.querySelector("main table tbody") || doc.querySelector("table tbody");
		var table = tbody && tbody.closest("table");
		var section = table && table.closest("section");
		var scroll_host = table && table.closest(".overflow-x-auto");
		var footer = null;
		if (table) {
			var anchor = scroll_host || table.parentElement;
			if (anchor && anchor.parentElement) {
				var parent = anchor.parentElement;
				var children = Array.from(parent.children);
				var anchor_index = children.indexOf(anchor);
				for (var i = anchor_index + 1; i < children.length; i++) {
					if (is_pagination_footer_node(children[i])) {
						footer = children[i];
						break;
					}
				}
			}
			if (!footer && section) {
				footer =
					section.querySelector("[data-std-prod-table-footer]") ||
					section.querySelector("footer[data-std-prod-table-footer]") ||
					section.querySelector("footer");
				if (!footer || !is_pagination_footer_node(footer)) {
					footer = null;
					Array.from(section.children).forEach(function (child) {
						if (!footer && child !== scroll_host && !child.contains(table) && is_pagination_footer_node(child)) {
							footer = child;
						}
					});
				}
			}
			if (!footer && table.parentElement) {
				var sibling = table.parentElement.nextElementSibling;
				if (is_pagination_footer_node(sibling)) {
					footer = sibling;
				}
			}
		}
		return {
			tbody: tbody,
			table: table,
			section: section,
			scrollHost: scroll_host,
			footer: footer,
		};
	}

	function enhance_table_scroll_ux(doc, surface) {
		surface = surface || resolve_table_surface(doc);
		if (!surface.scrollHost || surface.scrollHost.classList.contains("std-prod-scroll-wired")) {
			return;
		}
		surface.scrollHost.classList.add("std-prod-scroll-wired", "std-prod-table-scroll-host");
	}

	function should_paginate_tbody(tbody) {
		if (!tbody) {
			return false;
		}
		if (tbody.querySelector(".std-prod-clause-row")) {
			return false;
		}
		return true;
	}

	function detect_table_page_size(doc, footer, fallback) {
		var select = find_page_size_select(footer || doc);
		if (select) {
			normalize_page_size_select(select);
			var parsed = parseInt(select.value || "", 10);
			if (isNaN(parsed) && select.selectedIndex >= 0 && select.options[select.selectedIndex]) {
				parsed = parseInt(
					select.options[select.selectedIndex].value ||
						(select.options[select.selectedIndex].textContent || "").trim() ||
						"",
					10,
				);
			}
			if (!isNaN(parsed) && parsed > 0) {
				return parsed;
			}
		}
		return fallback || 10;
	}

	function find_page_size_select(root) {
		if (!root) {
			return null;
		}
		var footer = root.matches && root.matches("footer, [data-std-prod-table-footer]") ? root : null;
		if (!footer && root.querySelector) {
			footer =
				root.querySelector("[data-std-prod-table-footer] select") ||
				root.querySelector("footer select") ||
				root.querySelector(".border-t select");
			if (footer && footer.tagName === "SELECT") {
				return footer;
			}
			if (footer) {
				return footer.querySelector("select");
			}
		}
		return (
			(root.querySelector && root.querySelector("[data-std-prod-page-size]")) ||
			(root.querySelector && root.querySelector("footer select")) ||
			(root.querySelector && root.querySelector(".border-t select")) ||
			null
		);
	}

	function normalize_page_size_select(select) {
		if (!select || select.getAttribute("data-std-prod-page-size-normalized") === "1") {
			return select;
		}
		Array.from(select.options || []).forEach(function (option) {
			if (!option.value) {
				option.value = (option.textContent || "").trim();
			}
		});
		if ((!select.value || select.selectedIndex < 0) && select.options.length) {
			select.selectedIndex = 0;
			select.value = select.options[0].value;
		}
		select.setAttribute("data-std-prod-page-size", "1");
		select.setAttribute("data-std-prod-page-size-normalized", "1");
		select.classList.remove("w-12", "shrink-0", "bg-transparent", "border-none");
		select.classList.add(
			"bg-white",
			"border",
			"border-outline-variant",
			"rounded",
			"px-2",
			"py-1",
			"text-sm",
			"font-semibold",
			"min-w-[4.5rem]",
			"w-auto"
		);
		return select;
	}

	function is_paginated_data_row(row) {
		if (!row || row.querySelector("td[colspan]")) {
			return false;
		}
		return row.querySelectorAll("td").length > 0;
	}

	function apply_table_row_pagination(tbody, page, page_size) {
		if (!tbody) {
			return 0;
		}
		var rows = Array.from(tbody.querySelectorAll("tr")).filter(is_paginated_data_row);
		var start_index = Math.max(0, (page - 1) * page_size);
		var end_index = start_index + page_size;
		rows.forEach(function (row, index) {
			row.style.display = index >= start_index && index < end_index ? "" : "none";
		});
		return rows.length;
	}

	function update_showing_label(node, start, end, total, suffix) {
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
		var resolved_suffix =
			typeof suffix === "string" && suffix.length ? suffix : suffix_match ? suffix_match[1].trim() : "";
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
			if (resolved_suffix) {
				html += " " + resolved_suffix;
			}
			node.innerHTML = html;
			return true;
		}
		var plain = "Showing " + start + "-" + end + " of " + total;
		if (resolved_suffix) {
			plain += " " + resolved_suffix;
		}
		node.textContent = plain;
		return true;
	}

	function sync_page_of_labels(root, total_pages, current_page) {
		if (!root) {
			return;
		}
		var page = current_page || 1;
		root.querySelectorAll("span, div").forEach(function (node) {
			var text = (node.textContent || "").trim();
			if (/^PAGE\s+\d+\s+OF\s+\d+/i.test(text)) {
				node.textContent = "PAGE " + page + " OF " + total_pages;
				return;
			}
			if (/^\d+\s+OF\s+\d+$/i.test(text)) {
				node.textContent = page + " OF " + total_pages;
			}
		});
	}

	function sync_numbered_page_buttons(root, total_pages, current_page) {
		if (!root) {
			return;
		}
		var page = current_page || 1;
		root.querySelectorAll("button").forEach(function (btn) {
			var label = (btn.textContent || "").trim();
			if (!/^\d+$/.test(label)) {
				return;
			}
			var page_num = parseInt(label, 10);
			if (page_num <= total_pages) {
				btn.style.display = "";
				btn.disabled = page_num === page ? false : false;
				btn.removeAttribute("disabled");
				if (page_num === page) {
					btn.classList.add("bg-primary", "text-white");
				} else {
					btn.classList.remove("bg-primary", "text-white");
				}
			} else {
				btn.style.display = "none";
			}
		});
	}

	function sync_pager_ellipsis(root, total_pages) {
		if (!root) {
			return;
		}
		root.querySelectorAll("span").forEach(function (node) {
			if ((node.textContent || "").trim() !== "...") {
				return;
			}
			node.style.display = total_pages > 1 ? "" : "none";
		});
	}

	function sync_pager_nav_buttons(root, total_pages, current_page) {
		if (!root) {
			return;
		}
		var page = current_page || 1;
		var nav_icons = {
			first_page: true,
			chevron_left: true,
			chevron_right: true,
			last_page: true,
		};
		root.querySelectorAll("button").forEach(function (btn) {
			var icon = btn.querySelector(".material-symbols-outlined");
			if (!icon) {
				return;
			}
			var icon_name = (icon.textContent || "").trim();
			if (!nav_icons[icon_name]) {
				return;
			}
			var disable = false;
			if (total_pages <= 1) {
				disable = true;
			} else if (icon_name === "first_page" || icon_name === "chevron_left") {
				disable = page <= 1;
			} else if (icon_name === "chevron_right" || icon_name === "last_page") {
				disable = page >= total_pages;
			}
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

	function extract_showing_suffix(text) {
		var raw = (text || "").trim();
		var suffix_match = raw.match(/of\s+[\d,]+\s*(.*)$/i);
		return suffix_match ? suffix_match[1].trim() : "";
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

	function hydrate_table_footer_scoped(footer, doc, total, page_size, current_page) {
		if (!footer) {
			return;
		}
		var count = total || 0;
		var page = current_page || 1;
		var pageSize = page_size || detect_table_page_size(doc, footer, 10);
		var total_pages = count > 0 ? Math.max(1, Math.ceil(count / pageSize)) : 1;
		if (page > total_pages) {
			page = total_pages;
		}
		var start = count > 0 ? (page - 1) * pageSize + 1 : 0;
		var end = count > 0 ? Math.min(page * pageSize, count) : 0;

		var showing_nodes = [];
		footer.querySelectorAll("span, p, div").forEach(function (node) {
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
				update_showing_label(node, start, end, count, extract_showing_suffix(node.textContent || ""));
			}
		});

		sync_page_of_labels(footer, total_pages, page);
		sync_numbered_page_buttons(footer, total_pages, page);
		sync_pager_ellipsis(footer, total_pages);
		sync_pager_nav_buttons(footer, total_pages, page);
		var select = find_page_size_select(footer);
		if (select) {
			normalize_page_size_select(select);
			select.value = String(pageSize);
		}
	}

	function wire_table_pagination(doc, tbody, total) {
		var surface = resolve_table_surface(doc, tbody);
		if (!surface.footer || !surface.tbody || !should_paginate_tbody(surface.tbody)) {
			return surface;
		}
		surface.footer.setAttribute("data-std-prod-table-footer", "1");
		surface.footer.setAttribute("data-std-prod-row-total", String(total != null ? total : 0));
		var state = get_table_pagination_state(doc);
		state.pageSize = detect_table_page_size(doc, surface.footer, state.pageSize || 10);
		var visible_total = apply_table_row_pagination(surface.tbody, state.page, state.pageSize);
		var row_total = total != null ? total : visible_total;
		surface.footer.setAttribute("data-std-prod-row-total", String(row_total));
		hydrate_table_footer_scoped(surface.footer, doc, row_total, state.pageSize, state.page);

		var select = find_page_size_select(surface.footer);
		if (select && select.getAttribute("data-std-prod-page-size-wired") !== "1") {
			select.setAttribute("data-std-prod-page-size-wired", "1");
			select.addEventListener("change", function () {
				state.pageSize = parseInt(select.value, 10) || 10;
				state.page = 1;
				var stored_total = parseInt(surface.footer.getAttribute("data-std-prod-row-total") || "0", 10);
				apply_table_row_pagination(surface.tbody, state.page, state.pageSize);
				hydrate_table_footer_scoped(
					surface.footer,
					doc,
					stored_total,
					state.pageSize,
					state.page
				);
			});
		}

		if (surface.footer.getAttribute("data-std-prod-pager-wired") !== "1") {
			surface.footer.setAttribute("data-std-prod-pager-wired", "1");
			surface.footer.querySelectorAll("button").forEach(function (btn) {
				var icon = btn.querySelector(".material-symbols-outlined");
				if (!icon) {
					return;
				}
				var icon_name = (icon.textContent || "").trim();
				btn.addEventListener("click", function (event) {
					var label = (btn.textContent || "").trim();
					var stored_total = parseInt(surface.footer.getAttribute("data-std-prod-row-total") || "0", 10);
					var total_pages =
						stored_total > 0 ? Math.max(1, Math.ceil(stored_total / state.pageSize)) : 1;
					if (/^\d+$/.test(label)) {
						state.page = parseInt(label, 10);
					} else if (icon_name === "chevron_right") {
						state.page = Math.min(total_pages, state.page + 1);
					} else if (icon_name === "chevron_left") {
						state.page = Math.max(1, state.page - 1);
					} else if (icon_name === "last_page") {
						state.page = total_pages;
					} else if (icon_name === "first_page") {
						state.page = 1;
					} else {
						return;
					}
					event.preventDefault();
					event.stopPropagation();
					apply_table_row_pagination(surface.tbody, state.page, state.pageSize);
					hydrate_table_footer_scoped(
						surface.footer,
						doc,
						stored_total,
						state.pageSize,
						state.page
					);
				});
			});
		}
		return surface;
	}

	function finalize_table_surface(doc, tbody, total) {
		var surface = wire_table_pagination(doc, tbody, total);
		enhance_table_scroll_ux(doc, surface);
		return surface;
	}

	function hydrate_table_footer(doc, total, page_size, tbody) {
		var surface = resolve_table_surface(doc, tbody);
		var state = get_table_pagination_state(doc);
		if (page_size) {
			state.pageSize = page_size;
		}
		if (surface.tbody && surface.footer && should_paginate_tbody(surface.tbody)) {
			apply_table_row_pagination(surface.tbody, state.page, state.pageSize);
		}
		hydrate_table_footer_scoped(
			surface.footer,
			doc,
			total || 0,
			state.pageSize,
			state.page
		);
		if (surface.footer) {
			wire_table_pagination(doc, surface.tbody, total);
		}
		enhance_table_scroll_ux(doc, surface);
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
		doc
			.querySelectorAll(".text-headline-md, .font-headline-md, .text-headline-lg, .font-headline-lg")
			.forEach(function (node) {
				var parent_text = node.parentElement ? node.parentElement.textContent || "" : "";
				if (parent_text.indexOf(label) >= 0) {
					node.textContent = String(value);
				}
			});
	}

	function capture_row_template(doc, tbody, cache_key) {
		if (!tbody || doc[cache_key]) {
			return;
		}
		var sample = tbody.querySelector("tr");
		if (sample) {
			doc[cache_key] = sample.cloneNode(true);
		}
	}

	function row_cell(row, index) {
		if (!row || !row.cells) {
			return null;
		}
		return row.cells[index] || null;
	}

	function set_row_cell_text(row, index, text) {
		var cell = row_cell(row, index);
		if (cell) {
			cell.textContent = text == null || text === "" ? "—" : String(text);
		}
	}

	function set_row_cell_html(row, index, html) {
		var cell = row_cell(row, index);
		if (cell) {
			cell.innerHTML = html;
		}
	}

	function schema_actions_wrapper_html(inner_html) {
		return (
			'<div class="std-prod-schema-actions flex justify-end items-center gap-1 flex-nowrap">' +
			inner_html +
			"</div>"
		);
	}

	function set_actions_cell(row, index, inner_html) {
		var cell = row_cell(row, index);
		if (!cell) {
			return;
		}
		cell.className = "px-4 py-3 text-right std-prod-schema-actions-cell whitespace-nowrap align-middle";
		cell.innerHTML = schema_actions_wrapper_html(inner_html);
	}

	function compact_schema_list_chrome(doc) {
		if (!doc || !doc.body) {
			return;
		}
		doc.body.classList.add("std-prod-schema-list");
		var main = doc.querySelector("main");
		if (!main) {
			return;
		}
		var kpi_section = main.querySelector("section.grid");
		if (kpi_section) {
			kpi_section.style.display = "none";
		}
	}

	function format_field_type_label(field_type) {
		if (!field_type) {
			return "—";
		}
		return String(field_type).replace(/_/g, " ");
	}

	function format_requiredness_chip(required) {
		if (required) {
			return (
				'<span class="px-2 py-0.5 bg-status-committed/10 text-status-committed rounded-sm text-[10px] font-bold">MANDATORY</span>'
			);
		}
		return (
			'<span class="px-2 py-0.5 bg-outline-variant/20 text-on-surface-variant rounded-sm text-[10px] font-bold">OPTIONAL</span>'
		);
	}

	function format_validation_rules_cell(count) {
		if (!count) {
			return (
				'<div class="flex items-center gap-1 text-on-surface-variant"><span class="material-symbols-outlined text-base">info</span>' +
				'<span class="text-xs font-medium">None</span></div>'
			);
		}
		return (
			'<div class="flex items-center gap-1 text-status-available"><span class="material-symbols-outlined text-base">check_circle</span>' +
			'<span class="text-xs font-medium">' +
			String(count) +
			" Rules</span></div>"
		);
	}

	function format_status_chip(status) {
		var normalized = String(status || "ACTIVE").toUpperCase();
		return (
			'<span class="flex items-center gap-1.5 text-status-available text-xs font-bold uppercase">' +
			'<span class="w-1.5 h-1.5 rounded-full bg-status-available"></span>' +
			frappe.utils.escape_html(normalized) +
			"</span>"
		);
	}

	function parameter_row_actions_html() {
		return (
			'<button class="p-1 hover:text-primary" title="Open"><span class="material-symbols-outlined text-lg">visibility</span></button>' +
			'<button class="p-1 hover:text-primary" title="View Usage"><span class="material-symbols-outlined text-lg">account_tree</span></button>' +
			'<button class="p-1 hover:text-primary" title="View Rules"><span class="material-symbols-outlined text-lg">rule</span></button>' +
			'<button class="p-1 hover:text-primary" title="View Source"><span class="material-symbols-outlined text-lg">code</span></button>' +
			'<button class="p-1 hover:text-primary" title="Compare Previous Version"><span class="material-symbols-outlined text-lg">history</span></button>'
		);
	}

	function fill_parameter_row(row, item) {
		if (!row || !item) {
			return;
		}
		row.className = "bureau-table-row transition-colors std-prod-param-row cursor-pointer";
		row.setAttribute("data-parameter-key", item.id || "");
		set_row_cell_text(row, 0, item.code || item.id);
		var key_cell = row_cell(row, 0);
		if (key_cell) {
			key_cell.className = "px-4 py-4 parameter-key text-primary font-medium";
		}
		set_row_cell_text(row, 1, item.name || "");
		set_row_cell_html(
			row,
			2,
			item.fieldType
				? '<span class="px-2 py-0.5 bg-surface-container text-on-surface-variant rounded-full text-xs font-medium">' +
						frappe.utils.escape_html(format_field_type_label(item.fieldType)) +
						"</span>"
				: "—",
		);
		set_row_cell_text(row, 3, item.sectionTitle || "—");
		set_row_cell_text(row, 4, item.appliesTo || "—");
		set_row_cell_html(row, 5, format_requiredness_chip(item.required));
		var default_text =
			item.defaultValue != null && item.defaultValue !== ""
				? String(item.defaultValue)
				: item.optionSetKey
					? "Option set: " + item.optionSetKey
					: "—";
		set_row_cell_html(row, 6, '<span class="text-xs text-on-surface-variant">' + frappe.utils.escape_html(default_text) + "</span>");
		set_row_cell_html(row, 7, format_validation_rules_cell(item.validationRuleCount || 0));
		set_row_cell_text(row, 8, "—");
		set_row_cell_text(row, 9, item.renderBindingCount ? String(item.renderBindingCount) + " Blocks" : "—");
		set_row_cell_html(
			row,
			10,
			'<span class="font-mono text-[10px] text-on-surface-variant">' +
				frappe.utils.escape_html(item.sourceAnchorId || "—") +
				"</span>",
		);
		set_row_cell_html(row, 11, format_status_chip(item.validationStatus));
		set_actions_cell(row, 12, parameter_row_actions_html());
	}

	function severity_chip_html(severity) {
		var sev = String(severity || "INFO").toUpperCase();
		if (sev === "BLOCKER") {
			return (
				'<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-error-container text-on-error-container font-label-caps text-[10px] font-bold uppercase">' +
				'<span class="material-symbols-outlined text-[12px]" style="font-variation-settings: \'FILL\' 1;">error</span>BLOCKER</span>'
			);
		}
		if (sev === "WARNING") {
			return (
				'<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container-high text-status-reserved font-label-caps text-[10px] font-bold uppercase">' +
				'<span class="material-symbols-outlined text-[12px]" style="font-variation-settings: \'FILL\' 1;">warning</span>WARNING</span>'
			);
		}
		return (
			'<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-tertiary-fixed text-on-tertiary-fixed-variant font-label-caps text-[10px] font-bold uppercase">' +
			'<span class="material-symbols-outlined text-[12px]" style="font-variation-settings: \'FILL\' 1;">info</span>INFO</span>'
		);
	}

	function rule_type_chip_html(rule_type) {
		return (
			'<span class="px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant font-label-caps text-[10px] uppercase">' +
			frappe.utils.escape_html(String(rule_type || "Validation")) +
			"</span>"
		);
	}

	function test_coverage_chip_html(coverage) {
		var label = String(coverage || "—");
		if (label.toLowerCase() === "covered" || label.toLowerCase() === "passed") {
			return (
				'<span class="px-2 py-0.5 rounded bg-status-available/10 text-status-available font-label-caps text-[10px] font-bold uppercase">Covered</span>'
			);
		}
		if (label === "—") {
			return "—";
		}
		return (
			'<span class="px-2 py-0.5 rounded bg-outline/10 text-on-surface-variant font-label-caps text-[10px] font-bold uppercase">' +
			frappe.utils.escape_html(label) +
			"</span>"
		);
	}

	function rule_row_actions_html() {
		return (
			'<div class="flex items-center justify-end gap-1">' +
			'<button class="p-1.5 rounded hover:bg-surface-container text-primary transition-all" title="Open Rule"><span class="material-symbols-outlined text-[20px]">open_in_new</span></button>' +
			'<button class="p-1.5 rounded hover:bg-surface-container text-on-surface-variant" title="View Affected Objects"><span class="material-symbols-outlined text-[20px]">hub</span></button>' +
			'<button class="p-1.5 rounded hover:bg-surface-container text-on-surface-variant" title="View Source"><span class="material-symbols-outlined text-[20px]">code</span></button>' +
			'<button class="p-1.5 rounded hover:bg-surface-container text-on-surface-variant" title="View Test Coverage"><span class="material-symbols-outlined text-[20px]">fact_check</span></button>' +
			'<button class="p-1.5 rounded hover:bg-surface-container text-on-surface-variant" title="Export Rule Catalog"><span class="material-symbols-outlined text-[20px]">download</span></button>' +
			'<button class="p-1.5 rounded hover:bg-surface-container text-on-surface-variant" title="Create Draft Version"><span class="material-symbols-outlined text-[20px]">edit_document</span></button>' +
			"</div>"
		);
	}

	function fill_rule_row(row, item) {
		if (!row || !item) {
			return;
		}
		row.className = "hover:bg-surface-container-low/50 transition-colors std-prod-rule-row cursor-pointer";
		row.setAttribute("data-rule-key", item.id || "");
		set_row_cell_html(row, 0, '<span class="font-data-mono text-data-mono text-primary">' + frappe.utils.escape_html(item.code || item.id) + "</span>");
		set_row_cell_html(
			row,
			1,
			'<span class="font-body-md text-body-md font-semibold text-on-surface">' + frappe.utils.escape_html(item.name || "") + "</span>",
		);
		set_row_cell_html(row, 2, rule_type_chip_html(item.ruleType));
		set_row_cell_html(row, 3, severity_chip_html(item.severity));
		set_row_cell_text(row, 4, item.scope || "—");
		set_row_cell_html(row, 5, '<span class="font-data-mono text-[12px] text-on-surface-variant">' + frappe.utils.escape_html(item.lifecycleStage || "—") + "</span>");
		set_row_cell_html(row, 6, '<span class="font-data-mono text-[12px]">' + frappe.utils.escape_html(item.affectedObject || "—") + "</span>");
		set_row_cell_text(row, 7, item.sourceBasis || "—");
		set_row_cell_html(row, 8, test_coverage_chip_html(item.testCoverage));
		set_row_cell_html(row, 9, format_status_chip(item.isActive === false ? "INACTIVE" : "ACTIVE"));
		set_actions_cell(row, 10, rule_row_actions_html());
	}

	function render_design_rows(doc, tbody, items, cache_key, fill_fn, limit) {
		if (!tbody) {
			return;
		}
		capture_row_template(doc, tbody, cache_key);
		var template = doc[cache_key];
		if (!template) {
			return;
		}
		var rows = items || [];
		if (!rows.length) {
			tbody.innerHTML =
				'<tr><td class="px-4 py-6 text-on-surface-variant" colspan="' +
				template.cells.length +
				'">No records for this package.</td></tr>';
			return;
		}
		tbody.innerHTML = "";
		rows.forEach(function (item) {
			var row = template.cloneNode(true);
			fill_fn(row, item);
			tbody.appendChild(row);
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
		ctx = sync_context_from_package_context(payload.packageContext, ctx);
		hydrate_breadcrumb_trail(doc, ctx, "Parameter Dictionary");
		update_headline_counters(doc, "TOTAL PARAMETERS", data.count || params.length);
		var tbody = doc.querySelector("table tbody");
		render_design_rows(doc, tbody, params, "__stdProdParamRowTemplate", fill_parameter_row, 200);
		hydrate_table_footer(doc, data.count || params.length, null, tbody);
		compact_schema_list_chrome(doc);
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
		ctx = sync_context_from_package_context(package_context, ctx);
		hydrate_breadcrumb_trail(
			doc,
			ctx,
			{ label: business_code, testid: "std-prod-parameter-breadcrumb" },
			[{ label: "Parameter Dictionary", route: "std-parameter-dictionary" }],
		);
		var validation_rules = data.validationRules || [];
		var render_bindings = data.renderBindingItems || [];
		if (!validation_rules.length && (data.validationRuleKeys || []).length) {
			validation_rules = (data.validationRuleKeys || []).map(function (rule_key) {
				return {
					id: rule_key,
					code: business_code_from_key(rule_key, ".rule."),
					name: business_code_from_key(rule_key, ".rule."),
				};
			});
		}
		if (!render_bindings.length && (data.renderBindings || []).length) {
			render_bindings = (data.renderBindings || []).map(function (binding_key) {
				var code = business_code_from_key(binding_key, ".render_block.");
				if (code === binding_key) {
					code = business_code_from_key(binding_key, ".render.");
				}
				return { id: binding_key, code: code, name: code };
			});
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
			render_bindings.length
				? render_bindings.map(function (item) { return item.code || item.name; }).join(", ")
				: "None",
		);
		set_labeled_field(
			doc,
			"Rule Binding",
			validation_rules.length
				? validation_rules.map(function (item) { return item.code || item.name; }).join(", ")
				: "None",
		);

		var usage_section = find_bento_section(doc, "USAGE MAP");
		var usage_container = usage_section && usage_section.querySelector(".divide-y");
		if (usage_container) {
			var usage_items = [];
			render_bindings.forEach(function (binding) {
				usage_items.push({
					icon: "layers",
					title: binding.code || binding.name || binding.id,
					subtitle: binding.name || "Render binding",
				});
			});
			validation_rules.forEach(function (rule) {
				usage_items.push({
					icon: "rule",
					title: rule.code || rule.name || rule.id,
					subtitle: rule.name || "Validation rule",
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
			capture_row_template(doc, validation_body, "__stdProdParamRuleRowTemplate");
			var rule_template = doc.__stdProdParamRuleRowTemplate;
			if (!validation_rules.length) {
				validation_body.innerHTML =
					'<tr><td class="px-card-padding py-4 text-on-surface-variant italic" colspan="5">No validation rules are bound to this parameter.</td></tr>';
			} else if (rule_template) {
				validation_body.innerHTML = "";
				validation_rules.forEach(function (rule) {
					var row = rule_template.cloneNode(true);
					var cells = row.cells || [];
					if (cells[0]) {
						cells[0].textContent = rule.code || rule.name || rule.id || "—";
						cells[0].className = "px-card-padding py-4 font-semibold text-[13px]";
					}
					if (cells[1]) {
						cells[1].innerHTML = severity_chip_html(rule.severity);
					}
					if (cells[2]) {
						cells[2].textContent = rule.ruleType || "VALIDATION";
					}
					if (cells[3]) {
						cells[3].textContent = rule.lifecycleStage || "—";
					}
					if (cells[4]) {
						cells[4].className = "px-card-padding py-4 text-right";
						cells[4].innerHTML = "—";
					}
					validation_body.appendChild(row);
				});
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
		ctx = sync_context_from_package_context(payload.packageContext, ctx);
		hydrate_breadcrumb_trail(doc, ctx, "Rule Dictionary");
		var filter_key = ctx.filter_parameter_key || data.filterParameterKey || "";
		var summary = data.summary || {};
		var blocker_count = summary.blockerRules;
		var warning_count = summary.warningRules;
		var active_count = summary.activeRules;
		if (blocker_count == null || warning_count == null || active_count == null) {
			blocker_count = 0;
			warning_count = 0;
			active_count = 0;
			rules.forEach(function (rule) {
				var severity = String(rule.severity || "").toUpperCase();
				if (severity === "BLOCKER") {
					blocker_count += 1;
				} else if (severity === "WARNING") {
					warning_count += 1;
				}
				if (rule.isActive !== false) {
					active_count += 1;
				}
			});
		}
		update_headline_counters(doc, "Total Rules", summary.total != null ? summary.total : data.count || rules.length);
		update_headline_counters(doc, "Blocker Rules", blocker_count);
		update_headline_counters(doc, "Warning Rules", warning_count);
		update_headline_counters(doc, "Active Rules", active_count);
		if (filter_key && doc.body) {
			doc.body.setAttribute("data-std-filter-parameter-key", filter_key);
			var filter_banner = doc.querySelector("[data-std-prod-rule-filter-banner]");
			if (!filter_banner) {
				var main = doc.querySelector("main");
				if (main) {
					filter_banner = doc.createElement("div");
					filter_banner.setAttribute("data-std-prod-rule-filter-banner", "1");
					filter_banner.className =
						"mb-4 p-3 bg-primary-container/10 border border-primary/20 rounded-lg text-sm text-primary";
					main.insertBefore(filter_banner, main.firstChild);
				}
			}
			if (filter_banner) {
				filter_banner.textContent =
					"Showing validation rules linked to parameter " + filter_key + ". Open Rule Dictionary from Version Detail for the full catalogue.";
			}
		} else if (doc.body) {
			doc.body.removeAttribute("data-std-filter-parameter-key");
			var existing_banner = doc.querySelector("[data-std-prod-rule-filter-banner]");
			if (existing_banner) {
				existing_banner.remove();
			}
		}
		var tbody = doc.querySelector("table tbody");
		render_design_rows(doc, tbody, rules, "__stdProdRuleRowTemplate", fill_rule_row, 200);
		hydrate_table_footer(doc, data.count || rules.length, null, tbody);
		compact_schema_list_chrome(doc);
	}

	function hydrate_rule(doc, payload, ctx) {
		var data = payload.data || {};
		var metadata = data.metadata || {};
		var package_context = payload.packageContext || {};
		var business_code = data.code || metadata.rule_key || "";
		var display_name = data.name || business_code || "Rule";
		var lifecycle = package_context.lifecycleState || "DRAFT";
		ctx = sync_context_from_package_context(package_context, ctx);
		hydrate_breadcrumb_trail(
			doc,
			ctx,
			{ label: business_code, testid: "std-prod-rule-breadcrumb" },
			[{ label: "Rule Dictionary", route: "std-rule-dictionary" }],
		);

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

	function form_row_actions_html() {
		return (
			'<button class="p-1.5 text-primary hover:bg-primary-fixed rounded transition-colors" title="Open Form" data-std-prod-schema-action="open"><span class="material-symbols-outlined text-[20px]">open_in_new</span></button>' +
			'<button class="p-1.5 text-secondary hover:bg-secondary-fixed rounded transition-colors" title="Preview Form"><span class="material-symbols-outlined text-[20px]">visibility</span></button>' +
			'<button class="p-1.5 text-tertiary hover:bg-tertiary-fixed rounded transition-colors" title="Export Schema"><span class="material-symbols-outlined text-[20px]">download</span></button>'
		);
	}

	function fill_form_row(row, item) {
		if (!row || !item) {
			return;
		}
		row.className = "hover:bg-surface-container-low transition-colors std-prod-form-row cursor-pointer group";
		row.setAttribute("data-form-key", item.id || "");
		set_row_cell_html(
			row,
			0,
			'<span class="font-data-mono text-data-mono text-primary">' +
				frappe.utils.escape_html(item.code || item.id) +
				"</span>",
		);
		set_row_cell_html(row, 1, '<span class="font-medium">' + frappe.utils.escape_html(item.name || "") + "</span>");
		set_row_cell_text(row, 2, item.respondentType || "—");
		set_row_cell_text(row, 3, item.stage || "—");
		set_row_cell_html(row, 4, format_requiredness_chip(item.required !== false));
		set_row_cell_html(
			row,
			5,
			'<span class="font-data-mono">' + frappe.utils.escape_html(String(item.fieldCount || 0).padStart(2, "0")) + "</span>",
		);
		set_row_cell_html(
			row,
			6,
			'<span class="font-data-mono">' + frappe.utils.escape_html(String(item.evidenceCount || 0).padStart(2, "0")) + "</span>",
		);
		set_row_cell_html(
			row,
			7,
			'<span class="text-[12px]">' + frappe.utils.escape_html(item.activationRules || "—") + "</span>",
		);
		set_row_cell_html(
			row,
			8,
			'<span class="font-data-mono text-[12px]">' + frappe.utils.escape_html(item.sourceAnchorId || "—") + "</span>",
		);
		set_row_cell_html(row, 9, format_status_chip(item.validationStatus || "ACTIVE"));
		set_actions_cell(row, 10, form_row_actions_html());
	}

	function render_block_row_actions_html() {
		return (
			'<button class="p-1.5 hover:bg-surface-container-highest rounded transition-colors" title="Open Render Block" data-std-prod-schema-action="open"><span class="material-symbols-outlined text-on-surface-variant text-[20px]">open_in_new</span></button>' +
			'<button class="p-1.5 hover:bg-surface-container-highest rounded transition-colors" title="Preview Output"><span class="material-symbols-outlined text-on-surface-variant text-[20px]">visibility</span></button>' +
			'<button class="p-1.5 hover:bg-surface-container-highest rounded transition-colors" title="View Data Bindings"><span class="material-symbols-outlined text-on-surface-variant text-[20px]">link</span></button>' +
			'<button class="p-1.5 hover:bg-surface-container-highest rounded transition-colors" title="View Source Section" data-std-prod-schema-action="source"><span class="material-symbols-outlined text-on-surface-variant text-[20px]">anchor</span></button>' +
			'<button class="p-1.5 hover:bg-surface-container-highest rounded transition-colors" title="View Render Test"><span class="material-symbols-outlined text-on-surface-variant text-[20px]">assignment_turned_in</span></button>' +
			'<button class="p-1.5 hover:bg-surface-container-highest rounded transition-colors" title="Export Render Profile"><span class="material-symbols-outlined text-on-surface-variant text-[20px]">download</span></button>' +
			'<button class="p-1.5 hover:bg-surface-container-highest rounded transition-colors" title="Create Draft Version"><span class="material-symbols-outlined text-on-surface-variant text-[20px]">edit_square</span></button>'
		);
	}

	function render_block_validation_badge(status) {
		var normalized = String(status || "VALID").toUpperCase();
		if (normalized === "WARNING") {
			return '<span class="bg-status-reserved/10 text-status-reserved px-2 py-0.5 rounded-full text-[11px] font-bold tracking-tight">WARNING</span>';
		}
		if (normalized === "BLOCKER") {
			return '<span class="bg-status-exhausted/10 text-status-exhausted px-2 py-0.5 rounded-full text-[11px] font-bold tracking-tight">BLOCKER</span>';
		}
		return '<span class="bg-status-available/10 text-status-available px-2 py-0.5 rounded-full text-[11px] font-bold tracking-tight">VALID</span>';
	}

	function render_block_test_badge(status) {
		var normalized = String(status || "SUCCESS").toUpperCase();
		if (normalized === "WARNING") {
			return (
				'<div class="flex items-center gap-1.5 text-status-reserved font-semibold text-xs">' +
				'<span class="material-symbols-outlined text-[16px]">warning</span>WARNING</div>'
			);
		}
		return (
			'<div class="flex items-center gap-1.5 text-status-available font-semibold text-xs">' +
			'<span class="material-symbols-outlined text-[16px]">check_circle</span>SUCCESS</div>'
		);
	}

	function fill_render_block_row(row, item) {
		if (!row || !item) {
			return;
		}
		row.className = "hover:bg-surface-container-low transition-colors std-prod-render-row cursor-pointer group";
		row.setAttribute("data-render-block-key", item.id || "");
		row.setAttribute("data-render-block-code", item.code || "");
		set_row_cell_html(
			row,
			0,
			'<span class="font-data-mono text-data-mono text-primary">' +
				frappe.utils.escape_html(item.code || item.id) +
				"</span>",
		);
		set_row_cell_text(row, 1, item.documentArea || item.name || "—");
		set_row_cell_html(
			row,
			2,
			'<span class="font-body-md text-body-md text-on-surface-variant">' +
				frappe.utils.escape_html(item.clauseBinding || "—") +
				"</span>",
		);
		set_row_cell_html(
			row,
			3,
			'<span class="font-data-mono text-data-mono text-on-surface-variant">' +
				frappe.utils.escape_html(item.sourceDataObject || "—") +
				"</span>",
		);
		set_row_cell_text(row, 4, item.requiredLabel || "—");
		set_row_cell_text(row, 5, item.format || "—");
		set_row_cell_html(row, 6, render_block_test_badge(item.lastRenderTest));
		set_row_cell_html(row, 7, render_block_validation_badge(item.validationStatus));
		set_row_cell_html(
			row,
			8,
			'<span class="bg-status-available/10 text-status-available px-2 py-0.5 rounded-full text-[11px] font-bold tracking-tight">' +
				frappe.utils.escape_html(item.lifecycleState || "ACTIVE") +
				"</span>",
		);
		set_actions_cell(row, 9, render_block_row_actions_html());
	}

	function hydrate_forms(doc, payload, ctx) {
		var data = payload.data || {};
		var forms = data.forms || [];
		ctx = sync_context_from_package_context(payload.packageContext, ctx);
		hydrate_breadcrumb_trail(doc, ctx, "Form Schema Manager");
		update_headline_counters(doc, "Total Forms", data.count || forms.length);
		var tbody = doc.querySelector("table tbody");
		render_design_rows(doc, tbody, forms, "__stdProdFormRowTemplate", fill_form_row, 200);
		hydrate_table_footer(doc, data.count || forms.length, null, tbody);
		compact_schema_list_chrome(doc);
	}

	function hydrate_form(doc, payload, ctx) {
		var data = payload.data || {};
		var metadata = data.metadata || {};
		var package_context = payload.packageContext || {};
		ctx = sync_context_from_package_context(package_context, ctx);
		var business_code = data.code || metadata.form_code || "";
		var display_name = data.name || metadata.display_title || business_code || "Form";
		var fields = data.formFields || [];
		var lifecycle = package_context.lifecycleState || "DRAFT";
		hydrate_breadcrumb_trail(doc, ctx, display_name, [
			{ label: "Form Schema Manager", route: "std-form-schema-manager" },
		]);

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
		ctx = sync_context_from_package_context(payload.packageContext, ctx);
		hydrate_breadcrumb_trail(doc, ctx, "Requirement Schema");
		update_headline_counters(doc, "Requirement", data.count || items.length);
		var tbody = doc.querySelector("table tbody");
		render_design_rows(doc, tbody, items, "__stdProdRequirementRowTemplate", fill_requirement_row, 200);
		hydrate_table_footer(doc, data.count || items.length, null, tbody);
		compact_schema_list_chrome(doc);
	}

	function requirement_required_chip_html(required) {
		if (required !== false) {
			return (
				'<span class="bg-primary-fixed text-on-primary-fixed-variant px-2 py-0.5 rounded-full text-[11px] font-bold">REQUIRED</span>'
			);
		}
		return (
			'<span class="bg-outline-variant/30 text-on-surface-variant px-2 py-0.5 rounded-full text-[11px] font-bold">OPTIONAL</span>'
		);
	}

	function requirement_validation_badge_html(status) {
		var normalized = String(status || "VALID").toUpperCase();
		var dot_class = "bg-status-available";
		if (normalized === "WARNING") {
			dot_class = "bg-status-reserved";
		} else if (normalized === "BLOCKER") {
			dot_class = "bg-status-exhausted";
		}
		return (
			'<div class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full ' +
			dot_class +
			'"></span><span class="text-body-md">' +
			frappe.utils.escape_html(normalized) +
			"</span></div>"
		);
	}

	function requirement_carry_forward_html(enabled) {
		if (enabled) {
			return (
				'<span class="material-symbols-outlined text-status-available" style="font-variation-settings: \'FILL\' 1;">check_circle</span>'
			);
		}
		return '<span class="material-symbols-outlined text-outline">remove_circle</span>';
	}

	function requirement_row_actions_html() {
		return (
			'<button class="text-primary font-label-caps text-[11px] hover:underline" data-std-prod-schema-action="source">VIEW SOURCE</button>'
		);
	}

	function fill_requirement_row(row, item) {
		if (!row || !item) {
			return;
		}
		row.className = "hover:bg-surface-container-low transition-colors std-prod-req-row cursor-pointer group";
		row.setAttribute("data-requirement-key", item.id || "");
		set_row_cell_html(
			row,
			0,
			'<span class="font-medium text-body-md text-on-surface">' +
				frappe.utils.escape_html(item.category || item.name || "") +
				"</span>",
		);
		set_row_cell_html(
			row,
			1,
			'<span class="bg-surface-container px-2 py-0.5 rounded text-[10px] font-bold">' +
				frappe.utils.escape_html(item.requirementClass || "—") +
				"</span>",
		);
		set_row_cell_text(row, 2, item.requirementType || "—");
		set_row_cell_html(row, 3, requirement_required_chip_html(item.required));
		var required_cell = row_cell(row, 3);
		if (required_cell) {
			required_cell.className = "px-container-padding py-4 text-center";
		}
		set_row_cell_text(row, 4, item.responseRequired || "—");
		set_row_cell_text(row, 5, item.complianceResponseType || "—");
		set_row_cell_html(
			row,
			6,
			'<span class="font-data-mono text-data-mono text-secondary">' +
				frappe.utils.escape_html(item.evalLinkage || "—") +
				"</span>",
		);
		set_row_cell_html(row, 7, requirement_carry_forward_html(item.contractCarryForward));
		var carry_cell = row_cell(row, 7);
		if (carry_cell) {
			carry_cell.className = "px-container-padding py-4 text-center";
		}
		set_row_cell_html(
			row,
			8,
			'<span class="text-body-md text-on-surface-variant">' +
				frappe.utils.escape_html(item.sourceAnchorId || "—") +
				"</span>",
		);
		set_row_cell_html(row, 9, requirement_validation_badge_html(item.validationStatus));
		set_actions_cell(row, 10, requirement_row_actions_html());
	}

	function price_schedule_row_actions_html() {
		return (
			'<button class="p-1 hover:text-primary" title="Open Schedule" data-std-prod-schema-action="open"><span class="material-symbols-outlined text-[20px]">open_in_new</span></button>' +
			'<button class="p-1 hover:text-primary" title="View Line Schema"><span class="material-symbols-outlined text-[20px]">schema</span></button>' +
			'<button class="p-1 hover:text-primary" title="View Formula"><span class="material-symbols-outlined text-[20px]">functions</span></button>' +
			'<button class="p-1 hover:text-primary" title="Preview Price Form"><span class="material-symbols-outlined text-[20px]">visibility</span></button>' +
			'<button class="p-1 hover:text-primary" title="View Source" data-std-prod-schema-action="source"><span class="material-symbols-outlined text-[20px]">history_edu</span></button>'
		);
	}

	function price_validation_badge_html(status) {
		var normalized = String(status || "VALID").toUpperCase();
		if (normalized === "BLOCKER") {
			return '<span class="status-badge bg-status-exhausted/10 text-status-exhausted">BLOCKER</span>';
		}
		if (normalized === "WARNING") {
			return '<span class="status-badge bg-status-reserved/10 text-status-reserved">WARNING</span>';
		}
		return '<span class="status-badge bg-status-available/10 text-status-available">VALID</span>';
	}

	function price_lifecycle_badge_html(state) {
		var normalized = String(state || "ACTIVE").toUpperCase();
		return (
			'<span class="status-badge bg-status-available/10 text-status-available">' +
			frappe.utils.escape_html(normalized) +
			"</span>"
		);
	}

	function price_required_chip_html(required) {
		if (required) {
			return '<span class="px-2 py-0.5 rounded bg-primary/10 text-primary text-[10px] font-bold">MANDATORY</span>';
		}
		return (
			'<span class="px-2 py-0.5 rounded bg-outline-variant/30 text-on-surface-variant text-[10px] font-bold">OPTIONAL</span>'
		);
	}

	function price_eval_linkage_html(value) {
		var label = String(value || "—");
		if (label === "EVAL_FINAL") {
			return '<span class="text-status-committed font-bold text-xs">' + frappe.utils.escape_html(label) + "</span>";
		}
		if (label.toLowerCase() === "validator") {
			return '<span class="text-status-available font-bold text-xs uppercase">' + frappe.utils.escape_html(label) + "</span>";
		}
		return '<span class="text-xs text-on-surface-variant">' + frappe.utils.escape_html(label) + "</span>";
	}

	function fill_price_schedule_row(row, item) {
		if (!row || !item) {
			return;
		}
		row.className = "hover:bg-surface-container-low transition-colors std-prod-price-row cursor-pointer";
		row.setAttribute("data-price-key", item.id || "");
		row.setAttribute("data-price-code", item.code || "");
		set_row_cell_html(
			row,
			0,
			'<span class="font-data-mono text-primary font-bold">' + frappe.utils.escape_html(item.code || item.id) + "</span>",
		);
		set_row_cell_html(
			row,
			1,
			'<span class="font-semibold text-primary block">' +
				frappe.utils.escape_html(item.name || "") +
				"</span>" +
				(item.description
					? '<span class="text-xs text-on-surface-variant">' + frappe.utils.escape_html(item.description) + "</span>"
					: ""),
		);
		set_row_cell_text(row, 2, item.pricingBasis || "—");
		set_row_cell_text(row, 3, item.currencyPolicy || "—");
		set_row_cell_text(row, 4, item.taxPolicy || "—");
		set_row_cell_text(row, 5, item.recurrentCost || "—");
		set_row_cell_html(
			row,
			6,
			'<span class="font-data-mono text-[11px] text-on-surface-variant">' +
				frappe.utils.escape_html(item.formulaRule || "—") +
				"</span>",
		);
		set_row_cell_html(row, 7, price_required_chip_html(item.required));
		set_row_cell_html(row, 8, price_eval_linkage_html(item.evalLinkage));
		set_row_cell_text(row, 9, item.contractCarry || "—");
		set_row_cell_html(
			row,
			10,
			'<span class="font-data-mono text-xs">' + frappe.utils.escape_html(item.sourceAnchorId || "—") + "</span>",
		);
		set_row_cell_html(row, 11, price_validation_badge_html(item.validationStatus));
		set_row_cell_html(row, 12, price_lifecycle_badge_html(item.lifecycleState));
		set_actions_cell(row, 13, price_schedule_row_actions_html());
	}

	function hydrate_price_schedules(doc, payload, ctx) {
		var data = payload.data || {};
		var items = data.priceSchedules || [];
		var summary = data.summary || {};
		ctx = sync_context_from_package_context(payload.packageContext, ctx);
		hydrate_breadcrumb_trail(doc, ctx, "Price Schedule Schema");
		update_headline_counters(
			doc,
			"Price Schedules",
			summary.priceSchedules != null ? summary.priceSchedules : data.count || items.length,
		);
		update_headline_counters(doc, "Total Summaries", summary.totalSummaries || 0);
		if (summary.evaluationLinksLocked != null) {
			update_headline_counters(doc, "Evaluation Links", summary.evaluationLinksLocked);
		}
		update_headline_counters(doc, "Contract Bindings", summary.contractBindings || items.length);
		var tbody = doc.querySelector("table tbody");
		render_design_rows(doc, tbody, items, "__stdProdPriceRowTemplate", fill_price_schedule_row, 200);
		hydrate_table_footer(doc, data.count || items.length, null, tbody);
		compact_schema_list_chrome(doc);
	}

	function evaluation_row_actions_html() {
		return (
			'<button class="text-primary font-label-caps text-[11px] hover:underline" title="View Source" data-std-prod-schema-action="source">VIEW SOURCE</button>'
		);
	}

	function fill_evaluation_row(row, item) {
		if (!row || !item) {
			return;
		}
		row.className = "hover:bg-surface-container-low transition-colors std-prod-eval-row cursor-pointer";
		row.setAttribute("data-eval-key", item.id || "");
		set_row_cell_html(
			row,
			0,
			'<span class="font-data-mono text-primary">' + frappe.utils.escape_html(item.code || item.id) + "</span>",
		);
		set_row_cell_text(row, 1, item.name || "—");
		set_row_cell_text(row, 2, "—");
		set_row_cell_text(row, 3, "—");
		set_row_cell_text(row, 4, "—");
		set_row_cell_text(row, 5, "—");
		set_row_cell_text(row, 6, "—");
		set_row_cell_text(row, 7, "—");
		set_row_cell_text(row, 8, "—");
		set_row_cell_html(row, 9, format_status_chip(item.validationStatus || "ACTIVE"));
		set_actions_cell(row, 10, evaluation_row_actions_html());
	}

	function hydrate_evaluation(doc, payload, ctx) {
		var data = payload.data || {};
		var schemas = data.schemas || [];
		var schema = schemas[0] || {};
		ctx = sync_context_from_package_context(payload.packageContext, ctx);
		hydrate_breadcrumb_trail(doc, ctx, "Evaluation Schema");
		doc.querySelectorAll("h1, .font-headline-sm").forEach(function (node) {
			if ((node.textContent || "").indexOf("Evaluation Schema") >= 0 && schema.name) {
				node.textContent = schema.name;
			}
		});
		update_headline_counters(doc, "Criteria", data.count || schemas.length);
		var tbody = doc.querySelector("table tbody");
		render_design_rows(doc, tbody, schemas, "__stdProdEvalRowTemplate", fill_evaluation_row, 200);
		hydrate_table_footer(doc, data.count || schemas.length, null, tbody);
		compact_schema_list_chrome(doc);
	}

	function hydrate_render_blocks(doc, payload, ctx) {
		var data = payload.data || {};
		var blocks = data.renderBlocks || [];
		ctx = sync_context_from_package_context(payload.packageContext, ctx);
		hydrate_breadcrumb_trail(doc, ctx, "Render Blocks");
		update_headline_counters(doc, "Render Block", data.count || blocks.length);
		var tbody = doc.querySelector("table tbody");
		render_design_rows(doc, tbody, blocks, "__stdProdRenderRowTemplate", fill_render_block_row, 200);
		hydrate_table_footer(doc, data.count || blocks.length, null, tbody);
		compact_schema_list_chrome(doc);
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
		ctx = sync_context_from_package_context(payload.packageContext, ctx);
		hydrate_breadcrumb_trail(doc, ctx, "Usage and Tender Bindings");
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
		ctx = sync_context_from_package_context(payload.packageContext, ctx);
		hydrate_breadcrumb_trail(doc, ctx, "Import Package Review");
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
		ctx = sync_context_from_package_context(payload.packageContext, ctx);
		hydrate_breadcrumb_trail(doc, ctx, "Version Diff and Supersession");
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
		if (results.version && results.version.packageContext) {
			ctx = sync_context_from_package_context(results.version.packageContext, ctx);
		}
		hydrate_breadcrumb_trail(doc, ctx, "Review and Approval");
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

	function resolve_module_map_focus(row_label) {
		return MODULE_ROW_MAP_FOCUS[row_label] || "";
	}

	function navigation_context_with_map_focus(ctx, row_label) {
		var next = Object.assign({}, ctx || get_context());
		var focus = resolve_module_map_focus(row_label);
		if (focus) {
			next.map_focus = focus;
		} else {
			delete next.map_focus;
		}
		return next;
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
		hydrate_library_breadcrumb(doc, ctx);
		hydrate_library_kpis(doc, kpis, data.libraryHealth);
		hydrate_table_footer(doc, total_families);
		var tbody = doc.querySelector("table tbody");
		if (!tbody || !families.length) {
			return;
		}
		var rows = Array.from(tbody.querySelectorAll("tr"));
		families.slice(0, rows.length).forEach(function (family, index) {
			var row = rows[index];
			if (!row) {
				return;
			}
			row.setAttribute("data-family-code", family.familyCode || "");
			row.setAttribute("data-package-id", family.latestPackageId || "");
			row.setAttribute("data-version-count", String(family.versionCount || 0));
			row.style.display = "";
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
			if (cells[2] && family.latestPackageId) {
				cells[2].innerHTML =
					'<span class="bg-surface-container-highest text-secondary text-[10px] px-2 py-0.5 font-bold rounded">' +
					frappe.utils.escape_html(family.latestPackageId) +
					"</span>";
			}
		});
		rows.forEach(function (row, index) {
			if (index >= families.length) {
				row.style.display = "none";
			}
		});
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
		hydrate_family_breadcrumb(doc, ctx);
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
		hydrate_version_breadcrumb(doc, ctx);
		doc.querySelectorAll("h1.font-display-lg").forEach(function (node) {
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
		ctx = sync_context_from_package_context(payload.packageContext, ctx);
		hydrate_breadcrumb_trail(doc, ctx, "Source Document & Traceability");
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
		ctx = sync_context_from_package_context(payload.packageContext, ctx);
		hydrate_breadcrumb_trail(doc, ctx, "Section and Clause Map");
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

		function select_section(section_id, options) {
			var section = find_section(section_id);
			if (!section) {
				return;
			}
			doc.__stdProdSelectedSectionId = section.id;
			doc.__stdProdClauseView = "section";
			render_section_tree(section.id);
			update_clause_header(section);
			render_clause_rows(section.id);
			apply_map_focus("sections", options && options.emphasize);
		}

		function section_label(section_id) {
			var section = find_section(section_id);
			if (!section) {
				return "—";
			}
			return section.code || section.name || section.id;
		}

		function render_all_clause_rows() {
			var clause_panel = doc.querySelector("table.w-full tbody");
			if (!clause_panel) {
				return;
			}
			if (!clauses.length) {
				clause_panel.innerHTML =
					"<tr><td class='px-4 py-6 text-on-surface-variant' colspan='11'>No clauses mapped for this version.</td></tr>";
				hydrate_table_footer(doc, 0);
				return;
			}
			clause_panel.innerHTML = clauses
				.map(function (clause) {
					return (
						"<tr class='std-prod-clause-row zebra-stripe border-b border-outline-variant/30 hover:bg-secondary/5 transition-colors group cursor-pointer' data-clause-id='" +
						frappe.utils.escape_html(clause.id) +
						"'><td class='px-4 py-3 font-data-mono'>" +
						frappe.utils.escape_html(clause.code || clause.id) +
						"</td><td class='px-4 py-3 font-semibold'>" +
						frappe.utils.escape_html(clause.name || clause.id) +
						"<div class='text-[10px] text-on-surface-variant font-data-mono'>" +
						frappe.utils.escape_html(section_label(clause.sectionId)) +
						"</div></td><td class='px-4 py-3 text-on-surface-variant'>—</td><td class='px-4 py-3 text-on-surface-variant'>—</td><td class='px-4 py-3 text-on-surface-variant'>" +
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
			hydrate_table_footer(doc, clauses.length);
		}

		function update_clause_inventory_header() {
			var header_wrap = doc.querySelector(".flex-1 .bg-surface-container-low .flex.items-center.gap-4");
			if (!header_wrap) {
				return;
			}
			var title_node = header_wrap.querySelector("h4");
			var subtitle_node = header_wrap.querySelector("span.text-body-md");
			if (title_node) {
				title_node.setAttribute("data-testid", "std-prod-clause-map-header");
				title_node.textContent = "Clause Inventory";
			}
			if (subtitle_node) {
				subtitle_node.setAttribute("data-testid", "std-prod-clause-map-subtitle");
				subtitle_node.textContent = String(clauses.length) + " clauses across all sections";
			}
		}

		function show_clause_inventory(emphasize) {
			doc.__stdProdClauseView = "all";
			var selected_section_id = doc.__stdProdSelectedSectionId || (sections.length ? sections[0].id : "");
			if (selected_section_id) {
				render_section_tree(selected_section_id);
			}
			update_clause_inventory_header();
			render_all_clause_rows();
			apply_map_focus("clauses", emphasize);
		}

		function apply_map_focus(focus, emphasize) {
			var aside = doc.querySelector("aside.w-80");
			var clause_panel = doc.querySelector(".flex-1.bg-white.border.border-border-subtle");
			var layout = doc.querySelector(".flex.gap-section-gap");
			if (layout) {
				layout.setAttribute("data-testid", "std-prod-section-clause-layout");
			}
			if (aside) {
				aside.setAttribute("data-testid", "std-prod-section-tree-panel");
			}
			if (clause_panel) {
				clause_panel.setAttribute("data-testid", "std-prod-clause-map-panel");
			}
			doc.body.setAttribute("data-std-prod-map-focus", focus || "");
			[aside, clause_panel].forEach(function (panel) {
				if (!panel) {
					return;
				}
				panel.classList.remove("ring-2", "ring-primary/40", "shadow-sm");
			});
			if (!emphasize) {
				return;
			}
			if (focus === "clauses" && clause_panel) {
				clause_panel.classList.add("ring-2", "ring-primary/40", "shadow-sm");
				return;
			}
			if (aside) {
				aside.classList.add("ring-2", "ring-primary/40", "shadow-sm");
			}
		}

		doc.__stdProdSectionsState = {
			sections: sections,
			clauses: clauses,
			selectSection: select_section,
			showClauseInventory: show_clause_inventory,
		};

		var map_focus = (ctx.map_focus || "").trim();
		if (map_focus === "clauses") {
			doc.__stdProdSelectedSectionId = sections.length ? sections[0].id : "";
			show_clause_inventory(true);
		} else {
			var initial_section_id = sections.length ? sections[0].id : "";
			if (initial_section_id) {
				select_section(initial_section_id, { emphasize: map_focus === "sections" });
			}
		}
	}

	function find_clause_panel(doc, heading) {
		var headers = doc.querySelectorAll("h2.font-label-bold, h3.font-label-bold");
		for (var i = 0; i < headers.length; i += 1) {
			if ((headers[i].textContent || "").indexOf(heading) < 0) {
				continue;
			}
			var section = headers[i].closest("section");
			if (section) {
				return section;
			}
		}
		return null;
	}

	function hydrate_clause(doc, payload, ctx) {
		var data = payload.data || {};
		var metadata = data.metadata || {};
		ctx = sync_context_from_package_context(payload.packageContext, ctx);
		var business_code = data.code || metadata.clause_code || "";
		var clause_name = data.name || metadata.display_title || business_code || "Clause Detail";
		hydrate_breadcrumb_trail(doc, ctx, clause_name, [
			{ label: "Section and Clause Map", route: "std-section-clauses" },
		]);
		var section_label = data.sectionTitle || "";
		var render_block = data.renderBlock || null;
		var text_status = data.textStatus || metadata.text_status || "";

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
				text_status.replace(/_/g, " ") ||
				data.validationStatus ||
				"Clause metadata loaded from STD package.";
		}

		doc.querySelectorAll("span.font-data-mono.text-on-surface-variant, span.font-data-mono").forEach(function (node) {
			var text = (node.textContent || "").trim();
			if (text.indexOf("Render Block:") >= 0) {
				node.textContent = render_block
					? "Render Block: " + (render_block.code || render_block.name)
					: "Render Block: pending template binding";
			}
			if (text.indexOf("Policy:") >= 0 && data.mutabilityType) {
				node.textContent = "Policy: " + String(data.mutabilityType).replace(/_/g, " ");
			}
			if (text.indexOf("ID: RB-ITT") === 0 || text === "RB-ITT-3.1-V2.4") {
				node.textContent = render_block
					? render_block.code || render_block.name || render_block.id
					: "No render block mapped";
			}
		});
		doc.querySelectorAll("span.font-data-mono").forEach(function (node) {
			var label = (node.textContent || "").trim();
			if (label.indexOf("UUID:") === 0) {
				node.textContent = business_code ? "Clause: " + business_code : "Clause";
				node.setAttribute("data-testid", "std-prod-clause-ref");
			}
		});

		var legal_section = find_clause_panel(doc, "Legal Source Text");
		if (legal_section) {
			var hash_value = data.normalizedTextHash || (data.metadata && data.metadata.normalized_text_hash) || "";
			legal_section.querySelectorAll("span.font-data-mono").forEach(function (node) {
				if ((node.textContent || "").indexOf("SHA-256:") === 0) {
					node.textContent = hash_value ? "SHA-256: " + hash_value : "SHA-256: unavailable";
				}
			});
			var legal_footer = legal_section.querySelector(".px-6.py-3.bg-surface");
			if (legal_footer) {
				legal_footer.innerHTML =
					'<div class="text-xs text-on-surface-variant italic">Source page references and verification stamps are not exposed in the Milestone 1 read model.</div>';
			}
		}

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
					frappe.utils.escape_html("Full legal text is not available for this clause.") +
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
					if (label === "Source Page") {
						value_node.textContent = data.sourceAnchorId || "—";
					}
					if (label === "Source File") {
						value_node.textContent = (ctx.package_id || "") + " / Official IT STD Source PDF";
					}
					if (label === "Last Verified By") {
						value_node.textContent = "Not exposed in Milestone 1 read model";
					}
				});
			}
		}

		var parameters_panel = find_clause_panel(doc, "Embedded Parameters");
		if (parameters_panel) {
			var parameters_container = parameters_panel.querySelector(".divide-y");
			if (parameters_container) {
				parameters_container.innerHTML =
					'<div class="p-4 text-on-surface-variant italic text-xs">Clause-level parameter bindings are not exposed in the Milestone 1 read model.</div>';
			}
		}

		var rules_panel = find_clause_panel(doc, "Linked Validation Rules");
		if (rules_panel) {
			var rules_container = rules_panel.querySelector(".divide-y");
			if (rules_container) {
				rules_container.innerHTML =
					'<div class="p-4 text-on-surface-variant italic text-xs">Clause-level validation rule bindings are not exposed in the Milestone 1 read model.</div>';
			}
		}

		var render_preview_section = find_clause_panel(doc, "Final Document Render Preview");
		if (!render_preview_section) {
			var preview_body = doc.querySelector("section .p-8.bg-white.m-4.border");
			render_preview_section = preview_body && preview_body.closest("section");
		}
		if (render_preview_section) {
			var render_badges = render_preview_section.querySelector(".flex.items-center.gap-2");
			if (render_badges) {
				if (render_block) {
					render_badges.innerHTML =
						'<span class="text-[10px] font-data-mono bg-surface text-on-surface-variant border border-outline-variant px-2 py-0.5 rounded" data-testid="std-prod-clause-render-block">' +
						frappe.utils.escape_html(render_block.code || render_block.name || render_block.id) +
						'</span><span class="text-[10px] bg-surface-container-high text-on-surface-variant px-2 py-0.5 rounded font-bold uppercase">' +
						frappe.utils.escape_html(render_block.validationStatus || "PENDING") +
						"</span>";
				} else {
					render_badges.innerHTML =
						'<span class="text-[10px] font-data-mono bg-surface text-on-surface-variant border border-outline-variant px-2 py-0.5 rounded">No render block mapped</span>';
				}
			}
		}

		var render_preview_body = render_preview_section && render_preview_section.querySelector(".p-8.bg-white.m-4.border");
		if (render_preview_body) {
			render_preview_body.setAttribute("data-testid", "std-prod-clause-render-preview");
			var clause_text = (data.clauseText || "").trim();
			if (clause_text) {
				render_preview_body.innerHTML =
					"<div class='max-w-[650px] mx-auto'><p class='font-bold mb-4'>" +
					frappe.utils.escape_html(clause_name) +
					"</p><p class='text-sm leading-6 whitespace-pre-wrap'>" +
					frappe.utils.escape_html(clause_text) +
					"</p></div>";
			} else {
				render_preview_body.innerHTML =
					"<div class='max-w-[650px] mx-auto space-y-3'><p class='font-bold'>" +
					frappe.utils.escape_html(clause_name) +
					"</p><p class='text-on-surface-variant italic text-sm'>" +
					frappe.utils.escape_html(
						text_status
							? "Render preview unavailable: " + text_status.replace(/_/g, " ") + "."
							: "Render preview unavailable until full clause text is extracted.",
					) +
					"</p>" +
					(render_block
						? "<p class='text-xs text-on-surface-variant'>Linked render block: <span class='font-data-mono'>" +
							frappe.utils.escape_html(render_block.code || render_block.name) +
							"</span> (" +
							frappe.utils.escape_html(render_block.validationStatus || "PENDING") +
							")</p>"
						: "") +
					"</div>";
			}
		}

		var audit_panel = find_clause_panel(doc, "Audit History");
		if (audit_panel) {
			var audit_timeline = audit_panel.querySelector(".relative.space-y-6, .space-y-6");
			if (audit_timeline) {
				audit_timeline.innerHTML =
					'<div class="text-on-surface-variant italic text-xs">Clause-level audit events are not exposed in the Milestone 1 read model.</div>';
			}
			var audit_count = audit_panel.querySelector("span.text-\\[10px\\].uppercase");
			if (audit_count) {
				audit_count.textContent = "0 Events";
			}
		}
		if (doc.body) {
			doc.body.setAttribute("data-std-clause-key", data.id || ctx.clause_key || "");
		}
	}

	function hydrate_validation(doc, payload, ctx) {
		var data = payload.data || {};
		var summary = data.summary || payload.validationSummary || {};
		ctx = sync_context_from_package_context(payload.packageContext, ctx);
		hydrate_breadcrumb_trail(doc, ctx, "Validation Report");
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
		ctx = sync_context_from_package_context(payload.packageContext, ctx);
		hydrate_breadcrumb_trail(doc, ctx, "Audit Log");
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
			return call_read("get_std_version_rules", {
				package_id: package_id,
				parameter_key: ctx.filter_parameter_key || "",
			}).then(function (r) {
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

	function navigate_schema_source(ctx) {
		navigate("std-source-doc", ctx);
	}

	function navigate_schema_section_map(ctx, map_focus) {
		navigate("std-section-clauses", {
			package_id: ctx.package_id,
			family_code: ctx.family_code,
			version_code: ctx.version_code || "",
			lifecycle_state: ctx.lifecycle_state || "",
			map_focus: map_focus || "",
		});
	}

	function navigate_schema_action_by_title(title, ctx, row_ctx) {
		var route = SCHEMA_ACTION_TITLE_ROUTES[title];
		if (!route) {
			return false;
		}
		var next_ctx = Object.assign({}, ctx || get_context(), row_ctx || {});
		if (route === "std-rule-dictionary" && next_ctx.parameter_key) {
			next_ctx.filter_parameter_key = next_ctx.parameter_key;
			delete next_ctx.parameter_key;
		}
		navigate(route, next_ctx);
		return true;
	}

	function schema_row_context_from_element(row, ctx) {
		if (!row) {
			return ctx || get_context();
		}
		return Object.assign({}, ctx || get_context(), {
			parameter_key: row.getAttribute("data-parameter-key") || "",
			rule_key: row.getAttribute("data-rule-key") || "",
			form_key: row.getAttribute("data-form-key") || "",
			render_block_code: row.getAttribute("data-render-block-code") || "",
			price_code: row.getAttribute("data-price-code") || "",
			map_focus: row.getAttribute("data-render-block-code") || row.getAttribute("data-price-code") || "",
		});
	}

	function handle_schema_action_button(screen, target, event, ctx) {
		var button = target.closest("button[title]");
		if (!button) {
			return false;
		}
		var title = (button.getAttribute("title") || "").trim();
		if (!title) {
			return false;
		}
		var row =
			target.closest(
				".std-prod-param-row, .std-prod-rule-row, .std-prod-form-row, .std-prod-render-row, .std-prod-req-row, .std-prod-price-row, .std-prod-eval-row",
			) || null;
		var row_ctx = schema_row_context_from_element(row, ctx);

		if (title === "Open") {
			event.preventDefault();
			event.stopPropagation();
			navigate("std-parameter-detail", row_ctx);
			return true;
		}
		if (title === "Open Rule") {
			event.preventDefault();
			event.stopPropagation();
			navigate("std-rule-detail", row_ctx);
			return true;
		}
		if (title === "Open Form" || title === "Preview Form") {
			event.preventDefault();
			event.stopPropagation();
			open_form_detail_from_row(row, row_ctx);
			return true;
		}
		if (title === "Open Render Block" || title === "Preview Output") {
			event.preventDefault();
			event.stopPropagation();
			navigate_schema_section_map(row_ctx, row_ctx.render_block_code || "");
			return true;
		}
		if (title === "Open Schedule") {
			event.preventDefault();
			event.stopPropagation();
			navigate_schema_section_map(row_ctx, row_ctx.price_code || "");
			return true;
		}
		if (navigate_schema_action_by_title(title, ctx, row_ctx)) {
			event.preventDefault();
			event.stopPropagation();
			return true;
		}
		return false;
	}

	function open_form_detail_from_row(form_row, ctx) {
		if (!form_row) {
			return;
		}
		navigate("std-form-detail-field-builder", {
			package_id: ctx.package_id,
			family_code: ctx.family_code,
			form_key: form_row.getAttribute("data-form-key"),
		});
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

				var breadcrumb_link = target.closest(".std-prod-breadcrumb-link");
				if (breadcrumb_link) {
					var breadcrumb_nav = resolve_breadcrumb_navigation(breadcrumb_link, ctx);
					if (breadcrumb_nav) {
						event.preventDefault();
						event.stopPropagation();
						navigate(breadcrumb_nav.route, breadcrumb_nav.ctx);
						return;
					}
				}

				if (screen === "library") {
					var library_row = target.closest("tr[data-family-code]");
					var library_btn = target.closest("button");
					if (library_btn && library_row) {
						var btn_text = (library_btn.textContent || "").trim();
						if (btn_text === "Open" || btn_text === "View Version" || btn_text.indexOf("Open / View Version") === 0) {
							event.preventDefault();
							event.stopPropagation();
							var family_code = library_row.getAttribute("data-family-code") || ctx.family_code;
							var package_id = library_row.getAttribute("data-package-id") || ctx.package_id;
							var version_count = parseInt(library_row.getAttribute("data-version-count") || "0", 10);
							if (btn_text === "View Version" || (version_count === 1 && package_id)) {
								navigate("std-version-detail", {
									family_code: family_code,
									package_id: package_id,
								});
							} else {
								navigate("std-family-detail", { family_code: family_code });
							}
						}
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
					var workspace_btn = target.closest("[data-std-workspace-route]");
					if (workspace_btn) {
						var workspace_route = workspace_btn.getAttribute("data-std-workspace-route");
						if (workspace_route) {
							event.preventDefault();
							event.stopPropagation();
							navigate(workspace_route, ctx);
							return;
						}
					}
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
							navigate(route, navigation_context_with_map_focus(ctx, name));
							return;
						}
					}
					return;
				}

				if (
					[
						"parameters",
						"rules",
						"forms",
						"renderBlocks",
						"requirements",
						"priceSchedules",
						"evaluation",
					].indexOf(screen) !== -1
				) {
					if (
						button_contains_label(target, "VIEW SOURCE") ||
						target.closest('[data-std-prod-schema-action="source"]')
					) {
						event.preventDefault();
						event.stopPropagation();
						navigate_schema_source(ctx);
						return;
					}
					if (handle_schema_action_button(screen, target, event, ctx)) {
						return;
					}
					if (screen === "parameters") {
						var param_row = target.closest(".std-prod-param-row");
						if (param_row) {
							event.preventDefault();
							event.stopPropagation();
							navigate("std-parameter-detail", schema_row_context_from_element(param_row, ctx));
						}
						return;
					}
					if (screen === "rules") {
						var rule_row = target.closest(".std-prod-rule-row");
						if (rule_row) {
							event.preventDefault();
							event.stopPropagation();
							navigate("std-rule-detail", schema_row_context_from_element(rule_row, ctx));
						}
						return;
					}
					if (screen === "forms") {
						var form_row = target.closest(".std-prod-form-row");
						if (form_row) {
							event.preventDefault();
							event.stopPropagation();
							open_form_detail_from_row(form_row, schema_row_context_from_element(form_row, ctx));
						}
						return;
					}
					if (screen === "renderBlocks") {
						var render_row = target.closest(".std-prod-render-row");
						if (
							render_row &&
							!target.closest(
								'button[title="Export Render Profile"], button[title="Create Draft Version"]',
							)
						) {
							event.preventDefault();
							event.stopPropagation();
							var render_ctx = schema_row_context_from_element(render_row, ctx);
							navigate_schema_section_map(render_ctx, render_ctx.render_block_code || "");
						}
						return;
					}
					if (screen === "requirements") {
						var req_row = target.closest(".std-prod-req-row");
						if (req_row) {
							event.preventDefault();
							event.stopPropagation();
							navigate_schema_source(ctx);
						}
						return;
					}
					if (screen === "priceSchedules") {
						var price_row = target.closest(".std-prod-price-row");
						if (price_row) {
							event.preventDefault();
							event.stopPropagation();
							var price_ctx = schema_row_context_from_element(price_row, ctx);
							navigate_schema_section_map(price_ctx, price_ctx.price_code || "");
						}
						return;
					}
					if (screen === "evaluation") {
						var eval_row = target.closest(".std-prod-eval-row");
						if (eval_row) {
							event.preventDefault();
							event.stopPropagation();
							navigate_schema_source(ctx);
						}
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
		if (!iframe || ["clause", "parameter", "rule", "form", "rules"].indexOf(screen) === -1) {
			return false;
		}
		var doc = iframe.contentDocument;
		if (!doc || !doc.body || doc.body.getAttribute("data-std-prod-hydrated") !== "1") {
			return false;
		}
		if (screen === "rules") {
			var last_filter = doc.body.getAttribute("data-std-filter-parameter-key") || "";
			var next_filter = fresh_ctx.filter_parameter_key || "";
			return last_filter !== next_filter;
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
				var payload = results.version || results.rules || results.forms || results.evaluation || results.renderBlocks;
				if (payload && payload.packageContext) {
					ctx = sync_context_from_package_context(payload.packageContext, ctx);
				} else if (results.parameters && results.parameters.packageContext) {
					ctx = sync_context_from_package_context(results.parameters.packageContext, ctx);
				} else if (results.parameter && results.parameter.packageContext) {
					ctx = sync_context_from_package_context(results.parameter.packageContext, ctx);
				} else if (results.rule && results.rule.packageContext) {
					ctx = sync_context_from_package_context(results.rule.packageContext, ctx);
				} else if (results.form && results.form.packageContext) {
					ctx = sync_context_from_package_context(results.form.packageContext, ctx);
				} else if (results.requirements && results.requirements.packageContext) {
					ctx = sync_context_from_package_context(results.requirements.packageContext, ctx);
				} else if (results.priceSchedules && results.priceSchedules.packageContext) {
					ctx = sync_context_from_package_context(results.priceSchedules.packageContext, ctx);
				}
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
	kentender.std_prod.resolve_std_route = resolve_std_route;
	kentender.std_prod.STD_PROD_REGISTERED_ROUTES = STD_PROD_REGISTERED_ROUTES;
	kentender.std_prod.mount_page = mount_page;
	kentender.std_prod.hydrate_iframe = hydrate_iframe;
	kentender.std_prod.claim_page_routes_over_doctype_conflicts =
		claim_page_routes_over_doctype_conflicts;
	kentender.std_prod.install_route_conflict_guard = install_route_conflict_guard;
	kentender.std_prod.preserve_procurement_sidebar = preserve_procurement_sidebar;
	kentender.std_prod.hydrate_table_footer = hydrate_table_footer;
	kentender.std_prod.install_hydration_gate = install_hydration_gate;
	kentender.std_prod.hydrate_page_header = hydrate_page_header;
	kentender.std_prod.normalize_page_layout = normalize_page_layout;

	install_route_conflict_guard();
	$(document).on("app_ready", claim_page_routes_over_doctype_conflicts);
})();
