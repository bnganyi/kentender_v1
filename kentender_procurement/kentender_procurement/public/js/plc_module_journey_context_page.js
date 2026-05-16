/**
 * R5-001 — Desk Page **plc-module-journey-context** (smoke / QA host for ``ModuleJourneyContextHeader``).
 *
 * Optional query: ``?object_type=TM2%20Tender&object_code=TND-MOH-2026-001``
 */
(function () {
	const PAGE_NAME = "plc-module-journey-context";
	frappe.provide("frappe.pages");
	frappe.pages[PAGE_NAME] = frappe.pages[PAGE_NAME] || {};

	function queryParam(name) {
		try {
			var sp = new URLSearchParams(window.location.search || "");
			return String(sp.get(name) || "").trim();
		} catch (e) {
			return "";
		}
	}

	function runPage(wrapper) {
		var $wrap = $(wrapper);
		var $outer = $('<div class="plc-module-journey-context-page kt-plc-module-journey-context">').attr(
			"data-testid",
			"plc-module-journey-context-page",
		);
		var $container = $('<div class="container py-4">');
		var ot = queryParam("object_type");
		var oc = queryParam("object_code");
		$container.append(
			$("<h4>")
				.addClass("mb-3 text-muted")
				.attr("data-testid", "plc-module-journey-context-page-title")
				.text(__("Procurement journey context (module)")),
		);
		var $host = $('<div class="plc-module-journey-context-host">').attr(
			"data-testid",
			"plc-module-journey-context-host",
		);
		$container.append($host);
		$outer.append($container);
		$wrap.empty().append($outer);

		if (
			kentender_procurement &&
			kentender_procurement.ModuleJourneyContextHeader &&
			kentender_procurement.ModuleJourneyContextHeader.render
		) {
			kentender_procurement.ModuleJourneyContextHeader.render($host, {
				object_type: ot,
				object_code: oc,
			});
		} else {
			$host.append(
				$("<div>")
					.addClass("alert alert-danger mb-0")
					.text(__("ModuleJourneyContextHeader script failed to load.")),
			);
		}
	}

	frappe.pages[PAGE_NAME].on_page_load = function (wrapper) {
		runPage(wrapper);
	};
	frappe.pages[PAGE_NAME].on_page_show = function (wrapper) {
		runPage(wrapper);
	};
})();
