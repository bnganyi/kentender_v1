// BDS-CHG-001 v0.8 — Bid Submission's public portal surface (plan OD-B).
// kentender_core's portal runtime (kt_portal_runtime.bundle.js) loads first;
// this bundle registers the "tenders" surface and mounts one Vue app that
// stays mounted while the supplier moves between its paths.
import { createApp } from "vue";
import BidPortal from "./BidPortal.vue";

window.kentender_core.portal_page.register("tenders", {
	prefixes: ["/tenders", "/my-bids", "/account/receipts"],
	mount(el, { initial, portal }) {
		const app = createApp(BidPortal, { initial, portal });
		app.config.globalProperties.__ = window.__;
		app.provide("portal", portal);
		app.mount(el);
		return app;
	},
});
