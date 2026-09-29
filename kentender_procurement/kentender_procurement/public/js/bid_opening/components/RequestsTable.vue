<!-- "Requests and comments" (boards c9, c13b, h1): what attendees and members
     asked or said during the opening, and its outcome. -->
<template>
	<div class="kt-region" :class="{ 'is-secondary': secondary }"><h2>Requests and comments</h2>
		<table class="kt-table" data-testid="bop-requests"><thead><tr><th>Time</th><th>Who</th><th>What</th><th v-if="withResponse">Response</th><th>Outcome</th></tr></thead><tbody>
			<tr v-for="r in rows" :key="r.exception_id"><td>{{ r.recorded_label }}</td><td>{{ r.speaker_name }}</td><td>{{ r.observed_fact }}</td><td v-if="withResponse">{{ r.response }}</td>
				<td><span class="kt-status" :class="r.outcome === 'Recorded for Evaluation' ? 'is-pending' : 'is-live'">{{ r.outcome }}</span></td></tr>
		</tbody></table>
		<p v-if="!rows.length" style="margin:10px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty" data-testid="bop-requests-none">No requests or comments were recorded.</p>
		<p v-if="note" style="margin:10px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty">{{ note }}</p>
		<div v-if="$slots.default" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><slot /></div>
	</div>
</template>

<script setup>
defineProps({ rows: { type: Array, default: () => [] }, secondary: Boolean, withResponse: Boolean, note: { type: String, default: "" } });
</script>
