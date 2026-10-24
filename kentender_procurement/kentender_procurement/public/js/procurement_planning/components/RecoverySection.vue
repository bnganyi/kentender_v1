<!-- PLN-CHG-001 v1.32 §10.19 — Planning's account of the recovery of the unused allowance after a tender was cancelled, shared by the
     screens that show it (Procurement progress, Plan Item). It states the recovery in the specification's own local words, the exact
     quantities and values, the permitted next step, and identifiers only under Technical details. Nothing here restores, releases or
     edits anything; the next step is the ordinary requisition route, drawn only when the server says Planning currently offers it. -->
<template>
	<div class="kt-notice" :class="recovery.status === 'Needs attention' ? 'is-critical' : recovery.status === 'Completed' ? 'is-live' : 'is-warning'" :data-testid="prefix" :data-status="recovery.status">
		<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
			<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
		</svg>
		<div class="kt-notice-body">
			<strong :data-testid="`${prefix}-label`">{{ recovery.label }}</strong>
			<div class="kt-muted" style="font-size: 13px" :data-testid="`${prefix}-explanation`">{{ recovery.explanation }}</div>
			<div v-if="recovery.reason" style="font-size: 13px" :data-testid="`${prefix}-reason`">{{ recovery.reason }}</div>
			<table class="table" style="margin-top: 8px" :data-testid="`${prefix}-rows`">
				<thead><tr><th>Source</th><th>Quantity</th><th>Value</th><th v-if="recovery.status === 'Completed'">Restored</th></tr></thead>
				<tbody>
					<tr v-for="source in recovery.rows" :key="source.key"><td>{{ source.source }}</td><td>{{ source.quantity }}</td><td>{{ source.value }}</td><td v-if="recovery.status === 'Completed'">{{ source.restored }}</td></tr>
				</tbody>
			</table>
			<a v-if="recovery.next_step" href="#" :data-testid="`${prefix}-next`" @click.prevent="$emit('navigate', recovery.next_step.route)">{{ recovery.next_step.label }}</a>
			<details v-if="(recovery.technical || []).length" :data-testid="`${prefix}-technical`" style="margin-top: 6px">
				<summary style="font-size: 12px">Technical details</summary>
				<div v-for="item in recovery.technical" :key="`${item.label}-${item.value}`" class="kt-muted" style="font-size: 12px">{{ item.label }}: {{ item.value }}</div>
			</details>
		</div>
	</div>
</template>

<script setup>
defineProps({
	recovery: { type: Object, required: true },
	prefix: { type: String, default: "prg-recovery" },
});
defineEmits(["navigate"]);
</script>
