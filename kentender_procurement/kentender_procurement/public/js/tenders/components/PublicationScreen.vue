<!-- TPR-DES-08 Publication confirmation (§10.9), ported class-for-class: the
     header (no duplicate confirmation-required badge), the §10.17 guidance
     region — which states the "n of 4" count once, or the refused
     confirmation's own blocked answer — the channel table (Confirmed rows link
     to their confirmation, awaiting rows offer Confirm publication to the
     HoPF only, a conflicting request draws its inline row beneath the
     channel), the approved documents and the closed "Publication decision and
     rule". No automatic acknowledgement, retry, manual Published or package
     edit exists here. -->
<template>
	<div class="tnd-page" data-screen-label="TPR-DES-08 Publication confirmation">
		<BlueprintCard>
			<RecordHead :title="pub.tender.title" :refs="pub.tender.tender_reference" lede="Confirm where and when the approved Tender was published." />
			<TenderGuidance :guidance="refusal || pub.guidance || null" :pending="pending" @fix="$emit('fix', $event)" />
			<div v-if="withdrawn" class="tnd-section tnd-section--notice">
				<div class="kt-notice is-attention" data-testid="tnd-withdrawn-notice"><div class="kt-notice-body"><strong>Publication authorisation was withdrawn.</strong> {{ withdrawn }}</div></div>
			</div>
			<div class="tnd-section">
				<table class="table" data-testid="tnd-confirmation-table">
					<thead><tr><th>Channel</th><th>Result</th><th>Available at</th><th>Confirmation / action</th></tr></thead>
					<tbody>
						<template v-for="c in channels" :key="c.channel">
							<tr :data-testid="`tnd-channel-${c.channel}`" :data-status="c.status">
								<td>{{ c.channel_label }}</td>
								<td><span class="kt-status" :class="c.status === 'Confirmed' ? 'is-live' : 'is-attention'">{{ c.result_label }}</span></td>
								<td>{{ c.available_at_label || "—" }}</td>
								<td>
									<button v-if="c.status === 'Confirmed'" type="button" class="btn btn-ghost" data-testid="tnd-view-confirmation" @click="$emit('view-confirmation', c)">View confirmation</button>
									<button v-else-if="canConfirm" type="button" class="btn btn-ghost" :disabled="pending" data-testid="tnd-confirm-channel" @click="$emit('confirm-channel', c)">Confirm publication</button>
									<span v-else class="tnd-status-text">Awaiting the Head of Procurement Function</span>
								</td>
							</tr>
							<tr v-if="conflict && conflict.channel === c.channel" data-testid="tnd-already-confirmed">
								<td colspan="4"><strong>This channel is already confirmed.</strong> The later confirmation request changed nothing. <button type="button" class="btn btn-ghost" @click="$emit('view-confirmation', c)">View confirmation</button></td>
							</tr>
						</template>
					</tbody>
				</table>
			</div>
			<div class="tnd-section tnd-section--tight tnd-actions" data-testid="tnd-approved-documents">
				<button type="button" class="btn btn-secondary tnd-inline-btn" :disabled="pending" data-testid="tnd-view-invitation" @click="$emit('view-document', 'Invitation')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/></svg>View Invitation</button>
				<button type="button" class="btn btn-secondary tnd-inline-btn" :disabled="pending" data-testid="tnd-view-complete" @click="$emit('view-document', 'Complete Tender')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>View complete Tender</button>
				<button v-if="canWithdraw" type="button" class="btn btn-secondary kt-danger" :disabled="pending" data-testid="tnd-withdraw-authorisation" @click="$emit('withdraw')">Withdraw authorisation</button>
			</div>
			<div class="tnd-section tnd-section--content tnd-section--last">
				<div class="kt-disclosure">
					<div class="kt-disclosure-head" role="button" tabindex="0" :aria-expanded="ruleOpen ? 'true' : 'false'" data-testid="tnd-rule-disclosure" @click="ruleOpen = !ruleOpen" @keydown.enter.prevent="ruleOpen = !ruleOpen"><div class="kt-disclosure-title-row"><span class="kt-disclosure-title">Publication decision and rule</span></div><svg class="kt-disclosure-chevron" :class="{ 'is-open': ruleOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m6 9 6 6 6-6"/></svg></div>
					<div v-if="ruleOpen" class="kt-disclosure-body"><p class="tnd-card-body tnd-break" style="margin: 0" data-testid="tnd-rule-line">{{ summary.rule_line }}</p>
						<div v-if="(summary.technical_facts || []).length" class="tnd-tech" data-testid="tnd-technical-details"><div class="kt-label">Technical details</div>
							<div v-for="f in summary.technical_facts" :key="f.label" class="tnd-fact"><div class="kt-label">{{ f.label }}</div><div class="tnd-fact-value tnd-break tnd-mono">{{ f.value }}</div></div>
						</div></div>
				</div>
			</div>
		</BlueprintCard>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import BlueprintCard from "./BlueprintCard.vue";
import RecordHead from "./RecordHead.vue";
import TenderGuidance from "./TenderGuidance.vue";

const props = defineProps({
	pub: { type: Object, default: () => ({ tender: {} }) },
	// a refused confirmation's own guidance — next step and journey
	// (§10.17 DES-08 invalid evidence / conflicting confirmation)
	refusal: { type: Object, default: null },
	conflict: { type: Object, default: null },
	withdrawn: { type: String, default: "" },
	pending: Boolean,
});
defineEmits(["confirm-channel", "view-confirmation", "view-document", "withdraw", "fix"]);

const ruleOpen = ref(false);
const summary = computed(() => props.pub.publication || {});
const channels = computed(() => summary.value.channels || []);
const canConfirm = computed(() => (props.pub.allowed_actions || []).includes("confirm_publication_channel"));
const canWithdraw = computed(() => (props.pub.allowed_actions || []).includes("withdraw_publication_authorisation"));
</script>
