(function () {
	"use strict";

	frappe.provide("kentender.it_wizard.routes");

	var ITW_REGISTERED_ROUTES = [
		"it-tender-configuration-dashboard",
		"it-tender-configuration-overview",
		"it-tender-configuration-tender-profile",
		"it-tender-configuration-tds",
		"it-tender-configuration-it-requirements",
		"it-tender-configuration-implementation-schedule",
		"it-tender-configuration-system-inventory",
		"it-tender-configuration-price-schedule",
		"it-tender-configuration-evaluation-setup",
		"it-tender-configuration-forms-and-evidence",
		"it-tender-configuration-scc",
		"it-tender-configuration-validation-report",
		"it-tender-configuration-review-and-approval",
		"it-tender-configuration-render-preview",
		"it-tender-configuration-publication-readiness",
	];

	var CONFIGURATION_CONTEXT_ROUTES = {
		"it-tender-configuration-overview": 1,
		"it-tender-configuration-tender-profile": 1,
		"it-tender-configuration-tds": 1,
		"it-tender-configuration-it-requirements": 1,
		"it-tender-configuration-implementation-schedule": 1,
		"it-tender-configuration-system-inventory": 1,
		"it-tender-configuration-price-schedule": 1,
		"it-tender-configuration-evaluation-setup": 1,
		"it-tender-configuration-forms-and-evidence": 1,
		"it-tender-configuration-scc": 1,
		"it-tender-configuration-validation-report": 1,
		"it-tender-configuration-review-and-approval": 1,
		"it-tender-configuration-render-preview": 1,
		"it-tender-configuration-publication-readiness": 1,
	};

	var ROUTES = {
		DASHBOARD: "it-tender-configuration-dashboard",
		OVERVIEW: "it-tender-configuration-overview",
		VALIDATION: "it-tender-configuration-validation-report",
		PREVIEW: "it-tender-configuration-render-preview",
	};

	function desk_root_window() {
		return window;
	}

	function read_route_context(extraKeys) {
		var root = desk_root_window();
		var opts = root.frappe.route_options || {};
		var params = new URLSearchParams(root.location && root.location.search ? root.location.search : "");
		function pick(key) {
			return String(opts[key] || params.get(key) || "").trim();
		}
		var ctx = {
			configuration_id: pick("configuration_id"),
			procurement_package_id: pick("procurement_package_id"),
			tender_id: pick("tender_id"),
			std_version_id: pick("std_version_id"),
			plan_item_id: pick("plan_item_id"),
			procurement_entity_id: pick("procurement_entity_id"),
		};
		(extraKeys || []).forEach(function (key) {
			ctx[key] = pick(key);
		});
		return ctx;
	}

	function set_route_context(ctx) {
		var root = desk_root_window();
		root.frappe.route_options = Object.assign({}, root.frappe.route_options || {}, ctx || {});
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
		root.history.replaceState({}, "", url.pathname + url.search + url.hash);
	}

	function navigate(route, ctx) {
		if (
			window.kentender &&
			kentender.it_wizard &&
			typeof kentender.it_wizard.navigate === "function" &&
			kentender.it_wizard.navigate !== navigate
		) {
			kentender.it_wizard.navigate(route, ctx);
			return;
		}
		var normalized = String(route || "").trim();
		if (ITW_REGISTERED_ROUTES.indexOf(normalized) === -1) {
			frappe.msgprint({
				title: __("Navigation failed"),
				indicator: "red",
				message: __("Unknown IT Wizard page route: {0}", [route || ""]),
			});
			return;
		}
		if (ctx) {
			set_route_context(ctx);
		}
		if (normalized === ROUTES.DASHBOARD) {
			clear_configuration_id_from_url();
		}
		frappe.set_route(normalized);
		if (CONFIGURATION_CONTEXT_ROUTES[normalized] && ctx && ctx.configuration_id) {
			setTimeout(function () {
				sync_configuration_id_to_url(ctx.configuration_id);
			}, 0);
		}
	}

	function go_back_to_desk() {
		try {
			frappe.set_route("Workspaces", "Procurement");
		} catch (e) {
			frappe.set_route("/app");
		}
	}

	function consume_route_keys(keys) {
		if (!window.frappe || !frappe.route_options) {
			return;
		}
		(keys || []).forEach(function (key) {
			delete frappe.route_options[key];
		});
	}

	kentender.it_wizard.routes.ROUTES = ROUTES;
	kentender.it_wizard.routes.read_route_context = read_route_context;
	kentender.it_wizard.routes.navigate = navigate;
	kentender.it_wizard.routes.go_back_to_desk = go_back_to_desk;
	kentender.it_wizard.routes.consume_route_keys = consume_route_keys;
})();
