(function () {
	"use strict";
	var PAGE = "my-work";
	var GET = "kentender_core.services.my_work.get_my_work";
	var CLAIM = "kentender_core.services.my_work.claim_my_work_task";
	function esc(v) { return frappe.utils.escape_html(String(v == null ? "" : v)); }
	function open(row) {
		if (!row || !row.route || !row.route.length) return;
		frappe.route_options = Object.assign({}, row.route_options || {});
		frappe.set_route.apply(frappe, row.route);
	}
	function rowHtml(row, bucket) {
		var action = bucket === "assigned"
			? '<button class="btn btn-primary btn-sm" data-open="' + esc(row.task_id) + '">' + esc(row.action_label) + "</button>"
			: bucket === "claimable"
				? '<button class="btn btn-default btn-sm" data-claim="' + esc(row.task_id) + '">' + __("Claim") + "</button>"
				: '<span>' + __("No decision is available while another actor owns this task.") + "</span>";
		return '<article class="kt-mw-row"><div><strong>' + esc(row.title) + '</strong><span class="kt-mw-ref">' + esc(row.reference) +
			'</span></div><div><i>' + __("Module and stage") + '</i><strong>' + esc(row.module) + '</strong><span>' + esc(row.stage) +
			'</span></div><div><i>' + __("Scope") + '</i><strong>' + esc(row.procuring_entity) + '</strong><span>' + esc(row.financial_year) +
			'</span></div><div><i>' + __("Assignment") + '</i><strong>' + esc(row.assignment) + '</strong><span>' + esc(row.status) +
			'</span></div><div><i>' + __("Received") + '</i><strong>' + esc(row.received_at) + '</strong><span>' +
			(row.due_at ? __("Due") + " " + esc(row.due_at) : __("No due date")) + '</span></div><div>' + action + "</div></article>";
	}
	function filtered(state) {
		var q = String(state.query || "").toLowerCase();
		return (state.data.buckets[state.tab] || []).filter(function (row) {
			return (!state.pe || row.procuring_entity === state.pe) && (!state.fy || row.financial_year === state.fy) &&
				(!q || [row.title, row.reference, row.module, row.stage, row.assignment].join(" ").toLowerCase().indexOf(q) >= 0);
		});
	}
	function paint(page, state) {
		var rows = filtered(state);
		page.main.find("[data-rows]").html(rows.length ? rows.map(function (row) { return rowHtml(row, state.tab); }).join("") :
			'<div class="kt-mw-empty"><strong>' + __("No work in this view") + '</strong><p>' + __("No tasks match this tab and its filters.") + "</p></div>");
		page.main.find("[data-open]").on("click", function () {
			var id = $(this).attr("data-open"); open(rows.find(function (row) { return row.task_id === id; }));
		});
		page.main.find("[data-claim]").on("click", function () {
			var id = $(this).attr("data-claim"), row = rows.find(function (item) { return item.task_id === id; });
			$(this).prop("disabled", true);
			frappe.call(CLAIM, { task_id: id, expected_token: row.concurrency_token }).then(function (r) {
				open(r.message && r.message.claimed_task);
			});
		});
	}
	function option(v) { return '<option value="' + esc(v) + '">' + esc(v) + "</option>"; }
	function render(page, data) {
		if (data.state === "no_assignment") {
			page.main.html('<section class="kt-mw-shell"><header class="kt-mw-hero"><div><small>' + __("Operational work") + '</small><h1>' +
				__("My Work") + '</h1><p>' + __("Your governed tasks across KenTender modules.") + '</p></div></header><div class="kt-mw-no-access"><b>!</b><div><h2>' +
				__("No active operational assignment") + '</h2><p>' + esc(data.message) + '</p><p>' +
				__("Ask your system access administrator to assign a capability profile and operational scope to this account.") +
				'</p><button class="btn btn-default" data-access>' + __("View my access") + "</button></div></div></section>");
			page.main.find("[data-access]").on("click", function () { frappe.set_route("user-operational-acc"); });
			return;
		}
		var counts = data.counts || {}, all = [].concat(data.buckets.assigned || [], data.buckets.claimable || [], data.buckets.waiting || []);
		var pes = Array.from(new Set((data.assignments || []).map(function (r) { return r.procuring_entity; }).filter(Boolean))).sort();
		var fys = Array.from(new Set(all.map(function (r) { return r.financial_year; }).filter(Boolean))).sort();
		page.main.html('<section class="kt-mw-shell"><header class="kt-mw-hero"><div><small>' + __("Operational work") + '</small><h1>' + __("My Work") +
			'</h1><p>' + __("Assigned, claimable, and relationship-safe waiting work across every active scope.") + '</p></div><a data-access>' +
			__("View my access") + '</a></header><div class="kt-mw-summary"><strong>' + esc(data.assignment_count) + '</strong><span>' +
			__("active operational assignments") + '</span></div><div class="kt-mw-toolbar"><nav class="kt-mw-tabs"><button class="active" data-tab="assigned">' +
			__("Assigned to me") + '<b>' + esc(counts.assigned || 0) + '</b></button><button data-tab="claimable">' + __("Available to claim") + '<b>' +
			esc(counts.claimable || 0) + '</b></button><button data-tab="waiting">' + __("Waiting on others") + '<b>' + esc(counts.waiting || 0) +
			'</b></button></nav><div class="kt-mw-filters"><select data-pe><option value="">' + __("All procuring entities") + '</option>' +
			pes.map(option).join("") + '</select><select data-fy><option value="">' + __("All financial years") + '</option>' + fys.map(option).join("") +
			'</select><input data-search type="search" placeholder="' + __("Search work") + '"></div></div><div class="kt-mw-head"><span>' + __("Work item") +
			'</span><span>' + __("Module and stage") + '</span><span>' + __("PE and FY") + '</span><span>' + __("Assignment") + '</span><span>' +
			__("Received") + '</span><span>' + __("Action") + '</span></div><div data-rows></div></section>');
		var state = { data: data, tab: "assigned", pe: "", fy: "", query: "" };
		page.main.find("[data-access]").on("click", function () { frappe.set_route("user-operational-acc"); });
		page.main.find("[data-tab]").on("click", function () {
			state.tab = $(this).attr("data-tab"); page.main.find("[data-tab]").removeClass("active"); $(this).addClass("active"); paint(page, state);
		});
		page.main.find("[data-pe]").on("change", function () { state.pe = this.value; paint(page, state); });
		page.main.find("[data-fy]").on("change", function () { state.fy = this.value; paint(page, state); });
		page.main.find("[data-search]").on("input", function () { state.query = this.value; paint(page, state); });
		paint(page, state);
	}
	function load(page) {
		page.main.html('<div class="kt-mw-loading">' + __("Loading your governed work...") + "</div>");
		return frappe.call(GET).then(function (r) { render(page, r.message || {}); });
	}
	frappe.pages[PAGE].on_page_load = function (wrapper) {
		frappe.require("/assets/kentender_procurement/css/my_work.css");
		wrapper.ktMyWork = frappe.ui.make_app_page({ parent: wrapper, title: __("My Work"), single_column: true });
		wrapper.ktMyWork.main.addClass("kt-my-work");
	};
	frappe.pages[PAGE].on_page_show = function (wrapper) { return load(wrapper.ktMyWork); };
})();
