// Publishes kentender_core's Industry-design-system top page rail as a
// runtime mount helper, so other apps can reuse the one canonical PageRail.vue
// implementation without a cross-app source import at build time (each app's
// esbuild only bundles its own public/js tree, and apps must stay
// independently installable — see AGENTS.md §6.6).
//
// This is a mount HELPER, not a globally-registered Vue component, because
// this repo's shared esbuild config does not mark "vue" external — every
// bundle carries its own separate copy of the Vue runtime. A component
// object built by one bundle's Vue instance loses its internal wiring
// (scoped-CSS attributes, provide/inject, etc.) when rendered as a child
// vnode by a *different* bundle's Vue instance (confirmed live: the rendered
// element carried no data-v-* attribute at all, even though its scoped CSS
// was present and correctly injected). Mounting PageRail as its own isolated
// Vue app — entirely within this bundle's own Vue instance, exposed only as
// an imperative update()/unmount() handle — avoids ever crossing that
// boundary.
import { createApp, h, reactive } from "vue";
import PageRail from "./components/PageRail.vue";

frappe.provide("kentender_core.industry");

kentender_core.industry.mountPageRail = function (el, opts) {
	opts = opts || {};
	const state = reactive({
		trail: opts.trail || [],
		// CTX-CHG-001 — dormant unless the page opts in, so unconverted pages
		// never show a switcher whose change they would ignore.
		showPeSwitcher: !!opts.showPeSwitcher,
		epoch: 0,
	});
	const app = createApp({
		render() {
			return h(PageRail, {
				trail: state.trail,
				showPeSwitcher: state.showPeSwitcher,
				onPeChange: opts.onPeChange || null,
				epoch: state.epoch,
			});
		},
	});
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return {
		update(trail) {
			state.trail = trail;
		},
		refreshContext() {
			state.epoch += 1;
		},
		unmount() {
			app.unmount();
		},
	};
};
