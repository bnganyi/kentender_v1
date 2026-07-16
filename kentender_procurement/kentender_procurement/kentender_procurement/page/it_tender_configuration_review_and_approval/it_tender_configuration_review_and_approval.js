(function () {
	"use strict";

	frappe.pages["it-tender-configuration-review-and-approval"].on_page_load = function (wrapper) {
		kentender.it_wizard.mount_page(wrapper, {
			page: "it-tender-configuration-review-and-approval",
			title: __("Review and Approval"),
			asset: "/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_review_and_approval.html",
			screen: "review_and_approval",
			shell_class: "it-wizard-review-and-approval-shell",
			root_class: "it-wizard-review-and-approval-root",
			iframe_class: "it-wizard-review-and-approval-iframe",
			testid: "it-wizard-review-and-approval",
		});
	};
})();
