<!-- TPR-DES-10 Prepare and issue addendum (§10.11), ported class-for-class
     across the board's seven variants. The §10.17 guidance region replaces
     every result panel (Ready to issue, awaiting confirmation, Addendum
     issued, the material-change warning); the screen shows:
       - Draft: the scope warning, the form (the affected reference chosen
         from the server's catalogue of published rows, the current value
         shown, never typed), the deadline consequence and the four original
         channels;
       - Awaiting issue (HOPF): the changed-fields comparison, the deadline
         consequence read-only and the channels;
       - Awaiting publication confirmation / Issued: the comparison, the
         issue facts and the confirmation table;
       - Material proposal (and while or after the Accounting Officer's
         cancellation review): the comparison only; the fixes are the
         guidance's, and View cancellation requirements is a page link.
     Materiality, the deadline rule and every permitted action are the
     server's. -->
<template>
	<div class="tnd-page" data-screen-label="TPR-DES-10 Prepare and issue addendum">
		<BlueprintCard>
			<RecordHead title="Prepare addendum" :badge="badge" :badge-tone="badgeTone" :refs="refLine" lede="Identify the published wording that needs a non-material correction." />
			<TenderGuidance :guidance="data.guidance || null" :pending="pending" @fix="$emit('fix', $event)" />

			<template v-if="editable">
				<div class="tnd-section tnd-section--plain">
					<div class="kt-notice is-warning" data-testid="tnd-addendum-scope">
						<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
						<div class="kt-notice-body">An addendum cannot expand the purchase, add a requirement or change the evaluation basis. A material change requires cancellation and a newly governed Tender.</div>
					</div>
				</div>
				<div class="tnd-section tnd-section--form" data-testid="tnd-addendum-form">
					<div class="tnd-grid-3 tnd-form-row">
						<div class="kt-field" style="margin: 0"><label for="tnd-ad-change-class">Change class</label>
							<select id="tnd-ad-change-class" class="kt-input" v-model="form.change_class" data-testid="tnd-ad-change-class"><option v-for="c in data.change_classes || []" :key="c" :value="c">{{ c }}</option></select>
							<p v-if="errors.change_class" class="tnd-field-error">{{ errors.change_class }}</p>
						</div>
						<div class="kt-field" style="margin: 0"><label for="tnd-ad-area">Affected area</label>
							<select id="tnd-ad-area" class="kt-input" v-model="form.affected_area" data-testid="tnd-ad-area"><option v-for="a in data.affected_areas || []" :key="a" :value="a">{{ a }}</option></select>
							<p v-if="errors.affected_area" class="tnd-field-error">{{ errors.affected_area }}</p>
						</div>
						<div class="kt-field" style="margin: 0"><label for="tnd-ad-reference">Affected reference</label>
							<select id="tnd-ad-reference" class="kt-input" v-model="form.affected_reference_key" data-testid="tnd-ad-reference" @change="onReferenceChange"><option value="">Choose the published wording</option><option v-for="r in references" :key="r.key" :value="r.key">{{ r.label }}</option></select>
							<p v-if="errors.affected_reference_key" class="tnd-field-error" data-testid="tnd-ad-error-reference">{{ errors.affected_reference_key }}</p>
						</div>
					</div>
					<div class="tnd-fact tnd-form-row"><div class="kt-label">Current published value</div><div class="tnd-fact-value" data-testid="tnd-ad-previous">{{ previousValue || "—" }}</div></div>
					<div class="kt-field tnd-form-row"><label for="tnd-ad-revised">Revised value</label>
						<textarea id="tnd-ad-revised" class="kt-input" rows="2" v-model="form.revised_value" data-testid="tnd-ad-revised"></textarea>
						<p v-if="errors.revised_value" class="tnd-field-error" data-testid="tnd-ad-error-revised">{{ errors.revised_value }}</p>
					</div>
					<div class="kt-field tnd-form-row"><label for="tnd-ad-reason">Reason</label>
						<textarea id="tnd-ad-reason" class="kt-input" rows="2" v-model="form.reason" data-testid="tnd-ad-reason"></textarea>
						<p v-if="errors.reason" class="tnd-field-error">{{ errors.reason }}</p>
					</div>
					<div class="kt-field" style="margin: 0"><label for="tnd-ad-materiality">Why this is not material</label>
						<textarea id="tnd-ad-materiality" class="kt-input" rows="2" v-model="form.materiality_statement" data-testid="tnd-ad-materiality"></textarea>
						<p v-if="errors.materiality_statement" class="tnd-field-error">{{ errors.materiality_statement }}</p>
					</div>
				</div>
			</template>

			<div v-else class="tnd-section" data-testid="tnd-addendum-comparison">
				<h2 class="tnd-h2">Changed fields</h2>
				<table class="kt-table">
					<thead><tr><th>Field</th><th>Current published</th><th>Revised</th></tr></thead>
					<tbody><tr><td>{{ addendum.affected_reference }}</td><td>{{ addendum.previous_value }}</td><td>{{ addendum.revised_value }}</td></tr></tbody>
				</table>
				<div class="tnd-fact-grid tnd-fact-grid--2 tnd-gap-top">
					<div class="tnd-fact"><div class="kt-label">Change class</div><div class="tnd-fact-value">{{ material ? "Proposed change" : addendum.change_class }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Reason</div><div class="tnd-fact-value">{{ addendum.reason }}</div></div>
					<div v-if="addendum.cancellation_review_status === 'Closed'" class="tnd-fact tnd-span-4" data-testid="tnd-review-closed-reason"><div class="kt-label">Cancellation review closed</div><div class="tnd-fact-value">{{ addendum.cancellation_review_closed_reason }}</div></div>
				</div>
			</div>

			<div v-if="!material && (editable || awaitingIssue)" class="tnd-section" data-testid="tnd-deadline-rule">
				<h2 class="tnd-h2">{{ rule.required ? "Submission deadline must be extended" : "The submission deadline is unchanged" }}</h2>
				<p v-if="rule.explanation" class="tnd-small tnd-muted-700 tnd-h2-lede">{{ rule.explanation }}</p>
				<div class="tnd-grid-2 tnd-grid-start">
					<div class="tnd-fact"><div class="kt-label">Current deadline</div><div class="tnd-fact-value">{{ rule.current_deadline_label || data.tender.current_deadline_label }}</div></div>
					<div v-if="editable && (rule.required || form.change_class === 'Submission deadline extension')" class="kt-field" style="margin: 0"><label for="tnd-ad-deadline">Revised submission deadline</label>
						<input id="tnd-ad-deadline" type="datetime-local" class="kt-input" v-model="form.revised_submission_deadline" data-testid="tnd-ad-deadline" />
						<p v-if="errors.revised_submission_deadline" class="tnd-field-error" data-testid="tnd-ad-error-deadline">{{ errors.revised_submission_deadline }}</p>
					</div>
					<div v-else-if="addendum.revised_submission_deadline_label" class="tnd-fact"><div class="kt-label">Revised submission deadline</div><div class="tnd-fact-value">{{ addendum.revised_submission_deadline_label }}</div></div>
				</div>
			</div>

			<div v-if="confirming || issued" class="tnd-section tnd-fact-grid tnd-fact-grid--3" data-testid="tnd-addendum-facts">
				<template v-if="confirming">
					<div class="tnd-fact"><div class="kt-label">Issue decided by</div><div class="tnd-fact-value">{{ addendum.issue_decided_by_name }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Issue decided at</div><div class="tnd-fact-value">{{ addendum.issue_decided_at_label }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Successor submission deadline</div><div class="tnd-fact-value">{{ addendum.revised_submission_deadline_label || data.tender.current_deadline_label }}</div></div>
				</template>
				<template v-else>
					<div class="tnd-fact"><div class="kt-label">Effective</div><div class="tnd-fact-value">{{ addendum.issued_at_label }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Confirmation completed</div><div class="tnd-fact-value">{{ addendum.confirmation_completed_at_label }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Revised submission deadline</div><div class="tnd-fact-value">{{ addendum.revised_submission_deadline_label || data.tender.current_deadline_label }}</div></div>
				</template>
			</div>

			<div v-if="!material && (editable || awaitingIssue)" class="tnd-section tnd-section--last" data-testid="tnd-addendum-channels-plain">
				<h2 class="tnd-h2">Publication</h2>
				<p class="tnd-small tnd-muted-700 tnd-h2-lede">The addendum is published through the {{ originalChannels.length === 4 ? "four" : originalChannels.length }} original channels.</p>
				<table class="kt-table" data-testid="tnd-addendum-channels">
					<thead><tr><th>Channel</th></tr></thead>
					<tbody><tr v-for="c in originalChannels" :key="c.channel"><td>{{ c.label }}</td></tr></tbody>
				</table>
			</div>

			<div v-if="confirming || issued" class="tnd-section tnd-section--last">
				<h2 class="tnd-h2">Publication channels</h2>
				<table class="kt-table" data-testid="tnd-addendum-channels">
					<thead><tr><th>Channel</th><th>Result</th><th>Available at</th><th>Confirmation/action</th></tr></thead>
					<tbody>
						<tr v-for="c in channels" :key="c.channel" :data-testid="`tnd-ad-channel-${c.channel}`" :data-status="c.status">
							<td>{{ c.channel_label }}</td>
							<td><span class="kt-status" :class="c.status === 'Confirmed' ? 'is-live' : 'is-attention'">{{ c.result_label }}</span></td>
							<td>{{ c.available_at_label || "—" }}</td>
							<td>
								<button v-if="c.status === 'Confirmed'" type="button" class="tnd-link-btn" data-testid="tnd-ad-view-confirmation" @click="$emit('view-confirmation', c)">View confirmation</button>
								<button v-else-if="canConfirm" type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tnd-ad-confirm-channel" @click="$emit('confirm-channel', c)">Confirm publication</button>
								<span v-else class="tnd-status-text">Awaiting the Head of Procurement Function</span>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</BlueprintCard>
		<div class="tnd-footer">
			<div class="tnd-actions" style="align-items: center">
				<a href="#" class="tnd-footer-back" data-testid="tnd-back" @click.prevent="$emit('back')">Back</a>
				<a v-if="actions.includes('view_cancellation_requirements')" href="#" class="tnd-footer-back" data-testid="tnd-view-cancellation-requirements" @click.prevent="$emit('cancel-screen')">View cancellation requirements</a>
			</div>
			<div class="tnd-actions">
				<template v-if="editable">
					<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tnd-ad-save" @click="$emit('save', payload())">Save draft</button>
					<button v-if="actions.includes('submit_addendum_for_issue')" type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="tnd-ad-submit" @click="$emit('submit', payload())">Submit for issue</button>
				</template>
				<!-- the Accounting Officer's open cancellation review (§10.17 DES-12
				     request row): close it here, or decide on the Cancel Tender screen -->
				<template v-else-if="actions.includes('close_cancellation_review')">
					<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tnd-ad-close-review" @click="$emit('fix', { fix_id: 'close_cancellation_review', target: { addendum: addendum.name } })">Close cancellation review</button>
					<button type="button" class="kt-btn tnd-btn-danger" :disabled="pending" data-testid="tnd-ad-cancel-tender" @click="$emit('cancel-screen')">Cancel Tender</button>
				</template>
				<template v-else-if="actions.includes('issue_addendum')">
					<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tnd-ad-return" @click="$emit('return')">Return for correction</button>
					<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="tnd-ad-issue" @click="$emit('issue')">Issue addendum</button>
				</template>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import BlueprintCard from "./BlueprintCard.vue";
import RecordHead from "./RecordHead.vue";
import TenderGuidance from "./TenderGuidance.vue";
import { fromInputDateTime, toInputDateTime } from "../data/format.js";

const props = defineProps({
	data: { type: Object, default: () => ({ tender: {} }) },
	identity: { type: String, default: "" },
	errors: { type: Object, default: () => ({}) },
	pending: Boolean,
});
defineEmits(["back", "save", "submit", "return", "issue", "confirm-channel", "view-confirmation", "cancel-screen", "fix"]);

const addendum = computed(() => props.data.addendum || {});
const references = computed(() => props.data.references || []);
const rule = computed(() => props.data.deadline_rule || {});
const channels = computed(() => props.data.channels || []);
const originalChannels = computed(() => props.data.original_channels || []);
const actions = computed(() => props.data.allowed_actions || []);
// the saved proposal's materiality is the server's; a material proposal is
// shown as its comparison, never as an editable form (§10.11)
const material = computed(() => !!props.data.material);
const editable = computed(() => !!props.data.editable && !material.value);
const awaitingIssue = computed(() => addendum.value.status === "Awaiting issue");
const confirming = computed(() => addendum.value.status === "Awaiting publication confirmation");
const issued = computed(() => addendum.value.status === "Issued");
const canConfirm = computed(() => actions.value.includes("confirm_addendum_channel"));
const form = reactive({ change_class: "", affected_area: "", affected_reference_key: "", revised_value: "", reason: "", materiality_statement: "", revised_submission_deadline: "" });
const selectedReference = computed(() => references.value.find((r) => r.key === form.affected_reference_key) || null);
const previousValue = computed(() => (selectedReference.value || {}).value || addendum.value.previous_value);
const badge = computed(() => ({ "Awaiting issue": "Awaiting issue", "Awaiting publication confirmation": "Awaiting publication confirmation", Issued: "Issued" })[addendum.value.status] || "Draft addendum");
const badgeTone = computed(() => (issued.value ? "is-live" : awaitingIssue.value || confirming.value ? "is-attention" : "is-draft"));
const refLine = computed(() => [props.data.tender.tender_reference, addendum.value.addendum_reference, props.data.tender.current_deadline_label ? `Current deadline ${props.data.tender.current_deadline_label}` : ""].filter(Boolean).join(" · "));

let hydrated = "";
watch(
	() => props.identity,
	(id) => {
		if (id === hydrated) return;
		hydrated = id;
		const a = addendum.value;
		form.change_class = a.change_class || (props.data.change_classes || [])[0] || "";
		form.affected_area = a.affected_area || (props.data.affected_areas || [])[0] || "";
		form.affected_reference_key = a.affected_reference_key || "";
		form.revised_value = a.revised_value || "";
		form.reason = a.reason || "";
		form.materiality_statement = a.materiality_statement || "";
		form.revised_submission_deadline = toInputDateTime(a.revised_submission_deadline);
	},
	{ immediate: true }
);
function onReferenceChange() {
	const r = selectedReference.value;
	if (r && r.area) form.affected_area = r.area;
}
function payload() {
	const out = { change_class: form.change_class, affected_area: form.affected_area, affected_reference_key: form.affected_reference_key, revised_value: form.revised_value.trim(), reason: form.reason.trim(), materiality_statement: form.materiality_statement.trim() };
	if (form.revised_submission_deadline) out.revised_submission_deadline = fromInputDateTime(form.revised_submission_deadline);
	return out;
}
</script>
