<!-- TPR-DES-14 Common states, ported class-for-class: each is a full inline
     state under KT-STD-001 §3A. Successful content never renders behind it.
     `kind` picks the card; `heading`/`text` may override the board copy with
     the server's own verdict text (Forbidden and Not found carry it). -->
<template>
	<div class="tnd-page">
		<div class="kt-card kt-blueprint tnd-state-card" :data-testid="`tnd-state-${kind}`" data-screen-label="TPR-DES-14 Common states">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="tnd-state-icon" :class="tone">
				<svg v-if="kind === 'forbidden'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
				<svg v-else-if="kind === 'not-found'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/><path d="M8 11h6"/></svg>
				<svg v-else-if="kind === 'source-unavailable'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><path d="M14 2v6h6"/><path d="m9.5 12.5 5 5"/><path d="m14.5 12.5-5 5"/></svg>
				<svg v-else-if="kind === 'already-started'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 17H7A5 5 0 0 1 7 7h2"/><path d="M15 7h2a5 5 0 1 1 0 10h-2"/><line x1="8" x2="16" y1="12" y2="12"/></svg>
				<svg v-else-if="kind === 'template-unavailable'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><path d="M14 2v6h6"/><path d="M12 11v4"/><path d="M12 18h.01"/></svg>
				<svg v-else-if="kind === 'rule-unavailable'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
				<svg v-else-if="kind === 'stale'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-2.64-6.36"/><path d="M21 3v6h-6"/></svg>
				<svg v-else width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg>
			</div>
			<div class="tnd-state-kind" :class="tone">{{ copy.kind }}</div>
			<h2>{{ heading || copy.heading }}</h2>
			<p class="tnd-card-body">{{ text || copy.text }}</p>
			<button v-if="copy.action" type="button" class="kt-btn kt-btn-secondary" :data-testid="`tnd-state-action`" @click="$emit('action', kind)">{{ copy.action }}</button>
			<p v-if="supportRef" class="tnd-support-ref">Support reference: {{ supportRef }}</p>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	kind: { type: String, required: true },
	heading: { type: String, default: "" },
	text: { type: String, default: "" },
	supportRef: { type: String, default: "" },
});
defineEmits(["action"]);

// TPR-DES-14 — the eight cards, verbatim.
const COPY = {
	forbidden: { tone: "is-critical", kind: "Forbidden", heading: "You do not have access to Tenders", text: "This area needs one of these responsibilities: Procurement Officer, Head of Procurement Function, Accounting Officer, Departmental Author, Head of User Department, Auditor or Authorised technical operator. Ask your KenTender administrator to assign one in System setup.", action: "" },
	"not-found": { tone: "is-critical", kind: "Not found", heading: "Tender not found", text: "This Tender is unavailable or you do not have permission to view it.", action: "Back to Tenders" },
	"source-unavailable": { tone: "is-attention", kind: "Source unavailable", heading: "Authorised requisition unavailable", text: "The requisition is no longer available to start this Tender.", action: "Back to Tenders" },
	"already-started": { tone: "is-draft", kind: "Already started", heading: "Tender already started", text: "This requisition is linked to a Tender.", action: "Open Tender" },
	"template-unavailable": { tone: "is-attention", kind: "Template unavailable", heading: "Tender format unavailable", text: "The standard IT-equipment Tender format is not available.", action: "Back to Tenders" },
	"rule-unavailable": { tone: "is-attention", kind: "Publication not configured", heading: "Publication rule unavailable", text: "The publication rule is not configured for this Tender.", action: "Contact administrator" },
	stale: { tone: "is-attention", kind: "Stale write", heading: "Tender changed", text: "Another user changed this Tender.", action: "Reload" },
	failure: { tone: "is-critical", kind: "Load failure", heading: "Tenders could not be loaded", text: "Try again.", action: "Try again" },
};

const copy = computed(() => COPY[props.kind] || COPY.failure);
const tone = computed(() => copy.value.tone);
</script>
