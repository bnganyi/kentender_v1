<!-- PLN-CHG-001 v1.18 §7.2, ported class-for-class from
     U21-late-explanation-history: read-only, no retroactive date editor.
     `entries` arrives oldest-first (plan_read.py's own order); this renders
     the most recent first and marks any earlier, superseded explanation. -->
<template>
	<div class="pln-late-explanation-history" data-testid="pln-late-explanation-history">
		<div v-for="(entry, index) in ordered" :key="entry.name || index" class="kt-card" style="padding: 24px; max-width: 560px; margin-bottom: 16px">
			<span v-if="index > 0" class="kt-status is-pending" data-testid="pln-late-explanation-superseded">Superseded</span>
			<div class="pln-facts-row" style="margin-bottom: 16px">
				<div class="pln-fact">
					<span class="kt-label">Initial Plan Version</span>
					<span class="pln-fact-val">{{ initialVersion }}</span>
				</div>
				<div class="pln-fact">
					<span class="kt-label">Financial year started</span>
					<span class="pln-fact-val">{{ financialYearStarted }}</span>
				</div>
				<div class="pln-fact">
					<span class="kt-label">Activated</span>
					<span class="pln-fact-val">{{ activatedAt }}</span>
				</div>
			</div>
			<p style="margin: 0 0 16px">{{ entry.reason }}</p>
			<div class="pln-facts-row">
				<div class="pln-fact">
					<span class="kt-label">Recorded by</span>
					<span class="pln-fact-val">{{ entry.actor }}</span>
				</div>
				<div class="pln-fact">
					<span class="kt-label">Recorded</span>
					<span class="pln-fact-val">{{ entry.recordedAt }}</span>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	initialVersion: { type: [String, Number], default: "" },
	financialYearStarted: { type: String, default: "" },
	activatedAt: { type: String, default: "" },
	entries: { type: Array, default: () => [] },
});

const ordered = computed(() => [...props.entries].reverse());
</script>
