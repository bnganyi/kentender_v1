import { createApp } from "vue";
import BidEvaluation from "./BidEvaluation.vue";

// EVL-CHG-001 v0.4 §10 / plan D13: the Tenders page mounts this app into its
// host for /app/tenders/{ref}/evaluation… (AGENTS.md §6.6: an isolated app with
// its own Vue runtime, never a component across bundle boundaries).
frappe.kt_mount_bid_evaluation = function (el) {
	const app = createApp(BidEvaluation);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
