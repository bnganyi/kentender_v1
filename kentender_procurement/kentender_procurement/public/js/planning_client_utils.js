frappe.provide("kentender_procurement.planning_client");

(function () {
	"use strict";
	var sequence = 0;

	function escapeHtml(value) {
		return String(value == null ? "" : value).replace(/[&<>"']/g, function (char) {
			return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char];
		});
	}

	function call(method, args) {
		// Frappe can return a jQuery Deferred from task-role Desk sessions. Wrap it
		// so all split Planning controllers receive the same native Promise contract
		// (including catch/finally) regardless of the current actor.
		return Promise.resolve(frappe.call({ method: "kentender_procurement.procurement_planning.api." + method, args: args || {}, freeze: false })).then(function (response) {
			return response && response.message !== undefined ? response.message : response;
		});
	}

	function routeContext() {
		var params = new URLSearchParams(window.location.search || "");
		var state = kentender_core.kt_state && kentender_core.kt_state.restore("procurement_planning");
		return {
			plan: params.get("plan") || (frappe.route_options && frappe.route_options.plan) || "",
			task: params.get("task") || (frappe.route_options && frappe.route_options.task) || "",
			finance_task: params.get("finance_task") || (frappe.route_options && frappe.route_options.finance_task) || "",
			procuring_entity: params.get("procuring_entity") || (frappe.route_options && frappe.route_options.procuring_entity) || (state && state.procuring_entity) || "",
			financial_year: params.get("financial_year") || (frappe.route_options && frappe.route_options.financial_year) || (state && state.financial_year) || "",
			add_demand: params.get("add_demand") || (frappe.route_options && frappe.route_options.add_demand) || "",
		};
	}

	function idempotencyKey(command, record) {
		if (window.crypto && window.crypto.randomUUID) return command + ":" + record + ":" + window.crypto.randomUUID();
		return command + ":" + record + ":" + Date.now() + ":" + Math.random().toString(36).slice(2);
	}

	function saveContext(partial) {
		if (kentender_core.kt_state) kentender_core.kt_state.save("procurement_planning", partial || {});
	}

	function navigate(route) {
		var parsed = new URL(route, window.location.origin);
		var slug = parsed.pathname.replace(/^\/(app|desk)\//, "").replace(/^\//, "");
		var options = {};
		parsed.searchParams.forEach(function (value, key) { options[key] = value; });
		frappe.route_options = Object.assign({}, frappe.route_options || {}, options);
		frappe.set_route(slug);
	}

	function requestGuard($root) {
		var id = ++sequence;
		$root.attr("aria-busy", "true");
		return {
			id: id,
			isCurrent: function () { return Number($root.attr("data-kt-request-id")) === id && $.contains(document, $root[0]); },
			start: function () { $root.attr("data-kt-request-id", id); },
			finish: function () { if (this.isCurrent()) $root.attr("aria-busy", "false"); },
		};
	}

	kentender_procurement.planning_client = { escapeHtml: escapeHtml, call: call, routeContext: routeContext, saveContext: saveContext, navigate: navigate, requestGuard: requestGuard, idempotencyKey: idempotencyKey };
})();
