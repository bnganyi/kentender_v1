(function () {
	"use strict";

	var PAGE_CONFIGS = {
		"std-source-doc": {
			page: "std-source-doc",
			title: __("Source Document & Traceability"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_source_doc.html",
			screen: "source",
			shell_class: "std-prod-std-source-doc-shell",
			root_class: "std-prod-std-source-doc-root",
			iframe_class: "std-prod-std-source-doc-iframe",
			testid: "std-prod-std-source-doc",
		},
		"std-section-clauses": {
			page: "std-section-clauses",
			title: __("Section and Clause Map"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_section_clauses.html",
			screen: "sections",
			shell_class: "std-prod-std-section-clauses-shell",
			root_class: "std-prod-std-section-clauses-root",
			iframe_class: "std-prod-std-section-clauses-iframe",
			testid: "std-prod-std-section-clauses",
		},
		"std-clause-detail": {
			page: "std-clause-detail",
			title: __("Clause Detail"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_clause_detail.html",
			screen: "clause",
			shell_class: "std-prod-std-clause-detail-shell",
			root_class: "std-prod-std-clause-detail-root",
			iframe_class: "std-prod-std-clause-detail-iframe",
			testid: "std-prod-std-clause-detail",
		},
		"std-validation-report": {
			page: "std-validation-report",
			title: __("Validation Report"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_validation_report.html",
			screen: "validation",
			shell_class: "std-prod-std-validation-report-shell",
			root_class: "std-prod-std-validation-report-root",
			iframe_class: "std-prod-std-validation-report-iframe",
			testid: "std-prod-std-validation-report",
		},
		"std-audit-log": {
			page: "std-audit-log",
			title: __("Audit Log"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_audit_log.html",
			screen: "audit",
			shell_class: "std-prod-std-audit-log-shell",
			root_class: "std-prod-std-audit-log-root",
			iframe_class: "std-prod-std-audit-log-iframe",
			testid: "std-prod-std-audit-log",
		},
	};

	Object.keys(PAGE_CONFIGS).forEach(function (page_name) {
		if (!frappe.pages[page_name]) {
			return;
		}
		var config = PAGE_CONFIGS[page_name];
		frappe.pages[page_name].on_page_load = function (wrapper) {
			frappe.require(
				[
					"/assets/kentender_procurement/js/std_prod_engine.js",
					"/assets/kentender_procurement/css/std_prod_vertical_slice_pages.css",
				],
				function () {
					kentender.std_prod.mount_page(wrapper, config);
				}
			);
		};
	});
})();
