// KT-STD-001 v1.8 §2.9 / §4 — the shared next-step block and journey
// tracker, owned by kentender_core and published as runtime mount helpers
// for the same reason as kt_industry_page_rail.bundle.js: every bundle on
// this bench carries its own Vue runtime, so a component object cannot cross
// a bundle boundary (AGENTS.md §6.6). Each helper mounts its component as an
// isolated app on the host's element and exposes only update()/unmount().
//
// A module never builds its own next-step, status-narrative or tracker
// component (KT-STD-001 v1.8 §10); it passes the server's `next_step` and
// `journey` answers here unchanged.
import { createApp, h, reactive } from "vue";
import JourneyTracker from "./components/JourneyTracker.vue";
import NextStep from "./components/NextStep.vue";

frappe.provide("kentender_core.industry");

function mount(el, Component, initial, listeners) {
	const state = reactive({ ...initial });
	const app = createApp({
		render() {
			return h(Component, { ...state, ...listeners });
		},
	});
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return {
		update(next) {
			Object.assign(state, next || {});
		},
		unmount() {
			app.unmount();
		},
	};
}

// opts: { journey, onLink(link) }
kentender_core.industry.mountJourney = function (el, opts) {
	opts = opts || {};
	return mount(el, JourneyTracker, { journey: opts.journey || null }, { onLink: opts.onLink || (() => {}) });
};

// opts: { answer, placement: "head" | "body", pending, onFix(fix) }
kentender_core.industry.mountNextStep = function (el, opts) {
	opts = opts || {};
	return mount(
		el,
		NextStep,
		{ answer: opts.answer || null, placement: opts.placement || "head", pending: !!opts.pending },
		{ onFix: opts.onFix || (() => {}) },
	);
};
