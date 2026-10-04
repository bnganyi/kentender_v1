import { onMounted, onUnmounted, watch } from "vue";

/**
 * Mounts kentender_core's shared top page rail via
 * kentender_core.industry.mountPageRail — the one canonical PageRail
 * implementation (AGENTS.md §6.6), not a normal Vue child component. This
 * repo's esbuild does not mark "vue" external, so every bundle carries its
 * own separate copy of the Vue runtime; a component object built by one
 * bundle's Vue instance loses its internal wiring if rendered as a child
 * vnode by a different bundle's instance. kt_industry_page_rail.bundle.js
 * must already be loaded (via frappe.require alongside this page's own
 * bundle in its *_page.js) before this composable's onMounted() runs.
 */
export function usePageRail(elRef, trailRef, opts) {
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
