(function () {
	"use strict";

	var ARCHIVE_PATH = "apps/kentender_v1/archive/it-std-wizard-retired-2026-07/README.md";

	/* UI-00 dashboard + UI-01 overview stub are live — do not bind them here. */
	var RETIRED_PAGE_NAMES = [
		"it-std-wizard-retired",
		"it-tender-configuration-tender-profile",
		"it-tender-configuration-tds",
		"it-tender-configuration-it-requirements",
		"it-tender-configuration-implementation-schedule",
		"it-tender-configuration-system-inventory",
		"it-tender-configuration-price-schedule",
		"it-tender-configuration-evaluation-setup",
		"it-tender-configuration-forms-and-evidence",
		"it-tender-configuration-scc",
		"it-tender-configuration-validation-report",
		"it-tender-configuration-review-and-approval",
		"it-tender-configuration-render-preview",
		"it-tender-configuration-publication-readiness",
	];

	function renderRetiredNotice(page) {
		page.main.html(
			[
				'<div class="it-std-wizard-retired" data-testid="it-std-wizard-retired">',
				'  <div class="panel panel-default" style="max-width: 720px; margin: 2rem auto;">',
				'    <div class="panel-body">',
				'      <h3>' + __("IT Tender Configuration Wizard — Retired") + "</h3>",
				"      <p>",
				__(
					"The IT Tender Configuration Wizard (v1 and v2) has been retired from active use. Tender-specific document setup will return in a future release built on the STD Engine.",
				),
				"      </p>",
				"      <p>",
				__(
					"Use Tender Management and STD Library workflows that remain available. TM2 publication paths that depended on wizard instances are unavailable until the replacement module ships.",
				),
				"      </p>",
				'      <p class="text-muted">',
				__("Archive reference:") +
					' <code>' +
					frappe.utils.escape_html(ARCHIVE_PATH) +
					"</code>",
				"      </p>",
				"      <p>",
				'        <a class="btn btn-default btn-sm" href="/desk/procurement-home">',
				__("Return to Procurement Home"),
				"        </a>",
				"      </p>",
				"    </div>",
				"  </div>",
				"</div>",
			].join(""),
		);
	}

	function bindPage(pageName) {
		frappe.pages[pageName].on_page_load = function (wrapper) {
			var page = frappe.ui.make_app_page({
				parent: wrapper,
				title: __("IT Tender Configuration Wizard — Retired"),
				single_column: true,
			});
			if (
				frappe.app &&
				frappe.app.sidebar &&
				typeof frappe.app.sidebar.setup === "function"
			) {
				frappe.app.sidebar.setup("Procurement");
			}
			renderRetiredNotice(page);
		};
	}

	for (var i = 0; i < RETIRED_PAGE_NAMES.length; i += 1) {
		bindPage(RETIRED_PAGE_NAMES[i]);
	}
})();
