<!-- §12.7 — the Form Plan Items dialog, rendering PLN-DES-08 class-for-class:
     the source table (pre-checked, no search), the one-each/one-combined
     formation choice, and the result preview. No partial quantity, amount
     override, lot split, Strategy, method or Finance control. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="pln-form-dialog">
		<div class="kt-dialog" role="dialog" aria-modal="true" aria-labelledby="pln-form-title">
			<div id="pln-form-title" class="kt-dialog-title">Form Plan Items</div>
			<p class="pln-dialog-lede">
				Select accepted departmental entries and choose how they should form
				procurement packages.
			</p>

			<table class="pln-table">
				<thead>
					<tr>
						<th></th><th>Requirement</th><th>Department</th>
						<th>Classification</th><th class="pln-num">Quantity</th>
						<th class="pln-num">Amount</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in entries" :key="row.dpp_entry">
						<td>
							<input
								type="checkbox"
								:data-testid="`pln-form-select-${row.dpp_entry}`"
								:checked="selected.has(row.dpp_entry)"
								@change="toggle(row.dpp_entry)"
							/>
						</td>
						<td>{{ row.title }}</td>
						<td>{{ row.department }}</td>
						<td>{{ row.classification }}</td>
						<td class="pln-num">{{ row.quantity_display }}</td>
						<td class="pln-num">{{ row.amount_display }}</td>
					</tr>
				</tbody>
			</table>

			<div v-if="selectedRows.length > 1" class="pln-dialog-section">
				<p class="pln-section-label">Formation</p>
				<div class="pln-radio-group">
					<label class="pln-radio-option">
						<input type="radio" value="each" v-model="mode" data-testid="pln-form-mode-each" />
						Create one Plan Item for each selected requirement
					</label>
					<label class="pln-radio-option">
						<input
							type="radio" value="combined" v-model="mode"
							data-testid="pln-form-mode-combined"
						/>
						Create one combined Plan Item from all selected requirements
					</label>
				</div>
			</div>

			<div class="pln-dialog-section">
				<p class="pln-section-label">Summary</p>
				<div class="pln-summary-box">
					<div class="pln-result-row">
						<span>Selected entries</span><strong>{{ selectedRows.length }}</strong>
					</div>
					<div class="pln-result-row">
						<span>Plan Items to create</span>
						<strong>{{ effectiveMode === "each" ? selectedRows.length : Math.min(selectedRows.length, 1) }}</strong>
					</div>
					<div class="pln-result-row">
						<span>Total value</span><strong>{{ totalDisplay }}</strong>
					</div>
				</div>
			</div>

			<p v-if="error" class="pln-dialog-error" role="alert" data-testid="pln-form-error">
				{{ error }}
			</p>

			<div class="kt-dialog-actions">
				<button class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">
					Cancel
				</button>
				<button
					class="kt-btn kt-btn-primary"
					data-testid="pln-form-confirm"
					:disabled="pending || !selectedRows.length"
					@click="confirm"
				>
					Create {{ effectiveMode === "each" ? selectedRows.length : Math.min(selectedRows.length, 1) }}
					Plan Item{{ effectiveMode === "each" && selectedRows.length !== 1 ? "s" : "" }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";

const props = defineProps({
	entries: { type: Array, default: () => [] },
	pending: Boolean,
	error: String,
});

const emit = defineEmits(["confirm", "cancel"]);

// every source starts pre-checked (§11.9 fixture): the Planner is forming
// items from what they already opened the dialog to act on.
const selected = reactive(new Set(props.entries.map((row) => row.dpp_entry)));
const mode = ref("each");

function toggle(dppEntry) {
	if (selected.has(dppEntry)) selected.delete(dppEntry);
	else selected.add(dppEntry);
}

const selectedRows = computed(() =>
	props.entries.filter((row) => selected.has(row.dpp_entry))
);

// §12.7 — one selected source creates one item without asking a second
// choice; the formation radio only matters once several are selected.
const effectiveMode = computed(() => (selectedRows.value.length > 1 ? mode.value : "each"));

const totalDisplay = computed(() => {
	const total = selectedRows.value.reduce(
		(sum, row) => sum + Number(row.amount_display.replace(/[^\d.]/g, "") || 0),
		0
	);
	return `KES ${total.toLocaleString("en-KE")}`;
});

function confirm() {
	emit(
		"confirm",
		selectedRows.value.map((row) => row.dpp_entry),
		effectiveMode.value
	);
}
</script>
