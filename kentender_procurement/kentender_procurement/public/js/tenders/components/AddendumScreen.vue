<!-- TPR-DES-10 Prepare and issue addendum: Draft (officer edits), HOPF issue
     (read-only facts + Return / Issue), Material change blocked (the
     critical notice, no form). The affected reference is chosen from the
     server's catalogue of published rows; the current published value is
     shown, never typed. The deadline rule and materiality are the server's. -->
<template>
	<div class="tnd-page" data-screen-label="TPR-DES-10 Prepare and issue addendum">
		<BlueprintCard>
			<RecordHead :title="hopfIssue ? 'Issue addendum' : 'Prepare addendum'" :badge="badge" :badge-tone="hopfIssue ? 'is-attention' : 'is-draft'" :refs="`${data.tender.tender_reference} · Current deadline ${data.tender.current_deadline_label}`" lede="Identify the published wording that needs a non-material correction." />
			<div class="tnd-section">
				<div v-if="material" class="kt-notice is-critical" data-testid="tnd-addendum-material">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
					<div class="kt-notice-body"><strong>{{ data.material_text || "This change cannot be made by addendum." }}</strong> Cancel the Tender and start a newly governed Tender if procurement must continue. <button type="button" class="tnd-link-btn" @click="$emit('cancel-screen')">View cancellation requirements</button></div>
				</div>
				<div v-else-if="hopfIssue" class="kt-notice is-live" data-testid="tnd-addendum-ready">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 6L9 17l-5-5"/></svg>
					<div class="kt-notice-body"><strong>Ready to issue.</strong> Issue is immutable and channel confirmation follows separately.</div>
				</div>
				<div v-else-if="confirming" class="kt-notice is-attention" data-testid="tnd-addendum-confirming">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
					<div class="kt-notice-body"><strong>Issued — awaiting publication confirmation.</strong> The addendum takes effect once every original channel is confirmed.</div>
				</div>
				<div v-else-if="issued" class="kt-notice is-live" data-testid="tnd-addendum-issued">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 6L9 17l-5-5"/></svg>
					<div class="kt-notice-body"><strong>Issued and effective</strong> from {{ addendum.effective_at_label }}.</div>
				</div>
				<div v-else class="kt-notice is-attention" data-testid="tnd-addendum-draft-notice">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
					<div class="kt-notice-body"><strong>An addendum cannot expand the purchase, add a requirement or change the evaluation basis.</strong> A material change requires cancellation and a newly governed Tender.</div>
				</div>
				<div v-if="addendum.status === 'Returned' && addendum.return_reason" class="kt-notice is-attention" style="margin-top: 12px" data-testid="tnd-addendum-returned"><div class="kt-notice-body"><strong>Returned for correction.</strong> {{ addendum.return_reason }}</div></div>
			</div>

			<template v-if="!material || editable">
				<div class="tnd-section tnd-grid-2" data-testid="tnd-addendum-form">
					<div class="tnd-fact"><div class="kt-label">Change class</div>
						<select v-if="editable" class="kt-input" v-model="form.change_class" data-testid="tnd-ad-change-class"><option v-for="c in data.change_classes || []" :key="c" :value="c">{{ c }}</option></select>
						<div v-else class="tnd-fact-value">{{ addendum.change_class }}</div>
						<p v-if="errors.change_class" class="tnd-field-error">{{ errors.change_class }}</p>
					</div>
					<div class="tnd-fact"><div class="kt-label">Affected area</div>
						<select v-if="editable" class="kt-input" v-model="form.affected_area" data-testid="tnd-ad-area"><option v-for="a in data.affected_areas || []" :key="a" :value="a">{{ a }}</option></select>
						<div v-else class="tnd-fact-value">{{ addendum.affected_area }}</div>
						<p v-if="errors.affected_area" class="tnd-field-error">{{ errors.affected_area }}</p>
					</div>
					<div class="tnd-fact"><div class="kt-label">Affected reference</div>
						<select v-if="editable" class="kt-input" v-model="form.affected_reference_key" data-testid="tnd-ad-reference" @change="onReferenceChange"><option value="">Choose the published wording</option><option v-for="r in references" :key="r.key" :value="r.key">{{ r.label }}{{ r.material ? " — material" : "" }}</option></select>
						<div v-else class="tnd-fact-value">{{ addendum.affected_reference }}</div>
						<p v-if="errors.affected_reference_key" class="tnd-field-error" data-testid="tnd-ad-error-reference">{{ errors.affected_reference_key }}</p>
					</div>
					<div></div>
					<div class="tnd-fact"><div class="kt-label">Current published value</div><div class="tnd-fact-value tnd-fact-value--muted" data-testid="tnd-ad-previous">{{ previousValue || "—" }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Revised value</div>
						<textarea v-if="editable" class="kt-input" rows="2" v-model="form.revised_value" data-testid="tnd-ad-revised"></textarea>
						<div v-else class="tnd-fact-value">{{ addendum.revised_value }}</div>
						<p v-if="errors.revised_value" class="tnd-field-error" data-testid="tnd-ad-error-revised">{{ errors.revised_value }}</p>
					</div>
					<div class="tnd-fact tnd-span-2"><div class="kt-label">Reason</div>
						<textarea v-if="editable" class="kt-input" rows="2" v-model="form.reason" data-testid="tnd-ad-reason"></textarea>
						<div v-else class="tnd-fact-value">{{ addendum.reason }}</div>
						<p v-if="errors.reason" class="tnd-field-error">{{ errors.reason }}</p>
					</div>
					<div class="tnd-fact tnd-span-2"><div class="kt-label">Why this is not material</div>
						<textarea v-if="editable" class="kt-input" rows="2" v-model="form.materiality_statement" data-testid="tnd-ad-materiality"></textarea>
						<div v-else class="tnd-fact-value">{{ addendum.materiality_statement }}</div>
						<p v-if="errors.materiality_statement" class="tnd-field-error">{{ errors.materiality_statement }}</p>
					</div>
				</div>

				<div v-if="!material" class="tnd-section" data-testid="tnd-deadline-rule">
					<div class="kt-notice" :class="rule.required ? 'is-attention' : 'is-live'">
						<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
						<div class="kt-notice-body"><strong>{{ rule.required ? "Submission deadline must be extended." : "The current submission deadline is unchanged." }}</strong></div>
					</div>
					<div class="tnd-grid-2" style="margin-top: 14px">
						<div class="tnd-fact"><div class="kt-label">Current deadline</div><div class="tnd-fact-value">{{ rule.current_deadline_label || data.tender.current_deadline_label }}</div></div>
						<div class="tnd-fact"><div class="kt-label">Revised submission deadline</div>
							<input v-if="editable && (rule.required || form.change_class === 'Submission deadline extension')" type="datetime-local" class="kt-input" v-model="form.revised_submission_deadline" data-testid="tnd-ad-deadline" />
							<div v-else class="tnd-fact-value">{{ addendum.revised_submission_deadline_label || "—" }}</div>
							<p v-if="errors.revised_submission_deadline" class="tnd-field-error" data-testid="tnd-ad-error-deadline">{{ errors.revised_submission_deadline }}</p>
						</div>
					</div>
					<p class="tnd-small tnd-muted-700" style="margin: 12px 0 0">{{ rule.explanation }}</p>
				</div>

				<div v-if="!material" class="tnd-section tnd-section--last">
					<div class="kt-card-title" style="margin-bottom: 12px">Publication</div>
					<table class="kt-table" data-testid="tnd-addendum-channels">
						<thead><tr><th>Channel</th><th v-if="channels.length">Result</th><th v-if="channels.length">Available at</th><th v-if="channels.length">Confirmation / action</th></tr></thead>
						<tbody>
							<tr v-for="c in channels.length ? channels : originalChannels" :key="c.channel" :data-testid="`tnd-ad-channel-${c.channel}`" :data-status="c.status || ''">
								<td>{{ c.channel_label || c.label }}</td>
								<template v-if="channels.length">
									<td><span class="kt-status" :class="c.status === 'Confirmed' ? 'is-live' : 'is-attention'">{{ c.result_label }}</span></td>
									<td>{{ c.available_at_label || "—" }}</td>
									<td>
										<button v-if="c.status === 'Confirmed'" type="button" class="tnd-link-btn" @click="$emit('view-confirmation', c)">View confirmation</button>
										<button v-else-if="canConfirm" type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tnd-ad-confirm-channel" @click="$emit('confirm-channel', c)">Confirm publication</button>
										<span v-else class="tnd-status-text">Awaiting the Head of Procurement Function</span>
									</td>
								</template>
							</tr>
						</tbody>
					</table>
				</div>
			</template>
		</BlueprintCard>
		<div class="tnd-footer">
			<a href="#" class="tnd-footer-back" data-testid="tnd-back" @click.prevent="$emit('back')">Back</a>
			<div class="tnd-actions">
				<template v-if="editable">
					<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tnd-ad-save" @click="$emit('save', payload())">Save draft</button>
					<button type="button" class="kt-btn kt-btn-primary" :disabled="pending || material" data-testid="tnd-ad-submit" @click="$emit('submit', payload())">Submit for issue</button>
				</template>
				<template v-else-if="hopfIssue">
					<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tnd-ad-return" @click="$emit('return')">Return for correction</button>
					<button type="button" class="kt-btn kt-btn-primary" :disabled="pending || material" data-testid="tnd-ad-issue" @click="$emit('issue')">Issue addendum</button>
				</template>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import BlueprintCard from "./BlueprintCard.vue";
import RecordHead from "./RecordHead.vue";
import { fromInputDateTime, toInputDateTime } from "../data/format.js";

const props = defineProps({
	data: { type: Object, default: () => ({ tender: {} }) },
	identity: { type: String, default: "" },
	errors: { type: Object, default: () => ({}) },
	pending: Boolean,
});
defineEmits(["back", "save", "submit", "return", "issue", "confirm-channel", "view-confirmation", "cancel-screen"]);

const addendum = computed(() => props.data.addendum || {});
const references = computed(() => props.data.references || []);
const rule = computed(() => props.data.deadline_rule || {});
const channels = computed(() => props.data.channels || []);
const originalChannels = computed(() => props.data.original_channels || []);
const editable = computed(() => !!props.data.editable);
const actions = computed(() => props.data.allowed_actions || []);
const hopfIssue = computed(() => addendum.value.status === "Awaiting issue" && actions.value.includes("issue_addendum"));
const confirming = computed(() => addendum.value.status === "Awaiting publication confirmation");
const issued = computed(() => addendum.value.status === "Issued");
const canConfirm = computed(() => actions.value.includes("confirm_addendum_channel"));
const form = reactive({ change_class: "", affected_area: "", affected_reference_key: "", revised_value: "", reason: "", materiality_statement: "", revised_submission_deadline: "" });
const selectedReference = computed(() => references.value.find((r) => r.key === (editable.value ? form.affected_reference_key : addendum.value.affected_reference_key)) || null);
const material = computed(() => !!(props.data.material || (selectedReference.value && selectedReference.value.material)));
const previousValue = computed(() => (editable.value ? (selectedReference.value || {}).value : addendum.value.previous_value));
const badge = computed(() => (material.value ? "Material change" : hopfIssue.value ? "Ready to issue" : confirming.value ? "Awaiting publication confirmation" : issued.value ? "Issued" : addendum.value.status === "Awaiting issue" ? "Submitted for issue" : "Draft addendum"));

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
