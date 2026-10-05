<!-- BOP-DES-03 Opening record (BOP-CHG-001 v0.10 §10.4; boards r1–r5), ported
     class-for-class. The recorder reviews what happened (r1), prepares the
     draft (r2) and finishes it; each member reviews and signs their own
     targets (r3), then waits for the others (r4); a new version asks for fresh
     signatures (r5). Every action is a server command. -->
<template>
	<div class="kt-page" :data-screen="`record:${mode}`">
		<PageHead :title="`Opening record · ${opening.tender_reference}`" :desc="opening.title" :status="opening.status" />
		<Guidance :answer="answer" :journey="data.journey" :pending="pending" />

		<!-- r1: what the draft will be built from -->
		<template v-if="mode === 'review'">
			<RegisterTable :rows="register" empty-text="Empty register. There were no current bids." />
			<SessionTable :rows="chronology" title="What happened" />
			<div class="kt-region is-secondary"><h2>Attendance</h2>
				<table class="table" data-testid="bop-attendance"><thead><tr><th>Name</th><th>Attended as</th><th>Joined</th><th>Left</th></tr></thead><tbody>
					<tr v-for="(a, i) in data.attendees || []" :key="i"><td>{{ a.person_name }}</td><td>{{ a.represents ? `Representing ${a.represents}` : a.capacity }}</td><td>{{ a.joined_label }}</td><td>{{ endedLabel }}</td></tr>
				</tbody></table>
				<p v-if="!(data.attendees || []).length" style="margin:10px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty">No attendees joined.</p>
			</div>
			<div v-if="viewer.is_recorder" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><button type="button" class="btn btn-primary" data-testid="bop-prepare-record" @click="drafting = true">Prepare opening record</button></div>
		</template>

		<!-- r2: the generated draft -->
		<template v-else-if="mode === 'draft'">
			<div class="kt-region" data-testid="bop-draft"><h2>Opening record (the official minutes of the opening)</h2>
				<div class="kt-meta-row"><div><span class="kt-label">Status</span><span class="kt-meta-value">Draft</span></div><div><span class="kt-label">Pages</span><span class="kt-meta-value" data-testid="bop-draft-pages">{{ draft.pages }}</span></div><div><span class="kt-label">Prepared</span><span class="kt-meta-value">{{ draft.prepared_label }}</span></div></div>
				<div style="margin-top:16px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px;max-width:900px"><div v-for="n in draft.pages" :key="n" style="border:1px solid var(--color-divider);aspect-ratio:1/1.3;padding:16px;font-size:12px;color:var(--color-neutral-700)">Page {{ n }}{{ n === 1 ? " · committee, attendance, register" : "" }}{{ n === draft.pages ? " · what happened, names and designations for signature" : "" }}</div></div>
			</div>
			<div class="kt-region is-secondary"><h2>What each member will sign</h2>
				<SigningTable :rows="draftRows" />
			</div>
			<div class="kt-decision">
				<p style="margin:0 0 var(--space-4);font-size:15px;max-width:75ch">After finishing, the record cannot be changed without making a new version, which every member must sign again.</p>
				<p v-if="error" class="bop-field-error" role="alert">{{ error }}</p>
				<div style="display:flex;justify-content:flex-end;gap:12px"><button type="button" class="btn btn-secondary" @click="drafting = false">Back</button><button type="button" class="btn btn-primary" :disabled="pending" data-testid="bop-finish-record" @click="$emit('command', { method: 'finish_opening_record', args: {} })">Finish opening record</button></div>
			</div>
		</template>

		<!-- r3 / r5: review and sign -->
		<template v-else-if="mode === 'sign'">
			<div v-if="changed" class="kt-region" data-testid="bop-what-changed"><h2>What changed</h2>
				<div class="kt-meta-row"><div><span class="kt-label">New version</span><span class="kt-meta-value">{{ current.version_number }}, finished {{ current.frozen_label }}</span></div><div><span class="kt-label">Changed by</span><span class="kt-meta-value">{{ current.frozen_by }}</span></div><div><span class="kt-label">Reason</span><span class="kt-meta-value">{{ current.supersede_reason }}</span></div></div>
				<p style="margin:12px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty">Your signature on version {{ current.version_number - 1 }} is kept in the history but does not count for version {{ current.version_number }}.</p>
			</div>
			<div class="kt-region" :class="{ 'is-secondary': changed }"><h2>What you are signing</h2>
				<SigningTable :rows="mineRows" with-status :version="changed ? current.version_number : 0" />
				<div v-if="!changed" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><a class="btn btn-secondary" :href="recordPagesUrl" target="_blank" rel="noopener" data-testid="bop-read-record">Read opening record</a><a v-for="e in register.slice(0, 1)" :key="e.entry" class="btn btn-secondary" :href="bidPagesUrl(e)" target="_blank" rel="noopener">View bid pages</a></div>
			</div>
			<div class="kt-decision">
				<p style="margin:0 0 var(--space-4);font-size:15px;max-width:75ch">{{ changed ? `You sign version ${current.version_number} exactly as shown.` : `You sign for yourself only, against version ${current.version_number} exactly as shown.` }}</p>
				<p v-if="error" class="bop-field-error" role="alert">{{ error }}</p>
				<div style="display:flex;justify-content:flex-end;gap:12px"><button type="button" class="btn btn-primary" :disabled="pending" data-testid="bop-sign" @click="sign">Review and sign opening record</button></div>
			</div>
			<SignaturesTable v-if="!changed" :rows="signatures" :version="current.version_number" secondary />
		</template>

		<!-- r4, and every other reader while signatures are collected -->
		<template v-else>
			<SignaturesTable :rows="signatures" :version="current.version_number">
				<button v-if="viewer.is_recorder && !superseding" type="button" class="btn btn-secondary" data-testid="bop-new-version" @click="superseding = true">Make a new version</button>
			</SignaturesTable>
			<div v-if="superseding" class="kt-region" data-testid="bop-supersede-form"><h2>Make a new version</h2>
				<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px 24px;max-width:1000px">
					<div class="field" style="grid-column:1 / -1"><label for="bop-supersede-reason">Reason</label><input id="bop-supersede-reason" v-model="reason" class="input" data-testid="bop-supersede-reason"></div>
					<div class="field" style="grid-column:1 / -1"><label for="bop-supersede-note">What the new version adds</label><textarea id="bop-supersede-note" v-model="note" class="input" rows="2" data-testid="bop-supersede-note"></textarea></div>
				</div>
				<p style="margin:12px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty">Signatures on the current version are kept in the history but do not count for the new one. Every member signs again.</p>
				<p v-if="error" class="bop-field-error" role="alert">{{ error }}</p>
				<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><button type="button" class="btn btn-primary" :disabled="pending || !reason.trim() || !note.trim()" data-testid="bop-supersede" @click="supersede">Make new version</button><button type="button" class="btn btn-secondary" @click="superseding = false">Cancel</button></div>
			</div>
			<RegisterTable :rows="register" secondary empty-text="Empty register. There were no current bids." />
		</template>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import Guidance from "../components/Guidance.vue";
import PageHead from "../components/PageHead.vue";
import RegisterTable from "../components/RegisterTable.vue";
import SessionTable from "../components/SessionTable.vue";
import SignaturesTable from "../components/SignaturesTable.vue";
import SigningTable from "../components/SigningTable.vue";
import { pagesUrl } from "../data/api.js";

const props = defineProps({ data: { type: Object, required: true }, pending: Boolean, error: { type: String, default: "" } });
const emit = defineEmits(["command"]);

const opening = computed(() => props.data.opening);
const viewer = computed(() => props.data.viewer || {});
const record = computed(() => props.data.record || {});
const ceremony = computed(() => props.data.ceremony || {});
const register = computed(() => ceremony.value.register || []);
const chronology = computed(() => ceremony.value.chronology || []);
const draft = computed(() => record.value.draft || { pages: 0, targets: [] });
const versions = computed(() => record.value.versions || []);
const current = computed(() => versions.value[versions.value.length - 1] || { version_number: 1 });
const signatures = computed(() => record.value.signatures || []);
const mine = computed(() => record.value.mine || []);
const changed = computed(() => versions.value.length > 1);
const drafting = ref(false);
const superseding = ref(false);
const reason = ref("");
const note = ref("");
watch(() => opening.value.state, () => {
	drafting.value = false;
	superseding.value = false;
});

const mode = computed(() => {
	if (opening.value.state === "Readout complete") return drafting.value && record.value.draft ? "draft" : "review";
	if (mine.value.some((t) => !t.signed)) return "sign";
	return "waiting";
});
const answer = computed(() => {
	if (mode.value === "draft") return { kind: "your_turn", label: "Your turn", headline: "Check the draft and finish the opening record", sentence: "Finishing sends it to each member to review and sign.", fixes: [], blockers: [] };
	return props.data.next_step;
});
const endedLabel = computed(() => {
	const ended = [...chronology.value].reverse().find((r) => r.what === "Ended the opening");
	return ended ? ended.time.slice(0, 5) : "";
});

// Rows for the signing tables: one per bid page and price location, the
// minutes pages together, then the final page (boards r2, r3).
function rowsOf(targets, member) {
	const bids = Object.fromEntries(register.value.map((e) => [e.entry, e.tenderer]));
	const own = member ? targets.filter((t) => t.required_member === member) : targets;
	const seen = new Set();
	const out = [];
	const minutes = own.filter((t) => t.target_type === "Minutes page");
	for (const t of own) {
		if (t.target_type === "Minutes page") continue;
		const key = `${t.target_type}:${t.target_reference}:${t.page_number}`;
		if (seen.has(key)) continue;
		seen.add(key);
		if (t.target_type === "Final minutes page" && minutes.length) {
			const pages = [...new Set(minutes.map((m) => m.page_number))].sort((a, b) => a - b);
			out.push({ what: "Opening record", page: pages.length > 1 ? `Pages ${pages[0]}–${pages[pages.length - 1]}` : `Page ${pages[0]}`, does: minutes[0].what_you_do, signed: minutes.every((m) => m.signed) });
		}
		const bid = bids[t.target_reference];
		const page = t.target_type === "Price location" ? `Page ${t.page_number} (price)` : t.target_type === "Final minutes page" ? `Page ${t.page_number} (final)` : `Page ${t.page_number} (designated)`;
		out.push({ what: bid ? `${bid} bid` : "Opening record", page, does: t.what_you_do, signed: !!t.signed });
	}
	return out;
}
const draftRows = computed(() => {
	const first = (draft.value.targets[0] || {}).required_member;
	return rowsOf(draft.value.targets, first);
});
const mineRows = computed(() => rowsOf(mine.value, ""));

const recordPagesUrl = computed(() => pagesUrl(opening.value.tender_reference, "record", current.value.minutes_version_id));
function bidPagesUrl(entry) {
	return pagesUrl(opening.value.tender_reference, "bid", entry.entry);
}
function sign() {
	const targets = mine.value.filter((t) => !t.signed).map((t) => ({ target_id: t.target_id, target_digest: t.target_digest }));
	emit("command", { method: "sign_opening_record", args: { minutes_version: current.value.minutes_version_id, targets: JSON.stringify(targets) } });
}
function supersede() {
	emit("command", { method: "correct_opening_record_draft", args: { reason: reason.value.trim(), correction_note: note.value.trim() } });
}
</script>
