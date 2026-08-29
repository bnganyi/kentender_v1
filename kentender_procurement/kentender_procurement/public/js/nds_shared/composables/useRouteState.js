import { ref, onMounted, onUnmounted } from "vue";

/**
 * Generic route-param composable for the Departmental Needs Vue-in-Desk page.
 * Verbatim copy of kentender_budget's useRouteState.js (AGENTS.md §6.6 —
 * each app keeps its own copy of pure, non-component helpers rather than
 * importing across an app boundary).
 *
 * frappe.router.off() cannot actually remove a listener bound with
 * frappe.router.on(): frappe's EventEmitterMixin implements off() as a NEW
 * jQuery-unbind wrapper on every call, which never matches what on() bound
 * (see frappe/public/js/frappe/event_emitter.js — the same finding
 * documented in AGENTS.md §6.4). The only working mitigation without
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
