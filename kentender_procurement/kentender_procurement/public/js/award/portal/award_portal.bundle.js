// AWD-CHG-001 v0.4 plan D14 — the supplier's award notice in the public portal.
// kentender_core's portal runtime loads first; this registers the
// "supplier-awards" surface and mounts one Vue app.
import { createApp } from "vue";
import AwardPortal from "./AwardPortal.vue";

window.kentender_core.portal_page.register("supplier-awards", {
	prefixes: ["/supplier/awards"],
	mount(el, { initial, portal }) {
		const app = createApp(AwardPortal, { initial, portal });
		app.config.globalProperties.__ = window.__;
		app.mount(el);
		return app;
	},
});
