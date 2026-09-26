<!-- KT-STD-001 v1.8 §2.9.1 — the next-step block, drawn from the server's
     `next_step` answer (kentender_core.services.next_step.answer) to the
     Industry design-system handoff "Journey tracker and next-step block"
     (Project Owner approved 26 Sep 2026; TPR-CHG-001 v0.12 plan OD-1 applies
     it to every module):

       - Your turn / Waiting on someone / Done: a line with no container of
         its own — a 3px left rule (accent for Your turn, neutral otherwise),
         the kind label, the headline and at most one sentence;
       - Your turn, blocked: the only kind with a container, a warning notice
         listing every blocker with one control per fix.

     Placements (each module's approved change unit fixes where its line
     sits): `head` draws the line kinds inside the page header, `body` draws
     only the blocked notice after the tracker (Planning, PLN-CHG-001 v1.27);
     `region` draws whichever kind the answer is, in one guidance region
     below the header (Tenders, TPR-CHG-001 v0.12 §10.17). A placement that
     does not match the answer's kind draws nothing, as does Not involved or
     an absent answer (§2.9.3 rule 8). Fix controls emit `fix`; the host
     screen owns what each one does. -->
<template>
	<div v-if="showLine" class="kt-next-step" :class="`is-${lineKind}`" data-kt="next-step" :data-kind="answer.kind">
		<!-- Explicit spaces between the parts: the grid spaces them visually, but
		     without them the text (and a screen reader) runs "Your turnReturn…". -->
		<div class="kt-next-step-label">{{ answer.label }}</div>{{ " " }}<p class="kt-next-step-headline" data-testid="kt-next-step-headline">{{ answer.headline }}<template v-if="sinceText">{{ " " }}<span class="kt-next-step-since">{{ sinceText }}</span></template></p><template v-if="answer.sentence">{{ " " }}<p class="kt-next-step-sentence">{{ answer.sentence }}</p></template>
		<!-- A turn held on another page carries its one way there on the line. -->
		<div v-if="lineLinks.length" class="kt-next-step-links">
			<button v-for="item in lineLinks" :key="item.fix_id" type="button" class="kt-next-step-link" :data-fix="item.fix_id" @click="$emit('fix', item)">{{ item.label }}</button>
		</div>
	</div>
	<div v-else-if="showBlock" class="kt-notice is-warning kt-next-step kt-next-step-block" data-kt="next-step" :data-kind="answer.kind" role="status">
		<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
			<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"></path>
			<path d="M12 9v4"></path>
			<path d="M12 17h.01"></path>
		</svg>
		<div class="kt-notice-body kt-next-step-block-body">
			<div class="kt-next-step-label">{{ answer.label }}</div>{{ " " }}<div class="kt-next-step-headline kt-next-step-block-headline" data-testid="kt-next-step-headline">{{ answer.headline }}</div><template v-if="answer.sentence">{{ " " }}<p class="kt-next-step-sentence">{{ answer.sentence }}</p></template>

			<!-- One blocker: its labelled facts and its fixes directly. -->
			<template v-if="blockers.length <= 1">
				<div v-if="blockers[0] && blockers[0].facts && blockers[0].facts.length" class="kt-meta-row is-tight kt-next-step-facts">
					<div v-for="fact in blockers[0].facts" :key="fact.label">
						<span class="kt-label">{{ fact.label }}</span>
						<span class="kt-next-step-fact">{{ fact.value }}</span>
					</div>
				</div>
				<div v-if="blockFixes.length" class="kt-next-step-fixes">
					<template v-for="(item, index) in blockFixes" :key="item.fix_id">
						<span v-if="item.kind === 'text'" class="kt-next-step-fix-text">{{ item.label }}</span>
						<button
							v-else
							type="button"
							class="kt-btn"
							:class="item.primary || (index === 0 && !hasPrimary(blockFixes)) ? 'kt-btn-primary' : 'kt-btn-secondary'"
							:disabled="pending"
							:data-fix="item.fix_id"
							@click="$emit('fix', item)"
						>{{ item.label }}</button>
					</template>
				</div>
			</template>

			<!-- Several blockers: the headline gives the count and each blocker
			     follows on its own line with its fix. -->
			<ul v-else class="kt-next-step-blockers">
				<li v-for="entry in blockers" :key="entry.reason_code + entry.headline" :data-reason="entry.reason_code">
					<span class="kt-next-step-blocker-headline">{{ entry.headline }}</span>
					<span v-if="entry.facts && entry.facts.length" class="kt-next-step-blocker-facts">
						<span v-for="fact in entry.facts" :key="fact.label"><span class="kt-label">{{ fact.label }}</span>{{ " " }}{{ fact.value }}</span>
					</span>
					<template v-for="item in entry.fixes" :key="item.fix_id">
						<span v-if="item.kind === 'text'" class="kt-next-step-fix-text">{{ item.label }}</span>
						<button
							v-else
							type="button"
							class="kt-btn kt-btn-secondary"
							:disabled="pending"
							:data-fix="item.fix_id"
							@click="$emit('fix', item)"
						>{{ item.label }}</button>
					</template>
				</li>
			</ul>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	answer: { type: Object, default: null },
	placement: { type: String, default: "head" },
	pending: Boolean,
});
defineEmits(["fix"]);

const LINE_KINDS = { your_turn: "turn", waiting: "waiting", done: "done" };

const lineKind = computed(() => (props.answer ? LINE_KINDS[props.answer.kind] : ""));
const showLine = computed(
	() => !!props.answer && ["head", "region"].includes(props.placement) && !!lineKind.value && !!props.answer.headline,
);
const showBlock = computed(
	() => !!props.answer && ["body", "region"].includes(props.placement) && props.answer.kind === "your_turn_blocked" && !!props.answer.headline,
);
const blockers = computed(() => (props.answer && props.answer.blockers) || []);
// A blocked answer's fixes are its blockers' fixes unless the server gave the
// answer its own list (one blocker, or an answer-level fix set).
const blockFixes = computed(() => {
	if (!props.answer) return [];
	if (blockers.value.length === 1) return blockers.value[0].fixes || [];
	return props.answer.fixes || [];
});
const lineLinks = computed(() =>
	props.answer && props.answer.kind === "your_turn" ? (props.answer.fixes || []).filter((item) => item.kind === "route") : [],
);
// "since" is a recorded fact; a module whose headline already states it
// (TPR-CHG-001 §10.17 "… since 21 Apr 2027, 09:00 EAT.") is not repeated.
const sinceText = computed(() => {
	const answer = props.answer;
	if (!answer || answer.kind !== "waiting" || !answer.since || !answer.since.display) return "";
	return (answer.headline || "").includes(answer.since.display) ? "" : `since ${answer.since.display}`;
});

function hasPrimary(fixes) {
	return (fixes || []).some((item) => item.primary);
}
</script>
