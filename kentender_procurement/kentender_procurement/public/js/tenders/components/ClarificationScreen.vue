<!-- TPR-DES-11 Respond to supplier clarification (§10.12), ported
     class-for-class: the header (Tender reference and clarification
     deadline), the §10.17 guidance region, the candidate facts with the
     registration caveat, the question, and either the response form — the
     Yes/No "Would this response change the published Tender?" and, for No,
     who receives the answer — or, once answered, the recorded answer and the
     candidate-notice delivery table (the protected recipient only for the
     roles the server shows it to). Which guidance is shown for an unsaved Yes
     is the server's own alternative answer; nothing here composes it. -->
<template>
	<div class="tnd-page" data-screen-label="TPR-DES-11 Respond to supplier clarification">
		<BlueprintCard>
			<RecordHead title="Respond to supplier clarification" :badge="answered ? 'Answered' : ''" badge-tone="is-live" :refs="refs" lede="Answer the question and state whether the response changes the published Tender." />
			<TenderGuidance :guidance="shownGuidance" :pending="pending" @fix="$emit('fix', $event)" />
			<div class="tnd-section">
				<div class="tnd-fact-grid tnd-fact-grid--3">
					<div class="tnd-fact"><div class="kt-label">Candidate</div><div class="tnd-fact-value" data-testid="tnd-clarification-candidate">{{ clarification.candidate_label }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Received</div><div class="tnd-fact-value">{{ clarification.received_at_label }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Related addendum</div><div class="tnd-fact-value">{{ clarification.related_addendum_reference || "None" }}</div></div>
				</div>
				<p class="tnd-small tnd-muted-700 tnd-caveat">Registration confirms only that the candidate is registered for this Tender. It does not confirm supplier qualification or eligibility.</p>
				<div class="tnd-fact"><div class="kt-label">Question</div><p class="tnd-body-text" data-testid="tnd-clarification-question">{{ clarification.question }}</p></div>
			</div>
			<div v-if="editable" class="tnd-section tnd-section--form">
				<div class="field"><label for="tnd-clar-response">Response</label>
					<textarea id="tnd-clar-response" class="input" rows="3" maxlength="2000" v-model="form.response" :readonly="awaitingAddendum" data-testid="tnd-clar-response"></textarea>
					<p v-if="errors.response" class="tnd-field-error" data-testid="tnd-clar-error-response">{{ errors.response }}</p>
				</div>
				<div class="field"><label id="tnd-clar-changes-label">Would this response change the published Tender?</label>
					<div class="seg" role="radiogroup" aria-labelledby="tnd-clar-changes-label">
						<label class="seg-opt"><input type="radio" name="tnd-clar-changes" :checked="!form.changes" :disabled="awaitingAddendum" data-testid="tnd-clar-changes-no" @change="form.changes = false" />No</label>
						<label class="seg-opt"><input type="radio" name="tnd-clar-changes" :checked="form.changes" :disabled="awaitingAddendum" data-testid="tnd-clar-changes-yes" @change="form.changes = true" />Yes</label>
					</div>
				</div>
				<div v-if="!form.changes" class="field" data-testid="tnd-clar-audience"><label id="tnd-clar-audience-label">Who should receive this answer?</label>
					<div class="tnd-radio-list" role="radiogroup" aria-labelledby="tnd-clar-audience-label">
						<label v-for="a in data.audiences || []" :key="a.value" class="tnd-radio"><input type="radio" name="tnd-clar-audience" :value="a.value" v-model="form.audience" :data-testid="`tnd-clar-audience-${a.value === 'Asker only' ? 'asker' : 'all'}`" /><span class="dot"></span>{{ a.label }}</label>
					</div>
					<div class="kt-label tnd-hint-label">A general answer will not identify who asked.</div>
					<p v-if="errors.response_audience" class="tnd-field-error">{{ errors.response_audience }}</p>
				</div>
				<div v-if="awaitingAddendum && clarification.required_addendum_reference" class="tnd-fact" data-testid="tnd-clar-required-addendum"><div class="kt-label">Required addendum</div><div class="tnd-fact-value">{{ clarification.required_addendum_reference }}</div></div>
				<p v-if="error" class="tnd-field-error" role="alert" data-testid="tnd-clar-error">{{ error }}</p>
			</div>
			<template v-else-if="answered">
				<div class="tnd-section">
					<div class="tnd-fact"><div class="kt-label">Response</div><p class="tnd-body-text" data-testid="tnd-clar-recorded-response">{{ clarification.response }}</p></div>
					<div class="tnd-fact-grid tnd-fact-grid--3 tnd-gap-top">
						<div class="tnd-fact"><div class="kt-label">Audience</div><div class="tnd-fact-value">{{ clarification.response_audience }}</div></div>
						<div class="tnd-fact"><div class="kt-label">Answered by</div><div class="tnd-fact-value">{{ clarification.responded_by_name }}, {{ clarification.responded_at_label }}</div></div>
						<div class="tnd-fact"><div class="kt-label">Changes published Tender</div><div class="tnd-fact-value">{{ clarification.affects_published_tender ? "Yes" : "No" }}</div></div>
					</div>
				</div>
				<div class="tnd-section tnd-section--last">
					<h2 class="tnd-h2">Candidate notice delivery</h2>
					<table class="table" data-testid="tnd-clar-notices">
						<thead><tr><th>Candidate</th><th>Destination</th><th class="is-num">Attempts</th><th>Result</th></tr></thead>
						<tbody>
							<tr v-for="n in data.notices || []" :key="n.name" :data-status="n.status">
								<td>{{ n.candidate_registration_id || "Registered Tender candidate" }}</td>
								<td>{{ n.destination_snapshot || "Protected" }}</td>
								<td class="is-num">{{ n.attempt_count }}</td>
								<td><span class="kt-status" :class="noticeTone(n.status)">{{ n.status }}</span></td>
							</tr>
						</tbody>
					</table>
				</div>
			</template>
		</BlueprintCard>
		<div class="tnd-footer">
			<a href="#" class="tnd-footer-back" data-testid="tnd-back" @click.prevent="$emit('back')">Back to Tender</a>
			<div v-if="editable && canSend && (!form.changes || addendumEffective)" class="tnd-actions">
				<button type="button" class="btn btn-secondary" :disabled="pending" data-testid="tnd-clar-cancel" @click="$emit('back')">Cancel</button>
				<button type="button" class="btn btn-primary" :disabled="pending" data-testid="tnd-clar-send" @click="send">{{ addendumEffective ? "Send response to all registered candidates" : "Send response" }}</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import BlueprintCard from "./BlueprintCard.vue";
import RecordHead from "./RecordHead.vue";
import TenderGuidance from "./TenderGuidance.vue";

const props = defineProps({
	data: { type: Object, default: () => ({ tender: {}, clarification: {} }) },
	errors: { type: Object, default: () => ({}) },
	error: { type: String, default: "" },
	pending: Boolean,
});
const emit = defineEmits(["back", "send", "fix", "changes"]);

const clarification = computed(() => props.data.clarification || {});
const tender = computed(() => props.data.tender || {});
const refs = computed(() => [tender.value.tender_reference, tender.value.clarification_deadline_label ? `Clarification deadline ${tender.value.clarification_deadline_label}` : ""].filter(Boolean).join(" · "));
const answered = computed(() => clarification.value.status === "Answered");
const awaitingAddendum = computed(() => clarification.value.status === "Awaiting addendum");
// the holder's form: while the answer waits for its addendum it stays on
// screen, kept and read-only, until the addendum is effective
const editable = computed(() => ["Awaiting response", "Awaiting addendum"].includes(clarification.value.status) && ["send_response", "prepare_addendum"].some((a) => (props.data.allowed_actions || []).includes(a)));
const canSend = computed(() => (props.data.allowed_actions || []).includes("send_response"));
const addendumEffective = computed(() => awaitingAddendum.value && !!props.data.required_addendum_effective);

const form = reactive({ response: "", changes: false, audience: "All registered candidates" });
let hydrated = "";
watch(
	() => `${clarification.value.name}:${clarification.value.record_version}`,
	(identity) => {
		if (identity === hydrated) return;
		hydrated = identity;
		form.response = clarification.value.response || "";
		form.changes = !!clarification.value.affects_published_tender || awaitingAddendum.value;
		form.audience = clarification.value.response_audience || "All registered candidates";
	},
	{ immediate: true },
);
watch(() => form.changes, (value) => emit("changes", value));

// The server answers both ways for an unanswered question: the read's own
// guidance for "No", and its published-change answer for an unsaved "Yes".
const shownGuidance = computed(() => (form.changes && !awaitingAddendum.value && props.data.guidance_if_published_change) || props.data.guidance || null);

function send() {
	emit("send", { response: form.response, affects_published_tender: form.changes, response_audience: form.changes ? "All registered candidates" : form.audience, required_addendum: clarification.value.required_addendum || "" });
}
function noticeTone(status) {
	return status === "Delivered" ? "is-live" : status === "Failed" ? "is-critical" : "is-pending";
}
defineExpose({ form });
</script>
