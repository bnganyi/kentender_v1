<!-- TPR-DES-03 · Task 3 — Price schedule (§8.3, §13.5): no officer input.
     Generated rows with supplier placeholders only; the authorised value is
     never copied here (TPR-AC-013). -->
<template>
	<div>
		<p class="tpr-muted" style="margin: 0">Price currency is read-only KES. Prices are fixed for the contract period; taxes are shown separately. The authorised internal value is not copied into this schedule.</p>
		<table class="kt-table" data-testid="tpr-price-schedule">
			<thead><tr><th>Item</th><th class="tpr-num">Qty</th><th>Unit</th><th>Unit price</th><th>Tax</th><th>Line total</th></tr></thead>
			<tbody>
				<tr v-for="row in schedule.rows || []" :key="row.line">
					<td>{{ row.description }}</td><td class="tpr-num">{{ row.quantity }}</td><td>{{ row.unit }}</td><td class="tpr-muted">{{ row.unit_price }}</td><td class="tpr-muted">{{ row.tax }}</td><td class="tpr-muted">{{ row.line_total }}</td>
				</tr>
			</tbody>
			<tfoot><tr><td colspan="5" style="text-align: right; font-family: var(--font-heading); font-weight: 600">Tender total</td><td class="tpr-muted">{{ schedule.tender_total }}</td></tr></tfoot>
		</table>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({ editor: { type: Object, default: () => ({}) } });
const schedule = computed(() => (props.editor.generated || {}).price_schedule || {});
</script>
