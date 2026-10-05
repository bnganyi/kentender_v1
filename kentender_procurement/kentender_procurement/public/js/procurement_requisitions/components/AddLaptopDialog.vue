<!-- REQ-DES-04 — Add laptop request (base, ONE-SOURCE, VALIDATION), and the
     same shared details in "Edit shared details" mode. One shared definition,
     one source-linked row per approved requirement; the server creates every
     row or none and states any mismatch. -->
<template>
	<DialogFrame :title="mode === 'shared' ? 'Edit shared details' : 'Add laptop request'" :width="640" :busy="busy" testid="req-add-dialog" @close="$emit('close')">
		<Notice v-if="mismatch" tone="warning"><span data-testid="req-add-mismatch">{{ mismatch }}</span></Notice>
		<Notice v-else-if="otherError" tone="critical">{{ otherError }}</Notice>
		<p v-if="mode === 'add' && !mismatch" class="kt-muted" style="font-size: 13px; margin: 0">Enter the shared laptop details once, then confirm the quantity and intended use for each department.</p>
		<template v-if="mode === 'shared' || !mismatch">
			<div class="kt-label" style="margin-top: var(--kt-space-2)">Shared details</div>
			<div class="req-grid-2-tight">
				<div class="field">
					<label for="req-add-category">Equipment category</label>
					<select id="req-add-category" v-model="shared.equipment_category" class="input" :class="{ 'is-invalid': sharedError('equipment_category') }" data-testid="req-add-category">
						<option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
					</select>
					<span v-if="sharedError('equipment_category')" class="req-field-error">{{ sharedError("equipment_category") }}</span>
				</div>
				<div class="field">
					<label for="req-add-name">Item name</label>
					<input id="req-add-name" v-model="shared.item_name" class="input" :class="{ 'is-invalid': sharedError('item_name') }" data-testid="req-add-name" />
					<span v-if="sharedError('item_name')" class="req-field-error">{{ sharedError("item_name") }}</span>
				</div>
				<div class="field">
					<label for="req-add-location">Delivery location</label>
					<select id="req-add-location" v-model="shared.delivery_location" class="input" :class="{ 'is-invalid': sharedError('delivery_location') }" data-testid="req-add-location">
						<option value="">Same as the requisition</option>
						<option v-for="l in locations" :key="l.name" :value="l.name">{{ l.address || l.location_name }}</option>
					</select>
					<span v-if="sharedError('delivery_location')" class="req-field-error">{{ sharedError("delivery_location") }}</span>
				</div>
				<div class="field">
					<label for="req-add-latest">Latest delivery date</label>
					<DateField id="req-add-latest" v-model="shared.latest_delivery_date" :max="requisitionLatest" :invalid="!!sharedError('latest_delivery_date')" />
					<span v-if="sharedError('latest_delivery_date')" class="req-field-error">{{ sharedError("latest_delivery_date") }}</span>
				</div>
			</div>
		</template>
		<template v-if="mode === 'add'">
			<div v-if="rows.length > 1 || mismatch" class="kt-label" style="margin-top: var(--kt-space-3)">Department quantities and use</div>
			<table class="table" data-testid="req-add-rows">
				<thead><tr><th>Use</th><th>Department and approved requirement</th><th class="is-num">Quantity</th><th>Unit</th><th>Intended use</th></tr></thead>
				<tbody>
					<tr v-for="row in rows" :key="row.drawdown_line_id" data-testid="req-add-row">
						<td><label class="kt-checkbox"><input v-model="entry(row).use" type="checkbox" :aria-label="`Use ${row.department}`" /><span class="box"></span></label></td>
						<td>{{ row.department }}<div class="kt-label">{{ row.source_reference }}</div></td>
						<td class="is-num">
							<input v-model="entry(row).quantity" class="input" :class="{ 'is-invalid': rowError(row) }" style="max-width: 70px" inputmode="numeric" :aria-label="`Quantity for ${row.department}`" :disabled="!entry(row).use" data-testid="req-add-quantity" />
							<div v-if="rowError(row)" class="req-field-error" style="margin-top: 3px; white-space: nowrap" data-testid="req-add-row-error">{{ rowError(row) }}</div>
						</td>
						<td>{{ row.unit }}</td>
						<td><input v-model="entry(row).intended_use" class="input" :aria-label="`Intended use for ${row.department}`" :disabled="!entry(row).use" data-testid="req-add-use" /></td>
					</tr>
				</tbody>
			</table>
			<p class="kt-muted" style="font-size: 13px; margin: 0">{{ mismatch ? "Shared details are unchanged and retained. No equipment row is created until both rows are valid." : "The standard laptop requirements will be ready for review in the next task." }}</p>
		</template>
		<template #actions>
			<button type="button" class="btn btn-secondary" :disabled="busy" @click="$emit('close')">Cancel</button>
			<button type="button" class="btn" :class="ready ? 'btn-primary' : 'btn-secondary'" :disabled="busy || !ready" data-testid="req-add-confirm" @click="submit">{{ confirmLabel }}</button>
		</template>
	</DialogFrame>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { useReq } from "../data/context.js";
import DateField from "./shared/DateField.vue";
import DialogFrame from "./shared/DialogFrame.vue";
import Notice from "./shared/Notice.vue";

const props = defineProps({ view: { type: Object, required: true }, mode: { type: String, default: "add" } });
const emit = defineEmits(["close"]);
const ctx = useReq();
const busy = computed(() => ctx.pending.value);
const LABEL = props.mode === "shared" ? "update-shared" : "add-items";

const categories = computed(() => (props.view.catalogue || {}).categories || []);
const locations = computed(() => (props.view.request_information || {}).locations || []);
const requisitionLatest = computed(() => (props.view.request_information || {}).latest_delivery_date || "");
const spec = (props.view.equipment || {}).shared_specification || {};
const shared = reactive({
	equipment_category: spec.equipment_category || "Laptop",
	item_name: spec.item_name || "",
	delivery_location: spec.delivery_location || (props.view.request_information || {}).delivery_location || "",
	latest_delivery_date: spec.latest_delivery_date || requisitionLatest.value || "",
});

// One row per approved requirement still to be covered, in this actor's own
// departments; every value stays as typed until the actor changes it.
const rows = computed(() => ((props.view.equipment || {}).add_rows || []).filter((r) => r.editable && r.quantity > 0));
const entries = reactive({});
for (const row of rows.value) entries[row.drawdown_line_id] = { use: true, quantity: String(row.quantity), intended_use: "" };
function entry(row) {
	if (!entries[row.drawdown_line_id]) entries[row.drawdown_line_id] = { use: true, quantity: String(row.quantity), intended_use: "" };
	return entries[row.drawdown_line_id];
}
const chosen = computed(() => rows.value.filter((r) => entry(r).use));

const confirmLabel = computed(() => {
	if (props.mode === "shared") return "Save shared details";
	return chosen.value.length === 1 ? "Add equipment row" : `Add ${chosen.value.length} equipment rows`;
});

const error = computed(() => (ctx.commandError.value && ctx.commandError.value.label === LABEL ? ctx.commandError.value : null));
// Edits after a refusal clear it: the server's verdict applied to the values it saw.
const touched = ref(false);
watch([shared, entries], () => {
	touched.value = true;
}, { deep: true });
const rowErrors = computed(() => (!touched.value && error.value && error.value.detail && error.value.detail.rows) || {});
function rowError(row) {
	return rowErrors.value[row.drawdown_line_id] || "";
}
function sharedError(field) {
	const fields = !touched.value && error.value && error.value.detail && error.value.detail.fields;
	return (fields && fields[field]) || "";
}
const mismatch = computed(() => (!touched.value && error.value && error.value.code === "REQ_BATCH_ITEM_INVALID" && error.value.detail && error.value.detail.rows ? error.value.message : ""));
const otherError = computed(() => (!touched.value && error.value && !(error.value.detail && (error.value.detail.rows || error.value.detail.fields)) ? error.value.message : ""));

const ready = computed(() => {
	if (!shared.item_name.trim() || !shared.equipment_category) return false;
	if (props.mode === "shared") return true;
	if (!chosen.value.length) return false;
	if (Object.keys(rowErrors.value).length) return false;
	return chosen.value.every((r) => String(entry(r).quantity).trim() && entry(r).intended_use.trim());
});

async function submit() {
	touched.value = false;
	const base = { requisition: props.view.header.requisition, expected_record_version: props.view.package_record_version };
	const done =
		props.mode === "shared"
			? await ctx.run(LABEL, (key) => ctx.api.updateSharedItemDetails({ ...base, shared_values: { ...shared }, requisition_item_ids: spec.requisition_item_ids || [], idempotency_key: key }))
			: await ctx.run(LABEL, (key) =>
					ctx.api.addSameSpecificationItems({
						...base,
						shared_values: { ...shared },
						item_rows: chosen.value.map((r) => ({ drawdown_line_id: r.drawdown_line_id, quantity: String(entry(r).quantity).trim(), intended_use: entry(r).intended_use })),
						idempotency_key: key,
					})
				);
	if (done) emit("close");
	else touched.value = false;
}
</script>
