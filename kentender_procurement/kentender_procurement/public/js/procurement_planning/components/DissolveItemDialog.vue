<!-- PLN-CHG-001 v1.24 §10.8 U09-REMOVE, ported from Artboards-U09.dc.html.
     Confirms `DissolvePlanItem` on a Draft item; the caller owns the API
     call and the idempotency key. A scope-locked item cannot reach this
     dialog — the caller gates that before offering it.

     The heading names an action, not a record, so the dialog restates the
     exact item name and reference the artboard draws before anything else.
     The two things a Planner needs to know before removing a purchase are
     where its requirements go and whether any money moves. Both are stated.
     The requirements table itself stays to identity and allocation only —
     department is a page-level fact already visible behind this dialog. -->
<template>
	<div class="dialog-backdrop" data-testid="pln-dissolve-item-dialog">
		<div class="dialog" style="width: 520px" role="dialog" aria-modal="true" aria-labelledby="pln-dissolve-item-title">
			<div id="pln-dissolve-item-title" class="dialog-title">Remove this purchase?</div>
			<div v-if="item.title" class="pln-dialog-item" data-testid="pln-dissolve-item-summary">
				<div class="pln-task-title">{{ item.title }}</div>
				<div class="kt-muted pln-row-ref">{{ item.plan_item_id }}</div>
			</div>
			<table v-if="sources.length" class="table" data-testid="pln-dissolve-sources">
				<thead><tr><th>Requirement</th><th class="is-num">Allocation</th></tr></thead>
				<tbody>
					<tr v-for="row in sources" :key="row.requirement + row.department">
						<td>{{ row.requirement }}</td>
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
			<div class="dialog-actions">
				<button class="btn btn-secondary" :disabled="pending" @click="$emit('cancel')">
					Cancel
				</button>
				<button
					class="btn btn-primary kt-danger" data-testid="pln-dissolve-item-confirm"
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
	item: { type: Object, default: () => ({}) },
});
defineEmits(["confirm", "cancel"]);
</script>
