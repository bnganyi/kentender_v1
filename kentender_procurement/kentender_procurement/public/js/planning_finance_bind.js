frappe.provide("kentender_procurement.planning_finance");
(function () {
	"use strict";
	var client = function () { return kentender_procurement.planning_client; };
	function set($root, hook, value) { $root.find("[data-kt-pln-07-" + hook + "]").text(value || "—"); }
	function open(options) {
		var $host = options.$host, task = options.task, dto = null, $drawer = $(kentender_procurement.ui_fixtures.planning_finance_confirm_drawer());
		$host.append($drawer); $drawer.removeClass("hidden").prop("hidden", false); $drawer.attr("role", "dialog").attr("aria-modal", "true");
		function close() { $drawer.remove(); if (options.onClose) options.onClose(); }
		function render(data) {
			dto = data; var shortfall = data.variant === "shortfall";
			$drawer.find("[data-kt-pln-07-variant=sufficient]").toggleClass("hidden", shortfall).prop("hidden", shortfall); $drawer.find("[data-kt-pln-07-variant=shortfall]").toggleClass("hidden", !shortfall).prop("hidden", !shortfall);
			set($drawer, "code", data.plan_item_code); set($drawer, "title", data.requirement_title); set($drawer, "plan", data.plan_title + " · " + data.version_label); set($drawer, "ou", data.owner_org_unit_label); set($drawer, "status", data.plan_item_status_label); set($drawer, "demand", data.source_demand_code + " · " + data.source_demand); set($drawer, "line", data.budget_line && data.budget_line.display); set($drawer, "amount", data.amount_display); set($drawer, "available", data.available_before_display); set($drawer, "balance", data.available_after_display); set($drawer, "shortfall", data.shortfall_display);
			var sources = (data.sources || []).map(function (s) { return '<div class="border border-subtle rounded p-3"><div class="flex justify-between gap-3"><strong>' + client().escapeHtml(s.demand_code + " · " + s.need_item) + '</strong><span class="font-data-md">' + client().escapeHtml(data.currency + " " + Number(s.amount).toLocaleString()) + '</span></div><div class="text-body-sm text-on-surface-variant">' + client().escapeHtml((s.budget_line && s.budget_line.display) || "No Budget Line") + '</div></div>'; }).join("");
			$drawer.find("[data-kt-pln-07-sources]").html(sources); $drawer.find("[data-kt-pln-07a-notice]").text(data.notice || ""); $drawer.find("[data-testid=kt-pln-ui07a-resolve]").attr("href", data.budget_funding_route); $drawer.find("[data-kt-pln-action=confirm-finance]").prop("disabled", !data.can_confirm);
		}
		client().call("get_plan_finance_task", { task: task }).then(render).catch(function (error) { frappe.msgprint(error.message); close(); });
		$drawer.on("click.ktPlnFinance", "[data-kt-pln-action=close-finance]", close);
		$drawer.on("click.ktPlnFinance", "[data-kt-pln-action=confirm-finance]", function () { var $b = $(this).prop("disabled", true); client().call("confirm_plan_item_funding", { task: task, expected_token: dto.task_token, note: $drawer.find("[data-kt-field=reason]:visible").val(), idempotency_key: client().idempotencyKey("finance-confirm", task) }).then(function (result) { if (result.ok === false) throw new Error(result.errors.form); close(); if (options.onComplete) return options.onComplete(result); client().navigate(dto.builder_route); }).catch(function (e) { frappe.msgprint(e.message); $b.prop("disabled", false); }); });
		$drawer.on("click.ktPlnFinance", "[data-kt-pln-action=return-finance]", function () { var reason = $drawer.find("[data-kt-field=reason]:visible").val(); if (!reason) { $drawer.find("[data-kt-field-error=reason]:visible").text("A return reason is required.").removeClass("hidden").prop("hidden", false); return; } client().call("return_plan_item_from_finance", { task: task, expected_token: dto.task_token, reason: reason, idempotency_key: client().idempotencyKey("finance-return", task) }).then(function (result) { if (result.ok === false) throw new Error(result.errors.form); close(); if (options.onComplete) return options.onComplete(result); client().navigate(dto.builder_route); }).catch(function (e) { frappe.msgprint(e.message); }); });
		return $drawer;
	}
	kentender_procurement.planning_finance.open = open;
})();
