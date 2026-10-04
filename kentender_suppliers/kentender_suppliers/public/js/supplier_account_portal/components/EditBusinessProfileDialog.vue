<script setup>
// The business profile (release 1.4 plan, WP-2): the standing facts a tender's
// business questionnaire asks for, kept once on the Account and copied into each
// bid. One dialog, saved against the version the page read. A table (partners or
// directors) takes at most ten rows and its shares must total 100; the server
// checks both and names the row and cell, shown here beside the cell. A
// "Edit business profile" fix opens here with its field focused.
import { computed, inject, nextTick, onMounted, reactive, ref, watch } from "vue";

const METHOD = "kentender_suppliers.supplier_accounts.api.update_business_profile";
const STRUCTURES = ["Sole proprietor", "Partnership", "Registered company"];
const MAX_ROWS = 10;
const SOLE = [
	["sole_proprietor_name", "Name in full"], ["sole_proprietor_age", "Age", "number"], ["sole_proprietor_nationality", "Nationality"],
	["sole_proprietor_country_of_origin", "Country of origin"], ["sole_proprietor_citizenship", "Citizenship"],
];
const ALWAYS = [
	["trade_licence_number", "Current trade licence number"], ["trade_licence_expiry", "Trade licence expiry date", "date"],
	["maximum_business_value", "Maximum value of business handled (KES)"], ["year_of_registration", "Year of registration", "number"],
];
const PEOPLE = [["name", "Name"], ["nationality", "Nationality"], ["citizenship", "Citizenship"], ["shares", "Shares owned (%)"]];
const props = defineProps({
	profile: { type: Object, required: true },
	focus: { type: String, default: "" },
});
const emit = defineEmits(["close", "saved"]);
const portal = inject("portal");
const copy = (rows) => (rows || []).map((r) => ({ ...r }));
const form = reactive({ ...props.profile.values, partners: copy(props.profile.values.partners), directors: copy(props.profile.values.directors) });
const errors = ref({});
const failure = ref("");
const inputs = ref({});
const key = `acc-profile-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);
const structure = computed(() => form.business_structure);
// the one owners table the chosen structure asks for
const table = computed(() => (structure.value === "Partnership" ? "partners" : structure.value === "Registered company" ? "directors" : ""));
const total = (rows) => rows.reduce((sum, r) => sum + (Number(r.shares) || 0), 0);

function bind(name) {
	return (el) => {
		if (el) inputs.value[name] = el;
	};
}
// a table that is asked for starts with its first row, ready to fill
watch(table, (name) => {
	if (name && !form[name].length) form[name].push({ name: "", nationality: "", citizenship: "", shares: "" });
}, { immediate: true });
function addRow(table) {
	if (form[table].length < MAX_ROWS) form[table].push({ name: "", nationality: "", citizenship: "", shares: "" });
}
function removeRow(table, index) {
	form[table].splice(index, 1);
}
function cellError(table, index, column) {
	return errors.value[`${table}.${index}.${column}`] || "";
}
function save() {
	errors.value = {};
	failure.value = "";
	const values = { ...form };
	return runner.run(async () => {
		const result = await portal.call(METHOD, { organisation: props.profile.organisation, values: JSON.stringify(values), expected_version: props.profile.record_version, idempotency_key: key }, { type: "POST" });
		if (result && result.ok) emit("saved", result);
		else if (result && result.errors) errors.value = result.errors;
		else if (result) failure.value = result.message || "";
	}, "Save business profile");
}
onMounted(() => nextTick(() => {
	const target = inputs.value[props.focus] || inputs.value.business_structure;
	if (target) target.focus();
}));
</script>

<template>
	<div class="kt-dialog-backdrop" data-testid="acc-profile-dialog" @keydown.esc.stop="emit('close')">
		<div class="kt-dialog acc-dialog acc-dialog-wide" role="dialog" aria-modal="true" aria-labelledby="acc-profile-title">
			<div id="acc-profile-title" class="kt-dialog-title">{{ __("Edit business profile") }}</div>
			<p class="acc-help">{{ __("These facts are copied into each bid you prepare, so you enter them once. A bid keeps the copy it was prepared with; you can refresh it from here before you submit.") }}</p>

			<div class="kt-field">
				<label for="acc-profile-business_structure">{{ __("Business structure") }}</label>
				<select id="acc-profile-business_structure" :ref="bind('business_structure')" v-model="form.business_structure" class="kt-input" :aria-invalid="!!errors.business_structure" data-testid="acc-profile-business_structure">
					<option value="">{{ __("Choose…") }}</option>
					<option v-for="o in STRUCTURES" :key="o" :value="o">{{ __(o) }}</option>
				</select>
				<p v-if="errors.business_structure" class="kt-field-error">{{ errors.business_structure }}</p>
			</div>

			<template v-if="structure === 'Sole proprietor'">
				<div v-for="[name, label, type] in SOLE" :key="name" class="kt-field">
					<label :for="`acc-profile-${name}`">{{ __(label) }}</label>
					<input :id="`acc-profile-${name}`" :ref="bind(name)" v-model="form[name]" class="kt-input" :type="type || 'text'" :aria-invalid="!!errors[name]" :data-testid="`acc-profile-${name}`" />
					<p v-if="errors[name]" class="kt-field-error">{{ errors[name] }}</p>
				</div>
			</template>

			<template v-if="structure === 'Registered company'">
				<div class="kt-field">
					<label for="acc-profile-company_type">{{ __("Private or public company") }}</label>
					<select id="acc-profile-company_type" :ref="bind('company_type')" v-model="form.company_type" class="kt-input" :aria-invalid="!!errors.company_type" data-testid="acc-profile-company_type">
						<option value="">{{ __("Choose…") }}</option>
						<option value="Private company">{{ __("Private company") }}</option>
						<option value="Public company">{{ __("Public company") }}</option>
					</select>
					<p v-if="errors.company_type" class="kt-field-error">{{ errors.company_type }}</p>
				</div>
				<div v-for="[name, label] in [['nominal_capital', 'Nominal capital (KES)'], ['issued_capital', 'Issued capital (KES)']]" :key="name" class="kt-field">
					<label :for="`acc-profile-${name}`">{{ __(label) }}</label>
					<input :id="`acc-profile-${name}`" :ref="bind(name)" v-model="form[name]" class="kt-input" type="text" inputmode="decimal" :aria-invalid="!!errors[name]" :data-testid="`acc-profile-${name}`" />
					<p v-if="errors[name]" class="kt-field-error">{{ errors[name] }}</p>
				</div>
			</template>

			<fieldset v-if="table" :key="table" class="acc-people-table" :data-testid="`acc-profile-${table}`">
				<legend>{{ table === "partners" ? __("Partners") : __("Directors") }}</legend>
				<p class="acc-help">{{ __("Up to {0} rows. Shares owned must add up to 100.", [MAX_ROWS]) }}</p>
				<div v-for="(row, index) in form[table]" :key="index" class="acc-people-row" :data-testid="`acc-profile-${table}-row`">
					<div v-for="[column, label] in PEOPLE" :key="column" class="kt-field">
						<label :for="`acc-profile-${table}-${index}-${column}`">{{ __(label) }}</label>
						<input :id="`acc-profile-${table}-${index}-${column}`" v-model="row[column]" class="kt-input" :type="'text'" :inputmode="column === 'shares' ? 'decimal' : null" :aria-invalid="!!cellError(table, index, column)" :data-testid="`acc-profile-${table}-${index}-${column}`" />
						<p v-if="cellError(table, index, column)" class="kt-field-error">{{ cellError(table, index, column) }}</p>
					</div>
					<button type="button" class="kt-btn kt-btn-secondary acc-row-remove" :aria-label="__('Remove row {0}', [index + 1])" @click="removeRow(table, index)">{{ __("Remove") }}</button>
				</div>
				<p v-if="errors[table]" class="kt-field-error" role="alert" :data-testid="`acc-profile-${table}-error`">{{ errors[table] }}</p>
				<p class="acc-help" :data-testid="`acc-profile-${table}-total`">{{ __("Shares added up: {0}", [total(form[table])]) }}</p>
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="form[table].length >= MAX_ROWS" :data-testid="`acc-profile-${table}-add`" @click="addRow(table)">{{ form[table].length >= MAX_ROWS ? __("Table is full") : __("Add row") }}</button>
			</fieldset>

			<div v-for="[name, label, type] in ALWAYS" :key="name" class="kt-field">
				<label :for="`acc-profile-${name}`">{{ __(label) }}</label>
				<input :id="`acc-profile-${name}`" :ref="bind(name)" v-model="form[name]" class="kt-input" :type="type || 'text'" :aria-invalid="!!errors[name]" :data-testid="`acc-profile-${name}`" />
				<p v-if="errors[name]" class="kt-field-error">{{ errors[name] }}</p>
			</div>
			<div class="kt-field">
				<label for="acc-profile-state_owned">{{ __("Is the business state-owned?") }}</label>
				<select id="acc-profile-state_owned" :ref="bind('state_owned')" v-model="form.state_owned" class="kt-input" :aria-invalid="!!errors.state_owned" data-testid="acc-profile-state_owned">
					<option value="">{{ __("Choose…") }}</option>
					<option value="Yes">{{ __("Yes") }}</option>
					<option value="No">{{ __("No") }}</option>
				</select>
				<p v-if="errors.state_owned" class="kt-field-error">{{ errors.state_owned }}</p>
			</div>

			<div v-if="failure" class="kt-notice is-critical" role="alert"><div class="kt-notice-body">{{ failure }}</div></div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" @click="emit('close')">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="acc-profile-save" @click="save">{{ pending ? __("Saving…") : __("Save business profile") }}</button>
			</div>
		</div>
	</div>
</template>
