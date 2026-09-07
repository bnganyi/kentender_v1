<!-- §13.13 "Authorise Requisition?" — ported class-for-class: the total
     quantity/value line, the fixed commitment notice naming the Budget
     line(s) it reserves against, and Cancel/Authorise actions. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="req-authorise-dialog" @keydown.esc="$emit('cancel')">
		<div class="kt-dialog" role="dialog" aria-modal="true" ref="dialogEl" tabindex="-1">
			<div class="kt-dialog-title">Authorise Requisition?</div>
			<div class="req-context-body">
				{{ totalQuantity }} {{ unit }} · {{ money(totalValue) }}<br />
				This commits the Planning drawdown, reserves the requested value against {{ budgetLines }}, and creates the immutable Tender Preparation handoff.
			</div>
			<p v-if="error" class="req-field-error" role="alert">{{ error }}</p>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="req-authorise-dialog-confirm" @click="$emit('confirm')">Authorise</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from "vue";
import { formatMoney } from "../data/format.js";

const props = defineProps({
	task: { type: Object, required: true },
	pending: Boolean,
	error: { type: String, default: "" },
});

defineEmits(["confirm", "cancel"]);

const dialogEl = ref(null);
const drawdownLines = computed(() => (props.task.version || {}).drawdown_lines || []);
const totalQuantity = computed(() => drawdownLines.value.reduce((sum, l) => sum + (l.requested_quantity || 0), 0));
const totalValue = computed(() => drawdownLines.value.reduce((sum, l) => sum + (l.requested_value || 0), 0));
const unit = computed(() => drawdownLines.value[0]?.unit || "Each");
const budgetLines = computed(() => {
	const names = [...new Set((props.task.budget_affordability || []).map((r) => r.budget_line_label || r.budget_line))];
	return names.length ? names.join(", ") : "the approved Budget Line";
});

function money(amount) {
	return formatMoney(amount);
}

onMounted(() => {
	nextTick(() => dialogEl.value && dialogEl.value.focus());
});
</script>
