<script setup>
// BDS-CHG-001 v0.8 §4.7 / §10.5 reusable Account evidence: one file with its
// type, reference and expiry. The file is checked before it is kept; a
// refused file is named in place. A bid later links an exact copy, so
// changing this list never changes a submitted bid.
import { computed, inject, nextTick, onMounted, reactive, ref } from "vue";

const METHOD = "kentender_suppliers.supplier_accounts.api.upload_account_evidence";
const TYPES = ["Certificate of incorporation", "Tax compliance certificate", "Reservation evidence", "Signatory authority", "Joint-venture agreement", "Other"];
const props = defineProps({ organisation: { type: Object, required: true } });
const emit = defineEmits(["close", "saved"]);
const portal = inject("portal");
const form = reactive({ evidence_type: "", title: "", reference: "", valid_until: "" });
const file = ref(null);
const errors = ref({});
const failure = ref("");
const first = ref(null);
const key = `acc-evidence-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);

function chooseFile(event) {
	file.value = (event.target.files || [])[0] || null;
}
function save() {
	errors.value = {};
	failure.value = "";
	return runner.run(async () => {
		const result = await portal.upload(METHOD, { organisation: props.organisation.organisation, ...form, idempotency_key: key }, { file: file.value });
		if (result && result.ok) emit("saved", result);
		else if (result && result.errors) errors.value = result.errors;
		else if (result) failure.value = result.message || "";
	}, "Add evidence");
}
onMounted(() => nextTick(() => first.value && first.value.focus()));
</script>

<template>
	<div class="dialog-backdrop" data-testid="acc-evidence-dialog" @keydown.esc.stop="emit('close')">
		<div class="dialog acc-dialog" role="dialog" aria-modal="true" aria-labelledby="acc-evidence-title">
			<div id="acc-evidence-title" class="dialog-title">{{ __("Add evidence") }}</div>
			<div class="field">
				<label for="acc-evidence-type">{{ __("Evidence type") }}</label>
				<select id="acc-evidence-type" ref="first" v-model="form.evidence_type" class="input" :aria-invalid="!!errors.evidence_type" data-testid="acc-evidence-type">
					<option value="" disabled>{{ __("Choose the type") }}</option>
					<option v-for="t in TYPES" :key="t" :value="t">{{ __(t) }}</option>
				</select>
				<p v-if="errors.evidence_type" class="kt-field-error">{{ errors.evidence_type }}</p>
			</div>
			<div class="field">
				<label for="acc-evidence-name">{{ __("Name") }}</label>
				<input id="acc-evidence-name" v-model="form.title" class="input" :aria-invalid="!!errors.title" aria-describedby="acc-evidence-name-help" data-testid="acc-evidence-name" />
				<p v-if="errors.title" class="kt-field-error">{{ errors.title }}</p>
				<p v-else id="acc-evidence-name-help" class="acc-help">{{ __("Optional. The evidence type is used when this is empty.") }}</p>
			</div>
			<div class="acc-grid-2">
				<div class="field">
					<label for="acc-evidence-reference">{{ __("Reference") }}</label>
					<input id="acc-evidence-reference" v-model="form.reference" class="input" :aria-invalid="!!errors.reference" data-testid="acc-evidence-reference" />
					<p v-if="errors.reference" class="kt-field-error">{{ errors.reference }}</p>
				</div>
				<div class="field">
					<label for="acc-evidence-valid">{{ __("Valid until") }}</label>
					<input id="acc-evidence-valid" v-model="form.valid_until" class="input" type="date" :aria-invalid="!!errors.valid_until" data-testid="acc-evidence-valid" />
					<p v-if="errors.valid_until" class="kt-field-error">{{ errors.valid_until }}</p>
				</div>
			</div>
			<div class="field">
				<label for="acc-evidence-file">{{ __("File") }}</label>
				<input id="acc-evidence-file" class="input" type="file" accept=".pdf,.png,.jpg,.jpeg" :aria-invalid="!!errors.file" data-testid="acc-evidence-file" @change="chooseFile" />
				<p v-if="errors.file" class="kt-field-error">{{ errors.file }}</p>
			</div>
			<div v-if="failure" class="kt-notice is-critical" role="alert"><div class="kt-notice-body">{{ failure }}</div></div>
			<div class="dialog-actions">
				<button type="button" class="btn btn-secondary" :disabled="pending" @click="emit('close')">{{ __("Cancel") }}</button>
				<button type="button" class="btn btn-primary" :disabled="pending" data-testid="acc-evidence-save" @click="save">{{ pending ? __("Uploading…") : __("Add evidence") }}</button>
			</div>
		</div>
	</div>
</template>
