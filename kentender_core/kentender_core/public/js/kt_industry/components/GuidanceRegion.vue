<!-- KT-STD-001 v1.8 §2.9 — one guidance region: the journey tracker above the
     next-step block, below the page header and above the first working
     region (§2.9.3 rule 7), with a bottom divider and no card, shadow or
     band (design-system handoff "Journey tracker and next-step block" §2).
     Used where a module's change unit places both components together
     (TPR-CHG-001 v0.12 §10.17); Planning mounts the two separately. A region
     with neither a tracker nor a next step draws nothing. -->
<template>
	<section v-if="hasJourney || hasStep" class="kt-guidance" data-testid="kt-guidance">
		<JourneyTracker v-if="hasJourney" :journey="journey" :label="label" @link="$emit('link', $event)" />
		<NextStep v-if="hasStep" :answer="answer" placement="region" :pending="pending" @fix="$emit('fix', $event)" />
	</section>
</template>

<script setup>
import { computed } from "vue";
import JourneyTracker from "./JourneyTracker.vue";
import NextStep from "./NextStep.vue";

const props = defineProps({
	journey: { type: Object, default: null },
	answer: { type: Object, default: null },
	label: { type: String, default: "Journey" },
	pending: Boolean,
});
defineEmits(["fix", "link"]);

const hasJourney = computed(() => !!(props.journey && props.journey.stages && props.journey.stages.length));
const hasStep = computed(() => !!(props.answer && props.answer.kind !== "not_involved" && props.answer.headline));
</script>
