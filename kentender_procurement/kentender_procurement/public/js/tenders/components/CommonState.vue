<!-- TPR-DES-14 Common states (§10.15), ported class-for-class: each is a full
     inline state under KT-STD-001 §3A — the blueprint card, the tone icon and
     variant label, the heading, the message and the state's own actions.
     Successful content never renders behind it, and no state carries the
     §10.17 journey or next step. The root gives the variant (`kind`), any
     server wording that replaces the board copy, and the exact actions this
     viewer may take (e.g. View STD Template only for a user who may inspect
     templates, Open System setup only for a System Manager). -->
<template>
	<!-- The access state is the shared one (KT-STD-001 §3A access state): the board's tone card is for the other variants. -->
	<div v-if="kind === 'forbidden'" class="kt-page" data-testid="tnd-state-forbidden">
		<AccessDenied :heading="heading || copy.heading" :text="text || copy.text" />
	</div>
	<div v-else class="tnd-page">
		<div class="card blueprint tnd-state-card" :data-testid="`tnd-state-${kind}`" data-screen-label="TPR-DES-14 Common states">
			<i class="corner tl"></i><i class="corner tr"></i><i class="corner bl"></i><i class="corner br"></i>
			<div class="tnd-state-head">
				<div class="tnd-state-icon" :class="toneClass">
					<svg v-if="toneClass === 'is-critical'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>
					<svg v-else-if="toneClass === 'is-draft'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
					<svg v-else width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg>
				</div>
				<div class="tnd-state-kind" :class="toneClass">{{ label || copy.label }}</div>
			</div>
			<h2>{{ heading || copy.heading }}</h2>
			<p class="tnd-card-body" data-testid="tnd-state-text">{{ text || copy.text }}</p>
			<div v-if="shownActions.length" class="tnd-actions">
				<button v-for="action in shownActions" :key="action.key" type="button" class="btn" :class="action.primary ? 'btn-primary' : 'btn-secondary'" :data-testid="`tnd-state-action-${action.key}`" @click="$emit('action', action)">{{ action.label }}</button>
			</div>
			<p v-if="supportRef" class="tnd-support-ref">Support reference: {{ supportRef }}</p>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import AccessDenied from "../../access_shared/AccessDenied.vue";

const props = defineProps({
	kind: { type: String, required: true },
	heading: { type: String, default: "" },
	text: { type: String, default: "" },
	label: { type: String, default: "" },
	tone: { type: String, default: "" },
	// [{ key, label, primary?, route? }] — when absent, the variant's own default
	actions: { type: Array, default: null },
	supportRef: { type: String, default: "" },
});
defineEmits(["action"]);

// TPR-DES-14 — the board's variants, verbatim.
const BACK = { key: "back", label: "Back to Tenders" };
const COPY = {
	forbidden: { tone: "is-critical", label: "Forbidden", heading: "You do not have access to Tenders", text: "This area needs one of these responsibilities: Procurement Officer, Head of Procurement Function, Accounting Officer, Departmental Author, Head of User Department, Auditor or Authorised technical operator. Ask your KenTender administrator to assign one in System setup.", actions: [] },
	"not-found": { tone: "is-critical", label: "Not found", heading: "Tender not found", text: "This Tender is unavailable or you do not have permission to view it.", actions: [BACK] },
	"source-unavailable": { tone: "is-attention", label: "Source unavailable", heading: "Authorised requisition unavailable", text: "The requisition is no longer available to start this Tender.", actions: [BACK] },
	"already-started": { tone: "is-draft", label: "Already started", heading: "Tender already started", text: "This requisition is linked to a Tender.", actions: [{ key: "open-tender", label: "Open Tender" }] },
	"requisition-unavailable": { tone: "is-attention", label: "Already started", heading: "Requisition unavailable", text: "This requisition cannot be used to start a Tender.", actions: [BACK] },
	"template-unavailable": { tone: "is-attention", label: "Template unavailable", heading: "Tender format unavailable", text: "The standard IT-equipment Tender format is not available.", actions: [BACK] },
	"release-superseded": { tone: "is-draft", label: "Bound release Superseded", heading: "Tender format has a newer release", text: "", actions: [BACK] },
	"release-withdrawn": { tone: "is-critical", label: "Bound release Withdrawn", heading: "Tender format withdrawn", text: "", actions: [BACK] },
	"release-failed": { tone: "is-critical", label: "Bound release integrity failed", heading: "Tender format could not be verified", text: "", actions: [BACK] },
	"rule-unavailable": { tone: "is-attention", label: "Publication not configured", heading: "Publication rule unavailable", text: "The publication rule is not configured for this Tender. A System Manager must configure it.", actions: [BACK] },
	stale: { tone: "is-attention", label: "Stale write", heading: "Tender changed", text: "Another user changed this Tender.", actions: [{ key: "reload", label: "Reload" }] },
	failure: { tone: "is-critical", label: "Load failure", heading: "Tenders could not be loaded", text: "Try again.", actions: [{ key: "retry", label: "Try again" }] },
};

const copy = computed(() => COPY[props.kind] || COPY.failure);
const toneClass = computed(() => props.tone || copy.value.tone);
const shownActions = computed(() => props.actions || copy.value.actions);
</script>
