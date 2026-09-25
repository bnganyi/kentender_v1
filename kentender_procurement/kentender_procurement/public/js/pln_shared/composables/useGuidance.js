// KT-STD-001 v1.8 §2.9 — mounts kentender_core's shared journey tracker and
// next-step block (kt_industry_guidance.bundle.js) into a Planning screen, the
// same mount-helper way usePageRail mounts the rail (AGENTS.md §6.6: a
// component object cannot cross a bundle boundary). The screen supplies three
// host elements — the tracker below the page header, the Your turn / Waiting /
// Done line inside the header, and the blocked container after the tracker —
// and the server's `next_step` / `journey` answers, unchanged. Nothing here
// decides wording: the host only maps a fix or link to its own handler.
import { onMounted, onUnmounted, watch } from "vue";

export function useGuidance({ journeyEl, headEl, bodyEl }, source, { onFix, onLink } = {}) {
	let journey = null;
	let head = null;
	let body = null;
	const state = () => ({
		answer: source.answer() || null,
		journey: source.journey() || null,
		pending: !!(source.pending && source.pending()),
	});
	onMounted(() => {
		const industry = window.kentender_core?.industry;
		if (!industry || !industry.mountJourney) return;
		const now = state();
		if (journeyEl?.value) journey = industry.mountJourney(journeyEl.value, { journey: now.journey, onLink: onLink || (() => {}) });
		if (headEl?.value) head = industry.mountNextStep(headEl.value, { answer: now.answer, placement: "head", pending: now.pending, onFix: onFix || (() => {}) });
		if (bodyEl?.value) body = industry.mountNextStep(bodyEl.value, { answer: now.answer, placement: "body", pending: now.pending, onFix: onFix || (() => {}) });
	});
	watch(
		() => [source.answer(), source.journey(), source.pending && source.pending()],
		() => {
			const now = state();
			journey?.update({ journey: now.journey });
			head?.update({ answer: now.answer, pending: now.pending });
			body?.update({ answer: now.answer, pending: now.pending });
		},
	);
	onUnmounted(() => {
		journey?.unmount();
		head?.unmount();
		body?.unmount();
		journey = head = body = null;
	});
}

// PLN v1.27 §10.16 — the settings a next-step answer already states as its
// blockers (their "Setting" fact). A host screen does not draw a separate
// missing-setting panel for these; a technical reader's answer carries no
// fixes (KT-STD §3B.6), so their panel — with its Open System setup route —
// stays.
export function settingsStated(answer) {
	if (!answer || !["your_turn_blocked", "blocked"].includes(answer.kind)) return new Set();
	const named = [];
	for (const blocker of answer.blockers || []) {
		if (!(blocker.fixes || []).length) continue;
		for (const fact of blocker.facts || []) {
			if (fact.label === "Setting") named.push(fact.value);
		}
	}
	return new Set(named);
}
