<!-- What a member signs (boards r2, r3, r5): each bid page, the price, the
     opening record's pages and its final page, with what the member does. -->
<template>
	<table class="table" data-testid="bop-signing"><thead><tr><th>What</th><th>Page</th><th>What you do</th><th v-if="withStatus">Status</th></tr></thead><tbody>
		<tr v-for="(r, i) in rows" :key="i"><td>{{ version && r.what === "Opening record" ? `Opening record, version ${version}` : r.what }}</td><td>{{ r.page }}</td><td>{{ r.does }}</td>
			<td v-if="withStatus"><span v-if="r.signed" class="kt-status is-live">Signed</span><span v-else class="kt-status is-attention">Awaiting your signature</span></td></tr>
	</tbody></table>
</template>

<script setup>
defineProps({ rows: { type: Array, default: () => [] }, withStatus: Boolean, version: { type: Number, default: 0 } });
</script>
