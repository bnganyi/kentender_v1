<!-- "Register" (boards c6–c9, r1, r4, r6, h1, h2): each bid as it was read aloud and recorded. -->
<template>
	<div class="kt-region" :class="{ 'is-secondary': secondary }"><h2>Register</h2>
		<table class="table" data-testid="bop-register"><thead><tr><th>No.</th><th>Tenderer</th><th class="is-num">Submitted total</th><th>Security given</th><th>Recorded at</th></tr></thead><tbody>
			<tr v-for="r in rows" :key="r.entry || r.number"><td>{{ r.number }}</td><td>{{ r.tenderer }}</td><td class="is-num">{{ r.submitted_total }}</td><td>{{ r.security_given }}</td><td>{{ r.recorded_label }}</td></tr>
		</tbody></table>
		<div v-if="!rows.length" class="kt-empty" style="border-top:0;padding:16px"><p style="margin:0;font-size:14px;max-width:75ch;text-wrap:pretty">{{ emptyText }}</p></div>
		<p v-if="note" style="margin:10px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty">{{ note }}</p>
		<slot />
	</div>
</template>

<script setup>
defineProps({ rows: { type: Array, default: () => [] }, secondary: Boolean, emptyText: { type: String, default: "Nothing recorded yet." }, note: { type: String, default: "" } });
</script>
