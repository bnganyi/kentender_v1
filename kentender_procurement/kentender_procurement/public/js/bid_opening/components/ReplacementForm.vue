<!-- Appoint a replacement (BOP-CHG-001 v0.10 §10 branch 1): the Accounting
     Officer replaces a member who cannot return; the reason is required. Not
     drawn on a board (the boards stop at "appoint a replacement"); a
     registered departure. The successor is searched on the server through the
     same source as Add member, for the role the absent member held. -->
<template>
	<div class="kt-region" data-testid="bop-replacement"><h2>Appoint a replacement</h2>
		<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px 24px;max-width:1000px">
			<div class="field"><label for="bop-replace-who">Replace</label><select id="bop-replace-who" v-model="replaced" class="input"><option v-for="m in absent" :key="m.member_user" :value="m.member_user">{{ m.full_name }} · {{ m.committee_role }}</option></select></div>
			<div class="field"><label for="bop-replace-with">With</label>
				<RecordPickerHost
					v-model="successor"
					input-id="bop-replace-with"
					source="bid_opening.committee_member"
					noun="person"
					plural="people"
					placeholder="Search by name, role or department"
					:context="context"
					:value-label="picked.label || ''"
					@change="onPicked"
				/>
			</div>
			<div class="field" style="grid-column:1 / -1"><label for="bop-replace-reason">Reason</label><input id="bop-replace-reason" v-model="reason" class="input" data-testid="bop-replace-reason"></div>
		</div>
		<p v-if="error" class="bop-field-error" role="alert">{{ error }}</p>
		<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><button type="button" class="btn btn-primary" :disabled="pending || !successor || !!picked.disabled_reason || !reason.trim()" data-testid="bop-replace-confirm" @click="appoint">Appoint replacement</button></div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import RecordPickerHost from "../../record_picker_shared/RecordPickerHost.vue";

const props = defineProps({ tender: { type: String, required: true }, members: { type: Array, default: () => [] }, pending: Boolean, error: { type: String, default: "" } });
const emit = defineEmits(["appoint"]);
const absent = computed(() => props.members.filter((m) => !m.present));
const replaced = ref((absent.value[0] || {}).member_user || "");
const successor = ref(null);
const picked = ref({});
const reason = ref("");
// The successor takes the absent member's role; everyone on the committee now is already taken.
const context = computed(() => ({
	tender: props.tender,
	role: (props.members.find((m) => m.member_user === replaced.value) || {}).committee_role || "Member",
	taken: props.members.map((m) => m.member_user),
}));
function onPicked(row) {
	picked.value = row || {};
}
function appoint() {
	const roster = props.members.map((m) => (m.member_user === replaced.value ? { user: successor.value, committee_role: m.committee_role } : { user: m.member_user, committee_role: m.committee_role }));
	emit("appoint", { members: JSON.stringify(roster), reason: reason.value.trim() });
}
</script>
