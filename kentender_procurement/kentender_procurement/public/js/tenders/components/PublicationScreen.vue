<!-- TPR-DES-08 Publication confirmation, ported class-for-class: progress
     notice + bar, the invalid-evidence / already-confirmed notices, the
     channel table (Confirmed rows link to their confirmation; awaiting rows
     offer Confirm publication to the HoPF only), the document buttons and
     the "Publication decision and rule" disclosure. -->
<template>
	<div class="tnd-page" data-screen-label="TPR-DES-08 Publication confirmation">
		<BlueprintCard>
			<RecordHead :title="pub.tender.title" :badge="pub.tender.badge" :refs="pub.tender.tender_reference" lede="Confirm where and when the approved Tender was published." />
			<div class="tnd-section">
				<div class="kt-notice is-attention" data-testid="tnd-publication-progress">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
					<div class="kt-notice-body"><strong>{{ confirmedCount }} of {{ channels.length }} required channels confirmed.</strong> The Tender is not yet shown as Published. Confirm the remaining channels below.</div>
				</div>
				<div class="kt-bar tnd-bar tnd-bar--after"><i class="kt-bar-committed" :style="{ width: percent + '%' }"></i></div>
			</div>
			<div v-if="invalidEvidence" class="tnd-section tnd-section--notice">
				<div class="kt-notice is-critical" data-testid="tnd-invalid-evidence">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
					<div class="kt-notice-body"><strong>The selected file cannot be used as publication evidence.</strong> Choose an allowed document or image file.</div>
				</div>
			</div>
			<div v-if="conflict" class="tnd-section tnd-section--notice">
				<div class="kt-notice is-info" data-testid="tnd-already-confirmed">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
					<div class="kt-notice-body"><strong>This channel is already confirmed.</strong> <button type="button" class="tnd-link-btn" @click="$emit('view-confirmation', conflict)">View confirmation</button></div>
				</div>
			</div>
			<div v-if="withdrawn" class="tnd-section tnd-section--notice">
				<div class="kt-notice is-attention" data-testid="tnd-withdrawn-notice"><div class="kt-notice-body"><strong>Publication authorisation was withdrawn.</strong> {{ withdrawn }}</div></div>
			</div>
			<div class="tnd-section">
				<table class="kt-table" data-testid="tnd-confirmation-table">
					<thead><tr><th>Channel</th><th>Result</th><th>Available at</th><th>Confirmation / action</th></tr></thead>
					<tbody>
						<tr v-for="c in channels" :key="c.channel" :data-testid="`tnd-channel-${c.channel}`" :data-status="c.status">
							<td>{{ c.channel_label }}</td>
							<td><span class="kt-status" :class="c.status === 'Confirmed' ? 'is-live' : 'is-attention'">{{ c.result_label }}</span></td>
							<td>{{ c.available_at_label || "—" }}</td>
							<td>
								<button v-if="c.status === 'Confirmed'" type="button" class="tnd-link-btn" data-testid="tnd-view-confirmation" @click="$emit('view-confirmation', c)">View confirmation</button>
								<button v-else-if="canConfirm" type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tnd-confirm-channel" @click="$emit('confirm-channel', c)">Confirm publication</button>
								<span v-else class="tnd-status-text">Awaiting the Head of Procurement Function</span>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
			<div class="tnd-section tnd-section--tight tnd-actions">
				<button type="button" class="kt-btn kt-btn-secondary tnd-inline-btn" :disabled="pending" data-testid="tnd-view-invitation" @click="$emit('view-document', 'Invitation')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/></svg>View Invitation</button>
				<button type="button" class="kt-btn kt-btn-secondary tnd-inline-btn" :disabled="pending" data-testid="tnd-view-complete" @click="$emit('view-document', 'Complete Tender')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>View complete Tender</button>
				<button v-if="canWithdraw" type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tnd-withdraw-authorisation" @click="$emit('withdraw')">Withdraw authorisation</button>
			</div>
			<div class="tnd-section tnd-section--content">
				<div class="kt-disclosure" style="margin-top: 14px">
					<div class="kt-disclosure-head" role="button" tabindex="0" @click="ruleOpen = !ruleOpen" @keydown.enter.prevent="ruleOpen = !ruleOpen"><div class="kt-disclosure-title-row"><span class="kt-disclosure-title">Publication decision and rule</span></div><svg class="kt-disclosure-chevron" :class="{ 'is-open': ruleOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m6 9 6 6 6-6"/></svg></div>
					<div v-if="ruleOpen" class="kt-disclosure-body"><p class="tnd-card-body" data-testid="tnd-rule-line">Authorised by {{ summary.authorised_by_name }}, {{ summary.authorised_at_label }} · Rule snapshot {{ summary.rule_snapshot_id }} · minimum period {{ summary.minimum_preparation_days }} days.</p></div>
				</div>
			</div>
		</BlueprintCard>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import BlueprintCard from "./BlueprintCard.vue";
import RecordHead from "./RecordHead.vue";

const props = defineProps({
	pub: { type: Object, default: () => ({ tender: {} }) },
	invalidEvidence: Boolean,
	conflict: { type: Object, default: null },
	withdrawn: { type: String, default: "" },
	pending: Boolean,
});
defineEmits(["confirm-channel", "view-confirmation", "view-document", "withdraw"]);

const ruleOpen = ref(false);
const summary = computed(() => props.pub.publication || {});
const channels = computed(() => summary.value.required_channels_rows || summary.value.channels || []);
const confirmedCount = computed(() => channels.value.filter((c) => c.status === "Confirmed").length);
const percent = computed(() => (channels.value.length ? Math.round((confirmedCount.value / channels.value.length) * 100) : 0));
const canConfirm = computed(() => (props.pub.allowed_actions || []).includes("confirm_publication_channel"));
const canWithdraw = computed(() => (props.pub.allowed_actions || []).includes("withdraw_publication_authorisation"));
</script>
