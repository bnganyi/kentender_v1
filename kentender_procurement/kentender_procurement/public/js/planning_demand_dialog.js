frappe.provide("kentender_procurement.planning_dialog");

(function () {
	"use strict";
	var client = function () { return kentender_procurement.planning_client; };

	function money(value, currency) { return (currency || "KES") + " " + Number(value || 0).toLocaleString("en-KE", { maximumFractionDigits: 2 }); }
	function dateLabel(value) { if (!value) return "—"; return frappe.datetime && frappe.datetime.str_to_user ? frappe.datetime.str_to_user(value) : value; }

	function open(options) {
		var $host = options.$host; var plan = options.plan; var selected = new Set(); var selectedById = new Map(); var rows = []; var lastFocus = document.activeElement; var timer = null; var loadSequence = 0;
		$host.html(kentender_procurement.ui_fixtures.planning_add_demand_dialog());
		var $dialog = $host.find("[data-kt-pln-add-demand-dialog]").removeClass("hidden").prop("hidden", false);
		$dialog.find("[data-kt-pln-elig-category]").closest(".w-full").hide();
		$dialog.find("[data-kt-pln-elig-remaining]").closest(".flex").hide();
		var $panel = $dialog.find("[role=dialog]"); var $body = $dialog.find("[data-kt-pln-elig-body]");

		function selectedRows() { return Array.from(selected).map(function (name) { return selectedById.get(name); }).filter(Boolean); }
		function renderSummary() {
			var current = selectedRows(); var amount = current.reduce(function (sum, row) { return sum + Number(row.available_to_plan || 0); }, 0); var needs = current.reduce(function (sum, row) { return sum + Number(row.need_item_count || 0); }, 0); var ous = new Set(current.map(function (row) { return row.organisation_unit; })).size;
			$dialog.find("[data-kt-pln-elig-count-label]").text(current.length + (current.length === 1 ? " Approved Demand selected" : " Approved Demands selected"));
			$dialog.find("[data-kt-pln-elig-ou-count]").text(ous + (ous === 1 ? " Organisation Unit" : " Organisation Units"));
			$dialog.find("[data-kt-pln-elig-amount]").text(money(amount, current[0] && current[0].currency));
			var multi = current.length > 1; $dialog.find("[data-kt-pln-formation-wrap]").toggleClass("hidden", !multi).prop("hidden", !multi);
			var mode = multi ? String($dialog.find("[data-kt-pln-formation-mode]:checked").val() || "separate") : "";
			var combined = mode === "combined"; $dialog.find("[data-kt-pln-formation-reason-wrap]").toggleClass("hidden", !combined).prop("hidden", !combined);
			var resultCount = combined || current.length === 1 ? 1 : current.length;
			$dialog.find("[data-kt-pln-formation-preview]").text("Result: " + resultCount + (combined ? " combined Plan Item" : resultCount === 1 ? " Plan Item" : " Plan Items") + " · " + money(amount, current[0] && current[0].currency) + " · " + current.length + " Demand sources · " + needs + " Need Items");
			var label = current.length === 1 ? "Add Demand and continue" : combined ? "Create combined Plan Item and continue" : "Create " + current.length + " Plan Items";
			$dialog.find("[data-kt-pln-ui04-cta-label]").text(label); $dialog.find("[data-kt-pln-action=elig-add]").prop("disabled", !current.length);
		}

		function renderRows() {
			var esc = client().escapeHtml;
			$body.html(rows.map(function (row) { var checked = selected.has(row.demand); return '<tr class="hover:bg-surface-container-low transition-colors relative' + (checked ? ' kt-pln-selected-row' : '') + '" data-demand="' + esc(row.demand) + '"><td class="px-4 py-4 whitespace-nowrap"><input class="h-4 w-4 text-primary focus:ring-primary border-border-subtle rounded cursor-pointer" aria-label="Select ' + esc(row.title) + '" type="checkbox" data-kt-demand-select ' + (checked ? "checked" : "") + '></td><td class="px-4 py-4 min-w-[260px]"><div class="font-body-sm text-body-sm text-on-surface font-medium mb-1">' + esc(row.title) + '</div><div class="font-data-md text-xs text-on-surface-variant">' + esc(row.demand_code) + '</div></td><td class="px-4 py-4"><div class="font-body-sm text-body-sm text-on-surface">' + esc(row.organisation_unit_label) + '</div></td><td class="px-4 py-4 text-right font-data-md">' + row.need_item_count + '</td><td class="px-4 py-4 whitespace-nowrap text-right font-data-md">' + esc(row.available_to_plan_display) + '</td><td class="px-4 py-4 whitespace-nowrap font-body-sm">' + esc(dateLabel(row.required_by)) + '</td><td class="px-4 py-4 font-body-sm">' + esc(row.proposed_budget_line_display || "—") + '</td><td class="px-4 py-4 whitespace-nowrap"><span class="inline-flex items-center px-2.5 py-0.5 rounded-full font-label-caps text-[10px] font-bold bg-status-available/10 text-status-available border border-status-available/20">Planning Ready</span></td></tr>'; }).join("")); renderSummary();
		}

		function load(background) {
			var sequence = ++loadSequence;
			$panel.attr("aria-busy", "true");
			return client().call("list_eligible_demands", { plan: plan, search: $dialog.find("[data-kt-pln-elig-search]").val() || "", organisation_unit: $dialog.find("[data-kt-pln-elig-ou]").val() || "", requested_demand: options.preselect || "" }).then(function (data) {
				if (sequence !== loadSequence) return;
				rows = data.demands || []; rows.forEach(function (row) { selectedById.set(row.demand, row); });
				if (options.preselect && rows.some(function (row) { return row.demand === options.preselect; })) selected.add(options.preselect);
				var $ou = $dialog.find("[data-kt-pln-elig-ou]"); var value = $ou.val(); $ou.html('<option value="">Organisation Unit: All permitted units</option>' + (data.organisation_unit_options || []).map(function (row) { return '<option value="' + client().escapeHtml(row.id) + '">' + client().escapeHtml(row.label) + "</option>"; }).join("")).val(value || "");
				renderRows(); if (data.requested_exclusion) frappe.show_alert({ message: data.requested_exclusion.reason, indicator: "orange" });
			}).finally(function () { if (sequence === loadSequence) $panel.attr("aria-busy", "false"); });
		}

		function close() { loadSequence += 1; clearTimeout(timer); $dialog.off(".ktPlnDialog").remove(); if (lastFocus && lastFocus.focus) lastFocus.focus(); }
		$dialog.on("click.ktPlnDialog", "[data-kt-pln-action=elig-close],[data-kt-pln-action=elig-cancel]", close);
		$dialog.on("change.ktPlnDialog", "[data-kt-demand-select]", function () { var name = $(this).closest("tr").attr("data-demand"); this.checked ? selected.add(name) : selected.delete(name); renderRows(); });
		$dialog.on("change.ktPlnDialog", "[data-kt-pln-formation-mode]", renderSummary);
		$dialog.on("input.ktPlnDialog", "[data-kt-pln-elig-search]", function () { clearTimeout(timer); timer = setTimeout(function () { load(true); }, 250); });
		$dialog.on("change.ktPlnDialog", "[data-kt-pln-elig-ou]", function () { load(true); });
		$dialog.on("keydown.ktPlnDialog", function (event) {
			if (event.key === "Escape") { event.preventDefault(); close(); return; }
			if (event.key !== "Tab") return;
			var focusable = $panel.find('button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href]').filter(":visible").toArray();
			if (!focusable.length) return;
			var first = focusable[0]; var last = focusable[focusable.length - 1];
			if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
			else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
		});
		$dialog.on("click.ktPlnDialog", "[data-kt-pln-action=elig-add]", function () {
			var current = selectedRows(); if (!current.length) return; var mode = current.length > 1 ? String($dialog.find("[data-kt-pln-formation-mode]:checked").val() || "separate") : ""; var reason = String($dialog.find("[data-kt-pln-formation-reason]").val() || "").trim();
			var key = "PLN-FORM-" + plan + "-" + Date.now() + "-" + Math.random().toString(36).slice(2, 8); var $button = $(this).prop("disabled", true).attr("aria-busy", "true");
			client().call("add_demand_to_plan", { plan: plan, demands: current.map(function (row) { return row.demand; }), expected_version_token: options.concurrencyToken || "", formation_mode: mode, formation_reason: reason, idempotency_key: key }).then(function (data) {
				if (!data || data.ok === false) { var errors = data && data.errors || {}; throw new Error(errors.formation_reason || errors.form || __("Plan Items could not be created.")); }
				close(); if (data.editor_route) client().navigate(data.editor_route); else if (options.onCreated) options.onCreated(data); else client().navigate(data.builder_route);
			}).catch(function (error) { $dialog.find('[data-kt-field-error="formation_reason"]').removeClass("hidden").prop("hidden", false).text(error.message); }).finally(function () { $button.prop("disabled", false).attr("aria-busy", "false"); });
		});
		load(false).then(function () { $dialog.find("[data-kt-pln-elig-search]").trigger("focus"); });
		return { close: close };
	}

	kentender_procurement.planning_dialog = { open: open };
})();
