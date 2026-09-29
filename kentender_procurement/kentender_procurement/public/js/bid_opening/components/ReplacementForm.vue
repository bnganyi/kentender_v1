<!-- Appoint a replacement (BOP-CHG-001 v0.10 §10 branch 1): the Accounting
     Officer replaces a member who cannot return; the reason is required. Not
     drawn on a board (the boards stop at "appoint a replacement"); a
     registered departure. -->
<template>
	<div class="kt-region" data-testid="bop-replacement"><h2>Appoint a replacement</h2>
		<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px 24px;max-width:1000px">
			<div class="kt-field"><label for="bop-replace-who">Replace</label><select id="bop-replace-who" v-model="replaced" class="kt-input"><option v-for="m in absent" :key="m.member_user" :value="m.member_user">{{ m.full_name }} · {{ m.committee_role }}</option></select></div>
			<div class="kt-field"><label for="bop-replace-with">With</label><select id="bop-replace-with" v-model="successor" class="kt-input" data-testid="bop-replace-with"><option value="" disabled>Choose a person</option><option v-for="c in available" :key="c.user" :value="c.user">{{ c.full_name }} · {{ c.designation }}</option></select></div>
			<div class="kt-field" style="grid-column:1 / -1"><label for="bop-replace-reason">Reason</label><input id="bop-replace-reason" v-model="reason" class="kt-input" data-testid="bop-replace-reason"></div>
		</div>
		<p v-if="error" class="bop-field-error" role="alert">{{ error }}</p>
		<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><button type="button" class="kt-btn kt-btn-primary" :disabled="pending || !successor || !reason.trim()" data-testid="bop-replace-confirm" @click="appoint">Appoint replacement</button></div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";

const props = defineProps({ members: { type: Array, default: () => [] }, candidates: { type: Array, default: () => [] }, pending: Boolean, error: { type: String, default: "" } });
const emit = defineEmits(["appoint"]);
const absent = computed(() => props.members.filter((m) => !m.present));
const replaced = ref((absent.value[0] || {}).member_user || "");
const successor = ref("");
const reason = ref("");
const available = computed(() => props.candidates.filter((c) => !props.members.some((m) => m.member_user === c.user)));
function appoint() {
	const roster = props.members.map((m) => (m.member_user === replaced.value ? { user: successor.value, committee_role: m.committee_role } : { user: m.member_user, committee_role: m.committee_role }));
	emit("appoint", { members: JSON.stringify(roster), reason: reason.value.trim() });
}
</script>
