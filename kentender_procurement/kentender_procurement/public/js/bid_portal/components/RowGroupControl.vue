<script setup>
// A bounded table of rows (release 1.4; BDS-CHG-001 §4.4.3 row group): named
// columns, at most the published number of rows, and a running total where the
// Tender publishes one ("shares add up to 100"). The server canonicalises and
// checks the rows and names a refused cell as `handle.row.column`; each refusal
// is shown beside its own cell and what was entered is kept. A table the Account
// supplies (an entity's partners or directors) is shown read-only.
import { computed } from "vue";
import { useNarrow } from "../composables/useNarrow.js";

const props = defineProps({
	field: { type: Object, required: true },
	modelValue: { default: null },
	disabled: { type: Boolean, default: false },
	issue: { type: String, default: "" },
	errors: { type: Object, default: () => ({}) },
	idPrefix: { type: String, default: "bds-field" },
});
const emit = defineEmits(["update:modelValue"]);
const narrow = useNarrow();

const table = computed(() => props.field.row_group || { columns: [], minimum_rows: 0, maximum_rows: 10, totals: [] });
const columns = computed(() => table.value.columns);
const rows = computed(() => (Array.isArray(props.modelValue) && props.modelValue.length ? props.modelValue : props.disabled ? [] : [blank()]));
const full = computed(() => rows.value.length >= table.value.maximum_rows);
const id = computed(() => `${props.idPrefix}-${props.field.handle}`);

function blank() {
	return Object.fromEntries(columns.value.map((c) => [c.key, ""]));
}
function set(next) {
	emit("update:modelValue", next);
}
function setCell(index, key, value) {
	set(rows.value.map((row, i) => (i === index ? { ...row, [key]: value } : { ...row })));
}
function addRow() {
	if (!full.value) set([...rows.value.map((r) => ({ ...r })), blank()]);
}
// the only row of a required table stays; any other row can be taken out
function canRemove() {
	return !(rows.value.length === 1 && props.field.required);
}
function removeRow(index) {
	const rest = rows.value.filter((_, i) => i !== index).map((r) => ({ ...r }));
	set(rest.length ? rest : []);
}
function cellError(index, key) {
	return props.errors[`${props.field.handle}.${index}.${key}`] || "";
}
function added(total) {
	return rows.value.reduce((sum, row) => sum + (Number(String(row[total.column] ?? "").replace(/,/g, "")) || 0), 0);
}
function totalLabel(total) {
	const column = columns.value.find((c) => c.key === total.column);
	return __("{0} added up: {1} of {2}", [column ? column.label : total.column, added(total), total.equals]);
}
</script>

<template>
	<div v-if="disabled" class="kt-field bds-rowgroup" :data-testid="'bds-field-' + field.handle">
		<span class="kt-label">{{ field.label }}</span>
		<table v-if="rows.length && !narrow" class="kt-table" :data-testid="'bds-rowgroup-table-' + field.handle">
			<thead><tr><th v-for="c in columns" :key="c.key">{{ c.label }}</th></tr></thead>
			<tbody><tr v-for="(row, index) in rows" :key="index"><td v-for="c in columns" :key="c.key">{{ row[c.key] }}</td></tr></tbody>
		</table>
		<div v-else-if="rows.length">
			<div v-for="(row, index) in rows" :key="index" class="bds-card"><div v-for="c in columns" :key="c.key" class="bds-card-fact"><span class="kt-label">{{ c.label }}</span><span>{{ row[c.key] }}</span></div></div>
		</div>
		<p v-else class="bds-muted">{{ __("Nothing is recorded.") }}</p>
		<p v-if="issue" class="kt-field-error">{{ issue }}</p>
		<p v-else-if="field.supplied_from" class="bds-help">{{ __("From your Account; change it there.") }}</p>
	</div>

	<fieldset v-else class="kt-field bds-rowgroup" :data-testid="'bds-field-' + field.handle">
		<legend>{{ field.label }}</legend>
		<p v-if="field.help" class="bds-help">{{ field.help }}</p>
		<div v-for="(row, index) in rows" :key="index" class="bds-rg-row" :data-testid="'bds-rowgroup-row-' + field.handle">
			<div v-for="c in columns" :key="c.key" class="kt-field bds-rg-cell">
				<label :for="`${id}-${index}-${c.key}`">{{ c.label }}</label>
				<select v-if="c.type === 'choice'" :id="`${id}-${index}-${c.key}`" class="kt-input" :value="row[c.key] ?? ''" :aria-invalid="!!cellError(index, c.key)" :data-testid="`bds-cell-${field.handle}-${index}-${c.key}`" @change="setCell(index, c.key, $event.target.value)">
					<option value="">{{ __("Select") }}</option>
					<option v-for="o in c.options" :key="o" :value="o">{{ o }}</option>
				</select>
				<input v-else :id="`${id}-${index}-${c.key}`" class="kt-input" :inputmode="c.type === 'text' ? null : 'decimal'" :value="row[c.key] ?? ''" :maxlength="c.max_length || null" :aria-invalid="!!cellError(index, c.key)" :data-testid="`bds-cell-${field.handle}-${index}-${c.key}`" @input="setCell(index, c.key, $event.target.value)" />
				<p v-if="cellError(index, c.key)" class="kt-field-error">{{ cellError(index, c.key) }}</p>
			</div>
			<button type="button" class="kt-btn kt-btn-ghost bds-rg-remove" :disabled="!canRemove()" :aria-label="__('Remove row {0}', [index + 1])" :data-testid="`bds-rowgroup-remove-${field.handle}-${index}`" @click="removeRow(index)">{{ __("Remove") }}</button>
		</div>
		<p v-for="t in table.totals" :key="t.column" class="bds-help" :data-testid="'bds-rowgroup-total-' + field.handle">{{ totalLabel(t) }}</p>
		<p v-if="issue" class="kt-field-error" role="alert" :data-testid="'bds-rowgroup-error-' + field.handle">{{ issue }}</p>
		<button type="button" class="kt-btn kt-btn-secondary" :disabled="full" :data-testid="'bds-rowgroup-add-' + field.handle" @click="addRow">{{ full ? __("Table is full") : __("Add row") }}</button>
	</fieldset>
</template>
