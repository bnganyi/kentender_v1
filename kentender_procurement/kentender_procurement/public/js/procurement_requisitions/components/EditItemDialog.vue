<!-- "Edit quantity and use" for one source-linked item (§13.4 Complete
     variant). Category, name and delivery belong to the shared details and are
     not repeated here. The quantity typed here is the only place it changes; a
     quantity above what remains is refused with the real limit named (v1.15). -->
<template>
	<DialogFrame title="Edit quantity and use" :width="480" :busy="busy" testid="req-item-dialog" @close="$emit('close')">
		<p class="req-dialog-body">{{ item.item_name }} · {{ item.approved_requirement }}</p>
		<div class="field">
			<label for="req-item-quantity">Quantity (Each)</label>
			<input id="req-item-quantity" v-model="quantity" class="input" :class="{ 'is-invalid': quantityError }" inputmode="numeric" data-testid="req-item-quantity" />
			<span v-if="quantityError" class="req-field-error" data-testid="req-item-quantity-error">{{ quantityError }}</span>
		</div>
		<div class="field">
			<label for="req-item-use">Intended use</label>
			<textarea id="req-item-use" v-model="intendedUse" class="input" rows="3" :class="{ 'is-invalid': fieldError('intended_use') }" data-testid="req-item-use"></textarea>
			<span v-if="fieldError('intended_use')" class="req-field-error">{{ fieldError("intended_use") }}</span>
		</div>
		<Notice v-if="otherError" tone="critical">{{ otherError }}</Notice>
		<template #actions>
			<button type="button" class="btn btn-secondary" :disabled="busy" @click="$emit('close')">Cancel</button>
			<button type="button" class="btn btn-primary" :disabled="busy" data-testid="req-item-dialog-confirm" @click="submit">Save item</button>
		</template>
	</DialogFrame>
</template>

<script setup>
import { computed, ref } from "vue";
import { useReq } from "../data/context.js";
import DialogFrame from "./shared/DialogFrame.vue";
import Notice from "./shared/Notice.vue";

const props = defineProps({ view: { type: Object, required: true }, item: { type: Object, required: true } });
const emit = defineEmits(["close"]);
const ctx = useReq();
const busy = computed(() => ctx.pending.value);
const quantity = ref(String(props.item.quantity_value));
const intendedUse = ref(props.item.intended_use || "");

const error = computed(() => (ctx.commandError.value && ctx.commandError.value.label === "update-item" ? ctx.commandError.value : null));
function fieldError(field) {
	return (error.value && error.value.detail && error.value.detail.fields && error.value.detail.fields[field]) || "";
}
// The limit sentence the server returns for this item's requirement
// (REQ_QUANTITY_EXCEEDS_AVAILABLE) sits beside the quantity it refers to.
const quantityError = computed(() => {
	const detail = (error.value && error.value.detail) || {};
	return fieldError("quantity") || (detail.rows && detail.rows[props.item.drawdown_line_id]) || "";
});
const otherError = computed(() => (error.value && !(error.value.detail && (error.value.detail.fields || error.value.detail.rows)) ? error.value.message : ""));

async function submit() {
	const done = await ctx.run("update-item", (key) =>
		ctx.api.updateItem({
			requisition: props.view.header.requisition,
			requisition_item_id: props.item.requisition_item_id,
			item_values: { quantity: quantity.value.trim(), intended_use: intendedUse.value },
			expected_record_version: props.view.package_record_version,
			idempotency_key: key,
		})
	);
	if (done) emit("close");
}
</script>
