import { createApp } from "vue";
import BidEvaluationWorkspace from "./BidEvaluationWorkspace.vue";

// EVL-CHG-001 v0.4 §9.2 / plan D13: the Bid evaluation workspace Page
// (/app/bid-evaluation). kt_industry_page_rail.bundle.js and
// kt_industry_guidance.bundle.js load alongside from bid_evaluation_page.js.
frappe.kt_mount_bid_evaluation_workspace = function (el) {
	const app = createApp(BidEvaluationWorkspace);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
