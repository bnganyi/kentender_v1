<!-- A full inline state (KT-STD-001 §3A): Not found or a load failure. Same
     markup as the Tenders common states, so the opening sits in its page. -->
<template>
	<div class="tnd-page">
		<div class="card blueprint tnd-state-card" :data-testid="`bop-state-${kind}`">
			<i class="corner tl"></i><i class="corner tr"></i><i class="corner bl"></i><i class="corner br"></i>
			<div class="tnd-state-head">
				<div class="tnd-state-icon is-critical"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg></div>
				<div class="tnd-state-kind is-critical">{{ copy.label }}</div>
			</div>
			<h2>{{ copy.heading }}</h2>
			<p class="tnd-card-body">{{ text || copy.text }}</p>
			<div class="tnd-actions"><button type="button" class="btn btn-secondary" :data-testid="`bop-state-action-${copy.action.key}`" @click="$emit('action', copy.action.key)">{{ copy.action.label }}</button></div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({ kind: { type: String, required: true }, text: { type: String, default: "" } });
defineEmits(["action"]);
const COPY = {
	"not-found": { label: "Not found", heading: "Bid opening not found", text: "This bid opening is unavailable or you do not have permission to view it.", action: { key: "back", label: "Back to Tender" } },
	failure: { label: "Load failure", heading: "The bid opening could not be loaded", text: "Try again.", action: { key: "retry", label: "Try again" } },
};
const copy = computed(() => COPY[props.kind] || COPY.failure);
</script>
