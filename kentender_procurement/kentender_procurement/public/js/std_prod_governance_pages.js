(function () {
	"use strict";

	var PAGE_CONFIGS = {
		"std-review-and-approval": {
			page: "std-review-and-approval",
			title: __("Review and Approval"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_review_and_approval.html",
			screen: "review",
			shell_class: "std-prod-std-review-and-approval-shell",
			root_class: "std-prod-std-review-and-approval-root",
			iframe_class: "std-prod-std-review-and-approval-iframe",
			testid: "std-prod-std-review-and-approval",
		},
		"std-usage-and-tender-bindings": {
			page: "std-usage-and-tender-bindings",
			title: __("Usage and Tender Bindings"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_usage_and_tender_bindings.html",
			screen: "usage",
			shell_class: "std-prod-std-usage-and-tender-bindings-shell",
			root_class: "std-prod-std-usage-and-tender-bindings-root",
			iframe_class: "std-prod-std-usage-and-tender-bindings-iframe",
			testid: "std-prod-std-usage-and-tender-bindings",
		},
		"std-import-package-review": {
			page: "std-import-package-review",
			title: __("Import Package Review"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_import_package_review.html",
			screen: "importReview",
			shell_class: "std-prod-std-import-package-review-shell",
			root_class: "std-prod-std-import-package-review-root",
			iframe_class: "std-prod-std-import-package-review-iframe",
			testid: "std-prod-std-import-package-review",
		},
		"std-version-diff-and-supersession": {
			page: "std-version-diff-and-supersession",
			title: __("Version Diff and Supersession"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_version_diff_and_supersession.html",
			screen: "versionDiff",
			shell_class: "std-prod-std-version-diff-and-supersession-shell",
			root_class: "std-prod-std-version-diff-and-supersession-root",
			iframe_class: "std-prod-std-version-diff-and-supersession-iframe",
			testid: "std-prod-std-version-diff-and-supersession",
		},
	};

	Object.keys(PAGE_CONFIGS).forEach(function (page_name) {
		if (!frappe.pages[page_name]) {
			return;
		}
		var config = PAGE_CONFIGS[page_name];
		frappe.pages[page_name].on_page_load = function (wrapper) {
			frappe.require("/assets/kentender_procurement/js/std_prod_engine.js", function () {
				kentender.std_prod.mount_page(wrapper, config);
			});
		};
	});
})();
