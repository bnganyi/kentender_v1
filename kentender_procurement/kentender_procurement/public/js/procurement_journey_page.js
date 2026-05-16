/** G0-007 / R4-005 — Desk Page `plc-procurement-journey` (placeholder until full journey UI). */
(function () {
	frappe.provide("frappe.pages");
	const PAGE_NAME = "plc-procurement-journey";
	frappe.pages[PAGE_NAME] = frappe.pages[PAGE_NAME] || {};

	function optionValue(val) {
		if (val == null || val === "") return "";
		try {
			return String(JSON.parse(val)).trim();
		} catch (e) {
			return String(val).trim();
		}
	}

	function journeyCodeFromRoute() {
		try {
			const opts = frappe.route_options || {};
			if (opts.journey_code) {
				return optionValue(opts.journey_code);
			}
		} catch (e) {
			/* ignore */
		}
		try {
			const params = new URLSearchParams(window.location.search || "");
			if (params.has("journey_code")) {
				return optionValue(params.get("journey_code"));
			}
		} catch (e2) {
			/* ignore */
		}
		return "";
	}

	frappe.pages[PAGE_NAME].on_page_load = function (wrapper) {
		const $w = $(wrapper);
		const journeyCode = journeyCodeFromRoute();
		const $container = $('<div class="container py-4">').attr(
			"data-testid",
			"plc-procurement-journey-placeholder",
		);
		$container.append($("<h4>").text(__("Procurement Journeys")));
		if (journeyCode) {
			$container.append(
				$('<p class="text-muted small mb-2">')
					.attr("data-testid", "plc-journey-route-code")
					.text(journeyCode),
			);
		}
		$container.append(
			$("<p class='text-muted'>").text(
				__(
					"Placeholder: the lifecycle journey timeline will appear here when R4 ships.",
				),
			),
		);
		$w.empty().append($container);
	};
})();
