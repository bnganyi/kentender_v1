// NDS-CHG-001 v1.15 §5.5 / KT-STD-001 v1.9 §2.9 — mounts kentender_core's
// shared journey tracker and next-step block (kt_industry_guidance.bundle.js)
// into a Departmental Needs screen as one guidance region below the page
// header, the mount-helper way usePageRail mounts the rail (AGENTS.md §6.6:
// a component object cannot cross a bundle boundary). The screen supplies the
// host element and the server's `next_step` / `journey` answers, unchanged;
// nothing here decides wording. A fix is handed to the screen's own handler.
import { onMounted, onUnmounted, watch } from "vue";

export function useGuidance(el, source, { onFix, onLink } = {}) {
	let region = null;
	const state = () => ({
		answer: source.answer() || null,
		journey: source.journey() || null,
		pending: !!(source.pending && source.pending()),
	});
	onMounted(() => {
		const industry = window.kentender_core?.industry;
		if (!industry || !industry.mountGuidance || !el?.value) return;
		const now = state();
		region = industry.mountGuidance(el.value, {
			journey: now.journey,
			answer: now.answer,
			label: "Journey",
			pending: now.pending,
			onFix: onFix || (() => {}),
			onLink: onLink || (() => {}),
		});
	});
	watch(
		() => [source.answer(), source.journey(), source.pending && source.pending()],
		() => region?.update(state()),
	);
	onUnmounted(() => {
		region?.unmount();
		region = null;
	});
}

// A route fix opens its exact target; any other kind has no page action here.
export function followFix(fix) {
	if (fix && fix.kind === "route" && Array.isArray(fix.target) && fix.target.length) {
		frappe.set_route(...fix.target);
	}
}
