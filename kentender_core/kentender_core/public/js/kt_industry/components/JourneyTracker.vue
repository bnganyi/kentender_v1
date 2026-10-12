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

     DS-REV-004 (Project Owner approved 6 Oct 2026, "2e it is. Approved"): the
     row leads with one position figure, "{n} of {N}" with "Current · {holder}"
     or "Blocked · {holder}" beneath, and the track is the compact form: 6px
     bars rounded on every segment, a check in place of the number on done
     stages, and each stage's state kept as text for assistive technology and
     print only (the figure states the current state). The figure is derived
     from the supplied stages and adds no fact. With every stage done it reads
     "N of N · Done"; with none started it is left out (decision D1/K3,
     applied as recommended).

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
			<div class="kt-journey-lead" :class="{ 'has-position': !!position }">
				<div v-if="position" class="kt-journey-position" :class="{ 'is-blocked': position.blocked, 'is-done': position.done }" aria-hidden="true" data-testid="kt-journey-position">
					<span class="kt-journey-position-label">{{ t("Stage") }}</span>
					<span class="kt-journey-position-value">
						<span class="kt-journey-position-n">{{ position.n }}</span>
						<span class="kt-journey-position-of">{{ t("of") }} {{ position.total }}</span>
					</span>
					<span class="kt-journey-position-state">{{ position.state }}</span>
				</div>
				<ol class="kt-journey is-compact" :aria-label="ariaLabel" :style="{ '--kt-journey-n': journey.stages.length }">
					<li
						v-for="(stage, index) in journey.stages"
						:key="stage.code"
						class="kt-journey-stage"
						:class="markerClass(stage)"
						:data-stage="stage.code"
						:aria-current="stage.marker === 'current' || stage.marker === 'blocked' ? 'step' : null"
					>
						<span class="kt-journey-bar" aria-hidden="true"></span>
						<span class="kt-journey-title">
							<svg v-if="stage.marker === 'done'" class="kt-journey-check" aria-hidden="true" viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5" /></svg>
							<span v-else class="kt-journey-num">{{ index + 1 }}</span>{{ stage.label }}
						</span>
						<span class="kt-journey-state">{{ stateLine(stage) }}</span>
					</li>
				</ol>
			</div>
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

const t = (text) => (typeof window !== "undefined" && typeof window.__ === "function" ? window.__(text) : text);

// The position figure: the blocked stage, else the current one; with every
// stage done, the last; with none started, nothing.
const position = computed(() => {
	const stages = (props.journey && props.journey.stages) || [];
	if (!stages.length) return null;
	let at = stages.findIndex((stage) => stage.marker === "blocked");
	if (at < 0) at = stages.findIndex((stage) => stage.marker === "current");
	if (at >= 0) {
		const stage = stages[at];
		const state = stage.holder ? `${stage.marker_label} · ${stage.holder}` : stage.marker_label;
		return { n: at + 1, total: stages.length, blocked: stage.marker === "blocked", done: false, state };
	}
	if (stages.every((stage) => stage.marker === "done")) {
		return { n: stages.length, total: stages.length, blocked: false, done: true, state: stages[stages.length - 1].marker_label };
	}
	return null;
});

function markerClass(stage) {
	return `is-${String(stage.marker || "not_started").replace("_", "-")}`;
}

// The marker words are the server's (`marker_label`); the holder separator is
// the design system's state-line form. In the compact track this line is for
// assistive technology and print only: a done stage shows its check instead.
function stateLine(stage) {
	if ((stage.marker === "current" || stage.marker === "blocked") && stage.holder) return `${stage.marker_label} · ${stage.holder}`;
	return stage.marker_label;
}
</script>
