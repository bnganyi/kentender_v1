<script setup>
// BDS-CHG-001 v0.8 §10.5 / §7.2 `UpdateSupplierOrganisation`: the Account's
// organisation facts, edited in one dialog and saved against the version the
// page read. A "Edit organisation" fix opens here with its field focused
// (BDS-DES-04-ATTENTION). Changing the official email sends a new
// verification link; the result says where it went.
import { computed, inject, nextTick, onMounted, reactive, ref } from "vue";

const METHOD = "kentender_suppliers.supplier_accounts.api.update_supplier_organisation";
const FIELDS = [
	{ key: "legal_name", label: "Legal name" },
	{ key: "country", label: "Country", options: ["Kenya"] },
	{ key: "registration_number", label: "Registration number" },
	{ key: "tax_identifier", label: "KRA PIN" },
	{ key: "registered_address", label: "Registered address" },
	{ key: "official_email", label: "Official email", type: "email" },
	{ key: "official_phone", label: "Official phone", type: "tel" },
];
const props = defineProps({
	organisation: { type: Object, required: true },
	focus: { type: String, default: "" },
});
const emit = defineEmits(["close", "saved"]);
const portal = inject("portal");
const form = reactive(Object.fromEntries(FIELDS.map((f) => [f.key, props.organisation[f.key] || ""])));
const errors = ref({});
const failure = ref("");
const inputs = ref({});
const key = `acc-edit-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);

function bind(name) {
	return (el) => {
		if (el) inputs.value[name] = el;
	};
}
function save() {
	errors.value = {};
	failure.value = "";
	return runner.run(async () => {
		const result = await portal.call(METHOD, { organisation: props.organisation.organisation, values: JSON.stringify(form), expected_version: props.organisation.record_version, idempotency_key: key }, { type: "POST" });
		if (result && result.ok) emit("saved", result);
		else if (result && result.errors) errors.value = result.errors;
		else if (result) failure.value = result.message || "";
	}, "Save organisation");
}
onMounted(() => nextTick(() => {
	const target = inputs.value[props.focus] || inputs.value.legal_name;
	if (target) target.focus();
}));
</script>

<template>
	<div class="dialog-backdrop" data-testid="acc-edit-dialog" @keydown.esc.stop="emit('close')">
		<div class="dialog acc-dialog" role="dialog" aria-modal="true" aria-labelledby="acc-edit-title">
			<div id="acc-edit-title" class="dialog-title">{{ __("Edit organisation") }}</div>
			<div v-for="f in FIELDS" :key="f.key" class="field">
				<label :for="`acc-edit-${f.key}`">{{ __(f.label) }}</label>
				<select v-if="f.options" :id="`acc-edit-${f.key}`" :ref="bind(f.key)" v-model="form[f.key]" class="input" :aria-invalid="!!errors[f.key]">
					<option v-for="o in f.options" :key="o">{{ o }}</option>
				</select>
				<input v-else :id="`acc-edit-${f.key}`" :ref="bind(f.key)" v-model="form[f.key]" class="input" :type="f.type || 'text'" :aria-invalid="!!errors[f.key]" :data-testid="`acc-edit-${f.key}`" />
				<p v-if="errors[f.key]" class="kt-field-error">{{ errors[f.key] }}</p>
			</div>
			<p class="acc-help">{{ __("Changing the official email sends a verification link to the new address. Bids already submitted keep the details they were submitted with.") }}</p>
			<div v-if="failure" class="kt-notice is-critical" role="alert"><div class="kt-notice-body">{{ failure }}</div></div>
			<div class="dialog-actions">
				<button type="button" class="btn btn-secondary" :disabled="pending" @click="emit('close')">{{ __("Cancel") }}</button>
				<button type="button" class="btn btn-primary" :disabled="pending" data-testid="acc-edit-save" @click="save">{{ pending ? __("Saving…") : __("Save organisation") }}</button>
			</div>
		</div>
	</div>
</template>
