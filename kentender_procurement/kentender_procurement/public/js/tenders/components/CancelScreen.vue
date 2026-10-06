<!-- TPR-DES-12 Cancel Tender (§10.13), ported class-for-class across the
     board's five variants. The §10.17 guidance region states the viewer's
     next step; the screen shows:
       - the Accounting Officer's decision: the finality warning, the
         summary, the HOPF recommendation when one exists, ground and
         reason, and the consequences;
       - a cancellation-review request: who asked and the proposed change no
         addendum may make; Cancel Tender opens the same ground/reason
         decision, Close cancellation review asks for a reason;
       - the Cancelled detail: the decision facts and the compliance
         obligations, with evidence actions only for the authorised
         procurement function on an outstanding obligation.
     The HOPF may record a recommendation (never a decision). Grounds come
     from the server's catalogue; every action is the server's. -->
<template>
	<div class="tnd-page" data-screen-label="TPR-DES-12 Cancel Tender">
		<BlueprintCard>
			<RecordHead title="Cancel Tender" :badge="cancelled ? 'Cancelled' : tender.badge" :badge-tone="cancelled ? 'is-critical' : 'is-live'" :refs="tender.tender_reference" :lede="cancelled ? '' : 'Cancel this procurement proceeding using an applicable statutory ground.'" />
			<TenderGuidance :guidance="data.guidance || null" :pending="pending" @fix="onFix" />

			<template v-if="!cancelled">
				<div v-if="deciding" class="tnd-section tnd-section--plain">
					<div class="kt-notice is-critical" data-testid="tnd-cancel-warning">
						<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
						<div class="kt-notice-body">{{ data.warning_text || "Cancellation is final for this Tender. It does not restore the Requisition or create a replacement Tender." }}</div>
					</div>
				</div>
				<div v-if="review && !deciding" class="tnd-section" data-testid="tnd-review-request">
					<div class="tnd-fact-grid tnd-fact-grid--2">
						<div class="tnd-fact"><div class="kt-label">Purchase</div><div class="tnd-fact-value">{{ summary.purchase }}</div></div>
						<div class="tnd-fact"><div class="kt-label">Requested by</div><div class="tnd-fact-value">{{ review.requested_by_name }}, {{ review.requested_by_role }}</div></div>
					</div>
				</div>
				<CancelSummary v-else :summary="summary" :channel-names="channelNames" />
				<div v-if="review && !deciding" class="tnd-section tnd-section--last" data-testid="tnd-review-proposal">
					<h2 class="tnd-h2">Proposed change that cannot be made by addendum</h2>
					<p class="tnd-small tnd-muted-700 tnd-h2-lede">An addendum cannot expand the purchase. This is a request to consider cancellation, not a cancellation decision.</p>
					<table class="table">
						<thead><tr><th>Field</th><th>Current published</th><th>Proposed</th><th>Reason</th></tr></thead>
						<tbody><tr><td>{{ review.field }}</td><td>{{ review.current }}</td><td>{{ review.proposed }}</td><td>{{ review.reason }}</td></tr></tbody>
					</table>
				</div>
				<div v-if="recommendation && deciding" class="tnd-section" data-testid="tnd-recommendation">
					<h2 class="tnd-h2">HOPF recommendation</h2>
					<p class="tnd-body-text">{{ recommendation.text }}</p>
					<p class="tnd-small tnd-muted-700" style="margin: 6px 0 0">{{ recommendation.by_name }}, Head of Procurement Function · {{ recommendation.at_label }}</p>
				</div>
				<template v-if="deciding">
					<div class="tnd-section tnd-section--form">
						<div class="field tnd-form-row"><label for="tnd-cancel-ground">Ground</label>
							<select id="tnd-cancel-ground" class="input" v-model="ground" :disabled="!canDecide && !canRecommend" data-testid="tnd-cancel-ground"><option v-for="g in data.grounds || []" :key="g.key" :value="g.key">{{ g.label }}</option></select>
						</div>
						<div class="field" style="margin: 0"><label for="tnd-cancel-reason">Reason</label>
							<textarea id="tnd-cancel-reason" class="input" rows="3" v-model="reason" :disabled="!canDecide && !canRecommend" data-testid="tnd-cancel-reason"></textarea>
							<p v-if="fieldError" class="tnd-field-error" data-testid="tnd-cancel-error">{{ fieldError }}</p>
						</div>
					</div>
					<div class="tnd-section tnd-section--last">
						<h2 class="tnd-h2">Consequences</h2>
						<ul class="tnd-list" data-testid="tnd-consequences">
							<li>Tender closes immediately.</li>
							<li>Cancellation notice published through all original channels.</li>
							<li>PPRA report due {{ consequences.ppra_report_due_by }}.</li>
							<li>Candidate notices due {{ consequences.candidate_notice_due_by }}.</li>
							<li>{{ consequences.replacement_text || "Replacement procurement requires new governance." }}</li>
						</ul>
					</div>
				</template>
			</template>

			<template v-else>
				<CancelSummary :summary="summary" :channel-names="channelNames" />
				<div class="tnd-section tnd-fact-grid tnd-fact-grid--2" data-testid="tnd-cancelled-facts">
					<div class="tnd-fact"><div class="kt-label">Decided by</div><div class="tnd-fact-value">{{ cancellation.decided_by_name }}, Accounting Officer</div></div>
					<div class="tnd-fact"><div class="kt-label">Decided at</div><div class="tnd-fact-value">{{ cancellation.decided_at_label }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Ground</div><div class="tnd-fact-value">{{ cancellation.ground_label }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Reason</div><div class="tnd-fact-value">{{ cancellation.reason }}</div></div>
				</div>
				<div class="tnd-section tnd-section--last">
					<h2 class="tnd-h2">Compliance obligations</h2>
					<table class="table" data-testid="tnd-obligations">
						<thead><tr><th>Obligation</th><th>Due</th><th>Status</th><th v-if="canRecord">Action</th></tr></thead>
						<tbody>
							<tr v-for="row in data.compliance || []" :key="row.key" :data-testid="`tnd-obligation-${row.key}`" :data-status="row.status">
								<td>{{ row.label }}<span v-if="row.detail" class="tnd-sub">{{ row.detail }}</span></td>
								<td>{{ row.due_by }}</td>
								<td><span class="kt-status" :class="row.status === 'Recorded' ? 'is-live' : row.status === 'Overdue' ? 'is-critical' : 'is-attention'">{{ row.status }}</span></td>
								<td v-if="canRecord"><button v-if="row.action" type="button" class="btn btn-ghost" :disabled="pending" :data-testid="`tnd-${row.action.replace(/_/g, '-')}`" @click="$emit('record-evidence', obligationFor(row))">{{ row.action_label }}</button></td>
							</tr>
						</tbody>
					</table>
				</div>
			</template>
		</BlueprintCard>
		<div class="tnd-footer">
			<a href="#" class="tnd-footer-back" data-testid="tnd-back" @click.prevent="$emit('back')">Back</a>
			<div v-if="!cancelled" class="tnd-actions">
				<button v-if="canClose && !deciding" type="button" class="btn btn-secondary" :disabled="pending" data-testid="tnd-close-review" @click="$emit('close-review', review.addendum)">Close cancellation review</button>
				<button v-if="canRecommend" type="button" class="btn btn-secondary" :disabled="pending" data-testid="tnd-recommend" @click="recommend">Recommend cancellation</button>
				<button v-if="canDecide" type="button" class="btn tnd-btn-danger" :disabled="pending" data-testid="tnd-cancel-open-dialog" @click="decide">Cancel Tender</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, defineComponent, h, ref, watch } from "vue";
import BlueprintCard from "./BlueprintCard.vue";
import RecordHead from "./RecordHead.vue";
import TenderGuidance from "./TenderGuidance.vue";

const props = defineProps({
	data: { type: Object, default: () => ({ tender: {} }) },
	pending: Boolean,
	error: { type: String, default: "" },
	// bumped by the root when the guidance's Cancel Tender fix is chosen here
	focusDecision: { type: Number, default: 0 },
});
const emit = defineEmits(["back", "recommend", "cancel", "record-evidence", "close-review", "fix"]);

// The board's summary grid, drawn on the decision and the cancelled detail.
const CancelSummary = defineComponent({
	props: { summary: { type: Object, default: () => ({}) }, channelNames: { type: String, default: "" } },
	setup(p) {
		const fact = (label, value) => h("div", { class: "tnd-fact" }, [h("div", { class: "kt-label" }, label), h("div", { class: "tnd-fact-value" }, value || "—")]);
		return () => h("div", { class: "tnd-section tnd-fact-grid", "data-testid": "tnd-cancel-summary" }, [fact("Purchase", p.summary.purchase), fact("Published at", p.summary.published_at), fact("Submission deadline", p.summary.submission_deadline), fact("Required channels", p.channelNames)]);
	},
});
const tender = computed(() => props.data.tender || {});
const summary = computed(() => props.data.summary || {});
const consequences = computed(() => props.data.consequences || {});
const recommendation = computed(() => props.data.recommendation || null);
const cancellation = computed(() => props.data.cancellation || null);
const review = computed(() => props.data.review || null);
const cancelled = computed(() => tender.value.overall_status === "Cancelled" && !!cancellation.value);
const actions = computed(() => props.data.allowed_actions || []);
const canDecide = computed(() => actions.value.includes("cancel_tender"));
const canRecommend = computed(() => actions.value.includes("recommend_cancellation"));
const canRecord = computed(() => actions.value.includes("record_cancellation_evidence"));
const canClose = computed(() => actions.value.includes("close_cancellation_review") && !!review.value);
const channelNames = computed(() => summary.value.required_channels || String(summary.value.channel_count || ""));
// a review request is shown as the request first; Cancel Tender opens the
// same ground/reason decision (§10.13 TPR-DES-12-REQUEST)
const openedDecision = ref(false);
const deciding = computed(() => !review.value || openedDecision.value);
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
watch(() => props.focusDecision, () => {
	openedDecision.value = true;
});
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
	if (!deciding.value) {
		openedDecision.value = true;
		return;
	}
	const v = validate();
	if (v) emit("cancel", v);
}
function onFix(fix) {
	if (fix && fix.fix_id === "cancel_tender") {
		openedDecision.value = true;
		return;
	}
	emit("fix", fix);
}
function obligationFor(row) {
	return ((cancellation.value || {}).obligations || []).find((o) => o.obligation_id === row.obligation_id) || { obligation_id: row.obligation_id, label: row.label };
}
</script>
