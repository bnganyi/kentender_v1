<!-- Tender-security intake duty — Project Owner, 10 Oct 2026.
       /desk/tender-security-duty          assign and end the duty for one Tender
     The Head of Procurement Function names the existing officer who records
     tender-security originals and issuer confirmations for a Tender, with an
     effective period. The assignment grants only that duty; the Head sees the
     officers and the assignments, never an intake record, a supplier or a bid.
     An officer on the Tender's opening or evaluation cannot be assigned, and
     is refused with the incompatible duty named. The Tender reference lives in
     the URL fragment so refresh and Back keep it (AGENTS.md §6.4). -->
<template>
	<div class="kt-industry kt-tsr kt-tsd">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell" data-testid="tsd-shell" :data-loading="loading ? 'true' : 'false'" :data-refreshing="refreshing ? 'true' : 'false'">
			<div v-if="forbidden" class="kt-page tsr-page" data-testid="tsd-forbidden">
				<AccessDenied :heading="forbidden.heading" :text="forbidden.text" />
			</div>

			<div v-else class="kt-page tsr-page" data-testid="tsd-page">
				<div class="kt-page-head">
					<div>
						<p class="tsr-eyebrow">TENDER SECURITY</p>
						<h1 class="kt-page-title">Tender-security intake duty</h1>
						<p class="kt-page-desc">Choose the officer who records tender-security instruments for a Tender. You assign and end the duty; you do not see the instruments, any supplier or any bid.</p>
					</div>
				</div>

				<div class="kt-filter-bar" role="search">
					<div class="field is-wide">
						<label for="tsd-q">Tender reference</label>
						<input id="tsd-q" v-model="draftTender" class="input" type="search" data-testid="tsd-tender" @keydown.enter.prevent="applyTender" @change="applyTender" />
					</div>
				</div>

				<div v-if="error" class="kt-notice is-critical" role="alert" data-testid="tsd-failure"><div class="kt-notice-body"><strong>{{ error }}</strong></div></div>
				<p v-else-if="!tender" class="tsr-help" data-testid="tsd-prompt">Enter a Tender reference to see who can be assigned and who holds the duty.</p>
				<p v-else-if="duty && duty.officers && duty.officers.found === false" class="tsr-help" data-testid="tsd-not-found">{{ duty.officers.text }}</p>

				<template v-else-if="duty && duty.officers">
					<h2 class="tsd-h2">Officers</h2>
					<table class="table tsr-table" style="width: 100%" data-testid="tsd-officers">
						<thead><tr><th>Officer</th><th>Responsibilities</th><th>Eligibility</th><th><span class="tsr-sr-only">Actions</span></th></tr></thead>
						<tbody>
							<tr v-for="o in duty.officers.officers" :key="o.user" data-testid="tsd-officer">
								<td data-label="Officer"><strong>{{ o.full_name }}</strong></td>
								<td data-label="Responsibilities">{{ o.responsibilities.join(", ") }}</td>
								<td data-label="Eligibility"><span v-if="o.eligible" class="kt-status is-live">Eligible</span><template v-else><span class="kt-status is-draft">Not eligible</span><br /><span class="tsr-muted" data-testid="tsd-reason">{{ o.reason }}</span></template></td>
								<td data-label="Actions"><button v-if="o.eligible && !o.assigned" type="button" class="btn btn-secondary" data-testid="tsd-assign" @click="openAssign(o)">Assign duty</button><span v-else-if="o.assigned" class="tsr-muted">Assigned</span></td>
							</tr>
						</tbody>
					</table>

					<h2 class="tsd-h2">Assignments for {{ duty.officers.tender_reference }}</h2>
					<p v-if="!assignments.length" class="tsr-help" data-testid="tsd-no-assignments">Nobody holds the intake duty for this Tender.</p>
					<table v-else class="table tsr-table" style="width: 100%" data-testid="tsd-assignments">
						<thead><tr><th>Officer</th><th>Status</th><th>Effective</th><th>Assigned</th><th><span class="tsr-sr-only">Actions</span></th></tr></thead>
						<tbody>
							<tr v-for="a in assignments" :key="a.assignment" data-testid="tsd-assignment">
								<td data-label="Officer"><strong>{{ a.full_name }}</strong></td>
								<td data-label="Status">{{ a.status }}<template v-if="a.revoked_at"><br /><span class="tsr-muted">Ended by {{ a.revoked_by }} · {{ a.revocation_reason }}</span></template></td>
								<td data-label="Effective">From {{ a.effective_from || "now" }}<br /><span class="tsr-muted">Until {{ a.effective_to || "revoked" }}</span></td>
								<td data-label="Assigned">{{ a.assigned_by }}<br /><span class="tsr-muted">{{ a.assigned_at }}</span></td>
								<td data-label="Actions"><button v-if="a.status !== 'Revoked'" type="button" class="btn btn-ghost" data-testid="tsd-revoke" @click="openRevoke(a)">End duty</button></td>
							</tr>
						</tbody>
					</table>
					<p class="tsr-help">Ending the duty ends the access at once. Someone who has already recorded or viewed this Tender's intake stays ineligible for its opening and evaluation; an officer who never used it becomes eligible again.</p>
				</template>

				<template v-if="conflicts.length">
					<h2 class="tsd-h2">Duty conflicts flagged for resolution</h2>
					<table class="table tsr-table" style="width: 100%" data-testid="tsd-conflicts">
						<thead><tr><th>Tender</th><th>Person</th><th>Also on</th><th>Basis</th></tr></thead>
						<tbody>
							<tr v-for="c in conflicts" :key="c.name" data-testid="tsd-conflict">
								<td data-label="Tender">{{ c.tender_reference }}</td><td data-label="Person">{{ c.full_name }}</td><td data-label="Also on">{{ c.conflicting_duty }}</td><td data-label="Basis">{{ c.basis }}</td>
							</tr>
						</tbody>
					</table>
					<p class="tsr-help">The Accounting Officer resolves a flagged conflict, with a reason. Nothing is deleted or reassigned automatically.</p>
				</template>
			</div>

			<div v-if="dialog" class="dialog-backdrop" data-testid="tsd-dialog" @keydown.esc.stop="dialog = null">
				<div class="dialog tsr-dialog" role="dialog" aria-modal="true" aria-labelledby="tsd-d-title" tabindex="-1">
					<div id="tsd-d-title" class="dialog-title">{{ dialog.kind === "assign" ? `Assign the intake duty to ${dialog.name}` : `End the intake duty of ${dialog.name}` }}</div>
					<template v-if="dialog.kind === 'assign'">
						<p class="tsr-dialog-sub">For {{ duty.officers.tender_reference }}. The officer records tender-security instruments and sees nothing else.</p>
						<div class="field"><label for="tsd-from">Effective from (optional)</label><input id="tsd-from" v-model="form.effective_from" class="input" type="datetime-local" data-testid="tsd-d-from" /></div>
						<div class="field"><label for="tsd-to">Effective until (optional)</label><input id="tsd-to" v-model="form.effective_to" class="input" type="datetime-local" data-testid="tsd-d-to" /></div>
					</template>
					<div v-else class="field">
						<label for="tsd-reason">Reason</label>
						<textarea id="tsd-reason" v-model="form.reason" class="input" rows="2" maxlength="500" data-testid="tsd-d-reason"></textarea>
						<p class="tsr-help">Enter 10–500 characters.</p>
					</div>
					<div v-if="dialogError" class="kt-notice is-critical" role="alert" data-testid="tsd-d-error"><div class="kt-notice-body">{{ dialogError }}</div></div>
					<div class="dialog-actions">
						<button type="button" class="btn btn-secondary" :disabled="pending" data-testid="tsd-d-cancel" @click="dialog = null">Cancel</button>
						<button type="button" class="btn btn-primary" :disabled="pending" data-testid="tsd-d-submit" @click="submit">{{ dialog.kind === "assign" ? "Assign duty" : "End duty" }}</button>
					</div>
				</div>
			</div>
			<div v-if="notice" class="kt-notice is-success tsr-toast" role="status" data-testid="tsd-done"><div class="kt-notice-body">{{ notice }}</div></div>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { useRouteState } from "./composables/useRouteState.js";
import { usePageRail } from "../tnd_shared/composables/usePageRail.js";
import * as api from "./data/api.js";
import AccessDenied from "../access_shared/AccessDenied.vue";

const { epoch, hash, goHash } = useRouteState("tender-security-duty");
const loadGuard = kentender_core.desk_page.createSequenceGuard();
const railEl = ref(null);
const loading = ref(false);
const refreshing = ref(false);
const error = ref("");
const duty = ref(null);
const conflicts = ref([]);
const forbidden = ref(null);
const dialog = ref(null);
const dialogError = ref("");
const pending = ref(false);
const notice = ref("");
const form = reactive({ effective_from: "", effective_to: "", reason: "" });

// The caller's own selection, never the server echo (AGENTS.md §6.4).
const tender = computed(() => new URLSearchParams(hash.value || "").get("tender") || "");
const draftTender = ref(tender.value);
watch(tender, (value) => (draftTender.value = value));
const assignments = computed(() => (duty.value && duty.value.assignments && duty.value.assignments.rows) || []);

function applyTender() {
	const value = (draftTender.value || "").trim();
	goHash(value ? `tender=${encodeURIComponent(value)}` : "", { replace: true });
}

async function load(quiet) {
	const token = loadGuard.next();
	if (quiet) refreshing.value = true;
	else loading.value = true;
	error.value = "";
	try {
		const loaded = tender.value ? await api.getDuty(tender.value) : null;
		const flagged = await api.listConflicts();
		if (!loadGuard.isCurrent(token)) return;
		if ((loaded && loaded.outcome === "FORBIDDEN") || (flagged && flagged.outcome === "FORBIDDEN" && !loaded)) {
			forbidden.value = loaded && loaded.outcome === "FORBIDDEN" ? loaded : flagged;
			return;
		}
		forbidden.value = null;
		duty.value = loaded;
		conflicts.value = (flagged && flagged.rows) || [];
	} catch (e) {
		if (loadGuard.isCurrent(token)) error.value = e.message || "Tender-security intake duty could not be loaded. Try again.";
	} finally {
		if (loadGuard.isCurrent(token)) {
			loading.value = false;
			refreshing.value = false;
		}
	}
}

function openAssign(officer) {
	Object.assign(form, { effective_from: "", effective_to: "", reason: "" });
	dialogError.value = "";
	dialog.value = { kind: "assign", user: officer.user, name: officer.full_name };
}
function openRevoke(assignment) {
	Object.assign(form, { effective_from: "", effective_to: "", reason: "" });
	dialogError.value = "";
	dialog.value = { kind: "revoke", assignment: assignment.assignment, name: assignment.full_name };
}
const stamp = (v) => (v ? v.replace("T", " ") + (v.length === 16 ? ":00" : "") : "");

async function submit() {
	if (pending.value) return;
	pending.value = true;
	dialogError.value = "";
	try {
		const result = dialog.value.kind === "assign"
			? await api.assignOfficer({ tender_reference: duty.value.officers.tender_reference, officer: dialog.value.user, effective_from: stamp(form.effective_from), effective_to: stamp(form.effective_to) })
			: await api.revokeOfficer({ assignment: dialog.value.assignment, reason: form.reason });
		if (result && result.outcome === "OK") {
			notice.value = dialog.value.kind === "assign" ? `The intake duty is assigned to ${dialog.value.name}.` : `The intake duty of ${dialog.value.name} has ended.`;
			dialog.value = null;
			setTimeout(() => (notice.value = ""), 8000);
			await load(true);
			return;
		}
		dialogError.value = (result && (result.text || result.message)) || "That could not be done. Try again.";
	} catch (e) {
		dialogError.value = e.message || "That could not be done. Try again.";
	} finally {
		pending.value = false;
	}
}

watch(tender, () => load(false), { immediate: true });
watch(epoch, () => load(true));

const railTrail = computed(() => [{ label: __("Home"), route: ["Workspaces", "Procurement Home"] }, { label: "Tender-security intake duty" }]);
usePageRail(railEl, railTrail, { showPeSwitcher: false });
</script>
