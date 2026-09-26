<!-- STD-DES-02 Release detail, with variants 02A (Available), 02F (Failed
     verification), 02S (Superseded), 02W (Withdrawn) and 02R (read failure) —
     ported class-for-class from "STD Templates Artboards.dc.html"
     (DS .table/.tag/.btn -> .kt-table/.kt-tag/.kt-btn). Every value is the
     owner projection's; nothing is parsed or reconstructed here. -->
<template>
	<div v-if="failed && !data.outcome" class="kt-page stdt-page" data-testid="stdt-detail-failure" data-screen-label="STD-DES-02R Release detail read failure">
		<div class="kt-notice is-critical" style="align-items: center" role="alert">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" x2="12" y1="8" y2="12"></line><line x1="12" x2="12.01" y1="16" y2="16"></line></svg>
			<div class="kt-notice-body" style="flex: 1"><strong>STD Template details could not be loaded. Try again.</strong></div>
			<div style="display: flex; gap: 8px">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('back')">Back to STD Templates</button>
				<button type="button" class="kt-btn kt-btn-primary" data-testid="stdt-detail-retry" @click="$emit('retry')">Try again</button>
			</div>
		</div>
	</div>

	<div v-else-if="loading" class="kt-page stdt-page" data-testid="stdt-detail-loading">
		<div class="kt-skel" style="width: 180px; height: 16px"></div>
		<div class="kt-skel" style="width: 420px; height: 34px"></div>
		<div v-for="row in 4" :key="row" class="kt-skel" style="height: 60px"></div>
	</div>

	<div v-else-if="data.outcome === 'OK'" class="kt-page stdt-page" style="gap: 32px" data-testid="stdt-detail" :data-status="release.status" data-screen-label="STD-DES-02 Release detail">
		<div style="display: flex; flex-direction: column; gap: 16px">
			<a href="/app/std-templates" class="stdt-back" data-testid="stdt-back" @click.prevent="$emit('back')"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m12 19-7-7 7-7"></path><path d="M19 12H5"></path></svg>Back to STD Templates</a>
			<div>
				<p class="stdt-eyebrow">TENDER DOCUMENT STANDARDS</p>
				<h1 class="kt-page-title">{{ release.display_name }}</h1>
				<p class="kt-page-desc" style="display: flex; align-items: center; gap: 8px">Release {{ release.template_release }} · <span class="kt-status" :class="release.status_class" data-testid="stdt-detail-status">{{ release.status }}</span></p>
			</div>
			<div style="display: flex; flex-direction: column; gap: 4px; max-width: 860px">
				<p style="margin: 0; font-size: 16px; font-weight: 600" data-testid="stdt-consequence">{{ release.consequence }}</p>
				<p style="margin: 0; font-size: 15px; color: var(--kt-color-neutral-800)"><strong style="color: var(--kt-color-text)">{{ release.next_step.head }}</strong> {{ release.next_step.holder }}</p>
			</div>
		</div>

		<div v-if="variant.withdrawal" class="kt-region" data-testid="stdt-withdrawal">
			<h2>Withdrawal</h2>
			<div class="kt-meta-row" style="border-top: 1px solid var(--kt-color-divider); padding-top: 12px">
				<div v-for="fact in variant.withdrawal.filter((f) => f.value)" :key="fact.label"><span class="kt-label">{{ fact.label }}</span><span>{{ fact.value }}</span></div>
			</div>
		</div>
		<div v-if="variant.successor" class="kt-group" data-testid="stdt-successor"><span class="kt-label" style="display: block; margin-bottom: 4px">Successor release</span><span>{{ variant.successor }}</span></div>

		<div class="kt-region" data-testid="stdt-blockers">
			<h2>Blockers</h2>
			<p v-if="!data.blockers.length" style="margin: 0; font-size: 14px; color: var(--kt-color-neutral-800); border-top: 1px solid var(--kt-color-divider); padding-top: 10px">No blockers.</p>
			<ol v-else style="list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--kt-color-divider)">
				<li v-for="b in data.blockers" :key="b.n" class="stdt-blocker">
					<span style="font-family: var(--kt-font-heading); font-size: 17px; color: var(--kt-color-neutral-700)">{{ b.n }}</span>
					<span v-if="b.failed" style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap"><span class="kt-status is-critical">Failed</span><span style="font-size: 15px">{{ b.text }}</span></span>
					<span v-else style="font-size: 15px">{{ b.text }}</span>
					<span style="font-size: 13px; color: var(--kt-color-neutral-800)"><span class="kt-label" style="display: block">Owner</span>{{ b.owner }}</span>
				</li>
			</ol>
		</div>
		<div v-if="variant.earlier_success" class="kt-group" data-testid="stdt-earlier-success"><span class="kt-label" style="display: block; margin-bottom: 4px">Earlier successful evidence</span><span>{{ variant.earlier_success }}</span></div>

		<nav aria-label="Release sections" class="stdt-section-nav">
			<a v-for="s in SECTIONS" :key="s.id" :href="`#section=${s.id}`" :aria-current="hashState.section === s.id ? 'true' : undefined" :data-testid="`stdt-nav-${s.id}`" @click.prevent="selectSection(s.id)">{{ s.label }}</a>
		</nav>

		<div id="stdt-overview" class="kt-region" data-testid="stdt-section-overview">
			<h2>Overview</h2>
			<div class="stdt-grid-2-1">
				<div>
					<h3 class="stdt-h3">Supported use</h3>
					<dl class="stdt-dl" style="grid-template-columns: 180px minmax(0, 1fr); gap: 10px 16px">
						<template v-for="s in data.overview.supported" :key="s.label"><dt class="kt-label" style="padding-top: 2px">{{ s.label }}</dt><dd style="margin: 0">{{ s.value }}</dd></template>
					</dl>
				</div>
				<div>
					<h3 class="stdt-h3">Not supported</h3>
					<ul style="margin: 0; padding-left: 18px; font-size: 14px; display: flex; flex-direction: column; gap: 6px">
						<li v-for="n in data.overview.not_supported" :key="n">{{ n }}</li>
					</ul>
				</div>
			</div>
			<div class="stdt-grid-1-2" style="margin-top: 24px">
				<div class="kt-group">
					<h3 class="stdt-h3" style="margin-bottom: 8px">Release</h3>
					<dl class="stdt-dl" style="grid-template-columns: 120px 1fr; gap: 8px 16px">
						<dt class="kt-label" style="padding-top: 2px">Template release</dt><dd style="margin: 0">{{ data.overview.release.template_release }}</dd>
						<dt class="kt-label" style="padding-top: 2px">Status</dt><dd style="margin: 0"><span class="kt-status" :class="data.overview.release.status_class">{{ data.overview.release.status }}</span></dd>
					</dl>
				</div>
				<div class="kt-group">
					<h3 class="stdt-h3" style="margin-bottom: 8px">Official source</h3>
					<dl class="stdt-dl" style="grid-template-columns: 120px 1fr; gap: 8px 16px">
						<dt class="kt-label" style="padding-top: 2px">Title</dt><dd style="margin: 0">{{ data.overview.official_source.title }}</dd>
						<dt class="kt-label" style="padding-top: 2px">Source owner</dt><dd style="margin: 0">{{ data.overview.official_source.source_owner }}</dd>
						<dt class="kt-label" style="padding-top: 2px">Retrieval date</dt><dd style="margin: 0">{{ data.overview.official_source.retrieval_date }}</dd>
					</dl>
				</div>
			</div>
		</div>

		<div id="stdt-content" class="kt-region" data-testid="stdt-section-content">
			<h2>Tender content</h2>
			<div class="stdt-grid-2">
				<div v-for="o in data.tender_content.outputs" :key="o.output_id" class="stdt-output">
					<div><div style="font-weight: 600; font-size: 15px">{{ o.title }}</div><div style="font-size: 13px; color: var(--kt-color-neutral-800); margin-top: 2px">{{ o.summary }}</div></div>
					<a class="kt-btn kt-btn-secondary" :href="previewHref(o.output_id)" target="_blank" rel="noopener" :data-testid="`stdt-preview-${o.output_id}`" :aria-label="`Preview ${o.title}`"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path><circle cx="12" cy="12" r="3"></circle></svg>Preview</a>
				</div>
			</div>
			<p style="margin: 20px 0 0; font-size: 15px" data-testid="stdt-coverage-line"><strong>Source coverage:</strong> {{ data.tender_content.coverage_line }}</p>
			<div class="stdt-grid-3" style="margin-top: 20px">
				<div class="kt-group"><div style="font-weight: 600; font-size: 14px; margin-bottom: 4px">Inherited from the authorised Requisition</div><div style="font-size: 14px; color: var(--kt-color-neutral-800)">{{ data.tender_content.inherited }}</div></div>
				<div class="kt-group"><div style="font-weight: 600; font-size: 14px; margin-bottom: 4px">Entered during Tender preparation</div><div style="font-size: 14px; color: var(--kt-color-neutral-800)">{{ data.tender_content.entered }}</div></div>
				<div class="kt-group"><div style="font-weight: 600; font-size: 14px; margin-bottom: 4px">Generated by KenTender</div><div style="font-size: 14px; color: var(--kt-color-neutral-800)">{{ data.tender_content.generated }}</div></div>
			</div>
			<div style="margin-top: 20px">
				<a class="kt-btn kt-btn-secondary" :href="reviewPackHref" data-testid="stdt-review-pack"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><path d="m7 10 5 5 5-5"></path><path d="M12 15V3"></path></svg>Download review pack</a>
			</div>
		</div>

		<div id="stdt-bid" class="kt-region" data-testid="stdt-section-bid">
			<h2>Bid response and downstream use</h2>
			<div class="stdt-grid-2" style="gap: 40px">
				<div>
					<h3 class="stdt-h3">Supplier tasks</h3>
					<ol style="list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--kt-color-divider)">
						<li v-for="t in data.bid_response.tasks" :key="t.n" style="display: grid; grid-template-columns: 28px minmax(0, 1fr); gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--kt-color-divider)">
							<span style="font-family: var(--kt-font-heading); font-size: 16px; color: var(--kt-color-neutral-700)">{{ t.n }}</span>
							<span><span style="display: block; font-weight: 600; font-size: 14px">{{ t.name }}</span><span style="display: block; font-size: 13px; color: var(--kt-color-neutral-800)">{{ t.purpose }}</span></span>
						</li>
					</ol>
				</div>
				<div style="display: flex; flex-direction: column; gap: 20px">
					<div>
						<h3 class="stdt-h3">Permitted response controls</h3>
						<div style="display: flex; flex-wrap: wrap; gap: 6px"><span v-for="c in data.bid_response.controls" :key="c" class="kt-tag kt-tag-outline">{{ c }}</span></div>
					</div>
					<dl class="stdt-dl" style="grid-template-columns: 160px 1fr; gap: 10px 16px">
						<dt class="kt-label" style="padding-top: 2px">Response families</dt><dd style="margin: 0">{{ data.bid_response.response_families }}</dd>
						<dt class="kt-label" style="padding-top: 2px">MoH content</dt><dd style="margin: 0">{{ data.bid_response.fixture_content }}</dd>
						<dt class="kt-label" style="padding-top: 2px">Reservation evidence</dt><dd style="margin: 0">{{ data.bid_response.reservation_evidence }}</dd>
					</dl>
				</div>
			</div>
			<div class="stdt-grid-2" style="gap: 40px; margin-top: 28px">
				<div>
					<h3 class="stdt-h3">Evaluation groups</h3>
					<div class="stdt-eval-groups">
						<div v-for="e in data.bid_response.evaluation_groups" :key="e.n" style="padding: 10px 12px 10px 0; display: flex; flex-direction: column; gap: 2px">
							<span style="font-family: var(--kt-font-heading); font-size: 14px; color: var(--kt-color-neutral-700)">{{ e.n }}</span>
							<span style="font-weight: 600; font-size: 14px">{{ e.name }}</span>
							<span style="font-size: 12px; color: var(--kt-color-neutral-800)">{{ e.note }}</span>
						</div>
					</div>
				</div>
				<div>
					<h3 class="stdt-h3">Contract treatment</h3>
					<div class="stdt-grid-2" style="gap: 24px; border-top: 1px solid var(--kt-color-divider); padding-top: 10px; font-size: 14px">
						<div><span class="kt-label" style="display: block; margin-bottom: 6px">Carried forward</span><ul style="margin: 0; padding-left: 18px; display: flex; flex-direction: column; gap: 3px"><li v-for="c in data.bid_response.carried" :key="c">{{ c }}</li></ul></div>
						<div><span class="kt-label" style="display: block; margin-bottom: 6px">Not carried forward</span><ul style="margin: 0; padding-left: 18px; display: flex; flex-direction: column; gap: 3px"><li v-for="c in data.bid_response.not_carried" :key="c">{{ c }}</li></ul></div>
					</div>
				</div>
			</div>
		</div>

		<div id="stdt-coverage" class="kt-region" data-testid="stdt-section-coverage">
			<h2>Coverage and changes</h2>
			<div class="stdt-treatments" data-testid="stdt-treatments">
				<div v-for="tr in data.coverage.treatments" :key="tr.label" style="padding: 12px 12px 12px 0; display: flex; flex-direction: column; gap: 2px">
					<span style="font-family: var(--kt-font-heading); font-size: 26px; line-height: 1">{{ tr.n }}</span>
					<span style="font-size: 13px; color: var(--kt-color-neutral-800)">{{ tr.label }}</span>
				</div>
				<div class="stdt-treatment-total" style="padding: 12px 0 12px 16px; display: flex; flex-direction: column; gap: 2px; border-left: 1px solid var(--kt-color-divider)">
					<span style="font-family: var(--kt-font-heading); font-size: 26px; line-height: 1">{{ data.coverage.total }}</span>
					<span style="font-size: 13px; color: var(--kt-color-neutral-800)">Source rows in total; {{ data.coverage.forms_total }} forms counted separately</span>
				</div>
			</div>
			<div class="kt-disclosure" style="margin-top: 12px" data-testid="stdt-coverage-disclosure">
				<button type="button" class="kt-disclosure-head stdt-disclosure-button" :aria-expanded="coverageOpen ? 'true' : 'false'" aria-controls="stdt-coverage-body" @click="toggle('coverage')">
					<span class="kt-disclosure-title-row"><span class="kt-disclosure-title">View coverage details</span><span style="font-size: 13px; color: var(--kt-color-neutral-800)">Source locator, title, treatment, output anchor and reason for every source row</span></span>
					<svg class="kt-disclosure-chevron" :class="{ 'is-open': coverageOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m6 9 6 6 6-6"></path></svg>
				</button>
				<div v-if="coverageOpen" id="stdt-coverage-body" class="kt-disclosure-body">
					<CoverageDetails :release-id="release.release_id" :hash-state="hashState" @hash="(h) => $emit('hash', h)" />
				</div>
			</div>
			<div style="margin-top: 28px">
				<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap">
					<h3 class="stdt-h3" style="margin: 0">{{ data.coverage.changes.heading }}</h3>
					<span class="kt-tag" :class="data.coverage.changes.preceding_release ? 'kt-tag-accent' : 'kt-tag-neutral'" data-testid="stdt-change-result">{{ data.coverage.changes.result }}</span>
				</div>
				<p style="margin: 0 0 10px; font-size: 14px; color: var(--kt-color-neutral-800)">{{ data.coverage.changes.summary }}</p>
				<div style="display: flex; flex-wrap: wrap; gap: 6px"><span v-for="c in data.coverage.changes.chips" :key="c" class="kt-tag kt-tag-outline">{{ c }}</span></div>
			</div>
			<div class="kt-disclosure" style="margin-top: 12px" data-testid="stdt-changes-disclosure">
				<button type="button" class="kt-disclosure-head stdt-disclosure-button" :aria-expanded="changesOpen ? 'true' : 'false'" aria-controls="stdt-changes-body" @click="toggle('changes')">
					<span class="kt-disclosure-title-row"><span class="kt-disclosure-title">View change details</span><span style="font-size: 13px; color: var(--kt-color-neutral-800)">Grouped by change type and consequence</span></span>
					<svg class="kt-disclosure-chevron" :class="{ 'is-open': changesOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m6 9 6 6 6-6"></path></svg>
				</button>
				<div v-if="changesOpen" id="stdt-changes-body" class="kt-disclosure-body">
					<ChangeDetails :release-id="release.release_id" :hash-state="hashState" @hash="(h) => $emit('hash', h)" />
				</div>
			</div>
		</div>

		<div id="stdt-verification" class="kt-region" data-testid="stdt-section-verification">
			<h2>Verification</h2>
			<p style="margin: 0 0 12px; font-size: 14px; color: var(--kt-color-neutral-800)">{{ data.verification.caption }}</p>
			<table class="kt-table stdt-verification" style="width: 100%" data-testid="stdt-verification-table">
				<thead><tr><th style="text-transform: none; letter-spacing: 0; width: 260px">Check</th><th style="text-transform: none; letter-spacing: 0; width: 140px">Result</th><th style="text-transform: none; letter-spacing: 0">Explanation</th></tr></thead>
				<tbody>
					<tr v-for="v in data.verification.rows" :key="v.check">
						<td data-label="Check" style="font-weight: 600">{{ v.check }}</td>
						<td data-label="Result"><span class="kt-status" :class="v.result_class">{{ v.result }}</span></td>
						<td data-label="Explanation" style="color: var(--kt-color-neutral-800)">{{ v.note }}</td>
					</tr>
				</tbody>
			</table>
			<div class="stdt-verification-foot">
				<div class="kt-group">
					<h3 class="stdt-h3" style="margin-bottom: 8px">Source verification</h3>
					<div class="kt-meta-row is-tight" style="gap: 32px; font-size: 14px">
						<div><span class="kt-label">Last checked</span><span>{{ data.verification.source.last_checked }}</span></div>
						<div><span class="kt-label">Checked by</span><span>{{ data.verification.source.checked_by }}</span></div>
						<div><span class="kt-label">Outcome</span><span>{{ data.verification.source.outcome }}</span></div>
					</div>
				</div>
				<button type="button" class="kt-btn kt-btn-secondary" data-testid="stdt-report-concern" @click="$emit('report')"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path><line x1="4" x2="4" y1="22" y2="15"></line></svg>Report concern</button>
			</div>
			<div v-if="data.concerns && data.concerns.own.length" class="kt-group" style="margin-top: 16px" data-testid="stdt-own-concerns">
				<span class="kt-label" style="display: block; margin-bottom: 6px">Your concerns about this release</span>
				<ul style="margin: 0; padding-left: 18px; font-size: 14px; display: flex; flex-direction: column; gap: 4px">
					<li v-for="c in data.concerns.own" :key="c.concern_id">{{ c.summary }} — {{ c.category }} · <span class="kt-status" :class="c.status === 'Open' ? 'is-pending' : 'is-live'">{{ c.status }}</span></li>
				</ul>
			</div>
		</div>

		<div class="kt-disclosure" data-testid="stdt-technical">
			<button type="button" class="kt-disclosure-head stdt-disclosure-button" :aria-expanded="techOpen ? 'true' : 'false'" aria-controls="stdt-technical-body" @click="toggle('tech')">
				<span class="kt-disclosure-title-row"><span class="kt-disclosure-title">Technical details</span><span style="font-size: 13px; color: var(--kt-color-neutral-800)">Release and manifest identities, profiles, renderer version, digests, commit and schema versions</span></span>
				<svg class="kt-disclosure-chevron" :class="{ 'is-open': techOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m6 9 6 6 6-6"></path></svg>
			</button>
			<div v-if="techOpen" id="stdt-technical-body" class="kt-disclosure-body">
				<dl class="stdt-tech">
					<div v-for="t in data.technical" :key="t.label">
						<dt class="kt-label">{{ t.label }}</dt>
						<dd style="margin: 2px 0 0; color: var(--kt-color-neutral-800); overflow-wrap: anywhere">
							{{ t.value }}
							<button v-if="t.copy || /digest|ID|identity/i.test(t.label)" type="button" class="kt-btn kt-btn-ghost stdt-copy" :aria-label="`Copy ${t.label}`" @click="copy(t.value)">Copy</button>
						</dd>
					</div>
				</dl>
			</div>
		</div>

		<p style="margin: 0; font-size: 13px; color: var(--kt-color-neutral-700)" data-testid="stdt-footer">Last verified: {{ data.last_verified }}</p>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, watch } from "vue";
import { previewUrl, reviewPackUrl } from "../data/api.js";
import CoverageDetails from "./CoverageDetails.vue";
import ChangeDetails from "./ChangeDetails.vue";

const props = defineProps({
	data: { type: Object, required: true },
	loading: { type: Boolean, default: false },
	failed: { type: Boolean, default: false },
	hashState: { type: Object, default: () => ({}) },
});
const emit = defineEmits(["back", "retry", "hash", "report"]);

const SECTIONS = [
	{ id: "overview", label: "Overview" },
	{ id: "content", label: "Tender content" },
	{ id: "bid", label: "Bid response and downstream use" },
	{ id: "coverage", label: "Coverage and changes" },
	{ id: "verification", label: "Verification" },
];

const release = computed(() => props.data.release || {});
const variant = computed(() => props.data.variant || {});
const coverageOpen = computed(() => props.hashState.coverage === "1");
const changesOpen = computed(() => props.hashState.changes === "1");
const techOpen = computed(() => props.hashState.tech === "1");
const previewHref = (outputId) => previewUrl(release.value.release_id, outputId);
const reviewPackHref = computed(() => reviewPackUrl(release.value.release_id));

function toggle(name) {
	const open = props.hashState[name] === "1";
	emit("hash", { [name]: open ? "" : "1", __replace: true });
}
function selectSection(id) {
	emit("hash", { section: id });
	scrollTo(id);
}
function scrollTo(id) {
	nextTick(() => {
		const el = document.getElementById(`stdt-${id}`);
		if (el && el.scrollIntoView) el.scrollIntoView({ block: "start" });
	});
}
async function copy(value) {
	try {
		await navigator.clipboard.writeText(String(value));
		frappe.show_alert({ message: "Copied", indicator: "green" });
	} catch (e) {
		frappe.show_alert({ message: "Copy is not available in this browser.", indicator: "orange" });
	}
}

// Direct load, refresh and Back land on the selected section (§11.4).
onMounted(() => {
	if (props.hashState.section && props.data.outcome === "OK") scrollTo(props.hashState.section);
});
watch(
	() => props.data.outcome === "OK" && release.value.release_id,
	(ready) => {
		if (ready && props.hashState.section) scrollTo(props.hashState.section);
	}
);
</script>
