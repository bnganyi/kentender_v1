frappe.provide("kentender_procurement.live");

(function () {
	"use strict";
	function client() { return kentender_procurement.planning_client; }
	function esc(value) { return client().escapeHtml(value); }
	function statusPill(label, success) {
		return '<span class="kt-pln-chip ' + (success ? "kt-pln-chip-success" : "kt-pln-chip-primary") + '">' + esc(label) + "</span>";
	}

	function bindPlanningReview($root) {
		if (!$root || !$root.length) return;
		$root.off(".ktPlnReviewTask");
		var task = client().routeContext().task;
		var dto = null;

		function render(data) {
			dto = data;
			$root.attr("data-kt-pln-live", "1");
			$root.find("[data-kt-pln-review-secondary]").text(data.procuring_entity_label + " Annual Procurement Plan " + data.financial_year + " · " + data.version_number_label);
			$root.find("[data-kt-pln-review-total]").text(data.planned_total_display);
			$root.find("[data-kt-pln-review-items]").text(data.item_count);
			$root.find("[data-kt-pln-review-finance-confirmed]").text(data.finance_confirmed_label);
			$root.find("[data-kt-pln-review-validation]").text(data.validation_projection);
			$root.find("[data-kt-pln-review-issues-copy]").text(data.issues_message);
			$root.find("[data-kt-pln-review-items-body]").html((data.items || []).map(function (row) {
				var change = row.change_label || (row.baseline_state === "Proposed" ? "Added" : "Unchanged");
				var added = change === "Added";
				return '<tr' + (added ? ' class="kt-pln-review-added"' : "") + '><td>' + statusPill(change, added) + '</td><td><div class="font-data-md text-primary text-sm font-semibold">' + esc(row.plan_item_code) + '</div><div class="text-body-sm">' + esc(row.title) + "</div></td><td>" + esc(row.owner_org_unit_label) + '</td><td class="text-right font-data-md text-sm">' + esc(row.amount_display) + "</td><td>" + esc(row.method || "—") + "</td><td>" + esc(row.completion || "—") + '</td><td class="text-center">' + statusPill(row.finance_status_label, row.finance_status_label === "Confirmed") + '</td><td class="text-center">' + statusPill(row.validation_projection, row.validation_projection === "Ready") + '</td><td><button class="text-primary font-medium" type="button" data-kt-review-item-route="' + esc(row.editor_route || "") + '">View Plan Item</button></td></tr>';
			}).join(""));
			$root.find("[data-kt-pln-review-history]").html((data.prior_decision_trail || []).map(function (row) {
				return '<div class="kt-pln-timeline-entry"><strong class="text-body-md">' + esc(row.label) + '</strong><div class="font-data-md text-sm text-on-surface-variant">by ' + esc(row.actor) + (row.actor_role ? " (" + esc(row.actor_role) + ")" : "") + ' <span aria-hidden="true">·</span> ' + esc(row.date) + "</div>" + (row.reason ? '<p class="text-body-sm text-on-surface-variant">' + esc(row.reason) + "</p>" : "") + "</div>";
			}).join("") || '<div class="kt-pln-timeline-entry"><strong>Submitted for professional review</strong><div class="text-body-sm text-on-surface-variant">Current review task</div></div>');
			$root.find("[data-kt-pln-action=approve-review]").prop("disabled", !data.can_approve).toggle(!!data.can_approve);
			$root.find("[data-kt-pln-action=return-review]").prop("disabled", !data.can_return).toggle(!!data.can_return);
		}

		client().call("get_plan_review", { task: task }).then(render).catch(function (error) {
			$root.html('<div role="alert" class="p-4 text-status-exhausted">' + esc(error.message) + "</div>");
		});
		function decide(method, reason) {
			var args = { task: task, expected_token: dto.task_token, idempotency_key: client().idempotencyKey(method, task) };
			args[method === "return_plan_version" ? "reason" : "note"] = reason;
			return client().call(method, args).then(function (result) {
				if (result.ok === false) {
					$root.find("[data-kt-pln-review-error]").text((result.errors && (result.errors.reason || result.errors.form)) || "Unable to record decision.").removeClass("hidden");
					return;
				}
				client().navigate(result.route);
			});
		}
		$root.on("click.ktPlnReviewTask", "[data-kt-pln-action=approve-review]", function () { decide("approve_plan_version", $root.find("[data-kt-pln-review-note]").val()); });
		$root.on("click.ktPlnReviewTask", "[data-kt-pln-action=return-review]", function () {
			var reason = $root.find("[data-kt-pln-review-note]").val();
			if (!reason) { $root.find("[data-kt-pln-review-error]").text("A return reason is required.").removeClass("hidden"); return; }
			decide("return_plan_version", reason);
		});
		$root.on("click.ktPlnReviewTask", "[data-kt-review-item-route]", function () { var route = $(this).attr("data-kt-review-item-route"); if (route) client().navigate(route); });
	}

	kentender_procurement.live.bindPlanningReview = bindPlanningReview;
})();
