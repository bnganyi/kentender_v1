<!-- "Committee signatures" (boards r3, r4, r6, h1, h2, h5): each member's
     signature on the current version. -->
<template>
	<div class="kt-region" :class="{ 'is-secondary': secondary }"><h2>Committee signatures</h2>
		<table class="table" data-testid="bop-signatures"><thead><tr><th>Member</th><th>Role on committee</th><th>{{ column || `Version ${version}` }}</th></tr></thead><tbody>
			<tr v-for="s in rows" :key="s.member"><td>{{ s.member }}</td><td>{{ s.role }}</td><td><span v-if="s.signed" class="kt-status is-live">Signed</span><template v-if="s.signed"> {{ s.signed_label }}</template><span v-else class="kt-status is-attention">Awaiting signature</span></td></tr>
		</tbody></table>
		<div v-if="$slots.default" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><slot /></div>
	</div>
</template>

<script setup>
defineProps({ rows: { type: Array, default: () => [] }, version: { type: Number, default: 1 }, column: { type: String, default: "" }, secondary: Boolean });
</script>
