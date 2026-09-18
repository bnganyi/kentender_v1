// Mounts kentender_core's shared top page rail via
// kentender_core.industry.mountPageRail — the one canonical PageRail
// implementation (AGENTS.md §6.6), not a normal Vue child component. This
// repo's shared esbuild config does not mark "vue" external, so every bundle
// carries its own separate copy of the Vue runtime; a component object built
// by one bundle's Vue instance loses its internal wiring when rendered as a
// child vnode by a *different* bundle's Vue instance. Mounting it as its own
// isolated app — kentender_core's kt_industry_page_rail.bundle.js — and only
// exposing an imperative update()/unmount() handle avoids crossing that
// boundary. kt_industry_page_rail.bundle.js must already be loaded (via
// frappe.require alongside this page's own bundle in system_setup_page.js)
// before this composable's onMounted() runs. Copied per consuming app rather
// than imported across one (see kentender_budget/strategy's own copies).
import { inject, onActivated, onMounted, onUnmounted, watch } from "vue";

export const SETUP_RAIL = "kt-setup-rail";

export function usePageRail(elRef, trailRef, opts) {
	const publisher = inject(SETUP_RAIL, null);
	if (publisher) {
		const publish = () => publisher.setTrail(trailRef.value);
		onMounted(publish);
		onActivated(publish);
		watch(trailRef, publish);
		return;
	}
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
