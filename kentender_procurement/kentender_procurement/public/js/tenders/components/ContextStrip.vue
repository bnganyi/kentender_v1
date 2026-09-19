<!-- TPR-DES-03 context strip: four inherited facts (§4.3 — never editable)
     and the "View authorised requisition" drawer trigger. -->
<template>
	<div class="tnd-context" data-testid="tnd-context">
		<div class="tnd-context-facts">
			<div class="tnd-fact"><div class="kt-label">Purchase</div><div class="tnd-fact-value">{{ context.purchase }}</div></div>
			<div class="tnd-fact"><div class="kt-label">Method</div><div class="tnd-fact-value">{{ context.method }}</div></div>
			<div class="tnd-fact"><div class="kt-label">Quantity</div><div class="tnd-fact-value">{{ context.quantity }}</div></div>
			<div class="tnd-fact"><div class="kt-label">Latest delivery</div><div class="tnd-fact-value">{{ context.latest_delivery }}</div></div>
		</div>
		<button type="button" class="kt-btn kt-btn-secondary tnd-inline-btn" data-testid="tnd-open-drawer" @click="$emit('open-drawer')">
			<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/></svg>
			View authorised requisition
		</button>
	</div>
</template>

<script setup>
defineProps({ context: { type: Object, default: () => ({}) } });
defineEmits(["open-drawer"]);
</script>
