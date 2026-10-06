<!-- Procurement meetings — OVS-CHG-001 v0.6 §11, §13; PRC-CHG-001 v0.11 §7, §9:
       /app/procurement-meetings
     A read-only register of the sessions that actually started: a Bid Opening's
     single session and each Bid Evaluation discussion session, with the
     department each Tender belongs to. Totals by type and by lead department,
     filters (Type, Department, State, From, To, Find a tender), and a way to the
     meeting's own record. Ported class for class from the review board
     `17_oversight_visibility/design/OVS First Slice Review.dc.html` (OVS-PRC-01
     to 06). A row never carries a session's subject, notes, a bidder, a bid count
     or a finding; the record it links to applies its own rule again. -->
<template>
	<div class="kt-industry kt-pmt">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell" data-testid="pmt-shell" :data-loading="loading ? 'true' : 'false'" :data-refreshing="refreshing ? 'true' : 'false'">
			<div class="kt-page">
				<div class="kt-page-head">
					<div>
						<h1 class="kt-page-title" data-testid="pmt-title">Procurement meetings</h1>
						<p class="kt-page-desc">Bid opening and evaluation sessions, with the department each Tender belongs to.</p>
					</div>
				</div>

				<div v-if="loading" class="kt-region" data-testid="pmt-loading" role="status"><div class="kt-skel" style="width:40%"></div><div class="kt-skel" style="width:70%;margin-top:12px"></div></div>

				<div v-else-if="forbidden" class="kt-empty" data-testid="pmt-forbidden" role="alert">
					<p><strong>You do not have access to Procurement meetings.</strong></p>
					<p>This area needs one of these responsibilities: Accounting Officer, Head of Procurement Function, Head of User Department or authorised auditor. Ask your KenTender administrator to assign the appropriate responsibility in System setup.</p>
				</div>

				<div v-else-if="failure" class="kt-notice is-critical" role="alert" data-testid="pmt-failure">
					<div class="kt-notice-body" style="display:flex;justify-content:space-between;align-items:center;gap:16px;width:100%">
						<p style="margin:0;font-size:15px">We could not load Procurement meetings.</p>
						<button type="button" class="btn btn-secondary" @click="load()">Try again</button>
					</div>
				</div>

				<template v-else>
					<div v-if="stale" class="kt-notice is-warning" role="status" data-testid="pmt-stale" style="margin-bottom:16px">
						<div class="kt-notice-body" style="display:flex;justify-content:space-between;align-items:center;gap:16px;width:100%">
							<p style="margin:0;font-size:15px">We could not update this list. What you see may be out of date.</p>
							<button type="button" class="btn btn-secondary" @click="load({ quiet: true })">Try again</button>
						</div>
					</div>
					<div v-if="data.incomplete" class="kt-notice is-warning" role="status" data-testid="pmt-incomplete" style="margin-bottom:16px">
						<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"></path><path d="M12 9v4"></path><path d="M12 17h.01"></path></svg>
						<div class="kt-notice-body" style="display:flex;justify-content:space-between;align-items:center;gap:16px;width:100%">
							<p style="margin:0;font-size:15px">{{ data.incomplete_message }}</p>
							<button type="button" class="btn btn-secondary" @click="load({ quiet: true })">Try again</button>
						</div>
					</div>

					<div class="kt-region" data-testid="pmt-totals">
						<div style="display:flex;justify-content:space-between;align-items:baseline">
							<h2>Meetings held</h2>
							<span style="font-size:13px;color:var(--color-neutral-700)">{{ data.totals.grouping }}</span>
						</div>
						<div class="pmt-totals">
							<table class="table" data-testid="pmt-by-type">
								<thead><tr><th>Type</th><th class="is-num">Held</th></tr></thead>
								<tbody>
									<tr><td>Bid opening</td><td class="is-num">{{ data.totals.by_type["Bid opening"] }}</td></tr>
									<tr><td>Bid evaluation</td><td class="is-num">{{ data.totals.by_type["Bid evaluation"] }}</td></tr>
									<tr><td style="font-weight:600">{{ filtered ? "All matching meetings" : "All meetings" }}</td><td class="is-num" data-testid="pmt-held-total">{{ data.held_total }}</td></tr>
								</tbody>
							</table>
							<table class="table" data-testid="pmt-by-department">
								<thead><tr><th>Lead department</th><th class="is-num">Bid opening</th><th class="is-num">Bid evaluation</th><th class="is-num">Total</th></tr></thead>
								<tbody>
									<tr v-for="d in data.totals.by_department" :key="d.department || 'none'"><td>{{ d.department_name }}</td><td class="is-num">{{ d["Bid opening"] }}</td><td class="is-num">{{ d["Bid evaluation"] }}</td><td class="is-num">{{ d.total }}</td></tr>
								</tbody>
							</table>
						</div>
					</div>

					<div class="kt-region">
						<div class="kt-filter-bar" data-testid="pmt-filters">
							<div class="field"><label for="pmt-type">Type</label>
								<select id="pmt-type" v-model="form.type" class="input"><option value="">All types</option><option v-for="t in data.options.types" :key="t" :value="t">{{ t }}</option></select></div>
							<div class="field"><label for="pmt-dept">Department</label>
								<select id="pmt-dept" v-model="form.department" class="input"><option value="">All departments</option><option v-for="d in data.options.departments" :key="d.unit" :value="d.unit">{{ d.name }}</option></select></div>
							<div class="field"><label for="pmt-state">State</label>
								<select id="pmt-state" v-model="form.state" class="input"><option value="">All states</option><option v-for="s in data.options.states" :key="s" :value="s">{{ s }}</option></select></div>
							<div class="field"><label for="pmt-from">From</label><input id="pmt-from" v-model="form.date_from" type="date" class="input" /></div>
							<div class="field"><label for="pmt-to">To</label><input id="pmt-to" v-model="form.date_to" type="date" class="input" /></div>
							<div class="field is-wide"><label for="pmt-q">Find a tender</label><input id="pmt-q" v-model="form.query" class="input" placeholder="Reference or title" /></div>
						</div>
						<div style="display:flex;justify-content:space-between;align-items:center;margin:12px 0">
							<span style="font-size:14px;color:var(--color-neutral-800)" data-testid="pmt-count" aria-live="polite">{{ countLabel }}</span>
							<button v-if="filtered" type="button" class="btn btn-ghost" data-testid="pmt-clear" @click="clear()">Clear filters</button>
						</div>

						<table v-if="data.rows.length" class="table" data-testid="pmt-rows">
							<thead><tr><th>Type</th><th style="width:26%">Tender</th><th style="width:24%">Department</th><th class="is-num">Session</th><th>Meeting date</th><th class="is-num">Duration</th><th class="is-num">Present</th><th>State</th><th><span class="kt-visually-hidden" style="position:absolute;left:-9999px">Record</span></th></tr></thead>
							<tbody>
								<tr v-for="r in data.rows" :key="r.proceeding + ':' + (r.session || 0)" :data-testid="`pmt-row-${r.type === 'Bid opening' ? 'opening' : 'evaluation'}`">
									<td style="white-space:nowrap">{{ r.type }}</td>
									<td><div>{{ r.title }}</div><div style="font-size:13px;color:var(--color-neutral-700)">{{ r.tender }}</div></td>
									<td><div>{{ r.department_name }}</div><div v-for="c in r.contributors" :key="c" style="font-size:13px;color:var(--color-neutral-700)">Contributor: {{ c }}</div></td>
									<td class="is-num" style="white-space:nowrap">{{ r.session || "—" }}</td>
									<td style="white-space:nowrap">{{ r.date_label || "—" }}</td>
									<td class="is-num" style="white-space:nowrap">{{ duration(r) }}</td>
									<td class="is-num" style="white-space:nowrap">{{ r.present === null ? "—" : r.present }}</td>
									<td><span class="kt-status" :class="tone(r)">{{ r.state }}</span></td>
									<td style="white-space:nowrap"><a href="#" :aria-label="`View record: ${r.type} for ${r.tender}`" @click.prevent="open(r)">View record</a></td>
								</tr>
							</tbody>
						</table>
						<TablePagerHost v-if="data.matched" :total="data.matched" :page="page" :page-size="pageSize" noun="meeting" @update:page="setPage" @update:page-size="setPageSize" />

						<div v-if="!data.rows.length" class="kt-empty" data-testid="pmt-empty">
							<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"></circle><path d="m20 20-3.5-3.5"></path></svg>
							<p>{{ filtered ? "No meetings match these filters." : "No procurement meetings have been recorded yet." }}</p>
							<button v-if="filtered" type="button" class="btn btn-secondary" @click="clear()">Clear filters</button>
						</div>
					</div>
				</template>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";
import { frappeCall } from "./data/frappeCall.js";
import { usePageRail } from "../tnd_shared/composables/usePageRail.js";
import TablePagerHost from "../pager_shared/TablePagerHost.vue";
import { savePageSize, savedPageSize } from "../pager_shared/pageSize.js";

const railEl = ref(null);
const loading = ref(true); // a skeleton only until the first answer: later loads revalidate in place
const refreshing = ref(false);
const failure = ref(false);
const stale = ref(false); // a later load failed: the last answer stays, labelled
const forbidden = ref(false);
const data = ref(null);
// The table-pagination standard (AGENTS.md §6.11): the server cuts the page (`start`, `limit`) and says how many matched.
const page = ref(1);
const pageSize = ref(savedPageSize("meetings"));
// the controls bind to the reader's own choices, never to the server's echo
const form = reactive({ type: "", department: "", state: "", date_from: "", date_to: "", query: "" });
let seq = 0;
let timer = null;

const filtered = computed(() => Object.values(form).some(Boolean));
const countLabel = computed(() => {
	if (!data.value) return "";
	const m = data.value.matched;
	const noun = `${m} meeting${m === 1 ? "" : "s"}`;
	return filtered.value ? `${noun} match these filters` : noun;
});

async function load(opts = {}) {
	const token = ++seq;
	if (data.value) refreshing.value = true;
	try {
		const out = await frappeCall("kentender_procurement.proceedings.api.list_procurement_meetings", { ...form, limit: pageSize.value, start: (page.value - 1) * pageSize.value }, "GET");
		if (token !== seq) return;
		// A filter or a refresh can leave the reader past the last page: go to the last one.
		const last = Math.max(1, Math.ceil((out.matched || 0) / pageSize.value));
		if (page.value > last) {
			page.value = last;
			return load(opts);
		}
		forbidden.value = !!out.forbidden;
		data.value = out;
		failure.value = false;
		stale.value = false;
	} catch (e) {
		if (token !== seq) return;
		if (e.httpStatus === 403) forbidden.value = true;
		else if (!data.value) failure.value = true;
		else stale.value = true;
	} finally {
		if (token === seq) {
			loading.value = false;
			refreshing.value = false;
		}
	}
}

load();
watch(form, () => {
	page.value = 1;
	clearTimeout(timer);
	timer = setTimeout(load, 250);
});
onBeforeUnmount(() => clearTimeout(timer));

function clear() {
	Object.assign(form, { type: "", department: "", state: "", date_from: "", date_to: "", query: "" });
}
function setPage(n) {
	page.value = n;
	load({ quiet: true });
}
function setPageSize(size) {
	pageSize.value = size;
	page.value = 1;
	savePageSize("meetings", size);
	load({ quiet: true });
}
function open(r) {
	frappe.set_route(...r.route);
}
function duration(r) {
	const m = r.duration_minutes;
	if (m === null || m === undefined) return "—";
	return m < 60 ? `${m} min` : `${Math.floor(m / 60)} h${m % 60 ? ` ${m % 60} min` : ""}`;
}
function tone(r) {
	if (["Not held", "Aborted after start"].includes(r.state)) return "is-attention";
	if (r.state === "In session") return "is-live";
	return "is-pending";
}

const railTrail = computed(() => [{ label: __("Home"), route: ["Workspaces", "Procurement Home"] }, { label: "Procurement meetings" }]);
usePageRail(railEl, railTrail, { showPeSwitcher: false });
</script>
