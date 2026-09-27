// BDS-CHG-001 v0.8 (slices 11.3–11.4) — Supplier Accounts' portal surface
// (plan OD-B). kentender_core's portal runtime loads first; this bundle
// registers the "account" surface and mounts one Vue app that stays mounted
// while the supplier moves between /account, /account/register and
// /account/verify.
import { createApp } from "vue";
import SupplierAccountPortal from "./SupplierAccountPortal.vue";

window.kentender_core.portal_page.register("account", {
	prefixes: ["/account"],
	mount(el, { initial, portal }) {
		const app = createApp(SupplierAccountPortal, { initial, portal });
		app.config.globalProperties.__ = window.__;
		app.provide("portal", portal);
		app.mount(el);
		return app;
	},
});
