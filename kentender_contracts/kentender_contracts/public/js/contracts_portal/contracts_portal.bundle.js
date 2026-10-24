// CM-CHG-001 v0.8 section 9 — Contract Management's supplier portal surface. kentender_core's portal runtime loads first; this bundle registers the "contracts" surface and mounts one Vue app that
// stays mounted while the supplier moves between /supplier/contracts, a contract and its tabs. Its reads and its one command call go through the portal's own transport (no `frappe.call`).
import { createApp } from "vue";
import ContractsPortal from "./ContractsPortal.vue";
import { useTransport } from "../contracts/data/api.js";

window.kentender_core.portal_page.register("contracts", {
	prefixes: ["/supplier/contracts"],
	mount(el, { initial, portal }) {
		useTransport((method, args, options) => portal.call(method, args, options));
		const app = createApp(ContractsPortal, { initial, portal });
		app.config.globalProperties.__ = window.__;
		app.provide("portal", portal);
		app.mount(el);
		return app;
	},
});
