// Mounts kentender_core's shared top page rail via
// kentender_core.industry.mountPageRail — the one canonical PageRail
// implementation (AGENTS.md §6.6), not a normal Vue child component. This
// repo's shared esbuild config does not mark "vue" external, so every bundle
// carries its own separate copy of the Vue runtime; a component object built
// by one bundle's Vue instance loses its internal wiring (confirmed live:
// scoped-CSS attributes silently failed to apply) when rendered as a child
// vnode by a *different* bundle's Vue instance. Mounting it as its own
// isolated app — kentender_core's kt_industry_page_rail.bundle.js — and only
// exposing an imperative update()/unmount() handle avoids crossing that
// boundary. kt_industry_page_rail.bundle.js must already be loaded (via
// frappe.require alongside the page's own bundle in its *_page.js) before
// this composable's onMounted() runs.
//
// Inside Budget.vue's tree the root owns the one rail and provides a trail
// publisher; a screen calling this composable then only publishes its trail
// (on mount, on KeepAlive re-activation and on change) — it never mounts a
// second rail that would be torn down on the next screen switch.
import { inject, onActivated, onMounted, onUnmounted, watch } from "vue";

export const BUDGET_RAIL = "kt-budget-rail";

export function usePageRail(elRef, trailRef, opts) {
	const publisher = inject(BUDGET_RAIL, null);
	if (publisher) {
		const publish = () => publisher.setTrail(trailRef.value);
		onMounted(publish);
		onActivated(publish);
		watch(trailRef, publish);
		return;
	}
	// CTX-CHG-001 — opts: { showPeSwitcher, onPeChange }. Dormant by default;
	// a page that opts in receives the global PE switcher in the rail and its
	// onPeChange callback when the user switches entity.
	let handle = null;
	onMounted(() => {
		handle = kentender_core.industry.mountPageRail(elRef.value, {
			trail: trailRef.value,
			...(opts || {}),
		});
	});
	onUnmounted(() => {
		handle?.unmount();
		handle = null;
	});
	watch(trailRef, (trail) => {
		handle?.update(trail);
	});
}
