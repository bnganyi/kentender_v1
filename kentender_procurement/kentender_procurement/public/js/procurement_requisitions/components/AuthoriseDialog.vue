<!-- REQ-DES-09 — Authorisation confirmation: the material effects, in plain
     words, before the one authorising command. -->
<template>
	<DialogFrame title="Authorise this requisition?" :width="480" :busy="busy" testid="req-authorise-dialog" @close="$emit('close')">
		<div class="req-rule">
			<div class="kt-meta-row">
				<div><span class="kt-label">Quantity</span><span class="kt-meta-value" style="font-size: 14px">{{ confirmation.quantity }}</span></div>
				<div><span class="kt-label">Requisition value</span><span class="kt-meta-value" style="font-size: 14px">{{ confirmation.value }}</span></div>
			</div>
			<div class="kt-meta-row" style="margin-top: 10px">
				<div><span class="kt-label">Budget line</span><span class="kt-meta-value" style="font-size: 14px">{{ confirmation.budget_line }}</span></div>
				<div><span class="kt-label">Available after authorisation</span><span class="kt-meta-value" style="font-size: 14px">{{ confirmation.available_after }}</span></div>
			</div>
		</div>
		<p class="req-dialog-body">{{ confirmation.text }}</p>
		<Notice v-if="error" tone="critical"><span data-testid="req-authorise-error">{{ error }}</span></Notice>
		<template #actions>
			<button type="button" class="btn btn-secondary" :disabled="busy" @click="$emit('close')">Cancel</button>
			<button type="button" class="btn btn-primary" :disabled="busy" data-testid="req-authorise-confirm" @click="$emit('confirm')">{{ busy ? "Authorising…" : "Authorise requisition" }}</button>
		</template>
	</DialogFrame>
</template>

<script setup>
import DialogFrame from "./shared/DialogFrame.vue";
import Notice from "./shared/Notice.vue";

defineProps({ confirmation: { type: Object, required: true }, busy: { type: Boolean, default: false }, error: { type: String, default: "" } });
defineEmits(["close", "confirm"]);
</script>
