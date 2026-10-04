<!-- BOP-DES-05 Completed record (BOP-CHG-001 v0.10 §10.6; boards r6, h1–h5),
     ported class-for-class: the committee's view once the last signature
     completed the opening (r6), the read-only audit view (h1), the empty
     outcome (h2), the administrator's technical status (h3), and the
     recorder's correction of one of the four kinds (h4, h5). -->
<template>
	<div class="kt-page" :data-screen="`completed:${mode}`">
		<PageHead :title="`Opening record · ${opening.tender_reference}`" :desc="opening.title" :status="opening.status" />
		<!-- boards h1, h3: a reader who is not involved gets no guidance region -->
		<Guidance v-if="mode !== 'technical' && (answer || {}).kind !== 'not_involved'" :answer="answer" :journey="data.journey" :pending="pending" />

		<!-- h3 -->
		<template v-if="mode === 'technical'">
			<div class="kt-region" data-testid="bop-technical"><h2>Technical status</h2>
				<p style="margin:0 0 16px;font-size:14px;max-width:75ch;text-wrap:pretty">{{ technical.message }}</p>
				<div class="kt-meta-row"><div><span class="kt-label">{{ technical.completed_label ? "Opening completed" : "State" }}</span><span class="kt-meta-value">{{ technical.completed_label || technical.state }}</span></div><div><span class="kt-label">Technical incidents</span><span class="kt-meta-value">{{ technical.incidents ? technical.incidents : "None recorded" }}</span></div></div>
			</div>
		</template>

		<!-- h4 -->
		<template v-else-if="mode === 'correct'">
			<div class="kt-region" data-testid="bop-correct-form"><h2>Add a correction</h2>
				<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px 24px;max-width:1000px">
					<div class="kt-field" style="grid-column:1 / -1"><label id="bop-correct-kind-label">What needs correcting?</label>
						<div role="radiogroup" aria-labelledby="bop-correct-kind-label" style="display:flex;flex-wrap:wrap;gap:12px 24px;padding-top:4px">
							<label v-for="k in KINDS" :key="k" class="kt-radio"><input v-model="kind" type="radio" name="bop-correct-kind" :value="k" :data-testid="`bop-correct-kind-${KINDS.indexOf(k)}`"><span class="dot"></span>{{ k }}</label>
						</div>
					</div>
					<div class="kt-field"><label for="bop-correct-info">Correct information</label><input id="bop-correct-info" v-model="info" class="kt-input" data-testid="bop-correct-info"></div>
					<div class="kt-field"><label for="bop-correct-reason">Reason for correction</label><input id="bop-correct-reason" v-model="reason" class="kt-input" data-testid="bop-correct-reason"></div>
				</div>
				<p style="margin:12px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty">You can correct only these four kinds of information. A correction cannot change a bid, the register or anything the members signed.</p>
				<p v-if="error" class="bop-field-error" role="alert" data-testid="bop-correct-error">{{ error }}</p>
			</div>
			<div class="kt-decision"><p style="margin:0 0 var(--space-4);font-size:15px;max-width:75ch">The correction is added under your name with the time you submit it. Version {{ versionNumber }} and its signatures stay as they are.</p><div style="display:flex;justify-content:flex-end;gap:12px"><button type="button" class="kt-btn kt-btn-secondary" data-testid="bop-correct-cancel" @click="$emit('navigate', '')">Cancel</button><button type="button" class="kt-btn kt-btn-primary" :disabled="pending || !info.trim() || !reason.trim()" data-testid="bop-correct-add" @click="add">Add correction</button></div></div>
			<div class="kt-region is-secondary"><h2>Original opening record</h2>
				<div class="kt-group"><p style="margin:0;font-size:14px;max-width:75ch;text-wrap:pretty">Version {{ versionNumber }}, signed by every member. Read only.</p><a :href="recordPagesUrl" target="_blank" rel="noopener" style="font-size:14px">View version {{ versionNumber }}</a></div>
			</div>
		</template>

		<!-- h1: a reader who is not involved -->
		<template v-else-if="mode === 'audit'">
			<div class="kt-region" data-testid="bop-summary"><h2>Opening summary</h2>
				<div class="kt-meta-row"><div><span class="kt-label">Completed</span><span class="kt-meta-value">{{ completion.completed_label }}</span></div><div><span class="kt-label">Bids opened</span><span class="kt-meta-value">{{ completion.bids_opened }}</span></div><div><span class="kt-label">Passed to Evaluation</span><span class="kt-meta-value">{{ completion.evaluation_reference || "Nothing" }}</span></div></div>
			</div>
			<RegisterTable :rows="register" empty-text="Empty register. There were no current bids." :note="reportedSpeech" />
			<SessionTable :rows="chronology" title="What happened" />
			<RequestsTable :rows="requests" secondary />
			<SignaturesTable :rows="signatures" :version="versionNumber" secondary />
			<CorrectionsTable v-if="corrections.length" :rows="corrections" secondary />
			<History title="Evidence history" summary="Receipt, versions, signature and access history · read only" :rows="evidenceRows" />
		</template>

		<!-- h2: no bids -->
		<template v-else-if="mode === 'empty'">
			<RegisterTable :rows="[]" empty-text="Empty register. There were no current bids." />
			<SignaturesTable :rows="signatures" :column="`Opening record, ${pagesLabel}`" secondary />
		</template>

		<!-- r6 / h5: the committee's completed record -->
		<template v-else>
			<CorrectionsTable v-if="corrections.length" :rows="corrections" />
			<SignaturesTable :rows="signatures" :version="versionNumber" :secondary="corrections.length > 0">
				<button v-if="viewer.is_recorder" type="button" class="kt-btn kt-btn-secondary" data-testid="bop-correct-open" @click="$emit('navigate', 'correct')">Correct opening record</button>
			</SignaturesTable>
			<RegisterTable v-if="!corrections.length" :rows="register" secondary />
			<div v-if="corrections.length" class="kt-notice is-critical" style="margin-top:8px"><svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"></circle><path d="M12 8v4"></path><path d="M12 16h.01"></path></svg><div class="kt-notice-body"><p style="margin:0;font-size:14px"><strong>If a request uses any other kind, or tries to change a bid or a signed page:</strong> This correction cannot change a bid or replace the signed opening record.</p></div></div>
			<History title="Evidence details" :summary="evidenceSummary" :rows="evidenceRows" />
		</template>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import CorrectionsTable from "../components/CorrectionsTable.vue";
import Guidance from "../components/Guidance.vue";
import History from "../components/History.vue";
import PageHead from "../components/PageHead.vue";
import RegisterTable from "../components/RegisterTable.vue";
import RequestsTable from "../components/RequestsTable.vue";
import SessionTable from "../components/SessionTable.vue";
import SignaturesTable from "../components/SignaturesTable.vue";
import { pagesUrl } from "../data/api.js";

const KINDS = ["Attendance note", "Procedural note", "Typographical error in a note", "Observer name or organisation"];
const props = defineProps({ data: { type: Object, required: true }, pending: Boolean, error: { type: String, default: "" }, sub: { type: String, default: "" } });
const emit = defineEmits(["command", "navigate"]);

const opening = computed(() => props.data.opening);
const viewer = computed(() => props.data.viewer || {});
const record = computed(() => props.data.record || {});
const ceremony = computed(() => props.data.ceremony || {});
const technical = computed(() => props.data.technical_status || {});
const register = computed(() => ceremony.value.register || []);
const chronology = computed(() => ceremony.value.chronology || []);
const requests = computed(() => ceremony.value.requests || []);
const completion = computed(() => record.value.completion || {});
const signatures = computed(() => record.value.signatures || []);
const corrections = computed(() => record.value.corrections || []);
const versions = computed(() => record.value.versions || []);
const current = computed(() => versions.value[versions.value.length - 1] || {});
const versionNumber = computed(() => current.value.version_number || 1);
const pagesLabel = computed(() => `${current.value.page_count || 1} page${(current.value.page_count || 1) === 1 ? "" : "s"}`);

const mode = computed(() => {
	if (viewer.value.technical) return "technical";
	if (props.sub === "correct" && viewer.value.is_recorder) return "correct";
	if (!viewer.value.is_member) return "audit";
	if (completion.value.no_bids) return "empty";
	return "complete";
});
const answer = computed(() => {
	if (mode.value === "correct") return { kind: "your_turn", label: "Your turn", headline: "Correct opening record", sentence: "Your correction will be added to this record. The original will remain available.", fixes: [], blockers: [] };
	return props.data.next_step;
});
const reportedSpeech = computed(() => ((ceremony.value.opened || [])[0] || {}).reported_speech || "");
const evidenceSummary = computed(() => [completion.value.evaluation_reference && `Evaluation reference ${completion.value.evaluation_reference}`, `version ${versionNumber.value}`, corrections.value.length ? "correction history" : "signature history"].filter(Boolean).join(" · "));
const evidenceRows = computed(() => versions.value.map((v) => [`Version ${v.version_number}`, `Finished ${v.frozen_label} by ${v.frozen_by}`, v.state]));
const recordPagesUrl = computed(() => pagesUrl(opening.value.tender_reference, "record", current.value.minutes_version_id));

const kind = ref(KINDS[0]);
const info = ref("");
const reason = ref("");
function add() {
	emit("command", { method: "correct_opening_record", args: { kind: kind.value, correct_information: info.value.trim(), reason: reason.value.trim() }, then: "" });
}
</script>
