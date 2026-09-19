<!-- TPR-DES-12 Cancel Tender (900px): the decision form for the Accounting
     Officer (ground from the code-owned catalogue, reason, consequences),
     the HOPF recommendation panel (and the recommend action for the HoPF),
     and the Cancelled detail with compliance obligations and their
     Record evidence actions. -->
<template>
	<div class="tnd-page tnd-page--narrow" data-screen-label="TPR-DES-12 Cancel Tender">
		<BlueprintCard>
			<RecordHead title="Cancel Tender" :badge="cancelled ? 'Cancelled' : tender.badge" :badge-tone="cancelled ? 'is-critical' : 'is-live'" :refs="tender.tender_reference" :lede="cancelled ? '' : 'Cancel this procurement proceeding using an applicable statutory ground.'" />
			<template v-if="!cancelled">
				<div class="tnd-section">
					<div class="kt-notice is-critical" data-testid="tnd-cancel-warning">
						<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
						<div class="kt-notice-body"><strong>Cancellation is final for this Tender.</strong> It does not restore the Requisition or create a replacement Tender.</div>
					</div>
				</div>
				<div class="tnd-section tnd-grid-2" data-testid="tnd-cancel-summary">
					<div class="tnd-fact"><div class="kt-label">Purchase</div><div class="tnd-fact-value">{{ summary.purchase }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Tender</div><div class="tnd-fact-value">{{ summary.tender }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Published at</div><div class="tnd-fact-value">{{ summary.published_at }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Submission deadline</div><div class="tnd-fact-value">{{ summary.submission_deadline }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Required channels</div><div class="tnd-fact-value">{{ summary.channel_count }}</div></div>
				</div>
				<div v-if="recommendation" class="tnd-section">
					<div class="kt-notice is-attention" data-testid="tnd-recommendation">
						<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
						<div class="kt-notice-body"><strong>Recommended by {{ recommendation.by_name }}, HOPF.</strong> {{ recommendation.text }}</div>
					</div>
				</div>
				<div class="tnd-section">
					<div class="kt-field"><label for="tnd-cancel-ground">Ground</label>
						<select id="tnd-cancel-ground" class="kt-input" v-model="ground" :disabled="!canDecide && !canRecommend" data-testid="tnd-cancel-ground"><option v-for="g in data.grounds || []" :key="g.key" :value="g.key">{{ g.label }}</option></select>
					</div>
					<div class="kt-field" style="margin: 0"><label for="tnd-cancel-reason">Reason</label>
						<textarea id="tnd-cancel-reason" class="kt-input" rows="3" v-model="reason" :disabled="!canDecide && !canRecommend" data-testid="tnd-cancel-reason"></textarea>
						<p v-if="fieldError" class="tnd-field-error" data-testid="tnd-cancel-error">{{ fieldError }}</p>
					</div>
					<p v-if="!canDecide && !canRecommend" class="tnd-status-text" style="margin-top: 8px" data-testid="tnd-cancel-no-action">Only the Accounting Officer can cancel this Tender.</p>
				</div>
				<div class="tnd-section tnd-section--last">
					<div class="kt-card-title" style="margin-bottom: 12px">Consequences</div>
					<ul class="tnd-list" data-testid="tnd-consequences">
						<li>Tender closes immediately.</li>
						<li>Cancellation notice published through all original channels.</li>
						<li>PPRA report due {{ consequences.ppra_report_due_by }}.</li>
						<li>Candidate notices due {{ consequences.candidate_notice_due_by }}.</li>
						<li>{{ consequences.replacement_text || "Replacement procurement requires new governance." }}</li>
					</ul>
				</div>
			</template>
			<template v-else>
				<div class="tnd-section tnd-grid-2" data-testid="tnd-cancelled-facts">
					<div class="tnd-fact"><div class="kt-label">Decided by</div><div class="tnd-fact-value">{{ cancellation.decided_by_name }}, Accounting Officer</div></div>
					<div class="tnd-fact"><div class="kt-label">Decided at</div><div class="tnd-fact-value">{{ cancellation.decided_at_label }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Ground</div><div class="tnd-fact-value">{{ cancellation.ground_label }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Reason</div><div class="tnd-fact-value">{{ cancellation.reason }}</div></div>
				</div>
				<div v-if="cancellation.recommendation" class="tnd-section"><div class="kt-notice is-attention"><div class="kt-notice-body"><strong>Recommended by {{ cancellation.recommendation.by_name }}, HOPF.</strong> {{ cancellation.recommendation.text }}</div></div></div>
				<div class="tnd-section tnd-section--last">
					<div class="kt-card-title" style="margin-bottom: 12px">Compliance obligations</div>
					<table class="kt-table" data-testid="tnd-obligations">
						<thead><tr><th>Obligation</th><th>Due</th><th>Status</th><th></th></tr></thead>
						<tbody>
							<tr v-for="o in cancellation.obligations || []" :key="o.obligation_id" :data-testid="`tnd-obligation-${o.obligation_id}`" :data-status="o.status">
								<td>{{ o.label }}</td><td>{{ o.due_by }}</td>
								<td><span class="kt-status" :class="o.status === 'Recorded' ? 'is-live' : o.status === 'Overdue' ? 'is-critical' : 'is-attention'">{{ o.status === "Due" ? "Outstanding" : o.status }}</span><span v-if="o.evidence_reference" class="tnd-sub">{{ o.evidence_reference }} · {{ o.recorded_by_name }}</span></td>
								<td><button v-if="o.status !== 'Recorded' && canRecord" type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tnd-record-evidence" @click="$emit('record-evidence', o)">Record evidence</button></td>
							</tr>
						</tbody>
					</table>
				</div>
			</template>
		</BlueprintCard>
		<div v-if="!cancelled" class="tnd-footer">
			<a href="#" class="tnd-footer-back" data-testid="tnd-back" @click.prevent="$emit('back')">Back</a>
			<div class="tnd-actions">
				<button v-if="canRecommend" type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tnd-recommend" @click="recommend">Recommend cancellation</button>
				<button v-if="canDecide" type="button" class="kt-btn tnd-btn-danger" :disabled="pending" data-testid="tnd-cancel-open-dialog" @click="decide">Cancel Tender</button>
			</div>
		</div>
		<div v-else class="tnd-footer">
			<a href="#" class="tnd-footer-back" data-testid="tnd-back" @click.prevent="$emit('back')">Back</a>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import BlueprintCard from "./BlueprintCard.vue";
import RecordHead from "./RecordHead.vue";

const props = defineProps({
	data: { type: Object, default: () => ({ tender: {} }) },
	pending: Boolean,
	error: { type: String, default: "" },
});
const emit = defineEmits(["back", "recommend", "cancel", "record-evidence"]);

const tender = computed(() => props.data.tender || {});
const summary = computed(() => props.data.summary || {});
const consequences = computed(() => props.data.consequences || {});
const recommendation = computed(() => props.data.recommendation || null);
const cancellation = computed(() => props.data.cancellation || null);
const cancelled = computed(() => tender.value.overall_status === "Cancelled" && !!cancellation.value);
const actions = computed(() => props.data.allowed_actions || []);
const canDecide = computed(() => actions.value.includes("cancel_tender"));
const canRecommend = computed(() => actions.value.includes("recommend_cancellation"));
const canRecord = computed(() => actions.value.includes("record_cancellation_evidence"));
const ground = ref("");
const reason = ref("");
const localError = ref("");
const fieldError = computed(() => localError.value || props.error);
watch(
	() => props.data,
	(d) => {
		if (!ground.value && d.grounds && d.grounds.length) ground.value = (recommendation.value && recommendation.value.ground) || d.grounds[0].key;
	},
	{ immediate: true }
);
function validate() {
	const text = reason.value.trim();
	if (text.length < 20 || text.length > 2000) {
		localError.value = "Enter a reason of 20–2,000 characters.";
		return null;
	}
	localError.value = "";
	return { ground: ground.value, reason: text, ground_label: ((props.data.grounds || []).find((g) => g.key === ground.value) || {}).label || ground.value };
}
function recommend() {
	const v = validate();
	if (v) emit("recommend", v);
}
function decide() {
	const v = validate();
	if (v) emit("cancel", v);
}
</script>
