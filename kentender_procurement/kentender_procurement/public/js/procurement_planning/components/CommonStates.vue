<!-- PLN-CHG-001 v1.24 §10.17 (KT-STD-001 v1.7 §2.6) — the shared U21 states a
     record route replaces its entire page with: loading, masked (existence
     hidden) and load-failure, ported class-for-class from
     Artboards-C01-U21.dc.html. Each is one bare `.kt-page` sheet holding
     either the live skeleton or a `.kt-empty` block — never the older
     `.kt-card.kt-blueprint` bordered-rectangle treatment, which the v1.24
     artboards use nowhere (KT-STD-001 v1.7 §2.6.7/PLN24-CHG-007: no excessive
     cards, borders or equal emphasis).

     U01's own FORBIDDEN/NO_CONTEXT states stay in WorkspaceScreen.vue: their
     copy is server-supplied per §3A.4's named-responsibility list, which is
     module-entry content, not a generic empty state. Per-screen notice-banner
     states (changed record/authority, unsaved-save-failure, uncertain
     command result, historical read-only) are `.kt-notice` banners embedded
     in an otherwise still-rendering page, not a full-page replacement, so
     each screen composes those inline rather than through this component.

     Re-diffed 22 Sep 2026 against the actual v1.24 U21-MASKED/LOAD-FAILURE
     sections (this header previously cited that file from before it existed
     in the repo — see kentender_core's test_artboard_provenance_gate):
     headings, body copy and actions all match. The artboard draws a distinct
     SVG icon per state; every `.kt-empty` usage in the live app (this file,
     AnnualPlanScreen, ProgressScreen, both modules' WorkspaceScreen) omits
     it consistently, and `kt_industry_tokens.css`'s own `.kt-empty` rule has
     no icon slot — a deliberate, app-wide convention, not a gap unique to
     this component. -->
<template>
	<div class="kt-page" :data-testid="resolvedTestid">
		<div v-if="isLoading" role="status">
			<p class="pln-sr-only">{{ copy.heading }}</p>
			<div v-for="row in loadingRows" :key="row" class="pln-skel-row">
				<div class="kt-skel" style="width: 72%"></div>
				<div class="kt-skel" style="width: 52%"></div>
				<div class="kt-skel" style="width: 52%"></div>
				<div class="kt-skel" style="width: 44%"></div>
			</div>
		</div>
		<div v-else class="kt-empty">
			<h3 style="font-family: var(--kt-font-heading); font-weight: var(--kt-font-heading-weight); font-size: 23px; margin: 0">
				{{ copy.heading }}
			</h3>
			<p v-for="(line, index) in copy.text" :key="index">{{ line }}</p>
			<div v-if="copy.action">
				<button type="button" class="kt-btn kt-btn-primary" :data-testid="`${resolvedTestid}-action`" @click="$emit('action')">
					{{ copy.action }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const STATES = {
	// U21-LOADING-WORKSPACE / U21-LOADING-REVIEW — a live shimmer, not the
	// artboard's flat placeholder blocks: a static mockup cannot depict an
	// animation, and the shimmer is the approved skeleton every screen uses.
	"loading-workspace": { heading: "Loading procurement planning…" },
	"loading-review": { heading: "Loading plan review…" },
	// U21-MASKED — existence itself is not disclosed: no title, no reference.
	masked: {
		heading: "This record is not available to you.",
		text: [],
		action: "Go to procurement planning",
	},
	// U21-LOAD-FAILURE
	"load-failure": {
		heading: "Procurement Planning could not be loaded.",
		text: ["Try again. If the problem continues, contact support."],
		action: "Try again",
	},
	// Inline empty fragments (used inside a region's own table/list, never a
	// full-page replacement) — kept for a register with nothing to show.
	"empty-accepted-requirements": {
		heading: "No accepted departmental requirements",
		text: ["Accepted requirements will appear here after Procurement validation."],
	},
	// U21-FILTERED-EMPTY
	"filtered-empty": {
		heading: "No requirements match this search.",
		text: [],
		action: "Clear filters",
	},
	"empty-validation-queue": {
		heading: "No departmental plans awaiting validation",
		text: ["New submissions will appear here."],
	},
	"empty-corrections": {
		heading: "No correction requests",
		text: ["No upstream correction request is recorded for this Plan Item."],
	},
};

const LOADING_KINDS = new Set(["loading-workspace", "loading-review"]);

const props = defineProps({
	kind: { type: String, required: true },
	loadingRows: { type: Number, default: 3 },
	testid: { type: String, default: "" },
	supportRef: { type: String, default: "" },
});
defineEmits(["action"]);

const copy = computed(() => {
	const base = STATES[props.kind];
	if (props.kind === "load-failure" && props.supportRef) {
		return { ...base, text: [...base.text, `Support reference: ${props.supportRef}`] };
	}
	return base;
});
const isLoading = computed(() => LOADING_KINDS.has(props.kind));
const resolvedTestid = computed(() => props.testid || `pln-common-${props.kind}`);
</script>
