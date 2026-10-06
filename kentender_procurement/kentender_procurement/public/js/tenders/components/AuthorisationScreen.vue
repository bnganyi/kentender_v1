<!-- TPR-DES-07 AO publication authorisation (§10.8), ported class-for-class:
     the header (no awaiting-action badge), the §10.17 guidance region, the
     approval trail (no digest: TPR-CHG-001 v0.16 §10.8 item 2), the review note,
     key facts (with Tendering period), View Invitation / complete Tender,
     the required channels (read-only: no selector, no edit control, no
     progress bar), the closed "Complete Tender details" disclosure holding
     the six sections, and the footer's one action. -->
<template>
	<div class="tnd-page" data-screen-label="TPR-DES-07 AO publication authorisation">
		<BlueprintCard>
			<RecordHead title="Authorise Tender publication" :refs="refs" lede="Review the approved package and the channels through which it must be published." />
			<TenderGuidance :guidance="pub.guidance || null" :pending="pending" />
			<div class="tnd-section tnd-section--tight tnd-fact-grid" data-testid="tnd-approval-trail">
				<div class="tnd-fact"><div class="kt-label">Prepared by</div><div class="tnd-fact-value">{{ trail.prepared_by_name }}</div></div>
				<div class="tnd-fact"><div class="kt-label">Approved by</div><div class="tnd-fact-value">{{ trail.approved_by_name }}</div></div>
				<div class="tnd-fact"><div class="kt-label">Approved at</div><div class="tnd-fact-value">{{ trail.approved_at_label }}</div></div>
				<div class="tnd-fact"><div class="kt-label">Version</div><div class="tnd-fact-value">Version {{ trail.version_number }}</div></div>
			</div>
			<ReviewNote :notes="(pub.review || {}).review_notes || []" :linkable="false" />
			<KeyFacts :facts="pub.key_facts || []" />
			<div class="tnd-section tnd-section--tight tnd-actions">
				<button type="button" class="btn btn-secondary tnd-inline-btn" :disabled="pending" data-testid="tnd-view-invitation" @click="$emit('view-document', 'Invitation')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/></svg>View Invitation</button>
				<button type="button" class="btn btn-secondary tnd-inline-btn" :disabled="pending" data-testid="tnd-view-complete" @click="$emit('view-document', 'Complete Tender')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>View complete Tender</button>
			</div>
			<div class="tnd-section">
				<div class="tnd-block-title tnd-block-title--section">Required publication channels</div>
				<table class="table" data-testid="tnd-channel-table">
					<thead><tr><th>Channel</th><th>How confirmation is obtained</th><th>Current result</th></tr></thead>
					<tbody>
						<tr v-for="c in pub.proposed_channels || []" :key="c.channel"><td>{{ c.label }}</td><td>{{ c.how }}</td><td><span class="kt-status is-pending">{{ c.result }}</span></td></tr>
					</tbody>
				</table>
			</div>
			<div class="tnd-section tnd-section--content tnd-section--last">
				<div class="kt-disclosure">
					<div class="kt-disclosure-head" role="button" tabindex="0" :aria-expanded="detailsOpen ? 'true' : 'false'" data-testid="tnd-complete-details" @click="detailsOpen = !detailsOpen" @keydown.enter.prevent="detailsOpen = !detailsOpen"><div class="kt-disclosure-title-row"><span class="kt-disclosure-title">Complete Tender details</span></div><svg class="kt-disclosure-chevron" :class="{ 'is-open': detailsOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m6 9 6 6 6-6"/></svg></div>
					<div v-if="detailsOpen" class="kt-disclosure-body">
						<ContentSections :sections="pub.sections || []" nested />
					</div>
				</div>
			</div>
		</BlueprintCard>
		<div class="tnd-footer">
			<a href="#" class="tnd-footer-back" data-testid="tnd-back" @click.prevent="$emit('back')">Back to Tenders</a>
			<div class="tnd-footer-actions">
				<button v-if="canReturn" type="button" class="btn btn-secondary" :disabled="pending" data-testid="tnd-return-to-hopf" @click="$emit('return')">Return to Head of Procurement Function</button>
				<button v-if="canAuthorise" type="button" class="btn btn-primary" :disabled="pending" data-testid="tnd-authorise-publication" @click="$emit('authorise')">Authorise publication</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import BlueprintCard from "./BlueprintCard.vue";
import RecordHead from "./RecordHead.vue";
import TenderGuidance from "./TenderGuidance.vue";
import ReviewNote from "./ReviewNote.vue";
import KeyFacts from "./KeyFacts.vue";
import ContentSections from "./ContentSections.vue";

const props = defineProps({
	pub: { type: Object, default: () => ({ tender: {} }) },
	requisitionReference: { type: String, default: "" },
	pending: Boolean,
});
defineEmits(["authorise", "return", "view-document", "back"]);

const detailsOpen = ref(false);
const refs = computed(() => `${props.pub.tender.tender_reference}${props.requisitionReference ? " · " + props.requisitionReference : ""}`);
const trail = computed(() => props.pub.approval_trail || {});
const canAuthorise = computed(() => (props.pub.allowed_actions || []).includes("authorise_publication"));
const canReturn = computed(() => (props.pub.allowed_actions || []).includes("return_to_hopf"));
</script>
