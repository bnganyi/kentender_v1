/** G0-007 / LV-G0-012-02 — Desk Page `procurement-journey` placeholder until R4 journey timeline. */
(function () {
	frappe.provide("frappe.pages");
	frappe.pages["procurement-journey"] = frappe.pages["procurement-journey"] || {};

	frappe.pages["procurement-journey"].on_page_load = function (wrapper) {
		const $w = $(wrapper);
		$w.empty().append(
			$('<div class="container py-4">')
				.attr("data-testid", "plc-procurement-journey-placeholder")
				.append(
					$("<h4>").text(__("Procurement Journeys")),
					$("<p class='text-muted'>").text(
						__(
							"Placeholder: the lifecycle journey timeline will appear here when R4 ships.",
						),
					),
				),
		);
	};
})();
