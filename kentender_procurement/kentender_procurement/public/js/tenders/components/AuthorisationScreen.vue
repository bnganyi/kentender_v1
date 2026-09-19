<!-- TPR-DES-07 AO publication authorisation, ported class-for-class: the
     Ready / segregation notice, the four-fact decision row, review notes,
     key facts (with Tendering period), View Invitation / complete Tender,
     the required channels (read-only, no selector, no edit control), the
     nested "Complete Tender details" disclosure and the footer's one action. -->
<template>
	<div class="tnd-page" data-screen-label="TPR-DES-07 AO publication authorisation">
		<BlueprintCard>
			<RecordHead title="Authorise Tender publication" :badge="pub.tender.badge" :refs="refs" lede="Review the approved package and the channels through which it must be published." />
			<div class="tnd-section">
				<div v-if="pub.segregation_message" class="kt-notice is-critical" data-testid="tnd-segregation">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
					<div class="kt-notice-body"><strong>{{ segregationHead }}</strong> {{ segregationTail }}</div>
				</div>
				<div v-else class="kt-notice is-live" data-testid="tnd-ready-to-authorise">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 6L9 17l-5-5"/></svg>
					<div class="kt-notice-body"><strong>Ready to authorise publication.</strong> Authorisation allows publication work to begin. The Tender is shown as Published only after every required channel is confirmed.</div>
				</div>
			</div>
			<div class="tnd-section tnd-section--tight tnd-grid-4" data-testid="tnd-approval-trail">
				<div class="tnd-fact"><div class="kt-label">Prepared by</div><div class="tnd-fact-value">{{ trail.prepared_by_name }}</div></div>
				<div class="tnd-fact"><div class="kt-label">Approved by</div><div class="tnd-fact-value">{{ trail.approved_by_name }}</div></div>
				<div class="tnd-fact"><div class="kt-label">Approved at</div><div class="tnd-fact-value">{{ trail.approved_at_label }}</div></div>
				<div class="tnd-fact"><div class="kt-label">Version</div><div class="tnd-fact-value">Version {{ trail.version_number }}</div></div>
			</div>
			<div style="padding-top: 20px"><FindingsNotices :review="pub.review || {}" :linkable="false" /></div>
			<KpiFacts :facts="pub.key_facts || []" />
			<div class="tnd-section tnd-section--tight tnd-actions">
				<button type="button" class="kt-btn kt-btn-secondary tnd-inline-btn" :disabled="pending" data-testid="tnd-view-invitation" @click="$emit('view-document', 'Invitation')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/></svg>View Invitation</button>
				<button type="button" class="kt-btn kt-btn-secondary tnd-inline-btn" :disabled="pending" data-testid="tnd-view-complete" @click="$emit('view-document', 'Complete Tender')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>View complete Tender</button>
			</div>
			<div class="tnd-section">
				<div class="kt-card-title tnd-section-title--tight" style="margin-bottom: 12px">Required publication channels</div>
				<div class="kt-bar tnd-bar"><i class="kt-bar-committed" style="width: 0%"></i></div>
				<table class="kt-table" data-testid="tnd-channel-table">
					<thead><tr><th>Channel</th><th>How confirmation is obtained</th><th>Current result</th></tr></thead>
					<tbody>
						<tr v-for="c in pub.proposed_channels || []" :key="c.channel"><td>{{ c.label }}</td><td>{{ c.how }}</td><td><span class="kt-status is-pending">{{ c.result }}</span></td></tr>
					</tbody>
				</table>
				<p v-if="pub.rule" class="tnd-xs tnd-muted" style="margin: 10px 0 0">Minimum period after publication: {{ pub.rule.minimum_preparation_days }} days.</p>
			</div>
			<div class="tnd-section tnd-section--content">
				<div class="kt-disclosure" style="margin-top: 14px">
					<div class="kt-disclosure-head" role="button" tabindex="0" @click="detailsOpen = !detailsOpen" @keydown.enter.prevent="detailsOpen = !detailsOpen"><div class="kt-disclosure-title-row"><span class="kt-disclosure-title">Complete Tender details</span></div><svg class="kt-disclosure-chevron" :class="{ 'is-open': detailsOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m6 9 6 6 6-6"/></svg></div>
					<div v-if="detailsOpen" class="kt-disclosure-body">
						<ContentSections :sections="pub.sections || []" :findings="(pub.review || {}).findings || []" nested />
					</div>
				</div>
			</div>
		</BlueprintCard>
		<div class="tnd-footer tnd-footer--end">
			<button v-if="canAuthorise" type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="tnd-authorise-publication" @click="$emit('authorise')">Authorise publication</button>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import BlueprintCard from "./BlueprintCard.vue";
import RecordHead from "./RecordHead.vue";
import FindingsNotices from "./FindingsNotices.vue";
import KpiFacts from "./KpiFacts.vue";
import ContentSections from "./ContentSections.vue";

const props = defineProps({
	pub: { type: Object, default: () => ({ tender: {} }) },
	requisitionReference: { type: String, default: "" },
	pending: Boolean,
});
defineEmits(["authorise", "view-document"]);

const detailsOpen = ref(false);
const refs = computed(() => `${props.pub.tender.tender_reference}${props.requisitionReference ? " · " + props.requisitionReference : ""}`);
const trail = computed(() => props.pub.approval_trail || {});
const canAuthorise = computed(() => (props.pub.allowed_actions || []).includes("authorise_publication"));
const segregationHead = computed(() => (props.pub.segregation_message || "").split(". ")[0] + ".");
const segregationTail = computed(() => (props.pub.segregation_message || "").split(". ").slice(1).join(". "));
</script>
