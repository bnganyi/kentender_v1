<!-- TPR-DES-05/06/07 key facts (§10.6 item 3): the boards' four-column
     label grid — a label above each value, no cards, icons or badges. The
     facts and their order are the server's. -->
<template>
	<div class="tnd-section" data-testid="tnd-key-facts">
		<div class="tnd-fact-grid">
			<div v-for="fact in facts" :key="fact.label" class="tnd-fact"><div class="kt-label">{{ fact.label }}</div><div class="tnd-fact-value">{{ fact.value || "—" }}</div></div>
		</div>
	</div>
</template>

<script setup>
defineProps({ facts: { type: Array, default: () => [] } });
</script>
