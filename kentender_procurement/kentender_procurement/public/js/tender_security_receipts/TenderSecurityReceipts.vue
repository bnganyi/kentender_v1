<!-- Tender-security receipts — BDS-CHG-001 v0.8 owner decisions OD-G/OD-H
     (blind physical-original intake; replaces BDS-DES-15, which is not built
     as drawn: FU-V08-01, design redraw owed).
       /desk/tender-security-receipts          the recorder's own intakes
     The Head of Procurement Function records an original by Tender reference
     and the instrument's own details. Nothing about any bid appears here: no
     supplier, candidate, bid status or match. The Tender-reference filter
     lives in the URL fragment so refresh and Back keep it (AGENTS.md §6.4). -->
<template>
	<div class="kt-industry kt-tsr">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell" data-testid="tsr-shell" :data-loading="loading ? 'true' : 'false'" :data-refreshing="refreshing ? 'true' : 'false'">
			<div v-if="data.outcome === 'FORBIDDEN'" class="kt-page tsr-page" data-testid="tsr-forbidden">
				<div class="kt-empty">
					<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
					<h2 class="tsr-state-heading">{{ data.heading }}</h2>
					<p style="margin: 0 auto 16px; max-width: 520px">{{ data.text }}</p>
					<button type="button" class="btn btn-secondary" @click="goHome">Back to Procurement</button>
				</div>
			</div>

			<div v-else class="kt-page tsr-page" data-testid="tsr-list">
				<div class="kt-page-head">
					<div>
						<p class="tsr-eyebrow">TENDER SECURITY</p>
						<h1 class="kt-page-title">Tender-security receipts</h1>
						<p class="kt-page-desc">Record physical tender-security originals as they are received. Bids are never shown here.</p>
					</div>
					<button type="button" class="btn btn-primary" data-testid="tsr-record" @click="openDialog">Record receipt</button>
				</div>

				<div v-if="error" class="kt-notice is-critical" style="align-items: center" role="alert" data-testid="tsr-failure">
					<div class="kt-notice-body" style="flex: 1"><strong>Tender-security receipts could not be loaded. Try again.</strong></div>
					<button type="button" class="btn btn-secondary" data-testid="tsr-retry" @click="retry">Try again</button>
				</div>

				<div v-else-if="loading && !data.outcome" data-testid="tsr-loading">
					<div class="kt-filter-bar"><div class="is-wide"><div class="kt-skel" style="height: 40px"></div></div><div></div></div>
					<div v-for="row in 3" :key="row" class="kt-skel" style="height: 44px; margin-bottom: 8px"></div>
				</div>

				<template v-else>
					<div class="kt-filter-bar" role="search">
						<div class="field is-wide">
							<label for="tsr-q">Tender reference</label>
							<input id="tsr-q" v-model="draftTender" class="input" type="search" data-testid="tsr-filter-tender" @keydown.enter.prevent="applyFilter" @change="applyFilter" />
						</div>
						<div class="tsr-filter-actions">
							<button v-if="tenderFilter" type="button" class="btn btn-secondary" data-testid="tsr-clear-filters" @click="clearFilter">Clear filters</button>
						</div>
					</div>

					<div v-if="!rows.length" class="kt-empty" data-testid="tsr-empty">
						<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
						<p style="margin: 0 auto; font-size: 15px; max-width: 520px">{{ tenderFilter ? "No receipts match this Tender reference." : data.empty_text }}</p>
					</div>

					<table v-else class="table tsr-table" style="width: 100%" data-testid="tsr-table">
						<thead>
							<tr>
								<th>Intake reference</th>
								<th>Tender</th>
								<th>Instrument</th>
								<th>Amount</th>
								<th>Received</th>
								<th>Recorded</th>
								<th><span class="tsr-sr-only">Actions</span></th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="row in rows" :key="row.intake_reference" data-testid="tsr-row">
								<td data-label="Intake reference">
									<strong>{{ row.intake_reference }}</strong>
									<br v-if="row.status === 'Corrected' || row.corrects" />
									<span v-if="row.status === 'Corrected'" class="tsr-muted" data-testid="tsr-corrected-by">Corrected by {{ row.corrected_by }}</span>
									<span v-else-if="row.corrects" class="tsr-muted" data-testid="tsr-corrects">Corrects {{ row.corrects }}</span>
								</td>
								<td data-label="Tender">{{ row.tender_reference }}</td>
								<td data-label="Instrument">{{ row.instrument_type }} · {{ row.issuer }}<br /><span class="tsr-muted">{{ row.instrument_reference }}</span></td>
								<td data-label="Amount">{{ row.amount }}</td>
								<td data-label="Received">{{ row.received_at }}<br /><span class="tsr-muted">{{ row.deadline_class }}</span></td>
								<td data-label="Recorded">{{ row.recorded_at }}</td>
								<td data-label="Actions">
									<button v-if="row.status === 'Current'" type="button" class="btn btn-ghost" data-testid="tsr-correct" @click="openCorrection(row)">Correct</button>
								</td>
							</tr>
						</tbody>
					</table>
				</template>
			</div>

			<IntakeDialog v-if="dialogOpen" :pending="pending" :errors="fieldErrors" :error="dialogError" :initial-tender="tenderFilter" :correcting="correcting" v-bind="data.confirmation ? { confirmation: data.confirmation } : {}" @submit="onRecord" @cancel="closeDialog" />
			<div v-if="notice" class="kt-notice is-success tsr-toast" role="status" data-testid="tsr-recorded">
				<svg class="kt-notice-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"></path></svg>
				<div class="kt-notice-body">{{ notice }}</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRouteState } from "./composables/useRouteState.js";
import { usePageRail } from "../tnd_shared/composables/usePageRail.js";
import * as api from "./data/api.js";
import IntakeDialog from "./IntakeDialog.vue";

const PAGE = "tender-security-receipts";
const { epoch, hash, goHash } = useRouteState(PAGE);
const cache = kentender_core.desk_page.createScreenCache();
const loadGuard = kentender_core.desk_page.createSequenceGuard();

const railEl = ref(null);
const loading = ref(true);
const refreshing = ref(false);
const error = ref("");
const data = ref({});
const pending = ref(false);
const dialogOpen = ref(false);
const fieldErrors = ref({});
const dialogError = ref("");
const notice = ref("");
const correcting = ref(null);

// The caller's own selection, never the server echo (AGENTS.md §6.4).
const tenderFilter = computed(() => new URLSearchParams(hash.value || "").get("tender") || "");
const draftTender = ref(tenderFilter.value);
watch(tenderFilter, (value) => (draftTender.value = value));
const rows = computed(() => (data.value && data.value.rows) || []);

function goHome() {
	frappe.set_route("Workspaces", "Procurement Home");
}
function applyFilter() {
	const value = (draftTender.value || "").trim();
	goHash(value ? `tender=${encodeURIComponent(value)}` : "", { replace: true });
}
function clearFilter() {
	draftTender.value = "";
	goHash("", { replace: true });
}

async function load(opts) {
	const key = `list:${tenderFilter.value}`;
	const cached = cache.get(key);
	if (opts && opts.entering && cached) data.value = cached;
	const quiet = !!(opts && opts.quiet) || !!cached;
	const token = loadGuard.next();
	if (quiet) refreshing.value = true;
	else loading.value = true;
	error.value = "";
	try {
		const loaded = await api.listIntakes({ tender: tenderFilter.value });
		if (!loadGuard.isCurrent(token)) return;
		cache.set(key, loaded);
		data.value = loaded;
	} catch (e) {
		if (!loadGuard.isCurrent(token)) return;
		error.value = e.message || "failed";
	} finally {
		if (loadGuard.isCurrent(token)) {
			loading.value = false;
			refreshing.value = false;
		}
	}
}
function retry() {
	load({ quiet: !!cache.get(`list:${tenderFilter.value}`) });
}

function openDialog() {
	correcting.value = null;
	fieldErrors.value = {};
	dialogError.value = "";
	dialogOpen.value = true;
}
function openCorrection(row) {
	correcting.value = row;
	fieldErrors.value = {};
	dialogError.value = "";
	dialogOpen.value = true;
}
function closeDialog() {
	dialogOpen.value = false;
}
async function onRecord({ values, key }) {
	if (pending.value) return;
	pending.value = true;
	fieldErrors.value = {};
	dialogError.value = "";
	try {
		const result = await api.recordIntake(values, key);
		if (result && result.ok) {
			dialogOpen.value = false;
			notice.value = result.corrects ? `Correction recorded. Intake reference ${result.intake_reference} replaces ${result.corrects}.` : `Receipt recorded. Intake reference ${result.intake_reference}.`;
			setTimeout(() => (notice.value = ""), 8000);
			await load({ quiet: true });
			return;
		}
		if (result && result.errors) fieldErrors.value = result.errors;
		else dialogError.value = (result && result.message) || "The receipt could not be recorded. Try again.";
	} catch (e) {
		dialogError.value = e.message || "The receipt could not be recorded. Try again.";
	} finally {
		pending.value = false;
	}
}

watch(tenderFilter, () => load({ entering: true }), { immediate: true });
watch(epoch, () => load({ quiet: true }));

const railTrail = computed(() => [{ label: __("Home"), route: ["Workspaces", "Procurement Home"] }, { label: "Tender-security receipts" }]);
usePageRail(railEl, railTrail, { showPeSwitcher: false });
</script>
