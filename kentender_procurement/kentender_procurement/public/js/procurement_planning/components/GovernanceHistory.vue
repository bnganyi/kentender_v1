<!-- U11-decisions — every review so far (Finance, Preparation, Accounting
     Officer adoption, Statutory approval) in order, plus the current open
     stage as "Awaiting decision"; a later stage's row never overwrites an
     earlier one's (mirrors FinanceHistory's own U10-history table). -->
<template>
	<div class="kt-card kt-blueprint pln-card-pad" data-testid="rvw-history">
		<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
		<i class="kt-corner bl"></i><i class="kt-corner br"></i>
		<div class="kt-card-title">Decisions</div>
		<table class="pln-table">
			<thead><tr><th>Stage</th><th>Actor</th><th>Capacity</th><th>Decision</th><th>Date</th></tr></thead>
			<tbody>
				<tr v-for="row in rows" :key="row.stage" :data-testid="`rvw-history-${slug(row.stage)}`">
					<td>{{ row.stage }}</td>
					<td>{{ row.actor }}</td>
					<td>{{ row.capacity }}</td>
					<td>
						<span class="kt-status" :class="row.outcome === 'Awaiting decision' ? 'is-pending' : row.outcome === 'Returned' ? 'is-critical' : 'is-live'">{{ row.outcome }}</span>
					</td>
					<td>{{ row.date_display }}</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	history: { type: Array, default: () => [] },
});

const rows = computed(() => props.history);

function slug(stage) {
	return stage.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}
</script>
