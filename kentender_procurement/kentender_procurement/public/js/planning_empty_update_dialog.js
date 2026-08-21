frappe.provide("kentender_procurement.planning_empty_update");

(function () {
	"use strict";
	var active = null;
	function open(options) {
		if (active) active.close();
		var client = kentender_procurement.planning_client;
		var $host = options.$host, opener = options.opener, request = 0, key = "";
		$host.append(kentender_procurement.planning_fixtures.emptyUpdateCancel());
		var $dialog = $host.find("[data-kt-pln-05b]").last();
		function close() { request += 1; $dialog.off(".ktPln05b").remove(); active = null; if (opener && document.contains(opener)) opener.focus(); }
		active = { close: close };
		function setError(message) { $dialog.find("[data-kt-pln-05b-error]").text(message || "").prop("hidden", !message); }
		function focusables() { return $dialog.find("button:visible:not(:disabled)"); }
		$dialog.on("keydown.ktPln05b", function (event) {
			if (event.key === "Escape") { event.preventDefault(); close(); return; }
			if (event.key !== "Tab") return;
			var $items = focusables(), first = $items[0], last = $items[$items.length - 1];
			if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
			else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
		});
		$dialog.on("click.ktPln05b", "[data-kt-pln-05b-keep]", close);
		var current = ++request;
		client.call("get_empty_plan_update_cancellation", { plan: options.plan, successor_version: options.successorVersion }).then(function (dto) {
			if (current !== request || !$dialog.length) return;
			options.successorVersion = dto.successor_version;
			$dialog.data("dto", dto);
			$dialog.find("[data-kt-pln-05b-copy]").text(dto.draft_version_label + " no longer contains any changes. Cancelling it will remove the empty Draft from current work and keep " + dto.approved_version_label.replace("Version", "Approved Version") + " active.");
			$dialog.find("[data-kt-pln-05b-approved]").text(dto.approved_version_label);
			$dialog.find("[data-kt-pln-05b-value]").text(dto.approved_value_display);
			$dialog.find("[data-kt-pln-05b-draft]").text(dto.draft_version_label);
			$dialog.find("[data-kt-pln-05b-changes]").text(dto.effective_change_count);
			var tender = dto.tender_reference ? " Tender " + dto.tender_reference : " its Tender handoff";
			$dialog.find("[data-kt-pln-05b-info]").text("This does not cancel the annual Plan or affect the Approved Plan Item, its funding or" + tender + ".");
			$dialog.find("[data-kt-pln-05b-confirm]").prop("disabled", !dto.can_cancel);
			$dialog.find("[data-kt-pln-05b-keep]").trigger("focus");
		}).catch(function (error) { setError(error.message || "The Plan update could not be loaded."); });
		$dialog.on("click.ktPln05b", "[data-kt-pln-05b-confirm]", function () {
			var dto = $dialog.data("dto"); if (!dto || !dto.can_cancel) return;
			var $buttons = $dialog.find("button").prop("disabled", true); setError("");
			key = key || client.idempotencyKey("cancel-empty-plan-update", options.plan);
			client.call("cancel_empty_plan_update", { plan: options.plan, successor_version: dto.successor_version, expected_version_token: dto.concurrency_token, idempotency_key: key }).then(function (result) {
				if (result.ok === false) { setError((result.errors && result.errors.form) || "The empty update could not be cancelled."); $buttons.prop("disabled", false); return; }
				close(); client.navigate(result.route || dto.approved_route);
			}).catch(function (error) { setError(error.message || "The empty update could not be cancelled."); $buttons.prop("disabled", false); });
		});
		return active;
	}
	kentender_procurement.planning_empty_update.open = open;
})();
