/**
 * R5-001 / LV-R5-001-01 — Shared **Module Journey Context** header for source objects.
 *
 * Calls ``get_journey_by_object`` (pack §9.2) and renders a compact card with
 * ``data-testid="plc-module-journey-context-header"``. Other modules (e.g. TM2 Tender
 * R5-010) mount the same component by invoking ``render`` on a container element.
 */
(function () {
	frappe.provide("kentender_procurement");

	function render($host, opts) {
		var ot = String((opts && opts.object_type) || "").trim();
		var oc = String((opts && opts.object_code) || "").trim();
		$host.empty();

		if (!ot || !oc) {
			$host.append(
				$("<p>")
					.addClass("text-muted small mb-0")
					.attr("data-testid", "plc-module-journey-context-missing-params")
					.text(
						__(
							"Provide object_type and object_code (e.g. query string on the smoke page).",
						),
					),
			);
			return;
		}

		var $card = $('<div class="card plc-module-journey-context-header mb-0">')
			.attr("data-testid", "plc-module-journey-context-header")
			.attr("data-object-type", ot)
			.attr("data-object-code", oc);

		var $body = $('<div class="card-body py-2 px-3">');
		$body.append(
			$("<div>")
				.addClass("text-muted small")
				.attr("data-testid", "plc-module-journey-context-loading")
				.text(__("Loading journey context…")),
		);
		$card.append($body);
		$host.append($card);

		frappe.call({
			method:
				"kentender_procurement.procurement_lifecycle.api.journey_api.get_journey_by_object",
			args: { object_type: ot, object_code: oc },
			freeze: false,
			callback: function (r) {
				var payload = r && r.message;
				$body.empty();
				if (!payload || r.exc) {
					$body.append(
						$("<div>")
							.addClass("text-muted small")
							.attr("data-testid", "plc-module-journey-context-empty")
							.text(
								__(
									"No Procurement Journey is linked to this object, or you do not have access.",
								),
							),
					);
					return;
				}
				var jcode = String(payload.journey_code || "").trim();
				var title = String(payload.title || "").trim() || jcode;
				var stage = String(payload.current_stage || "").trim();
				var entity = String(payload.procuring_entity_code || "").trim();

				var $row = $('<div class="d-flex flex-wrap align-items-start justify-content-between gap-2">');
				var $left = $('<div class="min-w-0 flex-grow-1">');
				$left.append(
					$("<div>")
						.addClass("fw-semibold plc-module-journey-context-title")
						.attr("data-testid", "plc-module-journey-context-title")
						.text(title),
				);
				if (jcode) {
					$left.append(
						$("<div>")
							.addClass("text-muted small font-monospace")
							.attr("data-testid", "plc-module-journey-context-code")
							.text(jcode),
					);
				}
				if (entity) {
					$left.append(
						$("<div>")
							.addClass("text-muted small")
							.attr("data-testid", "plc-module-journey-context-entity")
							.text(entity),
					);
				}
				if (stage) {
					$left.append(
						$("<div>")
							.addClass("text-muted small mt-1")
							.attr("data-testid", "plc-module-journey-context-stage")
							.text(__("Current stage") + ": " + stage),
					);
				}

				var $btn = $('<a href="#" class="btn btn-sm btn-primary flex-shrink-0">')
					.attr("data-testid", "plc-module-journey-context-open")
					.text(__("Open journey"))
					.on("click", function (ev) {
						ev.preventDefault();
						if (jcode) {
							frappe.set_route("plc-procurement-journey", jcode);
						}
					});

				$row.append($left, $btn);
				$body.append($row);
			},
			error: function () {
				$body.empty().append(
					$("<div>")
						.addClass("alert alert-warning py-2 px-3 mb-0 small")
						.attr("data-testid", "plc-module-journey-context-error")
						.text(
							__(
								"Unable to load journey context. Check permissions or try again.",
							),
						),
				);
			},
		});
	}

	kentender_procurement.ModuleJourneyContextHeader = { render: render };
})();
