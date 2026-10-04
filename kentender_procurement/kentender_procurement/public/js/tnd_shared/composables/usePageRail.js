// Mounts kentender_core's shared top page rail via
// kentender_core.industry.mountPageRail — the one canonical PageRail
// implementation (AGENTS.md §6.6), as its own isolated app with an imperative
// update()/unmount() handle. kt_industry_page_rail.bundle.js is loaded by
// tenders_page.js before this composable's onMounted() runs.
import { onMounted, onUnmounted, watch } from "vue";

export function usePageRail(elRef, trailRef, opts) {
	let handle = null;
	onMounted(() => {
		handle = kentender_core.industry.mountPageRail(elRef.value, { trail: trailRef.value, ...(opts || {}) });
	});
	onUnmounted(() => {
		handle?.unmount();
		handle = null;
	});
	watch(trailRef, (trail) => {
		handle?.update(trail);
	});
}
