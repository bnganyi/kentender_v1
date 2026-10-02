<script setup>
// BDS-CHG-001 v0.8 §5.4–5.6 / plan D11 — one published response field, drawn
// by its control kind from the task read (label, help, options, limits,
// whether it is editable and the server's issue for it). The value is the
// caller's own entry until saved; the server checks and canonicalises it.
// Evidence files are their own commands (upload, replace, remove), run at
// once. Each file carries its own View, Replace and Remove; the field's one
// button adds a file, and only while the field has room for one.
import { computed, inject, ref } from "vue";
import CommonState from "./CommonState.vue";

const UPLOAD = "kentender_procurement.bid_submission.api.upload_bid_evidence";
const REPLACE = "kentender_procurement.bid_submission.api.replace_bid_evidence";
const REMOVE = "kentender_procurement.bid_submission.api.remove_bid_evidence";
const DOWNLOAD = "/api/method/kentender_procurement.bid_submission.api.download_bid_evidence";
const props = defineProps({
	field: { type: Object, required: true },
	modelValue: { default: null },
	error: { type: String, default: "" },
	bid: { type: Object, default: null }, // { reference, record_version } for evidence commands
	idPrefix: { type: String, default: "bds-field" },
});
const emit = defineEmits(["update:modelValue", "changed"]);
const portal = inject("portal");
const picker = ref(null);
const fileError = ref("");
const rejection = ref(null); // §10.17 Evidence rejected: the safe reason the file checks gave
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (fileError.value = e.message) });
const pending = computed(() => runner.pending.value);

const id = computed(() => `${props.idPrefix}-${props.field.handle}`);
const issue = computed(() => props.error || (props.field.issue && props.field.issue.severity === "Must fix" && props.field.value !== null && props.field.value !== "" ? props.field.issue.text : ""));
const limits = computed(() => props.field.limits || {});
const disabled = computed(() => !props.field.editable);
const files = computed(() => (props.field.evidence && props.field.evidence.files) || []);
// a refused file is only a record of the refusal: it does not fill the field
const held = computed(() => files.value.filter((f) => f.status !== "Rejected"));
const maximum = computed(() => (props.field.evidence && props.field.evidence.maximum) || 0); // 0: the requirement states none
const addLabel = computed(() => {
	if (!held.value.length) return "Upload file";
	return maximum.value && held.value.length >= maximum.value ? "" : "Add another file";
});
const replacing = ref(null); // the file the next chosen file takes the place of; null adds one
function choose(file = null) {
	replacing.value = file;
	if (picker.value) picker.value.click();
}

function set(value) {
	emit("update:modelValue", value);
}
function toggle(option, checked) {
	const current = Array.isArray(props.modelValue) ? [...props.modelValue] : [];
	set(checked ? [...current, option] : current.filter((o) => o !== option));
}
// A ports answer starts empty: no type chosen and no count, until the bidder gives them.
function ports() {
	return Array.isArray(props.modelValue) && props.modelValue.length ? props.modelValue : [{ port_type: "", count: null }];
}
function setPort(index, key, value) {
	const rows = ports().map((row) => ({ ...row }));
	rows[index][key] = key === "count" ? (value === "" ? null : Number(value)) : value;
	set(rows);
}
function addPort() {
	set([...ports(), { port_type: "", count: null }]);
}
function fileHref(file) {
	return `${DOWNLOAD}?bid_reference=${encodeURIComponent(props.bid.reference)}&evidence_id=${encodeURIComponent(file.id)}&inline=1`;
}
function upload(event) {
	const file = (event.target.files || [])[0];
	event.target.value = "";
	if (!file) return;
	fileError.value = "";
	rejection.value = null;
	return runner.run(async () => {
		const target = replacing.value;
		const common = { bid_reference: props.bid.reference, expected_record_version: props.bid.record_version, idempotency_key: `bds-evidence-${Date.now().toString(36)}` };
		const result = target
			? await portal.upload(REPLACE, { ...common, evidence_id: target.id }, { file })
			: await portal.upload(UPLOAD, { ...common, handle: props.field.handle }, { file });
		if (result && result.ok) {
			replacing.value = null;
			emit("changed", result);
		} else if (result && result.code === "BDS_EVIDENCE_REJECTED") {
			rejection.value = (result.errors && result.errors[props.field.handle]) || "";
			emit("changed", result); // the refused file is kept as a Rejected record
		} else if (result && result.errors) fileError.value = result.errors[props.field.handle] || result.message;
		else if (result) fileError.value = result.message || "";
	}, "Upload file");
}
function remove(file) {
	fileError.value = "";
	return runner.run(async () => {
		const result = await portal.call(REMOVE, { bid_reference: props.bid.reference, evidence_id: file.id, expected_record_version: props.bid.record_version, idempotency_key: `bds-evidence-remove-${Date.now().toString(36)}` }, { type: "POST" });
		if (result && result.ok) emit("changed", result);
		else if (result) fileError.value = result.message || "";
	}, "Remove file");
}
</script>

<template>
	<fieldset v-if="field.kind === 'confirmation'" class="kt-field bds-field-bare" :data-testid="'bds-field-' + field.handle">
		<legend class="bds-visually-hidden">{{ field.label }}</legend>
		<label class="kt-checkbox bds-acknowledge">
			<input :id="id" type="checkbox" :checked="!!modelValue" :disabled="disabled" :aria-invalid="!!issue" @change="set($event.target.checked)" />
			<span class="box"></span>
			<span>{{ field.label }}</span>
		</label>
		<p v-if="issue" class="kt-field-error">{{ issue }}</p>
	</fieldset>

	<div v-else-if="field.kind === 'evidence'" class="kt-field" :data-testid="'bds-field-' + field.handle">
		<label :for="id">{{ field.label }}</label>
		<input :id="id" ref="picker" class="bds-file-input" type="file" tabindex="-1" accept=".pdf,.png,.jpg,.jpeg" :disabled="disabled || pending" @change="upload" />
		<div v-for="file in files" :key="file.id" class="bds-file-row" :data-testid="'bds-file-' + file.id">
			<span class="bds-file-name">{{ file.name }}</span>
			<span v-if="file.status === 'Rejected'" class="kt-status is-critical">{{ __("Rejected") }}</span>
			<span v-else-if="file.status !== 'Accepted'" class="kt-status is-attention">{{ __(file.status) }}</span>
			<span class="bds-file-actions">
				<a v-if="file.status !== 'Rejected'" :href="fileHref(file)" target="_blank" rel="noopener">{{ __("View") }}</a>
				<button v-if="!disabled && file.status !== 'Rejected'" type="button" class="bds-link-button" :disabled="pending" :data-testid="'bds-replace-' + file.id" @click="choose(file)">{{ __("Replace") }}</button>
				<button v-if="!disabled" type="button" class="bds-link-button" :disabled="pending" @click="remove(file)">{{ __("Remove") }}</button>
			</span>
			<p v-if="file.reason" class="bds-muted">{{ file.reason }}</p>
		</div>
		<div v-if="!disabled && addLabel">
			<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" :data-testid="'bds-upload-' + field.handle" @click="choose()">{{ __(addLabel) }}</button>
		</div>
		<CommonState v-if="rejection !== null" inline state="evidence-rejected" :figures="{ reason: rejection }" @action="picker && picker.click()" />
		<p v-else-if="fileError || issue" class="kt-field-error">{{ fileError || issue }}</p>
		<p v-else-if="field.help" class="bds-help">{{ field.help }}</p>
	</div>

	<fieldset v-else-if="field.kind === 'yes_no'" class="kt-field bds-choice-field" :data-testid="'bds-field-' + field.handle">
		<legend>{{ field.label }}</legend>
		<label v-for="option in field.options" :key="option" class="bds-radio"><input type="radio" :name="id" :value="option" :checked="modelValue === option" :disabled="disabled" @change="set(option)" /> {{ __(option) }}</label>
		<p v-if="issue" class="kt-field-error">{{ issue }}</p>
		<p v-else-if="field.help" class="bds-help">{{ field.help }}</p>
	</fieldset>

	<fieldset v-else-if="field.kind === 'multi_select'" class="kt-field bds-choice-field" :data-testid="'bds-field-' + field.handle">
		<legend>{{ field.label }}</legend>
		<label v-for="option in field.options" :key="option" class="kt-checkbox"><input type="checkbox" :checked="Array.isArray(modelValue) && modelValue.includes(option)" :disabled="disabled" @change="toggle(option, $event.target.checked)" /><span class="box"></span><span>{{ option }}</span></label>
		<p v-if="issue" class="kt-field-error">{{ issue }}</p>
	</fieldset>

	<div v-else-if="field.kind === 'ports'" class="kt-field" :data-testid="'bds-field-' + field.handle">
		<label :for="id + '-0'">{{ field.label }}</label>
		<div v-for="(row, index) in ports()" :key="index" class="bds-port-row">
			<select :id="id + '-' + index" class="kt-input" :value="row.port_type" :disabled="disabled" @change="setPort(index, 'port_type', $event.target.value)">
				<option value="" disabled>{{ __("Select") }}</option>
				<option v-for="option in field.options" :key="option" :value="option">{{ option }}</option>
			</select>
			<input class="kt-input" type="number" min="1" :value="row.count ?? ''" :disabled="disabled" :placeholder="__('Number')" :aria-label="__('Number of ports')" @input="setPort(index, 'count', $event.target.value)" />
		</div>
		<button v-if="!disabled" type="button" class="kt-btn kt-btn-ghost" @click="addPort">{{ __("Add port type") }}</button>
		<p v-if="issue" class="kt-field-error">{{ issue }}</p>
	</div>

	<div v-else class="kt-field" :data-testid="'bds-field-' + field.handle">
		<label :for="id">{{ field.label }}</label>
		<select v-if="field.kind === 'single_choice'" :id="id" class="kt-input" :value="modelValue ?? ''" :disabled="disabled" :aria-invalid="!!issue" @change="set($event.target.value)">
			<option value="" disabled>{{ __("Select") }}</option>
			<option v-for="option in field.options" :key="option" :value="option">{{ option }}</option>
		</select>
		<textarea v-else-if="field.kind === 'long_text'" :id="id" class="kt-input" rows="3" :value="modelValue ?? ''" :maxlength="limits.max_length || null" :disabled="disabled" :aria-invalid="!!issue" @input="set($event.target.value)"></textarea>
		<input v-else-if="field.kind === 'date'" :id="id" class="kt-input" type="date" :value="modelValue ?? ''" :min="limits.not_before || null" :max="limits.not_after || null" :disabled="disabled" :aria-invalid="!!issue" @input="set($event.target.value)" />
		<input v-else-if="['integer', 'decimal', 'money'].includes(field.kind)" :id="id" class="kt-input" inputmode="decimal" :value="modelValue ?? ''" :disabled="disabled" :aria-invalid="!!issue" @input="set($event.target.value)" />
		<input v-else :id="id" class="kt-input" :value="modelValue ?? ''" :maxlength="limits.max_length || null" :disabled="disabled" :aria-invalid="!!issue" @input="set($event.target.value)" />
		<p v-if="issue" class="kt-field-error">{{ issue }}</p>
		<p v-else-if="field.supplied_from" class="bds-help">{{ __("From your Account; change it there.") }}</p>
		<p v-else-if="field.help" class="bds-help">{{ field.help }}</p>
	</div>
</template>
