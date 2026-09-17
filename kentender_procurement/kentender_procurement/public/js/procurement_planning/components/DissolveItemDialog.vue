<!-- PLN-CHG-001 v1.23 §10.8 U09-REMOVE. Confirms `DissolvePlanItem` on a
     Draft item; the caller owns the API call and the idempotency key. A
     scope-locked item cannot reach this dialog — the caller gates that before
     offering it.

     The two things a Planner needs to know before removing a purchase are
     where its requirements go and whether any money moves. Both are stated. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="pln-dissolve-item-dialog">
		<div class="kt-dialog" role="dialog" aria-modal="true" aria-labelledby="pln-dissolve-item-title">
			<div id="pln-dissolve-item-title" class="kt-dialog-title">Remove this purchase?</div>
			<table v-if="sources.length" class="kt-table" data-testid="pln-dissolve-sources">
				<thead><tr><th>Requirement</th><th>Department</th><th class="is-num">Allocation</th></tr></thead>
				<tbody>
					<tr v-for="row in sources" :key="row.requirement + row.department">
						<td>{{ row.requirement }}</td>
						<td>{{ row.department }}</td>
						<td class="is-num">{{ row.amount_display }}</td>
					</tr>
				</tbody>
			</table>
			<p class="pln-dialog-lede">
				These requirements will return to this draft plan so they can be added again. No funds are released.
			</p>
			<p v-if="error" class="pln-dialog-error" role="alert" data-testid="pln-dissolve-item-error">
				{{ error }}
			</p>
			<div class="kt-dialog-actions">
				<button class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">
					Cancel
				</button>
				<button
					class="kt-btn kt-btn-primary" data-testid="pln-dissolve-item-confirm"
					:disabled="pending" @click="$emit('confirm')"
				>
					Remove purchase
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
defineProps({
	pending: Boolean,
	error: String,
	sources: { type: Array, default: () => [] },
});
defineEmits(["confirm", "cancel"]);
</script>
