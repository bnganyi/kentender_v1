<script setup>
// BDS-CHG-001 v0.8 §4.2 / §7.2 `AssignSupplierRepresentative` and
// `AssignAuthorisedSignatory`: an Authorised Signatory adds a person with one
// responsibility and an effective period. A signatory needs the evidence of
// their authority to sign; a representative prepares bids but cannot sign.
// The assignment is immutable once made — a change is a new assignment.
import { computed, inject, nextTick, onMounted, reactive, ref } from "vue";

const REPRESENTATIVE = "kentender_suppliers.supplier_accounts.api.assign_supplier_representative";
const SIGNATORY = "kentender_suppliers.supplier_accounts.api.assign_authorised_signatory";
const props = defineProps({ organisation: { type: Object, required: true } });
const emit = defineEmits(["close", "saved"]);
const portal = inject("portal");
const form = reactive({ responsibility: "Supplier Representative", full_name: "", email: "", job_title: "", effective_from: "", effective_to: "" });
const file = ref(null);
const errors = ref({});
const failure = ref("");
const first = ref(null);
const key = `acc-person-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);
const signatory = computed(() => form.responsibility === "Authorised Signatory");

function chooseFile(event) {
	file.value = (event.target.files || [])[0] || null;
}
function save() {
	errors.value = {};
	failure.value = "";
	const fields = { organisation: props.organisation.organisation, email: form.email, full_name: form.full_name, job_title: form.job_title, effective_from: form.effective_from, effective_to: form.effective_to, idempotency_key: `${key}-${form.responsibility}` };
	return runner.run(async () => {
		const result = signatory.value ? await portal.upload(SIGNATORY, fields, { authority_evidence: file.value }) : await portal.call(REPRESENTATIVE, fields, { type: "POST" });
		if (result && result.ok) emit("saved", result);
		else if (result && result.errors) errors.value = result.errors;
		else if (result) failure.value = result.message || "";
	}, "Add person");
}
onMounted(() => nextTick(() => first.value && first.value.focus()));
</script>

<template>
	<div class="kt-dialog-backdrop" data-testid="acc-person-dialog" @keydown.esc.stop="emit('close')">
		<div class="kt-dialog acc-dialog" role="dialog" aria-modal="true" aria-labelledby="acc-person-title">
			<div id="acc-person-title" class="kt-dialog-title">{{ __("Add person") }}</div>
			<fieldset class="kt-field acc-choice">
				<legend>{{ __("Responsibility") }}</legend>
				<label class="acc-radio"><input ref="first" v-model="form.responsibility" type="radio" value="Supplier Representative" data-testid="acc-person-representative" /> {{ __("Supplier Representative") }} <span class="acc-help">{{ __("Prepares bids. Cannot sign or submit.") }}</span></label>
				<label class="acc-radio"><input v-model="form.responsibility" type="radio" value="Authorised Signatory" data-testid="acc-person-signatory" /> {{ __("Authorised Signatory") }} <span class="acc-help">{{ __("Signs and submits bids for the organisation.") }}</span></label>
			</fieldset>
			<div class="kt-field">
				<label for="acc-person-name">{{ __("Full name") }}</label>
				<input id="acc-person-name" v-model="form.full_name" class="kt-input" :aria-invalid="!!errors.full_name" data-testid="acc-person-name" />
				<p v-if="errors.full_name" class="kt-field-error">{{ errors.full_name }}</p>
			</div>
			<div class="kt-field">
				<label for="acc-person-email">{{ __("Email") }}</label>
				<input id="acc-person-email" v-model="form.email" class="kt-input" type="email" :aria-invalid="!!errors.email" data-testid="acc-person-email" />
				<p v-if="errors.email" class="kt-field-error">{{ errors.email }}</p>
			</div>
			<div class="kt-field">
				<label for="acc-person-title">{{ __("Job title") }}</label>
				<input id="acc-person-title" v-model="form.job_title" class="kt-input" :aria-invalid="!!errors.job_title" data-testid="acc-person-title" />
				<p v-if="errors.job_title" class="kt-field-error">{{ errors.job_title }}</p>
			</div>
			<div class="acc-grid-2">
				<div class="kt-field">
					<label for="acc-person-from">{{ __("Effective from") }}</label>
					<input id="acc-person-from" v-model="form.effective_from" class="kt-input" type="date" :aria-invalid="!!errors.effective_from" aria-describedby="acc-person-from-help" />
					<p v-if="errors.effective_from" class="kt-field-error">{{ errors.effective_from }}</p>
					<p v-else id="acc-person-from-help" class="acc-help">{{ __("Leave empty to start now.") }}</p>
				</div>
				<div class="kt-field">
					<label for="acc-person-to">{{ __("Effective to") }}</label>
					<input id="acc-person-to" v-model="form.effective_to" class="kt-input" type="date" :aria-invalid="!!errors.effective_to" aria-describedby="acc-person-to-help" />
					<p v-if="errors.effective_to" class="kt-field-error">{{ errors.effective_to }}</p>
					<p v-else id="acc-person-to-help" class="acc-help">{{ __("Optional.") }}</p>
				</div>
			</div>
			<div v-if="signatory" class="kt-field">
				<label for="acc-person-authority">{{ __("Authority evidence") }}</label>
				<input id="acc-person-authority" class="kt-input" type="file" accept=".pdf,.png,.jpg,.jpeg" :aria-invalid="!!errors.authority_evidence" data-testid="acc-person-authority" @change="chooseFile" />
				<p v-if="errors.authority_evidence" class="kt-field-error">{{ errors.authority_evidence }}</p>
			</div>
			<div v-if="failure" class="kt-notice is-critical" role="alert"><div class="kt-notice-body">{{ failure }}</div></div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" @click="emit('close')">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="acc-person-save" @click="save">{{ pending ? __("Adding…") : __("Add person") }}</button>
			</div>
		</div>
	</div>
</template>
