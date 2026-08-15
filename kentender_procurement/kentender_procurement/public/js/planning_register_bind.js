frappe.provide("kentender_procurement.live");

(function () {
	"use strict";
	var client = function () { return kentender_procurement.planning_client; };

	function renderIdentity($root, values) {
		var esc = client().escapeHtml;
		$root.find("[data-kt-pln-register-identity]").html((values || []).map(function (row) {
			return '<div class="flex flex-col sm:flex-row sm:items-start border-b border-surface-container-high pb-stack-sm last:border-0 last:pb-0"><dt class="font-body-sm text-body-sm text-on-surface-variant sm:w-1/3">' + esc(row.label) + '</dt><dd class="' + (row.mono ? "font-data-md text-data-md" : "font-body-md text-body-md font-medium") + ' text-on-surface sm:w-2/3">' + esc(row.value) + "</dd></div>";
		}).join(""));
	}

	function bindPlanningRegister($root) {
		if (!$root || !$root.length) return;
		$root.off(".ktPlnRegisterRevision");
		var context = client().routeContext();
		var $form = $root.find("[data-kt-pln-register-form]");
		var $error = $root.find("[data-kt-pln-register-error]");
		var scope = null;
		function showError(message) { $error.removeClass("hidden").prop("hidden", false).text(message || __("Unable to load Plan registration.")); }
		function load() {
			var guard = client().requestGuard($root); guard.start();
			return client().call("get_planning_create_scope", { procuring_entity: context.procuring_entity, financial_year: context.financial_year }).then(function (data) {
				if (!guard.isCurrent()) return; scope = data; renderIdentity($root, data.identity_values);
				client().saveContext({ procuring_entity: data.procuring_entity, financial_year: data.financial_year });
				if (data.existing) { frappe.show_alert({ message: data.message, indicator: "blue" }); client().navigate(data.destination || data.route); }
			}).catch(function (error) { if (guard.isCurrent()) showError(error.message); }).finally(function () { guard.finish(); });
		}
		$root.on("click.ktPlnRegisterRevision", "[data-kt-pln-register-cancel]", function () {
			client().navigate("/app/planning-workspace?procuring_entity=" + encodeURIComponent(context.procuring_entity) + "&financial_year=" + encodeURIComponent(context.financial_year));
		});
		$form.on("submit.ktPlnRegisterRevision", function (event) {
			event.preventDefault(); if (!scope || !scope.can_create) return;
			var $button = $root.find('[data-testid="kt-pln-ui02-submit"]'); var $cancel = $root.find("[data-kt-pln-register-cancel]");
			$button.add($cancel).prop("disabled", true); $button.attr("aria-busy", "true"); $root.find("[data-kt-pln-register-submit-label]").text(__("Creating…")); $error.addClass("hidden").prop("hidden", true);
			client().call("create_procurement_plan", { procuring_entity: scope.procuring_entity, financial_year: scope.financial_year }).then(function (data) {
				if (!data || data.ok === false) { showError(data && data.errors ? Object.values(data.errors)[0] : __("Plan could not be created.")); return; }
				client().saveContext({ procuring_entity: scope.procuring_entity, financial_year: scope.financial_year, selectedRecord: data.plan }); client().navigate(data.route || data.redirect);
			}).catch(function (error) { showError(error.message); }).finally(function () { $button.add($cancel).prop("disabled", false); $button.attr("aria-busy", "false"); $root.find("[data-kt-pln-register-submit-label]").text(__("Create plan")); });
		});
		return load();
	}

	kentender_procurement.live.bindPlanningRegister = bindPlanningRegister;
})();
