<!-- "Add member" (board a1): choose an eligible person and their role on the
     committee. The boards draw only the button; this picker is a registered
     departure (tests/ui/fidelity/departures/bid-opening.js). -->
<template>
	<div class="kt-dialog-backdrop" data-testid="bop-add-member-dialog" @keydown.esc.stop="$emit('cancel')">
		<div ref="dialogEl" class="kt-dialog bop-dialog" role="dialog" aria-modal="true" aria-labelledby="bop-add-member-title" tabindex="-1">
			<div id="bop-add-member-title" class="kt-dialog-title">Add member</div>
			<div class="bop-dialog-body">
				<div class="kt-field"><label for="bop-add-member-person">Member</label>
					<select id="bop-add-member-person" v-model="user" class="kt-input" data-testid="bop-add-member-person">
						<option value="" disabled>Choose a person</option>
						<option v-for="c in available" :key="c.user" :value="c.user">{{ c.full_name }} · {{ c.designation }}</option>
					</select>
				</div>
				<div class="kt-field"><label for="bop-add-member-role">Role on committee</label>
					<select id="bop-add-member-role" v-model="role" class="kt-input" data-testid="bop-add-member-role">
						<option v-for="r in roles" :key="r" :value="r">{{ r }}</option>
					</select>
				</div>
				<p v-if="involved" class="bop-field-error" data-testid="bop-add-member-involved">{{ chosen.full_name }} was involved in processing this Tender and cannot be the independent member.</p>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="!user || involved" data-testid="bop-add-member-confirm" @click="$emit('confirm', { user, committee_role: role })">Add member</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from "vue";

const props = defineProps({ candidates: { type: Array, default: () => [] }, chosen: { type: Array, default: () => [] }, suggestedRole: { type: String, default: "Member" } });
defineEmits(["confirm", "cancel"]);
const roles = ["Chair and recorder", "Chair", "Recorder", "Member", "Independent member"];
const dialogEl = ref(null);
const user = ref("");
const role = ref(props.suggestedRole);
const available = computed(() => props.candidates.filter((c) => !props.chosen.includes(c.user)));
const chosen = computed(() => props.candidates.find((c) => c.user === user.value) || {});
const involved = computed(() => role.value === "Independent member" && !!chosen.value.involved);
onMounted(() => nextTick(() => dialogEl.value && dialogEl.value.focus()));
</script>
