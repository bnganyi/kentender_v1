<!-- "Edit quantity and use" for one source-linked equipment row (§13.4
     Complete variant). Category, name and delivery belong to the shared
     details and are not repeated here. -->
<template>
	<DialogFrame title="Edit quantity and use" :width="480" :busy="busy" testid="req-item-dialog" @close="$emit('close')">
		<p class="req-dialog-body">{{ item.item_name }} · {{ item.approved_requirement }}</p>
		<div class="kt-field">
			<label for="req-item-quantity">Quantity (Each)</label>
			<input id="req-item-quantity" v-model="quantity" class="kt-input" :class="{ 'is-invalid': fieldError('quantity') }" inputmode="numeric" data-testid="req-item-quantity" />
			<span v-if="fieldError('quantity')" class="req-field-error">{{ fieldError("quantity") }}</span>
		</div>
		<div class="kt-field">
			<label for="req-item-use">Intended use</label>
			<textarea id="req-item-use" v-model="intendedUse" class="kt-input" rows="3" :class="{ 'is-invalid': fieldError('intended_use') }" data-testid="req-item-use"></textarea>
			<span v-if="fieldError('intended_use')" class="req-field-error">{{ fieldError("intended_use") }}</span>
		</div>
		<Notice v-if="otherError" tone="critical">{{ otherError }}</Notice>
		<template #actions>
			<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" @click="$emit('close')">Cancel</button>
			<button type="button" class="kt-btn kt-btn-primary" :disabled="busy" data-testid="req-item-dialog-confirm" @click="submit">Save equipment row</button>
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
const otherError = computed(() => (error.value && !(error.value.detail && error.value.detail.fields) ? error.value.message : ""));

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
