<!-- KT-STD-001 v1.8 §2.9.2 — the journey tracker: one row of a record's own
     formal stages, one marker each (Done, Current, Blocked, Not started, as
     text), the holder named on the current stage only, and at most one
     upstream and one downstream text link. Ported from the Planning boards'
     `data-kt="journey"` markup (Artboards-U07-U08, U11, U12-U13, 25 Sep 2026),
     whose inline styles became the `.kt-journey*` rules in
     kt_industry_tokens.css. `reduced` draws the one-line form required under
     the first-view budget (§2.9.3 rule 5).

     Everything shown comes from the server's `journey` answer
     (kentender_core.services.next_step.journey); nothing is composed here,
     and an absent journey draws nothing (§2.9.3 rule 8). -->
<template>
	<p v-if="journey && journey.reduced && journey.reduced_parts" class="kt-journey is-reduced" data-kt="journey">
		{{ journey.reduced_parts.prefix }}<span class="kt-journey-current">{{ journey.reduced_parts.label }}</span>{{ journey.reduced_parts.suffix }}
	</p>
	<div v-else-if="journey && journey.stages && journey.stages.length" class="kt-journey" data-kt="journey" aria-label="Journey">
		<ol class="kt-journey-stages" :style="{ gridTemplateColumns: `repeat(${journey.stages.length}, minmax(0, 1fr))` }">
			<li
				v-for="stage in journey.stages"
				:key="stage.code"
				class="kt-journey-stage"
				:class="`is-${stage.marker.replace('_', '-')}`"
				:data-stage="stage.code"
				:aria-current="stage.marker === 'current' || stage.marker === 'blocked' ? 'step' : null"
			>
				<div class="kt-journey-label">{{ stage.label }}</div>
				<div class="kt-journey-marker">
					{{ stage.marker_label }}<span v-if="stage.holder" class="kt-journey-holder"> · {{ stage.holder }}</span>
				</div>
			</li>
		</ol>
		<a v-if="journey.upstream" href="#" class="kt-journey-link" data-testid="kt-journey-upstream" @click.prevent="$emit('link', journey.upstream)">{{ journey.upstream.label }}</a>
		<a v-if="journey.downstream" href="#" class="kt-journey-link" data-testid="kt-journey-downstream" @click.prevent="$emit('link', journey.downstream)">{{ journey.downstream.label }}</a>
	</div>
</template>

<script setup>
defineProps({
	journey: { type: Object, default: null },
});
defineEmits(["link"]);
</script>
