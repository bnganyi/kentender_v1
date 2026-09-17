<!-- PLN-CHG-001 v1.18 §10.12 shared record-page states, ported class-for-class
     from U21-access/U21-empty, so every later screen family composes these
     instead of re-authoring the copy. One state renders at a time, chosen by
     `kind`; the two loading kinds render the same live `.kt-skel` shimmer bars
     every screen already uses rather than the artboard's static placeholder
     text, since a static mockup cannot depict an animation. -->
<template>
	<div
		v-if="isLoading"
		class="kt-card kt-blueprint"
		style="padding: 0; overflow: hidden"
		:data-testid="resolvedTestid"
		role="status"
	>
		<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
		<i class="kt-corner bl"></i><i class="kt-corner br"></i>
		<span class="pln-sr-only">{{ copy.heading }}</span>
		<div v-for="row in loadingRows" :key="row" class="pln-skel-row">
			<div class="kt-skel" style="width: 72%"></div>
			<div class="kt-skel" style="width: 52%"></div>
			<div class="kt-skel" style="width: 52%"></div>
			<div class="kt-skel" style="width: 44%"></div>
		</div>
	</div>
	<div v-else class="kt-card kt-blueprint pln-state-card" :data-testid="resolvedTestid">
		<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
		<i class="kt-corner bl"></i><i class="kt-corner br"></i>
		<h3>{{ copy.heading }}</h3>
		<p>{{ copy.text }}</p>
		<button v-if="copy.action" class="kt-btn kt-btn-secondary" @click="$emit('action')">
			{{ copy.action }}
		</button>
	</div>
</template>

<script setup>
import { computed } from "vue";

const STATES = {
	"forbidden-planning": {
		heading: "You do not have access to Procurement Planning",
		text: "This area needs one of these responsibilities: Departmental Author, Head of User Department, Procurement Planner, Head of Procurement Function, Finance Confirmation Officer, Accounting Officer, the configured statutory approver or Auditor. Ask your KenTender administrator to assign one in System setup.",
	},
	"forbidden-system-setup": {
		heading: "You do not have access to System setup",
		text: "This area needs Administrator or System Manager access.",
	},
	"record-not-available": {
		heading: "This record isn't available to you",
		text: "It may not exist, or you may not have access to it.",
		action: "Go to Procurement Planning",
	},
	"load-error": {
		heading: "Procurement Planning could not be loaded",
		text: "Try again. If the problem continues, contact support with the reference shown.",
		action: "Try again",
	},
	"config-missing": {
		heading: "Procurement rules are not configured",
		text: "Required configuration is missing or incomplete. Draft work can continue where permitted; the affected submission is unavailable.",
		action: "Back to Annual Plan",
	},
	"stale-action": {
		heading: "This action is no longer available",
		text: "The record changed after you opened it. Refresh to see its current state.",
		action: "Refresh",
	},
	"loading-planning": {
		heading: "Loading Procurement Planning…",
		text: "Approved skeleton rows only.",
	},
	"loading-review": {
		heading: "Loading Plan review…",
		text: "Approved skeleton sections only.",
	},
	"empty-accepted-requirements": {
		heading: "No accepted departmental requirements",
		text: "Accepted requirements will appear here after Procurement validation.",
	},
	"empty-search": {
		heading: "No requirements match this search",
		text: "Change the search or clear the filters.",
		action: "Clear filters",
	},
	"empty-validation-queue": {
		heading: "No departmental plans awaiting validation",
		text: "New submissions will appear here.",
	},
	"empty-corrections": {
		heading: "No correction requests",
		text: "No upstream correction request is recorded for this Plan Item.",
	},
	"historical-readonly": {
		heading: "Historical Plan Version",
		text: "This Version is read-only. Its reviewed evidence is preserved.",
		action: "View current Active Plan",
	},
};

const LOADING_KINDS = new Set(["loading-planning", "loading-review"]);

const props = defineProps({
	kind: { type: String, required: true },
	loadingRows: { type: Number, default: 3 },
	testid: { type: String, default: "" },
});
defineEmits(["action"]);

const copy = computed(() => STATES[props.kind]);
const isLoading = computed(() => LOADING_KINDS.has(props.kind));
const resolvedTestid = computed(() => props.testid || `pln-common-${props.kind}`);
</script>
