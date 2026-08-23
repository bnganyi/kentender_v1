import { ref, onMounted, onUnmounted } from "vue";

const PAGE_SLUG = "strategy-portfolio-pilot";

// Pattern reused from strategy_alignment_shell.js's planCodeFromRoute/ensurePlanRoute
// (jQuery/global-namespace there, reimplemented here for the Vue bundle).
function planCodeFromRoute() {
	const route = frappe.get_route() || [];
	return route.length > 1 && route[1] ? String(route[1]).trim() : null;
}

export function useRouteState() {
	const selectedCode = ref(planCodeFromRoute());

	function openPlan(code) {
		if (planCodeFromRoute() === code) return; // idempotent — no redundant history push
		frappe.set_route(PAGE_SLUG, code);
	}

	function closePlan() {
		if (!planCodeFromRoute()) return;
		frappe.set_route(PAGE_SLUG);
	}

	// frappe.router.off() cannot actually remove this listener: frappe's
	// EventEmitterMixin (frappe/public/js/frappe/event_emitter.js) implements off()
	// as `this.jq.unbind(evt, (e, data) => handler(data))` — a NEW wrapper function
	// on every call, wrapping a jQuery event system where unbind() only matches the
	// exact function reference bind() was given. on() wraps just as freshly, so the
	// wrapper off() constructs never matches what's actually bound. Verified by
	// reading the source, not assumed — frappe.router.off() is a silent no-op
	// throughout this codebase, not only here. The only working mitigation without
	// patching frappe core is an active-flag guard: the stale jQuery-bound closure
	// stays registered for the life of the browser tab, but becomes inert.
	let active = true;
	function onRouteChange() {
		if (!active) return;
		selectedCode.value = planCodeFromRoute();
	}

	onMounted(() => frappe.router.on("change", onRouteChange));
	onUnmounted(() => {
		active = false;
		frappe.router.off("change", onRouteChange); // no-op (see above) — kept for intent/symmetry
	});

	return { selectedCode, openPlan, closePlan };
}
