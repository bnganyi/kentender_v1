<script setup>
// BDS-CHG-001 v0.8 §10.11 BDS-DES-10 — Price, ported from "Bid Board v3 - C"
// (1440 table; 390 labelled cards). The read gives each published line with
// its quantity and unit, the bid's unit price and tax inputs, and the server's
// calculated line amount, subtotal, tax and bid total; nothing is calculated
// here and no total is entered. Save and continue saves the changed prices,
// then opens the review; until every line is priced it says what is missing.
import { computed, inject, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import PortalGuidance from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/PortalGuidance.vue";
import CommonState from "../components/CommonState.vue";
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
// the server says whether this Draft can change now (closed, or its bound
// release withdrawn): read-only fields and no Save and continue otherwise
const canEdit = computed(() => !data.value || !data.value.bid || data.value.bid.editable !== false);
const failure = ref("");
const errors = ref({});
const prices = reactive({});
const guard = portal.createSequenceGuard();
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);

function inputs(result) {
	return (result.lines || []).flatMap((line) => [line.unit_price, line.tax]).filter(Boolean);
}
function changes() {
	return Object.fromEntries(inputs(data.value).filter((f) => f.editable && JSON.stringify(prices[f.handle] ?? null) !== JSON.stringify(f.value ?? null)).map((f) => [f.handle, prices[f.handle]]));
}
function adopt(result) {
	const unsaved = data.value ? changes() : {};
	data.value = result;
	for (const key of Object.keys(prices)) delete prices[key];
	for (const f of inputs(result)) prices[f.handle] = f.handle in unsaved ? unsaved[f.handle] : f.value;
}
if (props.initial) adopt(props.initial);
const unpriced = computed(() => !!data.value && inputs(data.value).some((f) => prices[f.handle] === null || prices[f.handle] === undefined || prices[f.handle] === ""));

async function load() {
	const token = guard.next();
	try {
		const result = await portal.call(READ, { tender_reference: props.reference, bid_reference: "", task: "price", organisation: route.value.query.organisation || "" });
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
// A changed price is saved at once so the server's line amount and totals
// show beside it; typed entries on other lines survive the re-read.
// Saves run one at a time; an entry made while one is saving is saved right
// after it, never dropped.
let queued = null;
function savePrices() {
	if (runner.pending.value) {
		queued = queued || new Promise((resolve) => {
			const stop = watch(() => runner.pending.value, (busy) => {
				if (busy) return;
				stop();
				queued = null;
				resolve(savePrices());
			});
		});
		return queued;
	}
	const answers = changes();
	if (!Object.keys(answers).length) return Promise.resolve(true);
	return runner.run(async () => {
		failure.value = ""; // only when a save really starts
		errors.value = {};
		const result = await portal.call(SAVE, { bid_reference: data.value.bid.reference, task: "price", values: JSON.stringify(answers), expected_record_version: data.value.bid.record_version, idempotency_key: `bds-price-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}` }, { type: "POST" });
		if (result && result.ok) {
			for (const [handle] of Object.entries(answers)) {
				const field = inputs(data.value).find((f) => f.handle === handle);
				if (field) field.value = prices[handle]; // saved: no longer an unsaved entry
			}
			await load();
			return true;
		}
		if (result && result.errors) errors.value = result.errors;
		else if (result) failure.value = result.message || "";
		return false;
	}, "Save price");
}
function saveAndContinue() {
	failure.value = "";
	errors.value = {};
	if (!Object.keys(changes()).length) return go(data.value.footer.next_href);
	return savePrices().then((ok) => ok && go(data.value.footer.next_href));
}
function onFix(fix) {
	const href = fixRoute(fix, props.reference);
	if (href && href !== route.value.path) go(href);
}
watch(epoch, () => load());
onMounted(() => {
	portal.setTitle(__("Price"));
	if (!data.value) load();
});
</script>

<template>
	<div v-if="data" class="kt-page" data-testid="bds-price-task">
		<div class="kt-page-head">
			<div class="bds-head-main">
				<a :href="data.page.back_href" class="bds-back"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5" /><path d="m12 19-7-7 7-7" /></svg>{{ __("Back to bid") }}</a>
				<div class="bds-title-row">
					<h1 class="kt-page-title">{{ __(data.page.title) }}</h1>
					<span class="kt-status" :class="'is-' + data.badge.tone" data-testid="bds-price-badge">{{ data.badge.label }}</span>
				</div>
				<p class="kt-page-desc">{{ __(data.page.description) }}</p>
			</div>
		</div>

		<PortalGuidance :journey="data.journey" :answer="data.next_step" :label="__('Bid journey')" @fix="onFix" />
		<p v-if="data.terms" class="bds-muted bds-price-terms">{{ data.terms }}</p>

		<div class="kt-region">
			<h2>{{ __("Price schedule") }}</h2>
			<div class="bds-region-body">
				<table v-if="!narrow" class="kt-table" data-testid="bds-price-table">
					<thead><tr><th>{{ __("Item") }}</th><th class="is-num">{{ __("Quantity") }}</th><th>{{ __("Unit") }}</th><th class="is-num">{{ __("Unit price excluding tax") }}</th><th class="is-num">{{ __("Tax on this line") }}</th><th class="is-num">{{ __("Line amount before tax") }}</th></tr></thead>
					<tbody>
						<tr v-for="line in data.lines" :key="line.line" :data-testid="'bds-price-line-' + line.line">
							<td class="bds-strong">{{ line.description }}</td>
							<td class="is-num">{{ line.quantity }}</td>
							<td>{{ line.unit }}</td>
							<td class="is-num">
								<input v-if="line.unit_price" v-model="prices[line.unit_price.handle]" class="kt-input bds-money" inputmode="decimal" :disabled="!line.unit_price.editable" :aria-label="__('Unit price excluding tax')" @change="savePrices" :aria-invalid="!!errors[line.unit_price.handle]" :data-testid="'bds-unit-price-' + line.line" />
								<p v-if="line.unit_price && errors[line.unit_price.handle]" class="kt-field-error">{{ errors[line.unit_price.handle] }}</p>
							</td>
							<td class="is-num">
								<input v-if="line.tax" v-model="prices[line.tax.handle]" class="kt-input bds-money" inputmode="decimal" :disabled="!line.tax.editable" :aria-label="__('Tax on this line')" @change="savePrices" :aria-invalid="!!errors[line.tax.handle]" :data-testid="'bds-tax-' + line.line" />
								<p v-if="line.tax && errors[line.tax.handle]" class="kt-field-error">{{ errors[line.tax.handle] }}</p>
							</td>
							<td class="is-num"><strong>{{ line.amount_before_tax }}</strong></td>
						</tr>
					</tbody>
				</table>
				<div v-else data-testid="bds-price-cards">
					<div v-for="line in data.lines" :key="line.line" class="bds-card">
						<div class="bds-card-title">{{ line.description }}</div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Quantity") }}</span><span>{{ line.quantity }}</span></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Unit") }}</span><span>{{ line.unit }}</span></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Unit price excluding tax") }}</span><span><input v-if="line.unit_price" v-model="prices[line.unit_price.handle]" class="kt-input bds-money" inputmode="decimal" :disabled="!line.unit_price.editable" :aria-label="__('Unit price excluding tax')" /></span></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Tax on this line") }}</span><span><input v-if="line.tax" v-model="prices[line.tax.handle]" class="kt-input bds-money" inputmode="decimal" :disabled="!line.tax.editable" :aria-label="__('Tax on this line')" /></span></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Line amount before tax") }}</span><span><strong>{{ line.amount_before_tax }}</strong></span></div>
					</div>
				</div>
				<div class="bds-totals" data-testid="bds-price-totals">
					<div class="bds-total-line"><span class="kt-label">{{ __("Subtotal excluding tax") }}</span><span class="is-num">{{ data.totals.subtotal }}</span></div>
					<div class="bds-total-line"><span class="kt-label">{{ __("Tax") }}</span><span class="is-num">{{ data.totals.tax }}</span></div>
					<div class="bds-total-line bds-grand-total"><span>{{ __("Bid total") }}</span><span class="is-num" data-testid="bds-bid-total">{{ data.totals.total }}</span></div>
				</div>
				<p class="bds-muted">{{ data.note }}</p>
			</div>
		</div>

		<div v-if="failure" class="kt-notice is-critical bds-load-failure" role="alert" data-testid="bds-load-failure"><div class="kt-notice-body">{{ failure }}</div></div>

		<div v-if="narrow" class="bds-footer-stack">
			<p v-if="unpriced" class="bds-muted">{{ __("Enter the unit price before continuing.") }}</p>
			<button v-if="canEdit" type="button" class="kt-btn kt-btn-primary bds-btn-block" :disabled="pending" data-testid="bds-price-save" @click="saveAndContinue">{{ pending ? __("Saving…") : __(data.footer.save_label) }}</button>
			<a :href="data.page.back_href" class="kt-btn kt-btn-secondary bds-btn-block">{{ __("Back to bid") }}</a>
		</div>
		<div v-else class="bds-footer">
			<a :href="data.page.back_href" class="kt-btn kt-btn-secondary">{{ __("Back to bid") }}</a>
			<div class="bds-footer-end">
				<p v-if="unpriced" class="bds-muted" data-testid="bds-price-missing">{{ __("Enter the unit price before continuing.") }}</p>
				<button v-if="canEdit" type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bds-price-save" @click="saveAndContinue">{{ pending ? __("Saving…") : __(data.footer.save_label) }}</button>
			</div>
		</div>
	</div>
	<CommonState v-else-if="failure" state="load-failure" @action="load" />
	<div v-else class="kt-page" aria-hidden="true"><div class="bds-skeleton" data-testid="bds-price-loading"></div></div>
</template>
