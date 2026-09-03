<!-- NDS-DES-01/02/05/06/07/12 status pill. The label is always rendered, so
     colour is never the only carrier of state (§12.8). -->
<template>
	<span class="kt-status" :class="tone">
		<i class="dot"></i>{{ label }}
	</span>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({ label: { type: String, required: true } });

// The artboards map each state to one of four tones.
const TONES = {
	"Accepted for planning": "is-live",
	Accepted: "is-live",
	"Fully included": "is-live",
	Open: "is-live",
	Draft: "is-draft",
	New: "is-draft",
	Returned: "is-attention",
	"Awaiting planning clearance": "is-attention",
	Superseded: "is-attention",
};

const tone = computed(() => TONES[props.label] || "is-pending");
</script>
