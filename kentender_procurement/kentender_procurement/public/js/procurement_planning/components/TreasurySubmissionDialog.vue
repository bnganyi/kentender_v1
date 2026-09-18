<!-- PLN-CHG-001 v1.23 §10.12 — Treasury submission evidence
     (U13-TREASURY-FORM / U13-CORRECT-EVIDENCE), ported from U13.dc.html.

     This records something that happened outside the system: a document was
     sent to the National Treasury. So the Accounting Officer is asked to
     confirm, in as many words, that the plan approved here is the document
     that was sent. Until they do, there is nothing to record, and the control
     says why rather than sitting there inert.

     A correction never overwrites. The previously recorded evidence stays
     visible above the new values, and a reason is required, because the
     record of what was sent to the Treasury is itself evidence. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="pub-treasury-dialog">
		<div class="kt-dialog pln-treasury-dialog" role="dialog" aria-modal="true" aria-labelledby="pub-treasury-title">
			<div id="pub-treasury-title" class="kt-dialog-title" data-testid="pub-treasury-title">
				{{ isCorrection ? "Correct submission details" : "Record Treasury submission" }}
			</div>

			<div class="kt-meta-row" data-testid="pub-treasury-plan">
				<div>
					<span class="kt-label">Plan</span>
					<span class="kt-meta-value">{{ task.plan_title }}</span>
				</div>
				<div>
					<span class="kt-label">Reference</span>
					<span class="kt-meta-value">{{ task.plan_reference }}</span>
				</div>
				<div>
					<span class="kt-label">Version</span>
					<span class="kt-meta-value">{{ task.version?.number }}</span>
				</div>
			</div>

			<!-- U13-CORRECT-EVIDENCE — what is on record now, in full, above
			     the values being offered in its place. -->
			<template v-if="isCorrection">
				<h6 class="kt-card-title">Previous submission evidence</h6>
				<div class="kt-meta-row" data-testid="pub-treasury-prior">
					<div>
						<span class="kt-label">Date and time sent</span>
						<span class="kt-meta-value">{{ prior.submitted_display }}</span>
					</div>
					<div>
						<span class="kt-label">Submission channel</span>
						<span class="kt-meta-value">{{ prior.channel }}</span>
					</div>
					<div>
						<span class="kt-label">Destination</span>
						<span class="kt-meta-value">{{ prior.destination }}</span>
					</div>
					<div>
						<span class="kt-label">Dispatch reference</span>
						<span class="kt-meta-value">{{ prior.dispatch_reference }}</span>
					</div>
				</div>
			</template>

			<div class="kt-field">
				<label for="pub-treasury-sent" class="kt-label">Date and time sent</label>
				<input id="pub-treasury-sent" class="kt-input" type="datetime-local" data-testid="pub-treasury-sent" v-model="form.submitted_at">
			</div>
			<div class="kt-field">
				<label for="pub-treasury-channel" class="kt-label">Submission channel</label>
				<input id="pub-treasury-channel" class="kt-input" data-testid="pub-treasury-channel" v-model="form.channel">
			</div>
			<div class="kt-field">
				<label for="pub-treasury-destination" class="kt-label">Destination</label>
				<input id="pub-treasury-destination" class="kt-input" data-testid="pub-treasury-destination" v-model="form.destination">
			</div>
			<div class="kt-field">
				<label for="pub-treasury-dispatch" class="kt-label">Dispatch/reference number</label>
				<input id="pub-treasury-dispatch" class="kt-input" data-testid="pub-treasury-dispatch" v-model="form.dispatch_reference">
			</div>

			<div v-if="isCorrection" class="kt-field">
				<label for="pub-treasury-reason" class="kt-label">Reason for correction</label>
				<textarea id="pub-treasury-reason" class="kt-input" rows="3" data-testid="pub-treasury-reason" v-model="form.reason"></textarea>
			</div>

			<!-- Not a formality: the whole record rests on this being the same
			     document. It starts unchecked every time. -->
			<label v-else class="kt-checkbox pln-treasury-confirm">
				<input type="checkbox" data-testid="pub-treasury-confirm" v-model="form.exact_document_confirmed">
				<span class="box"></span>I confirm that this approved plan is the document submitted
			</label>

			<p v-if="error" class="pln-dialog-error" role="alert" data-testid="pub-treasury-error">{{ error }}</p>

			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">Cancel</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="pub-treasury-submit"
					:disabled="pending || !ready"
					@click="$emit('confirm', { ...form })"
				>
					{{ isCorrection ? "Save corrected details" : "Record submission" }}
				</button>
			</div>
			<!-- Says what is missing, rather than leaving a dead button. -->
			<p v-if="!ready" class="kt-muted" data-testid="pub-treasury-hint">{{ hint }}</p>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive } from "vue";

const props = defineProps({
	task: { type: Object, default: () => ({}) },
	pending: Boolean,
	error: String,
});

defineEmits(["confirm", "cancel"]);

const prior = computed(() => props.task.treasury_prior || {});
const isCorrection = computed(() => Boolean(props.task.treasury_prior));

const form = reactive({
	submitted_at: prior.value.submitted_at ? String(prior.value.submitted_at).slice(0, 16).replace(" ", "T") : "",
	channel: prior.value.channel || "",
	destination: prior.value.destination || "National Treasury",
	dispatch_reference: prior.value.dispatch_reference || "",
	reason: "",
	exact_document_confirmed: false,
});

const fieldsPresent = computed(() =>
	Boolean(form.submitted_at && form.channel.trim() && form.destination.trim() && form.dispatch_reference.trim()),
);

const ready = computed(() =>
	isCorrection.value
		? fieldsPresent.value && form.reason.trim().length >= 10
		: fieldsPresent.value && form.exact_document_confirmed,
);

const hint = computed(() => {
	if (!fieldsPresent.value) return "Enter the date sent, channel, destination and dispatch reference.";
	if (isCorrection.value) return "State why the recorded details are being corrected.";
	return "Confirm the document match to record this submission.";
});
</script>
