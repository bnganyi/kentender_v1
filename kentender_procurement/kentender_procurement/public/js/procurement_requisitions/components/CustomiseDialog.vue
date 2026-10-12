<!-- REQ-CHG-001 v1.18 §5.7A — Customise for one item: pick the item that needs its own value; the requirement is
     copied for it and taken out of the shared row. No other item changes. -->
<template>
	<DialogFrame title="Customise for one item" :width="480" :busy="busy" testid="req-customise-dialog" @close="$emit('close')">
		<p class="req-dialog-body">{{ row.label || row.check_type }} applies to {{ names }}. Choose the item that needs its own value; the others keep the shared one.</p>
		<fieldset class="field req-fieldset">
			<label v-for="item in covered" :key="item.requisition_item_id" class="kt-checkbox req-check-line">
				<input v-model="chosen" type="radio" :value="item.requisition_item_id" data-testid="req-customise-item" /><span class="box"></span>{{ item.item_name }} — {{ item.approved_requirement }}
			</label>
		</fieldset>
		<Notice v-if="error" tone="critical">{{ error }}</Notice>
		<template #actions>
			<button type="button" class="btn btn-secondary" :disabled="busy" @click="$emit('close')">Cancel</button>
			<button type="button" class="btn btn-primary" :disabled="busy || !chosen" data-testid="req-customise-confirm" @click="confirm">Customise</button>
		</template>
	</DialogFrame>
</template>

<script setup>
import { computed, ref } from "vue";
import { useReq } from "../data/context.js";
import DialogFrame from "./shared/DialogFrame.vue";
import Notice from "./shared/Notice.vue";

const props = defineProps({ view: { type: Object, required: true }, row: { type: Object, required: true }, requirementId: { type: String, required: true } });
const emit = defineEmits(["close", "done"]);
const ctx = useReq();
const busy = computed(() => ctx.pending.value);
const chosen = ref("");
const covered = computed(() => ((props.view.equipment || {}).rows || []).filter((i) => (props.row.applies_to_item_ids || []).includes(i.requisition_item_id)));
const names = computed(() => [...new Set(covered.value.map((i) => i.item_name))].join(", "));
const error = computed(() => (ctx.commandError.value && ctx.commandError.value.label === "customise" ? ctx.commandError.value.message : ""));

async function confirm() {
	const done = await ctx.run("customise", (key) =>
		ctx.api.customiseRequirement({ requisition: props.view.header.requisition, requirement_id: props.requirementId, requisition_item_id: chosen.value, expected_record_version: props.view.package_record_version, idempotency_key: key })
	);
	if (done) {
		emit("done");
		emit("close");
	}
}
</script>
