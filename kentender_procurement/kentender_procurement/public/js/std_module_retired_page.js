(function () {
	"use strict";

	frappe.pages["std-module-retired"].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("STD Module Retired"),
			single_column: true,
		});
		if (
			window.kentender &&
			kentender.std_prod &&
			typeof kentender.std_prod.preserve_procurement_sidebar === "function"
		) {
			kentender.std_prod.preserve_procurement_sidebar();
		} else if (
			frappe.app &&
			frappe.app.sidebar &&
			typeof frappe.app.sidebar.setup === "function"
		) {
			frappe.app.sidebar.setup("Procurement");
		}

		var archive_path =
			"apps/kentender_v1/archive/std-module-poc-retired-2026-07/README.md";

		page.main.html(
			[
				'<div class="std-module-retired" data-testid="std-module-retired">',
				'  <div class="panel panel-default" style="max-width: 720px; margin: 2rem auto;">',
				'    <div class="panel-body">',
				'      <h3>' + __("STD Module POC — Archived") + "</h3>",
				"      <p>",
				__(
					"The POC-era STD stack (library, configurator, governance UI, instance runtime, and related Desk assets) has been retired from active use. Database records are preserved for forensic reference."
				),
				"      </p>",
				"      <p>",
				__(
					"A production-grade STD Library Management module will be designed and built on a clean slate. Until then, STD catalogue, configurator, and instance workflows are unavailable."
				),
				"      </p>",
				'      <p class="text-muted">',
				__("Archive reference:") + " <code>" + frappe.utils.escape_html(archive_path) + "</code>",
				"      </p>",
				"      <p>",
				'        <a class="btn btn-default btn-sm" href="/desk/procurement-home">',
				__("Return to Procurement Home"),
				"        </a>",
				"      </p>",
				"    </div>",
				"  </div>",
				"</div>",
			].join("")
		);
	};
})();
