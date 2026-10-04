<!-- "Opening committee" (boards c1–c12, z1): who is on it and who is present. -->
<template>
	<div class="kt-region" :class="{ 'is-secondary': secondary }"><h2>Opening committee</h2>
		<table class="kt-table" data-testid="bop-committee-presence"><thead><tr><th>Member</th><th>Role on committee</th><th>Present</th></tr></thead><tbody>
			<tr v-for="m in members" :key="m.member_user" :data-user="m.member_user"><td>{{ m.full_name }}</td><td>{{ m.committee_role }}</td>
				<td v-if="m.present"><span class="kt-status is-live">Joined</span> {{ m.joined_label }}</td><td v-else><span class="kt-status is-pending">Not joined</span></td></tr>
		</tbody></table>
		<div v-if="$slots.default" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><slot /></div>
	</div>
</template>

<script setup>
defineProps({ members: { type: Array, default: () => [] }, secondary: Boolean });
</script>
