// TPR-CHG-001 v0.12 §10.17 / KT-STD-001 v1.8 §2.9 — mounts kentender_core's
// shared guidance region (journey tracker + next-step block,
// kt_industry_guidance.bundle.js) into a Tenders record screen, the same
// mount-helper way usePageRail mounts the rail (AGENTS.md §6.6: a component
// object cannot cross a bundle boundary). The screen supplies one host element
// below its header and the server's `next_step` / `journey` answers unchanged;
// nothing here decides wording — the host only maps a fix to its own handler.
import { onMounted, onUnmounted, watch } from "vue";

export function useGuidance(hostEl, source, { onFix, onLink } = {}) {
	let region = null;
	const state = () => ({
		answer: source.answer() || null,
		journey: source.journey() || null,
		pending: !!(source.pending && source.pending()),
	});
	onMounted(() => {
		const industry = window.kentender_core?.industry;
		if (!industry || !industry.mountGuidance || !hostEl?.value) return;
		region = industry.mountGuidance(hostEl.value, { ...state(), label: "Tender journey", onFix: onFix || (() => {}), onLink: onLink || (() => {}) });
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
