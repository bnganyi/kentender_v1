// Mounts kentender_core's shared top page rail via
// kentender_core.industry.mountPageRail — the one canonical PageRail
// implementation (AGENTS.md §6.6), not a normal Vue child component. This
// repo's shared esbuild config does not mark "vue" external, so every bundle
// carries its own separate copy of the Vue runtime; a component object built
// by one bundle's Vue instance loses its internal wiring when rendered as a
// child vnode by a *different* bundle's Vue instance. Mounting it as its own
// isolated app and only exposing an imperative update()/unmount() handle
// avoids crossing that boundary.
//
// Inside Strategy.vue's tree the root owns the one rail and provides a trail
// publisher; a screen calling this composable then only publishes its trail
// (on mount, on KeepAlive re-activation and on change) — it never mounts a
// second rail that would be torn down on the next screen switch.
import { inject, onActivated, onMounted, onUnmounted, watch } from "vue";

export const STRATEGY_RAIL = "kt-strategy-rail";

export function usePageRail(elRef, trailRef, opts) {
	const publisher = inject(STRATEGY_RAIL, null);
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
