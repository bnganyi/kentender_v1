import { ref, onMounted, onUnmounted } from "vue";

/**
 * Generic route-param composable for the Phase 7 production Strategy Vue
 * pages. Reused across strategy-portfolio / strategy-plan-workspace /
 * strategy-review-task rather than 3 copies of strategy_portfolio_pilot's
 * useRouteState.js (STR-CHG-001 v1.3 Phase 7 decision log).
 *
 * frappe.router.off() cannot actually remove a listener bound with
 * frappe.router.on(): frappe's EventEmitterMixin implements off() as a NEW
 * jQuery-unbind wrapper on every call, which never matches what on() bound
 * (verified by reading frappe/public/js/frappe/event_emitter.js — the same
 * finding documented in strategy_portfolio_pilot/composables/useRouteState.js
 * and in this repo's CLAUDE.md §6.4). The only working mitigation without
 * patching frappe core is an `active` flag guard, applied below.
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
