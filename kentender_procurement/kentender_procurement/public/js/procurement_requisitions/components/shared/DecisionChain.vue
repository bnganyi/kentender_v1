<!-- The board's read-only Decision / Correction chain (owner D2): recorded
     decisions and the stages not yet reached. -->
<template>
	<div class="req-rule" data-testid="req-decision-chain">
		<div class="kt-label" style="margin-bottom: 12px">{{ label }}</div>
		<div class="kt-timeline">
			<div v-for="(row, i) in rows" :key="row.title + i" class="kt-timeline-row">
				<div class="kt-timeline-dot-col">
					<i class="kt-timeline-dot" :class="row.tone"></i>
					<i v-if="i < rows.length - 1" class="kt-timeline-line" :class="{ 'is-upcoming': rows[i + 1].upcoming || row.tone === 'is-attention' }"></i>
				</div>
				<div class="kt-timeline-item">
					<div class="kt-timeline-item-title" :class="{ 'is-upcoming': row.upcoming }">{{ row.title }}</div>
					<div class="kt-timeline-item-meta">{{ row.meta }}</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
defineProps({ rows: { type: Array, required: true }, label: { type: String, default: "Decision chain" } });
</script>
