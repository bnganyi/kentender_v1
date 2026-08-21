frappe.provide("kentender_procurement.planning_removal");

(function () {
	"use strict";
	var client = function () { return kentender_procurement.planning_client; };
	function esc(value) { return client().escapeHtml(value); }
	function uid() { return "pln-remove-" + Date.now() + "-" + Math.random().toString(16).slice(2); }

	function open(options) {
		options = options || {};
		var $host = options.$host && options.$host.length ? options.$host : $(document.body);
		var opener = options.opener || document.activeElement;
		var html = kentender_procurement.ui_fixtures.planning_remove_item_dialog();
		var $dialog = $(html).appendTo($host);
		var request = 0; var dto = null; var busy = false;
		function close() {
			request += 1; $dialog.off(".ktPlnRemoval").remove();
			if (opener && document.contains(opener)) opener.focus();
		}
		function sourceRows(rows) {
			return (rows || []).map(function (row) {
				return '<div class="border border-subtle rounded p-3"><div class="font-data-md">' + esc(row.demand_code) + '</div><div class="font-body-md font-medium">' + esc(row.title) + '</div><div class="font-body-sm text-on-surface-variant">' + esc(row.organisation_unit_label) + ' · ' + esc(row.need_item_count) + (row.need_item_count === 1 ? ' Need Item · ' : ' Need Items · ') + esc(row.amount_display) + '</div></div>';
			}).join("");
		}
		function paint(data) {
			dto = data; $dialog.find("[data-kt-pln-removal-title]").text(data.dialog_title);
			$dialog.find("[data-kt-pln-removal-intro]").text(data.intro_copy);
			$dialog.find("[data-kt-pln-removal-code]").text(data.plan_item_code);
			$dialog.find("[data-kt-pln-removal-item-title]").text(data.title);
			$dialog.find("[data-kt-pln-removal-owner]").text(data.ownership_label);
			$dialog.find("[data-kt-pln-removal-value]").text(data.planned_value_display);
			$dialog.find("[data-kt-pln-removal-finance]").text(data.finance_status);
			$dialog.find("[data-kt-pln-removal-effect]").text(data.effect_copy);
			$dialog.find("[data-kt-pln-removal-confirm-label]").text(data.confirm_label);
			$dialog.find("[data-kt-pln-removal-reason]").attr("placeholder", data.reason_placeholder);
			var combined = !!data.combined; $dialog.find("[data-kt-pln-removal-sources]").toggleClass("hidden", !combined).prop("hidden", !combined);
			$dialog.find("[data-kt-pln-removal-single-source]").toggleClass("hidden", combined).prop("hidden", combined);
			$dialog.find("[data-kt-pln-removal-source]").text((data.sources || []).map(function (r) { return r.demand_code; }).join(", ") + " · " + data.need_item_count + (data.need_item_count === 1 ? " Need Item" : " Need Items"));
			$dialog.find("[data-kt-pln-removal-source-rows]").html(sourceRows(data.sources));
			if (!data.can_remove) { $dialog.find("[data-kt-pln-removal-confirm]").prop("disabled", true); $dialog.find("[data-kt-pln-removal-error]").text("This Plan Item can no longer be removed.").prop("hidden", false); }
			$dialog.attr("aria-busy", "false"); $dialog.find("[data-kt-pln-removal-reason]").trigger("focus");
		}
		function load() {
			var id = ++request; $dialog.attr("aria-busy", "true");
			client().call("get_plan_item_removal", { plan: options.plan, plan_item: options.planItem }).then(function (data) { if (id === request) paint(data); }).catch(function (error) { if (id === request) $dialog.find("[data-kt-pln-removal-error]").text(error.message || "Removal details could not be loaded.").prop("hidden", false); });
		}
		$dialog.on("click.ktPlnRemoval", "[data-kt-pln-removal-cancel],[data-kt-pln-removal-backdrop]", close);
		$dialog.on("keydown.ktPlnRemoval", function (event) {
			if (event.key === "Escape") { event.preventDefault(); close(); return; }
			if (event.key === "Tab") { var nodes = $dialog.find('button:not(:disabled),textarea:not(:disabled)').filter(':visible').toArray(); if (!nodes.length) return; var first = nodes[0], last = nodes[nodes.length - 1]; if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); } else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); } }
		});
		$dialog.on("click.ktPlnRemoval", "[data-kt-pln-removal-confirm]", function () {
			if (!dto || busy) return; var reason = String($dialog.find("[data-kt-pln-removal-reason]").val() || "").trim(); var $error = $dialog.find("[data-kt-pln-removal-error]");
			if (!reason) { $error.text("A reason for removal is required.").prop("hidden", false); $dialog.find("[data-kt-pln-removal-reason]").attr("aria-invalid", "true").attr("aria-describedby", "kt-pln-removal-error").trigger("focus"); return; }
			busy = true; $error.prop("hidden", true); $dialog.find("button,textarea").prop("disabled", true); $dialog.attr("aria-busy", "true");
			client().call("remove_plan_item_from_plan", { plan: dto.plan, plan_item: dto.plan_item, draft_version: dto.draft_version, expected_version_token: dto.expected_version_token, reason: reason, idempotency_key: uid() }).then(function (result) {
				if (!result || result.ok === false) throw new Error(result && result.errors && (result.errors.reason || result.errors.form) || "Removal could not be completed.");
				close(); if (typeof options.onRemoved === "function") options.onRemoved(result);
			}).catch(function (error) { busy = false; $dialog.find("button,textarea").prop("disabled", false); $dialog.attr("aria-busy", "false"); $error.text(error.message || "Removal could not be completed.").prop("hidden", false); });
		});
		load(); return { close: close };
	}
	kentender_procurement.planning_removal.open = open;
})();
