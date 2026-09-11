// Mounts kentender_core's shared top page rail via
// kentender_core.industry.mountPageRail — the one canonical PageRail
// implementation (AGENTS.md §6.6), as its own isolated app, never a child
// component across the bundle boundary. kt_industry_page_rail.bundle.js is
// required alongside this page's bundle by tender_preparation_page.js.
import { onMounted, onUnmounted, watch } from "vue";

export function usePageRail(elRef, trailRef, opts) {
	// TPR-CHG-001 v0.6 §5/§12 — no Procuring Entity selector anywhere in
	// Tender Preparation; `showPeSwitcher` is always false.
	let handle = null;
	onMounted(() => {
		handle = kentender_core.industry.mountPageRail(elRef.value, {
			trail: trailRef.value,
			showPeSwitcher: false,
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
