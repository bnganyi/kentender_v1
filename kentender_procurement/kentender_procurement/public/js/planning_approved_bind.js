frappe.provide("kentender_procurement.live");

(function () {
	"use strict";
	function client() { return kentender_procurement.planning_client; }
	function esc(value) { return client().escapeHtml(value); }
	function routeAction(actions, name) {
		var action = actions && actions[name];
		return action && typeof action.route === "string" && action.route ? action : null;
	}
	function handlerAction(actions, name, handler) {
		var action = actions && actions[name];
		return action && action.handler === handler ? action : null;
	}

	function bindPlanningApproved($root, options) {
		if (!$root || !$root.length) return;
		$root.off(".ktPlnApprovedCurrent");
		$root.find("[data-kt-pln-action=export-approved]").remove();
		var context = client().routeContext();
		var plan = (options && options.plan) || context.plan;
		var selectedPlanItem = (options && options.planItem) || context.plan_item;
		var dto = null;

		function openDemandDialog(preselect, opener) {
			if (!dto || !routeAction(dto.actions, "add_demand")) return;
			kentender_procurement.planning_dialog.open({
				$host: $root.find("[data-kt-pln-dialog-host]"), plan: plan,
				preselect: preselect || "", concurrencyToken: dto.concurrency_token, opener: opener,
				onCreated: function (result) {
					var continuation = routeAction(dto.actions, "continue_update");
					var destination = result && result.builder_route;
					if (destination || continuation) client().navigate(destination || continuation.route);
				},
			});
		}

		function renderItems(rows) {
			var html = (rows || []).map(function (row) {
				var view = routeAction(row.actions, "view");
				var removal = handlerAction(row.actions, "propose_removal", "plan_item_removal");
				var actionHtml = view ? '<button class="text-primary" data-kt-plan-item-view="' + esc(view.route) + '">' + esc(view.label || "View") + "</button>" : "";
				if (removal) actionHtml += '<button class="ml-2" aria-label="' + esc(removal.label || "Propose removal") + '" data-kt-pln-action="propose-removal" data-kt-plan-item-remove="' + esc(removal.plan_item) + '"><span class="material-symbols-outlined">more_vert</span></button>';
				return '<tr data-kt-pln-ui09-row data-plan-item="' + esc(row.plan_item) + '"><td><strong>' + esc(row.title) + '</strong><div class="font-data-md text-xs">' + esc(row.plan_item_code) + "</div></td><td>" + esc(row.owner_org_unit_label) + '</td><td class="text-right font-data-md">' + esc(row.amount_display) + "</td><td>" + esc(row.takeup_label) + (row.tender_reference ? '<div class="font-data-md text-xs">' + esc(row.tender_reference) + "</div>" : "") + "</td><td>" + esc(row.milestone_label || "—") + "</td><td>" + esc(row.actual_progress_label) + "</td><td>" + esc(row.variance_label) + "</td><td>" + actionHtml + "</td></tr>";
			}).join("");
			$root.find("[data-kt-pln-ui09-body]").html(html || '<tr><td colspan="8" class="p-8 text-center text-on-surface-variant">No Plan Items match these filters.</td></tr>');
		}

		function applyFilters() {
			if (!dto) return;
			var ou = $root.find('[data-kt-pln-ui09-filter="ou"]').val() || "";
			var status = $root.find('[data-kt-pln-ui09-filter="status"]').val() || "";
			renderItems((dto.items || []).filter(function (row) { return (!ou || row.owner_org_unit === ou) && (!status || row.actual_progress_label === status); }));
		}

		function render(data) {
			dto = data;
			$root.find("[data-kt-pln-action=export-approved]").remove();
			$root.attr("data-kt-pln-live", "1");
			$root.find("[data-kt-pln-ui09-title]").text(data.title);
			$root.find("[data-kt-pln-ui09-version]").text(data.version_label);
			$root.find("[data-kt-pln-ui09-approved-evidence]").text(data.version_history && data.version_history[0] && data.version_history[0].approved_by ? "Approved by " + data.version_history[0].approved_by : "");
			$root.find("[data-kt-pln-ui09-total]").text(data.planned_total_display);
			$root.find("[data-kt-pln-ui09-items]").text(data.item_count);
			$root.find("[data-kt-pln-ui09-finance]").text(data.items.filter(function (row) { return row.finance_status === "Confirmed"; }).length + " of " + data.item_count);
			$root.find("[data-kt-pln-ui09-takeup]").text(data.takeup_label);
			$root.find('[data-kt-pln-ui09-filter="period"]').html("<option>" + esc(data.reporting_period_label) + "</option>");
			$root.find("[data-kt-pln-ui09-as-at]").text(data.as_at_display);
			$root.find('[data-kt-pln-ui09-filter="ou"]').html('<option value="">All permitted units</option>' + (data.ou_options || []).map(function (row) { return '<option value="' + esc(row.id) + '">' + esc(row.label) + "</option>"; }).join(""));
			var statuses = [];
			(data.items || []).forEach(function (row) { if (row.actual_progress_label && statuses.indexOf(row.actual_progress_label) < 0) statuses.push(row.actual_progress_label); });
			$root.find('[data-kt-pln-ui09-filter="status"]').html('<option value="">All statuses</option>' + statuses.map(function (value) { return '<option value="' + esc(value) + '">' + esc(value) + "</option>"; }).join(""));
			renderItems(selectedPlanItem ? (data.items || []).filter(function (row) { return row.plan_item === selectedPlanItem; }) : data.items || []);
			$root.find("[data-kt-pln-ui09-history]").html((data.version_history || []).map(function (row) { return '<div class="p-4 border-b border-subtle flex justify-between"><span class="font-data-md">' + esc(row.version_code) + "</span><span>" + esc(row.status) + "</span></div>"; }).join(""));
			var continuation = routeAction(data.actions, "continue_update");
			$root.find("[data-kt-pln-ui09-successor]").toggleClass("hidden", !continuation).prop("hidden", !continuation);
			$root.find("[data-kt-pln-ui09-successor-copy]").text(data.successor_copy);
			$root.find("[data-kt-pln-action=add-demand]").toggle(!!routeAction(data.actions, "add_demand"));
			if (context.add_demand && routeAction(data.actions, "add_demand")) {
				var preselect = context.add_demand === "1" ? "" : context.add_demand;
				context.add_demand = "";
				openDemandDialog(preselect);
			}
		}

		client().call("get_plan_implementation", { plan: plan }).then(render).catch(function (error) { $root.html('<div role="alert" class="p-4 text-status-exhausted">' + esc(error.message) + "</div>"); });
		$root.on("change.ktPlnApprovedCurrent", '[data-kt-pln-ui09-filter="ou"],[data-kt-pln-ui09-filter="status"]', applyFilters);
		$root.on("click.ktPlnApprovedCurrent", "[data-kt-pln-action=continue-update]", function () { var action = dto && routeAction(dto.actions, "continue_update"); if (action) client().navigate(action.route); });
		$root.on("click.ktPlnApprovedCurrent", "[data-kt-pln-action=add-demand]", function () { openDemandDialog("", this); });
		$root.on("click.ktPlnApprovedCurrent", "[data-kt-plan-item-view]", function () { var route = $(this).attr("data-kt-plan-item-view"); if (route) client().navigate(route); });
		$root.on("click.ktPlnApprovedCurrent", "[data-kt-plan-item-remove]", function () {
			kentender_procurement.planning_removal.open({
				$host: $root.find("[data-kt-pln-dialog-host]"), plan: plan,
				planItem: $(this).attr("data-kt-plan-item-remove"), opener: this,
				onRemoved: function (result) { if (result && result.destination) client().navigate(result.destination); },
			});
		});
	}

	kentender_procurement.live.bindPlanningApproved = bindPlanningApproved;
})();
