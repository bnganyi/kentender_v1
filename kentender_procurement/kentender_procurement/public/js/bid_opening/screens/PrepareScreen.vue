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
				<table class="table" data-testid="bop-committee-draft"><thead><tr><th>Member</th><th>Designation</th><th>Role on committee</th><th>Eligibility</th></tr></thead><tbody>
					<tr v-for="row in draftRows" :key="row.user" :data-user="row.user">
						<td>{{ row.full_name }}</td><td>{{ row.designation }}</td><td>{{ row.committee_role }}</td>
						<td><span v-if="rowError(row.user)" class="kt-status is-critical" :data-testid="`bop-row-error-${row.user}`">{{ rowError(row.user) }}</span><span v-else class="kt-status is-live">Eligible</span><template v-if="row.committee_role === 'Independent member' && !rowError(row.user)"> <span style="font-size:13px;color:var(--color-neutral-800)">Not involved in processing this Tender and will not evaluate it</span></template>
							<button v-if="!blocked" type="button" class="btn btn-ghost bop-row-action" :data-testid="`bop-remove-${row.user}`" @click="removeRow(row.user)">Remove</button></td>
					</tr>
				</tbody></table>
				<div v-if="!blocked" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><button type="button" class="btn btn-secondary" data-testid="bop-add-member" @click="adding = true">Add member</button></div>
				<p v-if="draft.length" class="kt-muted" style="margin:12px 0 0;font-size:13px" data-testid="bop-draft-note">Not appointed yet. This list is kept in this browser until you appoint the committee.</p>
			</div>
			<div v-if="draft.length && !blocked" class="kt-decision">
				<p style="margin:0 0 var(--space-4);font-size:15px;max-width:75ch">Each member gets their own task to join the opening at {{ opening.deadline_label }}.<template v-if="independentName"> As the independent member, {{ independentName }} cannot later be appointed to evaluate this Tender.</template></p>
				<div style="display:flex;justify-content:flex-end;gap:12px"><button type="button" class="btn btn-primary" :disabled="pending" data-testid="bop-appoint" @click="$emit('appoint', draft)">Appoint committee</button></div>
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
				<table class="table" data-testid="bop-committee"><thead><tr><th>Member</th><th>Designation</th><th>Role on committee</th><th>Task to join</th></tr></thead><tbody>
					<tr v-for="m in committee.members" :key="m.member_user"><td>{{ m.full_name }}</td><td>{{ m.designation }}</td><td>{{ m.committee_role }}</td><td>Sent</td></tr>
				</tbody></table>
			</div>
			<div class="kt-region is-secondary"><h2>How to attend</h2>
				<div class="kt-group"><p style="margin:0 0 12px;font-size:14px;max-width:75ch;text-wrap:pretty">Not published. The public Tender page says “{{ arrangements.message }}”.</p><button type="button" class="btn btn-primary" data-testid="bop-open-arrangements" @click="showForm = true">Publish how to attend</button></div>
			</div>
			<History title="Appointment history" :summary="`Appointed ${committee.appointed_label} by ${committee.appointed_by}`" :rows="historyRows" />
		</template>

		<!-- a5: published -->
		<template v-else>
			<div class="kt-region"><h2>How to attend</h2>
				<div class="kt-meta-row" data-testid="bop-arrangements"><div><span class="kt-label">Attendance method</span><span class="kt-meta-value">{{ arrangements.attendance_method }}</span></div><div><span class="kt-label">Join opens</span><span class="kt-meta-value">{{ arrangements.join_opens_label }}</span></div><div><span class="kt-label">Opening time</span><span class="kt-meta-value">{{ arrangements.scheduled_label }}</span></div><div><span class="kt-label">Published</span><span class="kt-meta-value">{{ arrangements.published_label }}</span></div></div>
				<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><button type="button" class="btn btn-secondary" data-testid="bop-update-arrangements" @click="editingArrangements = true">Update instructions</button></div>
			</div>
			<div class="kt-region is-secondary"><h2>Opening committee</h2>
				<div class="kt-group"><p style="margin:0;font-size:14px;max-width:75ch;text-wrap:pretty" data-testid="bop-committee-summary">{{ committeeSentence }} Appointed {{ committee.appointed_label }}.</p></div>
			</div>
			<History title="Appointment and publication history" :summary="`${historyRows.length + 1} events by ${committee.appointed_by}`" :rows="historyRows" />
		</template>

		<AddMemberDialog v-if="adding" :tender="opening.tender" :draft="draft" :pending="pending" :error="dialogError" @appoint="appointFrom" @cancel="adding = false" />
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
// The committee being named is recorded only when Appoint committee is chosen (one command), so until then it is the reader's own
// work in this browser: kept in the tab's session storage, so a refresh or coming back never loses it (a convenience: a blocked or
// damaged store means an empty list), and dropped once the committee is appointed.
const ROLES = ["Chair and recorder", "Chair", "Recorder", "Member", "Independent member"];
const draftKey = () => `kt.bop.draft.${window.frappe?.session?.user || ""}.${props.data.opening?.opening_id || ""}`;
function readDraft() {
	try {
		const stored = JSON.parse(window.sessionStorage.getItem(draftKey()) || "[]");
		return Array.isArray(stored) ? stored.filter((d) => d && typeof d.user === "string" && d.user && ROLES.includes(d.committee_role)).slice(0, 12) : [];
	} catch (error) {
		return [];
	}
}
function writeDraft(rows) {
	try {
		if (rows.length) window.sessionStorage.setItem(draftKey(), JSON.stringify(rows));
		else window.sessionStorage.removeItem(draftKey());
	} catch (error) {
		// a blocked store only means the draft does not survive a refresh
	}
}
const draft = ref(props.data.committee?.appointed ? [] : readDraft());
if (props.data.committee?.appointed) writeDraft([]);
watch(draft, writeDraft, { deep: true });
watch(() => !!(props.data.committee || {}).appointed, (appointed) => {
	if (appointed) draft.value = [];
});
const adding = ref(false);
const showForm = ref(false);
const editingArrangements = ref(false);
watch(() => arrangements.value.version, () => { editingArrangements.value = false; showForm.value = false; });

// A draft row carries the name and designation the Add member dialog was given by the server's search.
const draftRows = computed(() => draft.value.map((d) => ({ full_name: d.user, designation: "", ...d })));
const independentName = computed(() => (draftRows.value.find((r) => r.committee_role === "Independent member") || {}).full_name || "");
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

// The dialog hands over everyone it staged, with their roles. They join what the table already holds and the one command
// appoints the whole committee (the same command as Appoint committee, with the same guard when it is refused). The dialog stays
// open while that runs and closes when the committee is appointed or the guard is shown on the page; any other failure is shown in it.
const submitted = ref(false);
const dialogError = computed(() => props.error);
function appointFrom(rows) {
	const names = new Set(rows.map((r) => r.user));
	draft.value = [...draft.value.filter((d) => !names.has(d.user)), ...rows];
	submitted.value = true;
	emit("edited");
	emit("appoint", draft.value);
}
watch(() => props.pending, (now, before) => {
	if (!before || now || !submitted.value) return;
	submitted.value = false;
	if (committee.value.appointed || (props.refusal && props.refusal.guard)) adding.value = false;
});
// A refused appointment names the people it refused: their row says why.
const rowError = (user) => ((props.refusal && props.refusal.errors) || {})[user] || "";

function removeRow(user) {
	draft.value = draft.value.filter((d) => d.user !== user);
	emit("edited");
}
function onFix(fix) {
	if (fix.fix_id === "add_member") adding.value = true;
	if (fix.fix_id === "publish") showForm.value = true;
}
</script>
