// Mounts kentender_core's shared guidance region (journey tracker and next
// step) into a host element, as the Tenders and Bid Opening screens do
// (AGENTS.md §6.6). The server's answers are drawn unchanged.
import { onMounted, onUnmounted, watch } from "vue";

export function useGuidance(hostEl, source, { onFix } = {}) {
	let region = null;
	const state = () => ({ answer: source.answer() || null, journey: source.journey() || null, pending: !!(source.pending && source.pending()) });
	onMounted(() => {
		const industry = window.kentender_core?.industry;
		if (!industry || !industry.mountGuidance || !hostEl?.value) return;
		region = industry.mountGuidance(hostEl.value, { ...state(), label: "Evaluation journey", onFix: onFix || (() => {}), onLink: () => {} });
	});
	watch(() => [source.answer(), source.journey(), source.pending && source.pending()], () => region?.update(state()), { deep: true });
	onUnmounted(() => {
		region?.unmount();
		region = null;
	});
}
