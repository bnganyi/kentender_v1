<!-- REQ-DES-04 — Add item (base, ONE-SOURCE, VALIDATION), and the same shared
     details in "Edit shared details" mode (REQ-CHG-001 v1.15 §13.5). One
     shared definition, one source-linked row per approved requirement; the
     quantity is typed here, once, and nowhere else. The server creates every
     row or none and names the limit when a quantity is too high. The dialog
     opens from the draft on screen — saved or not — so what the requester sees
     on the page is what the dialog starts from. -->
<template>
	<DialogFrame :title="mode === 'shared' ? 'Edit shared details' : 'Add item'" :width="640" :busy="busy" testid="req-add-dialog" @close="$emit('close')">
		<Notice v-if="mismatch" tone="warning"><span data-testid="req-add-mismatch">{{ mismatch }}</span></Notice>
		<Notice v-else-if="otherError" tone="critical">{{ otherError }}</Notice>
		<p v-if="mode === 'add'" class="kt-muted" style="font-size: 13px; margin: 0">Enter the shared item details once, then enter the quantity and intended use for each department.</p>
		<p v-else class="kt-muted" style="font-size: 13px; margin: 0" data-testid="req-shared-scope">Changes apply to the {{ (spec.requisition_item_ids || []).length }} approved requirement{{ (spec.requisition_item_ids || []).length === 1 ? "" : "s" }} listed under {{ spec.item_name }}. Quantity and intended use are edited on each row.</p>
		<div class="kt-label" style="margin-top: var(--kt-space-2)">Shared details</div>
		<div class="req-grid-2-tight">
			<div class="field">
				<label for="req-add-category">Equipment category</label>
				<select id="req-add-category" v-model="shared.equipment_category" class="input" :class="{ 'is-invalid': sharedError('equipment_category') }" data-testid="req-add-category">
					<option value="" disabled>Select a category</option>
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
					<option value="">Select a delivery location</option>
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
		<template v-if="mode === 'add'">
			<div v-if="rows.length > 1" class="kt-label" style="margin-top: var(--kt-space-3)">Department quantities and use</div>
			<table class="table" data-testid="req-add-rows">
				<thead><tr><th>Use</th><th>Department and approved requirement</th><th class="is-num">Quantity</th><th>Unit</th><th>Intended use</th></tr></thead>
				<tbody>
					<template v-for="row in rows" :key="row.drawdown_line_id">
						<tr data-testid="req-add-row">
							<td><label class="kt-checkbox"><input v-model="entry(row).use" type="checkbox" :aria-label="`Use ${row.department}`" /><span class="box"></span></label></td>
							<td>{{ row.department }}<div class="kt-label">{{ row.source_reference }}</div></td>
							<td class="is-num">
								<input v-model="entry(row).quantity" class="input" :class="{ 'is-invalid': rowError(row) }" style="max-width: 70px" inputmode="numeric" :placeholder="String(row.room)" :aria-label="`Quantity for ${row.department}`" :disabled="!entry(row).use" data-testid="req-add-quantity" />
							</td>
							<td>{{ row.unit }}</td>
							<td><input v-model="entry(row).intended_use" class="input" :aria-label="`Intended use for ${row.department}`" :disabled="!entry(row).use" data-testid="req-add-use" /></td>
						</tr>
						<tr v-if="rowError(row)">
							<td colspan="5"><div class="req-field-error" data-testid="req-add-row-error">{{ rowError(row) }}</div></td>
						</tr>
					</template>
				</tbody>
			</table>
			<p class="kt-muted" style="font-size: 13px; margin: 0">{{ hasRowErrors ? "Shared details are unchanged and retained. Nothing is added until every selected row is valid." : "The standard requirements for the chosen category will be ready for review in the next task." }}</p>
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

// `draft` is the request's title, delivery location and latest delivery date as
// the requester sees them on the page — typed but possibly not yet saved. The
// dialog starts from them and falls back to what is saved (v1.15 §13.5).
// In "shared" mode `group` is the set of items that share this specification; only they are changed.
const props = defineProps({ view: { type: Object, required: true }, mode: { type: String, default: "add" }, draft: { type: Object, default: () => ({}) }, group: { type: Object, default: null } });
const emit = defineEmits(["close", "added"]);
const ctx = useReq();
const busy = computed(() => ctx.pending.value);
const LABEL = props.mode === "shared" ? "update-shared" : "add-items";

const categories = computed(() => (props.view.catalogue || {}).categories || []);
const locations = computed(() => (props.view.request_information || {}).locations || []);
const saved = props.view.request_information || {};
const requisitionLatest = computed(() => props.draft.latest_delivery_date || saved.latest_delivery_date || "");
const spec = props.group || (props.view.equipment || {}).shared_specification || {};
const editing = props.mode === "shared";
const shared = reactive({
	// A new item starts with no category and no name (nothing is assumed about
	// what is being bought); editing the shared details starts from them.
	equipment_category: editing ? spec.equipment_category || "" : "",
	item_name: editing ? spec.item_name || "" : "",
	delivery_location: (editing && spec.delivery_location) || props.draft.delivery_location || saved.delivery_location || "",
	latest_delivery_date: (editing && spec.latest_delivery_date) || props.draft.latest_delivery_date || saved.latest_delivery_date || "",
});

// One row per approved requirement that can still take items, in this actor's
// own departments. Nothing is prefilled: the requester types each quantity, and
// the room left on that requirement is the placeholder.
const rows = computed(() => ((props.view.equipment || {}).add_rows || []).filter((r) => r.editable && r.room > 0));
const entries = reactive({});
function entry(row) {
	if (!entries[row.drawdown_line_id]) entries[row.drawdown_line_id] = { use: true, quantity: "", intended_use: "" };
	return entries[row.drawdown_line_id];
}
for (const row of rows.value) entry(row);
const chosen = computed(() => rows.value.filter((r) => entry(r).use));

const confirmLabel = computed(() => {
	if (props.mode === "shared") return "Save shared details";
	return chosen.value.length === 1 ? "Add item" : `Add ${chosen.value.length} items`;
});

const error = computed(() => (ctx.commandError.value && ctx.commandError.value.label === LABEL ? ctx.commandError.value : null));
// Edits after a refusal clear it: the server's verdict applied to the values it saw.
const touched = ref(false);
watch([shared, entries], () => {
	touched.value = true;
}, { deep: true });
const rowErrors = computed(() => (!touched.value && error.value && error.value.detail && error.value.detail.rows) || {});
const hasRowErrors = computed(() => Object.keys(rowErrors.value).length > 0);
function rowError(row) {
	return rowErrors.value[row.drawdown_line_id] || "";
}
function sharedError(field) {
	const fields = !touched.value && error.value && error.value.detail && error.value.detail.fields;
	return (fields && fields[field]) || "";
}
// A batch refusal that names no limit keeps one summary above the rows; a
// quantity above what remains is said once, beside its own row.
const mismatch = computed(() => (!touched.value && error.value && error.value.code === "REQ_BATCH_ITEM_INVALID" && error.value.detail && error.value.detail.rows && error.value.message ? error.value.message : ""));
const otherError = computed(() => (!touched.value && error.value && !(error.value.detail && (error.value.detail.rows || error.value.detail.fields)) ? error.value.message : ""));

const ready = computed(() => {
	if (!shared.item_name.trim() || !shared.equipment_category) return false;
	if (props.mode === "shared") return true;
	if (!chosen.value.length) return false;
	if (hasRowErrors.value) return false;
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
	if (done) {
		emit("added", { ...shared });
		emit("close");
	} else touched.value = false;
}
</script>
