<!-- BOP-DES-01 Prepare opening (BOP-CHG-001 v0.10 §10.2; boards a1–a5), ported
     class-for-class: the Accounting Officer names the committee, then
     publishes how to attend. The guidance region is the server's answer, or a
     refused appointment's own guard (board a2) until the next change. -->
<template>
	<div class="kt-page" data-screen="prepare">
		<PageHead :title="opening.title" :desc="`${opening.tender_reference} · Bid opening · Submissions close ${opening.deadline_label}`" />
		<Guidance :answer="answer" :journey="data.journey" :pending="pending" @fix="onFix" />

		<!-- a1 / a2: naming the committee -->
		<template v-if="!committee.appointed">
			<div class="kt-region"><h2>Opening committee</h2>
				<table class="kt-table" data-testid="bop-committee-draft"><thead><tr><th>Member</th><th>Designation</th><th>Role on committee</th><th>Eligibility</th></tr></thead><tbody>
					<tr v-for="row in draftRows" :key="row.user" :data-user="row.user">
						<td>{{ row.full_name }}</td><td>{{ row.designation }}</td><td>{{ row.committee_role }}</td>
						<td><span class="kt-status is-live">Eligible</span><template v-if="row.committee_role === 'Independent member'"> <span style="font-size:13px;color:var(--color-neutral-800)">Not involved in processing this Tender and will not evaluate it</span></template>
							<button v-if="!blocked" type="button" class="kt-btn kt-btn-ghost bop-row-action" :data-testid="`bop-remove-${row.user}`" @click="removeRow(row.user)">Remove</button></td>
					</tr>
				</tbody></table>
				<div v-if="!blocked" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><button type="button" class="kt-btn kt-btn-secondary" data-testid="bop-add-member" @click="adding = true">Add member</button></div>
			</div>
			<div v-if="draft.length && !blocked" class="kt-decision">
				<p style="margin:0 0 var(--space-4);font-size:15px;max-width:75ch">Each member gets their own task to join the opening at {{ opening.deadline_label }}.<template v-if="independentName"> As the independent member, {{ independentName }} cannot later be appointed to evaluate this Tender.</template></p>
				<div style="display:flex;justify-content:flex-end;gap:12px"><button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bop-appoint" @click="$emit('appoint', draft)">Appoint committee</button></div>
			</div>
			<History title="Appointment history" summary="No appointments yet" />
		</template>

		<!-- a4: editing how to attend -->
		<template v-else-if="editingArrangements || (!arrangements.published && showForm)">
			<ArrangementsForm :initial="arrangements" :opening-label="opening.deadline_label" :published-label="arrangements.published_label || ''" :published="arrangements.published" :pending="pending" :error="error" @publish="$emit('publish', $event)" @cancel="editingArrangements = false" />
		</template>

		<!-- a3: appointed, not yet published -->
		<template v-else-if="!arrangements.published">
			<div class="kt-region"><h2>Opening committee</h2>
				<table class="kt-table" data-testid="bop-committee"><thead><tr><th>Member</th><th>Designation</th><th>Role on committee</th><th>Task to join</th></tr></thead><tbody>
					<tr v-for="m in committee.members" :key="m.member_user"><td>{{ m.full_name }}</td><td>{{ m.designation }}</td><td>{{ m.committee_role }}</td><td>Sent</td></tr>
				</tbody></table>
			</div>
			<div class="kt-region is-secondary"><h2>How to attend</h2>
				<div class="kt-group"><p style="margin:0 0 12px;font-size:14px;max-width:75ch;text-wrap:pretty">Not published. The public Tender page says “{{ arrangements.message }}”.</p><button type="button" class="kt-btn kt-btn-primary" data-testid="bop-open-arrangements" @click="showForm = true">Publish how to attend</button></div>
			</div>
			<History title="Appointment history" :summary="`Appointed ${committee.appointed_label} by ${committee.appointed_by}`" :rows="historyRows" />
		</template>

		<!-- a5: published -->
		<template v-else>
			<div class="kt-region"><h2>How to attend</h2>
				<div class="kt-meta-row" data-testid="bop-arrangements"><div><span class="kt-label">Attendance method</span><span class="kt-meta-value">{{ arrangements.attendance_method }}</span></div><div><span class="kt-label">Join opens</span><span class="kt-meta-value">{{ arrangements.join_opens_label }}</span></div><div><span class="kt-label">Opening time</span><span class="kt-meta-value">{{ arrangements.scheduled_label }}</span></div><div><span class="kt-label">Published</span><span class="kt-meta-value">{{ arrangements.published_label }}</span></div></div>
				<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><button type="button" class="kt-btn kt-btn-secondary" data-testid="bop-update-arrangements" @click="editingArrangements = true">Update instructions</button></div>
			</div>
			<div class="kt-region is-secondary"><h2>Opening committee</h2>
				<div class="kt-group"><p style="margin:0;font-size:14px;max-width:75ch;text-wrap:pretty" data-testid="bop-committee-summary">{{ committeeSentence }} Appointed {{ committee.appointed_label }}.</p></div>
			</div>
			<History title="Appointment and publication history" :summary="`${historyRows.length + 1} events by ${committee.appointed_by}`" :rows="historyRows" />
		</template>

		<AddMemberDialog v-if="adding" :candidates="data.candidates || []" :chosen="draft.map((d) => d.user)" :suggested-role="suggestedRole" @confirm="addRow" @cancel="adding = false" />
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import AddMemberDialog from "../components/AddMemberDialog.vue";
import ArrangementsForm from "../components/ArrangementsForm.vue";
import Guidance from "../components/Guidance.vue";
import History from "../components/History.vue";
import PageHead from "../components/PageHead.vue";

const props = defineProps({ data: { type: Object, required: true }, pending: Boolean, error: { type: String, default: "" }, refusal: { type: Object, default: null } });
const emit = defineEmits(["appoint", "publish", "edited"]);

const opening = computed(() => props.data.opening || {});
const committee = computed(() => props.data.committee || { members: [] });
const arrangements = computed(() => props.data.arrangements || {});
const draft = ref([]);
const adding = ref(false);
const showForm = ref(false);
const editingArrangements = ref(false);
watch(() => arrangements.value.version, () => { editingArrangements.value = false; showForm.value = false; });

const byUser = computed(() => Object.fromEntries((props.data.candidates || []).map((c) => [c.user, c])));
const draftRows = computed(() => draft.value.map((d) => ({ ...(byUser.value[d.user] || { full_name: d.user, designation: "" }), ...d })));
const independentName = computed(() => (draftRows.value.find((r) => r.committee_role === "Independent member") || {}).full_name || "");
const suggestedRole = computed(() => {
	const roles = draft.value.map((d) => d.committee_role);
	if (!roles.some((r) => ["Chair and recorder", "Chair"].includes(r))) return "Chair and recorder";
	if (!roles.includes("Independent member")) return "Independent member";
	return "Member";
});
const committeeSentence = computed(() => {
	const parts = committee.value.members.map((m) => (m.is_independent ? `${m.full_name} (independent member)` : m.is_chair ? `${m.full_name} (${m.committee_role.toLowerCase()})` : m.full_name));
	return parts.length > 1 ? `${parts.slice(0, -1).join(", ")}, ${parts[parts.length - 1]}.` : `${parts.join("")}.`;
});
const historyRows = computed(() => (committee.value.history || []).map((h) => [`Version ${h.version}`, `Appointed ${h.appointed_label} by ${h.appointed_by}`, h.status]));

// A refused appointment's guard is the next step until the draft changes (board
// a2): its fix replaces Add member and Appoint committee until then.
const blocked = computed(() => !!(props.refusal && props.refusal.guard) && !committee.value.appointed);
const answer = computed(() => {
	const guard = props.refusal && props.refusal.guard;
	if (!blocked.value) return props.data.next_step;
	return { kind: "your_turn_blocked", label: "Your turn, blocked", headline: guard.headline, sentence: guard.message, stage: "prepare", holder: null, since: null,
		blockers: [{ reason_code: guard.reason_code, message: guard.message, headline: guard.headline, figures: {}, fixes: guard.fixes || [], facts: [] }], fixes: guard.fixes || [], primary_action: "" };
});

function addRow(row) {
	draft.value = [...draft.value.filter((d) => d.user !== row.user), row];
	adding.value = false;
	emit("edited");
}
function removeRow(user) {
	draft.value = draft.value.filter((d) => d.user !== user);
	emit("edited");
}
function onFix(fix) {
	if (fix.fix_id === "add_member") adding.value = true;
	if (fix.fix_id === "publish") showForm.value = true;
}
</script>
