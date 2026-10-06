<!-- Forbidden and Not found for STD Templates (KT-STD-001 §3A). The STD
     boards draw no common-state card, so these reuse the boards' own read-
     failure notice pattern (STD-DES-01R/02R) — a registered departure. -->
<template>
	<div class="kt-page stdt-page" :data-testid="`stdt-state-${kind}`">
		<div class="kt-notice is-critical" style="align-items: center" role="alert">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect v-if="kind === 'forbidden'" width="18" height="11" x="3" y="11" rx="2"></rect><path v-if="kind === 'forbidden'" d="M7 11V7a5 5 0 0 1 10 0v4"></path><circle v-if="kind !== 'forbidden'" cx="11" cy="11" r="8"></circle><path v-if="kind !== 'forbidden'" d="m21 21-4.3-4.3"></path></svg>
			<div class="kt-notice-body" style="flex: 1"><strong>{{ heading }}</strong><div style="margin-top: 4px">{{ text }}</div></div>
			<button v-if="kind === 'not-found'" type="button" class="btn btn-secondary" data-testid="stdt-state-back" @click="$emit('back')">Back to STD Templates</button>
		</div>
	</div>
</template>

<script setup>
defineProps({ kind: { type: String, required: true }, heading: { type: String, default: "" }, text: { type: String, default: "" } });
defineEmits(["back"]);
</script>
