<!-- KT-STD-001 v1.8 §2.9.2 — the journey tracker: one row of a record's own
     formal stages, one marker each (Done, Current, Blocked, Not started, as
     visible text), the holder named on the current stage only, and at most
     one upstream and one downstream text link.

     Drawn to the Industry design-system handoff "Journey tracker and
     next-step block" (Project Owner approved for formalisation 26 Sep 2026;
     TPR-CHG-001 v0.12 plan OD-1 applies it to every module): an ordered list
     of N equal columns, each a 4px bar, a numbered label and a state line
     ("✓ Done", "Current · {holder}", "Blocked · {holder}", "Not started").
     The one-line reduced form (mini bars + the server's reduced wording) is
     drawn when the server asks for it (§2.9.3 rule 5), and automatically when
     the host is narrower than 600px (a container query on the host), so a
     390px screen never scrolls sideways.

     Everything shown comes from the server's `journey` answer
     (kentender_core.services.next_step.journey); nothing is composed here,
     and an absent journey draws nothing (§2.9.3 rule 8). -->
<template>
	<div v-if="journey && journey.stages && journey.stages.length" class="kt-journey-host" data-kt="journey">
		<div v-if="journey.reduced" class="kt-journey is-reduced">
			<div class="kt-journey-bars" aria-hidden="true">
				<span v-for="stage in journey.stages" :key="stage.code" :class="markerClass(stage)"></span>
			</div>
			<p v-if="journey.reduced_parts" class="kt-journey-reduced-text">{{ journey.reduced_parts.prefix }}<span class="kt-journey-current">{{ journey.reduced_parts.label }}</span>{{ journey.reduced_parts.suffix }}</p>
		</div>
		<template v-else>
			<ol class="kt-journey" :aria-label="ariaLabel" :style="{ '--kt-journey-n': journey.stages.length }">
				<li
					v-for="(stage, index) in journey.stages"
					:key="stage.code"
					class="kt-journey-stage"
					:class="markerClass(stage)"
					:data-stage="stage.code"
					:aria-current="stage.marker === 'current' || stage.marker === 'blocked' ? 'step' : null"
				>
					<span class="kt-journey-bar" aria-hidden="true"></span>
					<span class="kt-journey-title"><span class="kt-journey-num">{{ index + 1 }}</span>{{ stage.label }}</span>
					<span class="kt-journey-state">{{ stateLine(stage) }}</span>
				</li>
			</ol>
			<!-- the same answer, one line: shown instead of the row under 600px -->
			<div class="kt-journey-compact" aria-hidden="true">
				<div class="kt-journey-bars">
					<span v-for="stage in journey.stages" :key="stage.code" :class="markerClass(stage)"></span>
				</div>
				<p v-if="journey.reduced_parts" class="kt-journey-reduced-text">{{ journey.reduced_parts.prefix }}<span class="kt-journey-current">{{ journey.reduced_parts.label }}</span>{{ journey.reduced_parts.suffix }}</p>
			</div>
		</template>
		<div v-if="journey.upstream || journey.downstream" class="kt-journey-links">
			<a v-if="journey.upstream" href="#" class="kt-journey-link" data-testid="kt-journey-upstream" @click.prevent="$emit('link', journey.upstream)">{{ journey.upstream.label }}</a>
			<a v-if="journey.downstream" href="#" class="kt-journey-link" data-testid="kt-journey-downstream" @click.prevent="$emit('link', journey.downstream)">{{ journey.downstream.label }}</a>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	journey: { type: Object, default: null },
	label: { type: String, default: "Journey" },
});
defineEmits(["link"]);

const ariaLabel = computed(() => props.label || "Journey");

function markerClass(stage) {
	return `is-${String(stage.marker || "not_started").replace("_", "-")}`;
}

// The marker words are the server's (`marker_label`); the check mark and the
// holder separator are the design system's state-line form.
function stateLine(stage) {
	if (stage.marker === "done") return `✓ ${stage.marker_label}`;
	if ((stage.marker === "current" || stage.marker === "blocked") && stage.holder) return `${stage.marker_label} · ${stage.holder}`;
	return stage.marker_label;
}
</script>
