import { createApp } from "vue";
import BidOpening from "./BidOpening.vue";

// BOP-CHG-001 v0.10 §9 / plan D9: the Tenders page mounts this app into its
// host for /app/tenders/{ref}/opening… (AGENTS.md §6.6: an isolated app with
// its own Vue runtime, never a component across bundle boundaries).
frappe.kt_mount_bid_opening = function (el) {
	const app = createApp(BidOpening);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
