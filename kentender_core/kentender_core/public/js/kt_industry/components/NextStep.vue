<!-- KT-STD-001 v1.8 §2.9.1 — the next-step block, drawn from the server's
     `next_step` answer (kentender_core.services.next_step.answer). Ported
     from the Planning boards' `data-kt="next-step"` markup (25 Sep 2026).

     Two placements, because the boards put the kinds in two places:
       - `head`: Your turn, Waiting and Done are one line of text inside the
         page header, after its scope line — no container of their own;
       - `body`: Your turn, blocked is the one kind with a container, a
         warning notice placed after the tracker, listing every blocker with
         one control per fix.
     A placement that does not match the answer's kind draws nothing, as does
     Not involved or an absent answer (§2.9.3 rule 8). Fix controls emit
     `fix`; the host screen owns what each one does. -->
<template>
	<p v-if="showLine" class="kt-next-step" data-kt="next-step" :data-kind="answer.kind">
		<!-- Explicit spaces between the parts: flex gap spaces them visually, but
		     without these the line's text (and a screen reader) runs them
		     together as "WaitingWaiting for…". -->
		<span class="kt-next-step-label">{{ answer.label }}</span>{{ " " }}<span class="kt-next-step-headline" data-testid="kt-next-step-headline">{{ answer.headline }}</span><template v-if="answer.kind === 'waiting' && answer.since">{{ " " }}<span class="kt-next-step-since">since {{ answer.since.display }}</span></template>
		<!-- A turn held on another page (a Budget Officer's revision request,
		     read from the plan) carries its one way there on the line. -->
		<template v-for="item in lineLinks" :key="item.fix_id">{{ " " }}<button type="button" class="kt-next-step-link" :data-fix="item.fix_id" @click="$emit('fix', item)">{{ item.label }}</button></template>
	</p>
	<div v-else-if="showBlock" class="kt-notice is-warning kt-next-step-block" data-kt="next-step" :data-kind="answer.kind" role="status">
		<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
			<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"></path>
			<path d="M12 9v4"></path>
			<path d="M12 17h.01"></path>
		</svg>
		<div class="kt-next-step-block-body">
			<div class="kt-next-step-label">{{ answer.label }}</div>
			<div class="kt-next-step-block-headline" data-testid="kt-next-step-headline">{{ answer.headline }}</div>
			<p v-if="answer.sentence" class="kt-next-step-sentence">{{ answer.sentence }}</p>

			<!-- One blocker: its labelled facts and its fixes directly. -->
			<template v-if="blockers.length === 1">
				<div v-if="blockers[0].facts && blockers[0].facts.length" class="kt-meta-row is-tight kt-next-step-facts">
					<div v-for="fact in blockers[0].facts" :key="fact.label">
						<span class="kt-label">{{ fact.label }}</span>
						<span class="kt-next-step-fact">{{ fact.value }}</span>
					</div>
				</div>
				<div class="kt-next-step-fixes">
					<template v-for="(item, index) in blockers[0].fixes" :key="item.fix_id">
						<span v-if="item.kind === 'text'" class="kt-next-step-fix-text">{{ item.label }}</span>
						<button
							v-else
							type="button"
							class="kt-btn"
							:class="item.primary || (index === 0 && !hasPrimary(blockers[0])) ? 'kt-btn-primary' : 'kt-btn-secondary'"
							:disabled="pending"
							:data-fix="item.fix_id"
							@click="$emit('fix', item)"
						>{{ item.label }}</button>
					</template>
				</div>
			</template>

			<!-- Several blockers (PLN §10.1A.5 D1): the headline gives the count
			     and each blocker follows on its own line with its fix. -->
			<ul v-else class="kt-next-step-blockers">
				<li v-for="entry in blockers" :key="entry.reason_code + entry.headline" :data-reason="entry.reason_code">
					<span class="kt-next-step-blocker-headline">{{ entry.headline }}</span>
					<!-- A blocker's own facts (a declined budget revision: who,
					     when, why) stay with it in the list form too. -->
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

const LINE_KINDS = ["your_turn", "waiting", "done"];

const showLine = computed(
	() => !!props.answer && props.placement === "head" && LINE_KINDS.includes(props.answer.kind) && !!props.answer.headline,
);
const showBlock = computed(
	() => !!props.answer && props.placement === "body" && props.answer.kind === "your_turn_blocked" && !!props.answer.headline,
);
const blockers = computed(() => (props.answer && props.answer.blockers) || []);
const lineLinks = computed(() =>
	props.answer && props.answer.kind === "your_turn" ? (props.answer.fixes || []).filter((item) => item.kind === "route") : [],
);

function hasPrimary(entry) {
	return (entry.fixes || []).some((item) => item.primary);
}
</script>
