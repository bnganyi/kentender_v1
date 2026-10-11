<!-- Record receipt — the blind tender-security intake (owner decisions
     OD-G/OD-H; the explicit Tender-scoped duty, 10 Oct 2026). The recorder
     enters a Tender reference they are assigned and the instrument's own
     details, for a physical original or an issuer's confirmation. Looking up the reference shows only the
     published Tender's own security facts (permitted forms, amount,
     currency, deadline); nothing about any bid. Invalid input keeps what was
     entered and names each field (AGENTS.md §6.10). One request key per
     opened dialog, so a retried click cannot record twice. -->
<template>
	<div class="dialog-backdrop" data-testid="tsr-dialog" @keydown.esc.stop="$emit('cancel')">
		<div class="dialog tsr-dialog" role="dialog" aria-modal="true" aria-labelledby="tsr-d-title" tabindex="-1">
			<div>
				<div id="tsr-d-title" class="dialog-title">{{ correcting ? `Correct receipt ${correcting.intake_reference}` : "Record receipt" }}</div>
				<div class="tsr-dialog-sub">{{ correcting ? "Record the corrected details. The first receipt stays in the record, marked Corrected." : "Record a tender-security instrument received by the procuring entity: a physical original, or an electronic confirmation from the issuer." }}</div>
			</div>

			<div class="field" role="radiogroup" aria-labelledby="tsr-d-kind-label" data-testid="tsr-d-kind">
				<span id="tsr-d-kind-label" class="kt-label">What was received</span>
				<label v-for="kind in kinds" :key="kind" class="tsr-check">
					<input v-model="form.intake_kind" type="radio" name="tsr-kind" :value="kind" :data-testid="kind === 'Issuer confirmation' ? 'tsr-d-kind-issuer' : 'tsr-d-kind-physical'" />
					<span>{{ kind }}</span>
				</label>
				<p v-if="errors.intake_kind" class="kt-field-error">{{ errors.intake_kind }}</p>
			</div>

			<div class="field">
				<label for="tsr-d-tender">Tender reference</label>
				<input id="tsr-d-tender" ref="firstEl" v-model="form.tender_reference" class="input" maxlength="40" autocomplete="off" list="tsr-d-tenders" :aria-invalid="!!errors.tender_reference" data-testid="tsr-d-tender" @change="lookUp" />
				<datalist id="tsr-d-tenders"><option v-for="t in tenders" :key="t.tender_reference" :value="t.tender_reference">{{ t.title }}</option></datalist>
				<p v-if="errors.tender_reference" class="kt-field-error">{{ errors.tender_reference }}</p>
				<p v-else-if="lookup.text" class="tsr-help" data-testid="tsr-d-requirement">{{ lookup.text }}</p>
				<p v-else-if="lookup.required" class="tsr-help" data-testid="tsr-d-requirement">Required: {{ lookup.required_amount }} as {{ lookup.permitted_forms.join(" or ") }}. Submission deadline {{ lookup.deadline }}.</p>
			</div>

			<div class="field">
				<label for="tsr-d-type">Instrument type</label>
				<select id="tsr-d-type" v-model="form.instrument_type" class="input" :aria-invalid="!!errors.instrument_type" data-testid="tsr-d-type">
					<option value="" disabled>Choose the instrument type</option>
					<option v-for="form_name in forms" :key="form_name" :value="form_name">{{ form_name }}</option>
				</select>
				<p v-if="errors.instrument_type" class="kt-field-error">{{ errors.instrument_type }}</p>
			</div>

			<div class="field">
				<label for="tsr-d-issuer">Issuing bank or insurer</label>
				<input id="tsr-d-issuer" v-model="form.issuer" class="input" maxlength="160" :aria-invalid="!!errors.issuer" data-testid="tsr-d-issuer" />
				<p v-if="errors.issuer" class="kt-field-error">{{ errors.issuer }}</p>
			</div>

			<div class="field">
				<label for="tsr-d-ref">Instrument reference</label>
				<input id="tsr-d-ref" v-model="form.instrument_reference" class="input" maxlength="80" :aria-invalid="!!errors.instrument_reference" data-testid="tsr-d-reference" />
				<p v-if="errors.instrument_reference" class="kt-field-error">{{ errors.instrument_reference }}</p>
			</div>

			<div class="tsr-dialog-row">
				<div class="field">
					<label for="tsr-d-amount">Amount on the instrument</label>
					<input id="tsr-d-amount" v-model="form.amount" class="input" inputmode="decimal" :aria-invalid="!!errors.amount" data-testid="tsr-d-amount" />
					<p v-if="errors.amount" class="kt-field-error">{{ errors.amount }}</p>
				</div>
				<div class="field">
					<label for="tsr-d-currency">Currency</label>
					<input id="tsr-d-currency" v-model="form.currency" class="input" maxlength="3" :aria-invalid="!!errors.currency" data-testid="tsr-d-currency" />
					<p v-if="errors.currency" class="kt-field-error">{{ errors.currency }}</p>
				</div>
			</div>

			<div class="field">
				<label for="tsr-d-received">{{ isIssuer ? "Date and time the confirmation was received" : "Date and time received" }}</label>
				<input id="tsr-d-received" v-model="form.received_at" class="input" type="datetime-local" step="60" :aria-invalid="!!errors.received_at" data-testid="tsr-d-received" />
				<p v-if="errors.received_at" class="kt-field-error">{{ errors.received_at }}</p>
			</div>

			<div v-if="isIssuer" class="field">
				<label for="tsr-d-issuer-confirmed">Date and time the issuer confirmed</label>
				<input id="tsr-d-issuer-confirmed" v-model="form.issuer_confirmed_at" class="input" type="datetime-local" step="60" :aria-invalid="!!errors.issuer_confirmed_at" data-testid="tsr-d-issuer-confirmed" />
				<p v-if="errors.issuer_confirmed_at" class="kt-field-error">{{ errors.issuer_confirmed_at }}</p>
				<p v-else class="tsr-help">The time the issuer states it confirmed the instrument, kept apart from when you received and recorded it.</p>
			</div>

			<div class="field">
				<label for="tsr-d-notes">Notes (optional)</label>
				<textarea id="tsr-d-notes" v-model="form.notes" class="input" rows="3" maxlength="500" style="resize: vertical; height: auto" :aria-invalid="!!errors.notes" data-testid="tsr-d-notes"></textarea>
				<p v-if="errors.notes" class="kt-field-error">{{ errors.notes }}</p>
			</div>

			<div v-if="correcting" class="field">
				<label for="tsr-d-reason">Reason for correction</label>
				<textarea id="tsr-d-reason" v-model="form.correction_reason" class="input" rows="2" maxlength="500" style="resize: vertical; height: auto" :aria-invalid="!!errors.correction_reason" aria-describedby="tsr-d-reason-help" data-testid="tsr-d-reason"></textarea>
				<p v-if="errors.correction_reason" class="kt-field-error">{{ errors.correction_reason }}</p>
				<p v-else id="tsr-d-reason-help" class="tsr-help">Enter 10–500 characters.</p>
				<p v-if="errors.corrects" class="kt-field-error">{{ errors.corrects }}</p>
			</div>

			<div class="field">
				<label class="tsr-check">
					<input v-model="form.confirmed" type="checkbox" :aria-invalid="!!errors.confirmed" data-testid="tsr-d-confirm" />
					<span>{{ confirmation }}</span>
				</label>
				<p v-if="errors.confirmed" class="kt-field-error">{{ errors.confirmed }}</p>
			</div>

			<div v-if="error" class="kt-notice is-critical" role="alert" data-testid="tsr-d-error"><div class="kt-notice-body">{{ error }}</div></div>
			<div class="dialog-actions">
				<button type="button" class="btn btn-secondary" :disabled="pending" data-testid="tsr-d-cancel" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="btn btn-primary" :disabled="pending" data-testid="tsr-d-submit" @click="submit">{{ pending ? "Recording…" : correcting ? "Record correction" : isIssuer ? "Record confirmation" : "Record receipt" }}</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from "vue";
import * as api from "./data/api.js";

const props = defineProps({
	pending: { type: Boolean, default: false },
	errors: { type: Object, default: () => ({}) },
	error: { type: String, default: "" },
	initialTender: { type: String, default: "" },
	correcting: { type: Object, default: null },
	tenders: { type: Array, default: () => [] },
	kinds: { type: Array, default: () => ["Physical original", "Issuer confirmation"] },
	confirmation: { type: String, default: "I confirm that the instrument identified above was received at the date and time recorded." },
});
const emit = defineEmits(["submit", "cancel"]);

const from = props.correcting;
const form = reactive({
	tender_reference: from ? from.tender_reference : props.initialTender, instrument_type: from ? from.instrument_type : "", issuer: from ? from.issuer : "",
	instrument_reference: from ? from.instrument_reference : "", amount: from ? from.amount_value : "", currency: from ? from.currency : "",
	received_at: from ? from.received_at_value : "", notes: "", confirmed: false, correction_reason: "",
	intake_kind: from ? from.intake_kind : "Physical original", issuer_confirmed_at: from ? from.issuer_confirmed_at_value : "",
});
const isIssuer = computed(() => form.intake_kind === "Issuer confirmation");
const lookup = ref({});
const firstEl = ref(null);
const requestKey = `tsi-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
const lookupGuard = kentender_core.desk_page.createSequenceGuard();

// Permitted forms come from the published Tender once looked up; before
// that the two forms every released template offers are listed.
const forms = computed(() => (lookup.value.permitted_forms && lookup.value.permitted_forms.length ? lookup.value.permitted_forms : ["Demand Bank Guarantee", "Insurance Guarantee"]));

async function lookUp() {
	const reference = (form.tender_reference || "").trim();
	const token = lookupGuard.next();
	if (!reference) {
		lookup.value = {};
		return;
	}
	try {
		const result = await api.getRequirement(reference);
		if (!lookupGuard.isCurrent(token)) return;
		lookup.value = result && result.outcome === "OK" ? result : {};
		if (lookup.value.required && !form.currency) form.currency = lookup.value.currency;
		if (lookup.value.required && form.instrument_type && !lookup.value.permitted_forms.includes(form.instrument_type)) form.instrument_type = "";
	} catch (e) {
		if (lookupGuard.isCurrent(token)) lookup.value = {};
	}
}

function submit() {
	const { correction_reason, ...entered } = form;
	const stamp = (v) => (v ? v.replace("T", " ") + (v.length === 16 ? ":00" : "") : "");
	const values = { ...entered, received_at: stamp(form.received_at), issuer_confirmed_at: isIssuer.value ? stamp(form.issuer_confirmed_at) : "" };
	if (props.correcting) Object.assign(values, { corrects: props.correcting.intake_reference, correction_reason });
	emit("submit", { values, key: requestKey });
}
onMounted(() => {
	nextTick(() => firstEl.value && firstEl.value.focus());
	if (form.tender_reference) lookUp();
});
</script>
