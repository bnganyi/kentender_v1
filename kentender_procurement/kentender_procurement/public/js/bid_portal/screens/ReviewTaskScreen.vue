<script setup>
// BDS-CHG-001 v0.8 §10.12 BDS-DES-11 — Review bid, ported from "Bid Board v3
// - D" (1440 table; 390 labelled cards). The read decides everything shown:
// the one header action this viewer may take (Submit bid for the Authorised
// Signatory on a Ready bid; Continue saved bid while supplier portal
// information is restored), the computed result, the physical original, the
// summary, the five tasks with their exact issue links, what is offered, the
// declarations and evidence, and the price summary. Nothing is saved here.
import { inject, onMounted, onUnmounted, ref, watch } from "vue";
import PortalGuidance from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/PortalGuidance.vue";
import CommonState from "../components/CommonState.vue";
import { fixRoute } from "../composables/fixRoute.js";
import { useNarrow } from "../composables/useNarrow.js";

const READ = "kentender_procurement.bid_submission.api.get_bid_task";
const props = defineProps({
	initial: { type: Object, default: null },
	reference: { type: String, required: true },
});
const emit = defineEmits(["not-found"]);
const portal = inject("portal");
const { route, go, epoch } = portal.useRoute({ ref, onMounted, onUnmounted });
const narrow = useNarrow();
const data = ref(props.initial);
const failure = ref("");
const guard = portal.createSequenceGuard();

async function load() {
	const token = guard.next();
	try {
		const result = await portal.call(READ, { tender_reference: props.reference, bid_reference: "", task: "review", organisation: route.value.query.organisation || "" });
		if (!guard.isCurrent(token)) return;
		if (result && result.outcome === "NOT_FOUND") {
			emit("not-found");
			return;
		}
		data.value = result;
		failure.value = "";
	} catch (e) {
		if (guard.isCurrent(token)) failure.value = e.message;
	}
}
function onFix(fix) {
	const href = fixRoute(fix, props.reference);
	if (href && href !== route.value.path) go(href);
}
watch(epoch, () => load());
onMounted(() => {
	portal.setTitle(__("Review bid"));
	if (!data.value) load();
});
</script>

<template>
	<div v-if="data" class="kt-page" data-testid="bds-review-task">
		<div class="kt-page-head">
			<div class="bds-head-main">
				<a :href="data.page.back_href" class="bds-back"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5" /><path d="m12 19-7-7 7-7" /></svg>{{ __("Back to bid") }}</a>
				<div class="bds-title-row"><h1 class="kt-page-title">{{ __(data.page.title) }}</h1></div>
				<p class="kt-page-desc">{{ __(data.page.description) }}</p>
			</div>
			<div v-if="data.page.action" class="kt-page-actions" :class="{ 'bds-actions-stack': narrow }">
				<a :href="data.page.action.href" class="kt-btn" :class="[data.page.action.tone === 'primary' ? 'kt-btn-primary' : 'kt-btn-secondary', narrow ? 'bds-btn-block' : '']" data-testid="bds-review-action">{{ __(data.page.action.label) }}</a>
			</div>
		</div>

		<PortalGuidance :journey="data.journey" :answer="data.next_step" :label="__('Bid journey')" @fix="onFix" />

		<div v-if="data.result" class="kt-notice" :class="'is-' + data.result.tone" role="status" data-testid="bds-review-result">
			<svg class="kt-notice-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10" /><path d="m9 12 2 2 4-4" /></svg>
			<div class="kt-notice-body"><div>{{ data.result.text }}</div></div>
		</div>
		<div v-if="data.availability_notice" class="kt-notice" :class="'is-' + data.availability_notice.tone" role="status" data-testid="bds-review-availability">
			<svg class="kt-notice-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3" /><path d="M12 9v4" /><path d="M12 17h.01" /></svg>
			<div class="kt-notice-body">
				<strong>{{ data.availability_notice.title }}</strong>
				<div>{{ data.availability_notice.text }}</div>
			</div>
		</div>
		<div v-if="data.security_notice" class="kt-notice" :class="'is-' + data.security_notice.tone" role="status" data-testid="bds-review-security">
			<svg class="kt-notice-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10" /><path v-if="data.security_notice.tone === 'live'" d="m9 12 2 2 4-4" /><path v-else d="M12 8v4M12 16h.01" /></svg>
			<div class="kt-notice-body">
				<strong v-if="data.security_notice.title">{{ data.security_notice.title }}</strong>
				<div>{{ data.security_notice.text }}</div>
			</div>
		</div>

		<div class="bds-facts" data-testid="bds-review-summary">
			<div v-for="fact in data.summary" :key="fact.label" class="bds-fact"><span class="kt-label">{{ __(fact.label) }}</span><span class="bds-fact-value"><strong v-if="fact.strong">{{ fact.value }}</strong><template v-else>{{ fact.value }}</template></span></div>
		</div>

		<div class="kt-region">
			<h2>{{ __("Bid tasks") }}</h2>
			<div class="bds-region-body">
				<table v-if="!narrow" class="kt-table" data-testid="bds-review-tasks">
					<thead><tr><th>{{ __("Task") }}</th><th>{{ __("Status") }}</th><th>{{ __("Action") }}</th></tr></thead>
					<tbody>
						<tr v-for="row in data.task_rows" :key="row.key" :data-testid="'bds-review-task-' + row.key">
							<td class="bds-strong">
								{{ __(row.label) }}
								<div v-for="issue in row.issues" :key="issue.href + issue.label" class="bds-issue-link"><a :href="issue.href">{{ issue.label }}</a></div>
							</td>
							<td><span class="kt-status" :class="'is-' + row.tone">{{ __(row.status) }}</span></td>
							<td><a v-if="row.href" :href="row.href">{{ __("Review") }}</a><template v-else>—</template></td>
						</tr>
					</tbody>
				</table>
				<div v-else data-testid="bds-review-task-cards">
					<div v-for="row in data.task_rows" :key="row.key" class="bds-card">
						<div class="bds-card-title">{{ __(row.label) }}</div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Status") }}</span><span><span class="kt-status" :class="'is-' + row.tone">{{ __(row.status) }}</span></span></div>
						<div v-if="row.href || row.issues.length" class="bds-card-actions">
							<a v-for="issue in row.issues" :key="issue.href + issue.label" :href="issue.href">{{ issue.label }}</a>
							<a v-if="row.href" :href="row.href">{{ __("Review") }}</a>
						</div>
					</div>
				</div>
			</div>
		</div>

		<div class="kt-region">
			<h2>{{ __("What you are offering") }}</h2>
			<div class="bds-region-body">
				<div class="bds-facts" data-testid="bds-review-offering">
					<div v-for="fact in data.offering" :key="fact.label" class="bds-fact"><span class="kt-label">{{ __(fact.label) }}</span><span class="bds-fact-value">{{ fact.value || "—" }}</span></div>
				</div>
			</div>
		</div>

		<div class="kt-region">
			<h2>{{ __("Declarations and evidence") }}</h2>
			<div class="bds-region-body">
				<div class="bds-facts" data-testid="bds-review-declarations">
					<div v-for="fact in data.declarations" :key="fact.label" class="bds-fact"><span class="kt-label">{{ __(fact.label) }}</span><span class="bds-fact-value">{{ fact.value }}</span></div>
				</div>
			</div>
		</div>

		<div class="kt-region">
			<h2>{{ __("Price summary") }}</h2>
			<div class="bds-region-body">
				<div class="bds-facts" data-testid="bds-review-price">
					<div v-for="fact in data.price_summary" :key="fact.label" class="bds-fact"><span class="kt-label">{{ __(fact.label) }}</span><span class="bds-fact-value"><strong v-if="fact.strong">{{ fact.value }}</strong><template v-else>{{ fact.value }}</template></span></div>
				</div>
			</div>
		</div>

		<div v-if="failure" class="kt-notice is-critical bds-load-failure" role="alert" data-testid="bds-load-failure"><div class="kt-notice-body">{{ failure }}</div></div>

		<div v-if="narrow" class="bds-footer-stack">
			<a v-if="data.footer.submit" :href="data.footer.submit.href" class="kt-btn kt-btn-primary bds-btn-block" data-testid="bds-review-submit">{{ __(data.footer.submit.label) }}</a>
			<a :href="data.footer.back_href" class="kt-btn kt-btn-secondary bds-btn-block">{{ __("Back to bid") }}</a>
		</div>
		<div v-else class="bds-footer">
			<a :href="data.footer.back_href" class="kt-btn kt-btn-secondary">{{ __("Back to bid") }}</a>
			<div v-if="data.footer.submit" class="bds-footer-end"><a :href="data.footer.submit.href" class="kt-btn kt-btn-primary" data-testid="bds-review-submit">{{ __(data.footer.submit.label) }}</a></div>
		</div>
	</div>
	<CommonState v-else-if="failure" state="load-failure" @action="load" />
	<div v-else class="kt-page" aria-hidden="true"><div class="bds-skeleton" data-testid="bds-review-loading"></div></div>
</template>
