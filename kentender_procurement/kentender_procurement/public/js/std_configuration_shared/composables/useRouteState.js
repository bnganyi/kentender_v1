import { ref, onMounted, onUnmounted } from "vue";

/**
 * Generic route-param composable, ported from kentender_strategy's
 * strategy_shared/composables/useRouteState.js (STR-CHG-001 v1.3 Phase 7) —
 * AGENTS.md §6.6 requires each app to consume kt_industry_tokens.css directly
 * rather than fork it, but a page-level JS composable with no CSS/DOM
 * ownership is copied per-app rather than published cross-app (matches
 * kentender_strategy's own precedent: shared logic like this is ported, not
 * cross-app imported at build time, since each app's esbuild only bundles
 * its own public/js tree).
 *
 * frappe.router.off() cannot actually remove a listener bound with
 * frappe.router.on() (CLAUDE.md §6.4) — the only working mitigation is an
 * `active` flag guard, applied below.
 */
export function useRouteState(pageSlug) {
	function currentRoute() {
		const route = frappe.get_route();
		return route && route.length ? route : [pageSlug];
	}

	const route = ref(currentRoute());

	function go(...segments) {
		frappe.set_route(pageSlug, ...segments);
	}

	let active = true;
	function onRouteChange() {
		if (!active) return;
		route.value = currentRoute();
	}

	onMounted(() => frappe.router.on("change", onRouteChange));
	onUnmounted(() => {
		active = false;
		frappe.router.off("change", onRouteChange); // no-op — kept for intent/symmetry
	});

	return { route, go };
}
