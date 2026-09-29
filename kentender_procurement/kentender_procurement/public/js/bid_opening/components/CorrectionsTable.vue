<!-- "Corrections" (board h5): what was added after completion, by whom and why. -->
<template>
	<div class="kt-region" :class="{ 'is-secondary': secondary }"><h2>Corrections</h2>
		<table class="kt-table" data-testid="bop-corrections"><thead><tr><th>Added</th><th>By</th><th>Kind</th><th>Correction</th><th>Reason</th></tr></thead><tbody>
			<tr v-for="c in rows" :key="c.supplement_id"><td>{{ c.added_label }}</td><td>{{ c.author }}</td><td>{{ c.kind }}</td><td>{{ c.correct_information }}</td><td>{{ c.reason }}</td></tr>
		</tbody></table>
	</div>
</template>

<script setup>
defineProps({ rows: { type: Array, default: () => [] }, secondary: Boolean });
</script>
