<!-- "Session so far" / "What happened" (boards c8, c10b, c12, r1, h1): the
     session's events in order, from the Proceedings record. -->
<template>
	<div class="kt-region" :class="{ 'is-secondary': secondary }"><h2>{{ title }}</h2>
		<table class="kt-table" data-testid="bop-session"><thead><tr><th>Time</th><th>Who</th><th>What happened</th></tr></thead><tbody>
			<tr v-for="(r, i) in rows" :key="i"><td>{{ r.time }}</td><td>{{ r.who }}</td><td>{{ r.what }}<template v-if="r.reported"> ({{ r.reported }})</template></td></tr>
		</tbody></table>
	</div>
</template>

<script setup>
defineProps({ rows: { type: Array, default: () => [] }, title: { type: String, default: "Session so far" }, secondary: { type: Boolean, default: true } });
</script>
