<script setup>
// BDS-CHG-001 v0.8 §10.10 BDS-DES-09 — Requirements and supporting evidence,
// ported from "Bid Board v3 - C" (1440 tables; 390 labelled cards). The task
// read groups the published requirements by the definition's compositions
// and decides each row's response, files and state, what must be fixed and
// each region's link state. A requirement row opens the response drawer; a
// file is its own command; Save and continue saves the offered-goods form and
// opens the next task. A refusal is named in place; typed entries survive
// re-reads.
import { computed, inject, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import PortalGuidance from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/PortalGuidance.vue";
import FieldControl from "../components/FieldControl.vue";
import ResponseDrawer from "../components/ResponseDrawer.vue";
import { fixRoute } from "../composables/fixRoute.js";
import { useNarrow } from "../composables/useNarrow.js";

const READ = "kentender_procurement.bid_submission.api.get_bid_task";
const SAVE = "kentender_procurement.bid_submission.api.save_bid_task";
const props = defineProps({
	initial: { type: Object, default: null },
	reference: { type: String, required: true },
});
const emit = defineEmits(["not-found"]);
const portal = inject("portal");
const { route, go, epoch } = portal.useRoute({ ref, onMounted, onUnmounted });
const narrow = useNarrow();
const data = ref(null);
const failure = ref("");
const errors = ref({});
const drawer = ref(null);
const goods = reactive({});
const guard = portal.createSequenceGuard();
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);
const bid = computed(() => (data.value ? { reference: data.value.bid.reference, record_version: data.value.bid.record_version } : null));
const rows = computed(() => (data.value ? [...data.value.technical, ...data.value.warranty, ...(data.value.experience ? data.value.experience.rows : []), ...data.value.acceptance, ...data.value.evidence] : []));

function goodsChanges() {
	const fields = (data.value && data.value.goods && data.value.goods.fields) || [];
	return Object.fromEntries(fields.filter((f) => f.editable && f.kind !== "evidence" && JSON.stringify(goods[f.handle]) !== JSON.stringify(f.value)).map((f) => [f.handle, goods[f.handle]]));
}
function adopt(result) {
	const unsaved = data.value ? goodsChanges() : {};
	data.value = result;
	for (const key of Object.keys(goods)) delete goods[key];
	for (const f of (result.goods && result.goods.fields) || []) goods[f.handle] = f.handle in unsaved ? unsaved[f.handle] : f.value;
}
if (props.initial) adopt(props.initial);

function read() {
	return portal.call(READ, { tender_reference: props.reference, bid_reference: "", task: "requirements", organisation: route.value.query.organisation || "" });
}
async function load() {
	const token = guard.next();
	try {
		const result = await read();
		if (!guard.isCurrent(token)) return;
		if (result && result.outcome === "NOT_FOUND") {
			emit("not-found");
			return;
		}
		adopt(result);
		failure.value = "";
	} catch (e) {
		if (guard.isCurrent(token)) failure.value = e.message;
	}
}
function open(key) {
	drawer.value = rows.value.find((row) => row.key === key) || null;
}
async function afterDrawer() {
	drawer.value = null;
	await load();
}
async function drawerChanged() {
	await load();
	if (drawer.value) open(drawer.value.key);
}
function saveAndContinue() {
	failure.value = "";
	errors.value = {};
	const answers = goodsChanges();
	if (!Object.keys(answers).length) return go(data.value.footer.next_href);
	return runner.run(async () => {
		const result = await portal.call(SAVE, { bid_reference: data.value.bid.reference, task: "requirements", values: JSON.stringify(answers), expected_record_version: data.value.bid.record_version, idempotency_key: `bds-requirements-${Date.now().toString(36)}` }, { type: "POST" });
		if (result && result.ok) go(data.value.footer.next_href);
		else if (result && result.errors) errors.value = result.errors;
		else if (result) failure.value = result.message || "";
	}, "Save and continue");
}
function onFix(fix) {
	const href = fixRoute(fix, props.reference);
	if (href && href !== route.value.path) go(href);
	else if (data.value.attention && data.value.attention.items.length) open(data.value.attention.items[0].key);
}
watch(epoch, () => load());
onMounted(() => {
	portal.setTitle(__("Requirements and supporting evidence"));
	if (!data.value) load();
});
</script>

<template>
	<div v-if="data" class="kt-page" data-testid="bds-requirements-task">
		<div class="kt-page-head">
			<div class="bds-head-main">
				<a :href="data.page.back_href" class="bds-back"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5" /><path d="m12 19-7-7 7-7" /></svg>{{ __("Back to bid") }}</a>
				<div class="bds-title-row">
					<h1 class="kt-page-title">{{ __(data.page.title) }}</h1>
					<span class="kt-status" :class="'is-' + data.badge.tone" data-testid="bds-requirements-badge">{{ data.badge.label }}</span>
				</div>
				<p class="kt-page-desc">{{ __(data.page.description) }}</p>
			</div>
		</div>

		<PortalGuidance :journey="data.journey" :answer="data.next_step" :label="__('Bid journey')" @fix="onFix" />

		<div v-if="data.attention" class="kt-notice" :class="data.attention.tone === 'critical' ? 'is-critical' : 'is-warning'" role="status" data-testid="bds-requirements-attention">
			<svg class="kt-notice-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 8v4" /><path d="M12 16h.01" /></svg>
			<div class="kt-notice-body">
				<strong>{{ data.attention.title }}</strong>
				<div v-for="item in data.attention.items" :key="item.key"><button type="button" class="bds-link-button" @click="open(item.key)">{{ item.label }}</button></div>
			</div>
		</div>

		<nav class="bds-section-nav" :aria-label="__('Requirement groups')" data-testid="bds-requirements-nav">
			<a v-for="section in data.sections" :key="section.key" :href="'#bds-region-' + section.key" class="bds-section-link"><span class="bds-section-name">{{ __(section.label) }}</span><span class="bds-section-state" :class="'is-' + section.tone">{{ section.status }}</span></a>
		</nav>

		<div v-if="data.goods" id="bds-region-goods" class="kt-region">
			<h2>{{ __("Offered goods") }}</h2>
			<div class="bds-region-body">
				<div class="bds-grid-2">
					<template v-for="field in data.goods.fields" :key="field.handle">
						<FieldControl v-if="field.kind !== 'evidence'" v-model="goods[field.handle]" :field="field" :error="errors[field.handle] || ''" :bid="bid" id-prefix="bds-goods" @changed="load" />
					</template>
					<div v-for="fact in data.goods.published" :key="fact.label" class="bds-drawer-fact"><span class="kt-label">{{ fact.label }}</span><span>{{ fact.value }}</span></div>
				</div>
				<template v-for="field in data.goods.fields" :key="'goods-proof-' + field.handle">
					<FieldControl v-if="field.kind === 'evidence'" :model-value="field.value" :field="field" :bid="bid" id-prefix="bds-goods" @changed="load" />
				</template>
			</div>
		</div>

		<template v-for="table in [['technical', 'Technical requirements'], ['warranty', 'Warranty and support']]" :key="table[0]">
		<div v-if="data[table[0]].length" :id="'bds-region-' + table[0]" class="kt-region">
			<h2>{{ __(table[1]) }}</h2>
			<div class="bds-region-body">
				<table v-if="!narrow" class="kt-table" :data-testid="'bds-' + table[0] + '-table'">
					<thead><tr><th>{{ __("Requirement") }}</th><th v-if="table[0] === 'technical'">{{ __("Tender requirement") }}</th><th>{{ __("Your response") }}</th><th>{{ __("Evidence") }}</th><th>{{ __("Status") }}</th></tr></thead>
					<tbody>
						<tr v-for="row in data[table[0]]" :key="row.key" :data-testid="'bds-row-' + row.key">
							<td class="bds-strong"><button type="button" class="bds-link-button bds-strong" @click="open(row.key)">{{ table[0] === 'warranty' && row.requirement ? row.label + ' ' + row.requirement : row.label }}</button></td>
							<td v-if="table[0] === 'technical'">{{ row.requirement }}</td>
							<td>{{ row.response }}</td>
							<td>{{ row.evidence }}</td>
							<td><span class="kt-status" :class="'is-' + row.tone">{{ row.status }}</span></td>
						</tr>
					</tbody>
				</table>
				<div v-else :data-testid="'bds-' + table[0] + '-cards'">
					<div v-for="row in data[table[0]]" :key="row.key" class="bds-card" :data-testid="'bds-row-' + row.key">
						<div class="bds-card-title">{{ row.label }}</div>
						<div v-if="row.requirement" class="bds-card-fact"><span class="kt-label">{{ __("Tender requirement") }}</span><span>{{ row.requirement }}</span></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Your response") }}</span><span>{{ row.response }}</span></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Evidence") }}</span><span>{{ row.evidence }}</span></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Status") }}</span><span><span class="kt-status" :class="'is-' + row.tone">{{ row.status }}</span></span></div>
						<div class="bds-card-actions"><button type="button" class="bds-link-button" @click="open(row.key)">{{ __("Edit") }}</button></div>
					</div>
				</div>
			</div>
		</div>
		</template>

		<div v-if="data.experience" id="bds-region-experience" class="kt-region">
			<h2>{{ __("Comparable experience") }}</h2>
			<div class="bds-region-body">
				<p v-if="data.experience.text" class="bds-muted">{{ data.experience.text }}</p>
				<table v-if="!narrow" class="kt-table" data-testid="bds-experience-table">
					<thead><tr><th>{{ __("Customer") }}</th><th>{{ __("Supply") }}</th><th>{{ __("Completion date") }}</th><th>{{ __("Evidence") }}</th><th>{{ __("Action") }}</th></tr></thead>
					<tbody>
						<tr v-for="row in data.experience.rows" :key="row.key" :data-testid="'bds-row-' + row.key">
							<td class="bds-strong">{{ row.customer || row.label }}</td>
							<td>{{ row.supply }}</td>
							<td>{{ row.completed }}</td>
							<td>{{ row.evidence }}</td>
							<td><button type="button" class="bds-link-button" @click="open(row.key)">{{ __("Edit") }}</button></td>
						</tr>
					</tbody>
				</table>
				<div v-else data-testid="bds-experience-cards">
					<div v-for="row in data.experience.rows" :key="row.key" class="bds-card">
						<div class="bds-card-title">{{ row.customer || row.label }}</div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Supply") }}</span><span>{{ row.supply }}</span></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Completion date") }}</span><span>{{ row.completed }}</span></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Evidence") }}</span><span>{{ row.evidence }}</span></div>
						<div class="bds-card-actions"><button type="button" class="bds-link-button" @click="open(row.key)">{{ __("Edit") }}</button></div>
					</div>
				</div>
			</div>
		</div>

		<div v-if="data.acceptance.length" id="bds-region-acceptance" class="kt-region" data-testid="bds-acceptance">
			<h2>{{ __("Acceptance") }}</h2>
			<div class="bds-region-body">
				<div v-for="row in data.acceptance" :key="row.key" class="bds-acceptance-row">
					<span>{{ row.label }}</span>
					<span class="kt-status" :class="'is-' + row.tone">{{ row.status }}</span>
					<button type="button" class="bds-link-button" @click="open(row.key)">{{ __("Edit") }}</button>
				</div>
			</div>
		</div>

		<div v-if="data.evidence.length" id="bds-region-evidence" class="kt-region">
			<h2>{{ __("Supporting evidence") }}</h2>
			<div class="bds-region-body">
				<table v-if="!narrow" class="kt-table" data-testid="bds-evidence-table">
					<thead><tr><th>{{ __("Evidence") }}</th><th>{{ __("File") }}</th><th>{{ __("Status") }}</th><th>{{ __("Action") }}</th></tr></thead>
					<tbody>
						<tr v-for="row in data.evidence" :key="row.key" :data-testid="'bds-row-' + row.key">
							<td class="bds-strong">{{ row.label }}</td>
							<td>{{ row.file || "—" }}</td>
							<td><span class="kt-status" :class="'is-' + row.file_tone">{{ row.file_status }}</span></td>
							<td><button type="button" class="bds-link-button" @click="open(row.key)">{{ row.file ? __("Replace") : __("Upload") }}</button></td>
						</tr>
					</tbody>
				</table>
				<div v-else data-testid="bds-evidence-cards">
					<div v-for="row in data.evidence" :key="row.key" class="bds-card">
						<div class="bds-card-title">{{ row.label }}</div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("File") }}</span><span>{{ row.file || "—" }}</span></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Status") }}</span><span><span class="kt-status" :class="'is-' + row.file_tone">{{ row.file_status }}</span></span></div>
						<div class="bds-card-actions"><button type="button" class="bds-link-button" @click="open(row.key)">{{ row.file ? __("Replace") : __("Upload") }}</button></div>
					</div>
				</div>
			</div>
		</div>

		<div v-if="failure" class="kt-notice is-critical bds-load-failure" role="alert" data-testid="bds-load-failure"><div class="kt-notice-body">{{ failure }}</div></div>

		<div v-if="narrow" class="bds-footer-stack">
			<button type="button" class="kt-btn kt-btn-primary bds-btn-block" :disabled="pending" data-testid="bds-requirements-save" @click="saveAndContinue">{{ pending ? __("Saving…") : __(data.footer.save_label) }}</button>
			<a :href="data.page.back_href" class="kt-btn kt-btn-secondary bds-btn-block">{{ __("Back to bid") }}</a>
		</div>
		<div v-else class="bds-footer">
			<a :href="data.page.back_href" class="kt-btn kt-btn-secondary">{{ __("Back to bid") }}</a>
			<div class="bds-footer-end"><button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bds-requirements-save" @click="saveAndContinue">{{ pending ? __("Saving…") : __(data.footer.save_label) }}</button></div>
		</div>

		<ResponseDrawer v-if="drawer" :key="drawer.key" :group="drawer" task="requirements" :bid="bid" @close="drawer = null" @saved="afterDrawer" @changed="drawerChanged" />
	</div>
	<div v-else-if="failure" class="kt-page">
		<div class="kt-notice is-critical bds-load-failure" role="alert">
			<div class="kt-notice-body">{{ failure }}</div>
			<button type="button" class="kt-btn kt-btn-secondary" @click="load">{{ __("Try again") }}</button>
		</div>
	</div>
	<div v-else class="kt-page" aria-hidden="true"><div class="bds-skeleton" data-testid="bds-requirements-loading"></div></div>
</template>
