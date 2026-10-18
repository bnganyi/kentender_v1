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
     from the server's catalogue; every action is the server's.

     TPR-CHG-001 v0.24 §10.13 POSTCLOSE / §10.19: after the submission period
     ended, the same route carries the server's verdict (`data.decision`):
       - allowed: the Award notification status with its evidence, the verified
         grounds, the finality warning and the separate funding explanation,
         then the ordinary ground/reason decision;
       - blocked: **Cancellation cannot be decided here**, **A tender decision
         is needed** and every blocker with its holder and permitted route — no
         form, no Cancel Tender button;
       - cancelled: who decided and when, and the closing of the opening record
         as its own status, apart from notices, reports and funding. -->
<template>
	<div class="tnd-page" data-screen-label="TPR-DES-12 Cancel Tender">
		<BlueprintCard>
			<RecordHead title="Cancel Tender" :badge="cancelled ? 'Cancelled' : tender.badge" :badge-tone="cancelled ? 'is-critical' : 'is-live'" :refs="tender.tender_reference" :lede="cancelled ? '' : 'Cancel this procurement proceeding using an applicable statutory ground.'" />
			<TenderGuidance :guidance="data.guidance || null" :pending="pending" @fix="onFix" />

			<template v-if="!cancelled">
				<div v-if="postClose" class="tnd-section" data-testid="tnd-postclose" :data-allowed="decision.allowed ? 'true' : 'false'">
					<h2 class="tnd-h2" data-testid="tnd-postclose-title">{{ decision.allowed ? "Cancel this Tender" : decision.blocked_title }}</h2>
					<p v-if="decision.award" class="tnd-body-text" style="margin: 0 0 6px" data-testid="tnd-award-status">{{ decision.award.label }}</p>
					<details v-if="decision.award" class="tnd-technical" data-testid="tnd-award-evidence">
						<summary class="tnd-small">Evidence for this status</summary>
						<dl class="tnd-small"><dt class="kt-label">Source</dt><dd>{{ decision.award.source }}</dd><dt class="kt-label">Revision</dt><dd>{{ decision.award.source_revision }}</dd><dt class="kt-label">Checked</dt><dd>{{ decision.award.checked_at_label }}</dd></dl>
					</details>
					<p v-if="decision.opening && decision.opening.message" class="tnd-small" style="margin: 8px 0 0" data-testid="tnd-opening-context">{{ decision.opening.message }}<span v-if="decision.opening.item" class="tnd-muted-700"> Decision item {{ decision.opening.item }}.</span></p>
					<div v-if="!decision.allowed" style="margin-top: 12px" data-testid="tnd-blockers">
						<h3 class="tnd-h2" style="font-size: 15px" data-testid="tnd-blockers-heading">{{ decision.heading }}</h3>
						<ul class="tnd-list">
							<li v-for="b in decision.blockers" :key="b.code" data-testid="tnd-blocker" :data-code="b.code">
								<strong>{{ b.message }}</strong>
								<span class="tnd-small tnd-muted-700"> Held by {{ b.holder }}.</span>
								<a v-if="b.link" href="#" class="tnd-small" data-testid="tnd-blocker-link" @click.prevent="emit('fix', { kind: 'route', target: b.link.route })">{{ b.link.label }}</a>
							</li>
						</ul>
					</div>
				</div>
				<div v-if="deciding && !blockedPost" class="tnd-section tnd-section--plain">
					<div class="kt-notice is-critical" data-testid="tnd-cancel-warning">
						<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
						<div class="kt-notice-body">{{ postClose ? data.postclose_warning_text : (data.warning_text || "The tender will end. KenTender will restore its unused planning allowance and release its unused budget reservation after checking the linked records. A replacement purchase requires a new requisition.") }}<template v-if="postClose"><br><span data-testid="tnd-postclose-recovery">{{ data.postclose_recovery_text }}</span></template></div>
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
				<template v-if="deciding && !blockedPost">
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
							<li v-if="postClose" data-testid="tnd-postclose-consequence">The opening record ends with what was recorded so far; no bid is opened or evaluated.</li>
							<li>Cancellation notice published through all original channels.</li>
							<li>PPRA report due {{ consequences.ppra_report_due_by }}.</li>
							<li>Candidate notices due {{ consequences.candidate_notice_due_by }}.</li>
							<li>{{ consequences.replacement_text || "A replacement purchase requires a new requisition." }}</li>
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
					<div v-if="cancellation.previous_status" class="tnd-fact"><div class="kt-label">Cancelled from</div><div class="tnd-fact-value" data-testid="tnd-cancelled-from">{{ cancellation.previous_status }}</div></div>
				</div>
				<div v-if="delivery.length" class="tnd-section" data-testid="tnd-delivery">
					<h2 class="tnd-h2">Closing the opening record</h2>
					<p v-for="row in delivery" :key="row.consumer" class="tnd-body-text" style="margin: 0 0 6px" :data-testid="`tnd-delivery-${row.consumer}`" :data-status="row.status">
						<span class="kt-status" :class="row.status === 'Delivered' ? 'is-live' : 'is-attention'">{{ row.label }}: {{ row.status === "Delivered" ? "Updated" : "Being updated" }}</span>
						<span class="tnd-small tnd-muted-700" style="display: block">{{ row.status === "Delivered" ? "The opening record shows this tender was cancelled." : "Cancellation recorded. The opening record is being updated." }}</span>
					</p>
				</div>
				<div v-if="recovery" class="tnd-section" data-testid="tnd-resource-recovery" :data-status="recovery.status">
					<h2 class="tnd-h2">{{ recovery.title }}</h2>
					<p class="tnd-body-text" style="margin: 0 0 6px"><span class="kt-status" :class="recoveryTone" data-testid="tnd-resource-recovery-label">{{ recovery.label }}</span></p>
					<p class="tnd-small tnd-muted-700" style="margin: 0 0 6px" data-testid="tnd-resource-recovery-explanation">{{ recovery.explanation }}</p>
					<p v-if="recovery.reason" class="tnd-small" style="margin: 0 0 6px" data-testid="tnd-resource-recovery-reason">{{ recovery.reason }}</p>
					<table v-if="(recovery.rows || []).length" class="table" data-testid="tnd-resource-recovery-rows">
						<thead><tr><th>Source</th><th>Quantity</th><th>Value</th><th v-if="recovery.status === 'Completed'">Allowance restored</th><th v-if="recovery.status === 'Completed'">Funding released</th></tr></thead>
						<tbody>
							<tr v-for="row in recovery.rows" :key="row.key"><td>{{ row.source }}</td><td>{{ row.quantity }}</td><td>{{ row.value }}</td><td v-if="recovery.status === 'Completed'">{{ row.restored }}</td><td v-if="recovery.status === 'Completed'">{{ row.released }}</td></tr>
						</tbody>
					</table>
					<p v-if="recovery.partial_view" class="tnd-small tnd-muted-700" style="margin: 6px 0 0">Only the sources of your department are shown.</p>
					<p v-if="recovery.next_step" class="tnd-small" style="margin: 8px 0 0" data-testid="tnd-resource-recovery-next"><a v-if="recovery.next_step.route" :href="recovery.next_step.route" data-testid="tnd-resource-recovery-next-link">{{ recovery.next_step.label }}</a><span v-else>{{ recovery.next_step.label }}</span></p>
					<details v-if="(recovery.technical || []).length" class="tnd-technical" data-testid="tnd-resource-recovery-technical">
						<summary class="tnd-small">Technical details</summary>
						<dl class="tnd-small"><template v-for="item in recovery.technical" :key="item.label"><dt class="kt-label">{{ item.label }}</dt><dd>{{ item.value }}</dd></template></dl>
					</details>
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
// TPR-CHG-001 v0.24 §10.13 POSTCLOSE: the server's verdict for a Tender whose submission period has ended
const decision = computed(() => props.data.decision || null);
const postClose = computed(() => !!decision.value && decision.value.stage === "post_close");
const blockedPost = computed(() => postClose.value && !decision.value.allowed);
const delivery = computed(() => props.data.delivery || []);
// TPR-CHG-001 v0.21 §5.7A: Requisitions' recovery of the unused allowance and funding, in the server's words (permitted rows and links only)
const recovery = computed(() => props.data.resource_recovery || null);
const recoveryTone = computed(() => ({ Completed: "is-live", "Needs attention": "is-critical" }[(recovery.value || {}).status] || "is-attention"));
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
