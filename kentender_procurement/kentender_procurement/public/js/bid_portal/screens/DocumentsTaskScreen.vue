<script setup>
// BDS-CHG-001 v0.8 §10.8 BDS-DES-07 — Tender documents, clarifications and
// addenda, ported from "Bid Board v3 - B" (1440 tables; 390 labelled cards).
// The task read decides the documents, each addendum's notice state and this
// bid's acknowledgement, the answers and their notice result, whether a
// question may be asked and whether Save and continue waits. Save and
// continue saves an acknowledgement through `SaveBidTask`, then opens the
// next task; a refusal is named in place and the tick is kept.
import { computed, inject, onMounted, onUnmounted, ref, watch } from "vue";
import PortalGuidance from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/PortalGuidance.vue";
import CommonState from "../components/CommonState.vue";
import NotifySignatory from "../components/NotifySignatory.vue";
import TaskStepper from "../components/TaskStepper.vue";
import NoticeContactDialog from "../components/NoticeContactDialog.vue";
import MyQuestions from "../components/MyQuestions.vue";
import QuestionDialog from "../components/QuestionDialog.vue";
import { fixRoute } from "../composables/fixRoute.js";
import { useNarrow } from "../composables/useNarrow.js";
import { arrive, destinationOf } from "../composables/saveDestination.js";

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
const data = ref(props.initial);
// the server says whether this Draft can change now (closed, or its bound
// release withdrawn): read-only fields and no Save and continue otherwise
const canEdit = computed(() => !data.value || !data.value.bid || data.value.bid.editable !== false);
const failure = ref("");
const errors = ref({});
const ticks = ref({}); // addendum reference → the caller's own tick, until saved
const asking = ref(false);
const updatingContact = ref(false);
const guard = portal.createSequenceGuard();
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);

const acknowledged = computed(() => ((data.value && data.value.addenda) || []).filter((a) => a.acknowledgement));
function ticked(a) {
	return a.reference in ticks.value ? ticks.value[a.reference] : a.acknowledgement.value;
}
const waiting = computed(() => acknowledged.value.some((a) => !ticked(a)));
const addendaHeading = computed(() => {
	const count = ((data.value && data.value.addenda) || []).length;
	return count === 0 ? __("Addenda") : count === 1 ? __("Issued addendum") : __("Issued addenda");
});

function read() {
	return portal.call(READ, { tender_reference: props.reference, bid_reference: "", task: "documents", organisation: route.value.query.organisation || "" });
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
		data.value = result;
		failure.value = "";
	} catch (e) {
		if (guard.isCurrent(token)) failure.value = e.message;
	}
}
function save(values) {
	return portal.call(SAVE, { bid_reference: data.value.bid.reference, task: "documents", values: JSON.stringify(values), expected_record_version: data.value.bid.record_version, idempotency_key: `bds-documents-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}` }, { type: "POST" });
}
// A Draft still bound to an earlier definition moves first (its next save
// does that and asks for review); the acknowledgement then has its field
// and is saved as ticked. Nothing ticked means nothing to save.
function saveAndContinue() {
	failure.value = "";
	errors.value = {};
	const changed = acknowledged.value.filter((a) => ticked(a) !== a.acknowledgement.value);
	const destination = destinationOf(data.value.footer);
	if (!changed.length) return arrive(destination, { go, load });
	return runner.run(async () => {
		if (changed.some((a) => a.acknowledgement.moves_bid)) {
			const moved = await save({});
			if (!(moved && (moved.ok || moved.refreshed))) {
				failure.value = (moved && moved.message) || "";
				return;
			}
			data.value = await read();
		}
		const values = {};
		for (const a of acknowledged.value) {
			if (a.reference in ticks.value && ticks.value[a.reference] !== a.acknowledgement.value && a.acknowledgement.handle) values[a.acknowledgement.handle] = ticks.value[a.reference];
		}
		if (Object.keys(values).length) {
			const result = await save(values);
			if (!(result && result.ok)) {
				if (result && result.errors) errors.value = result.errors;
				else if (result) failure.value = result.message || "";
				return;
			}
		}
		ticks.value = {};
		await arrive(destination, { go, load });
	}, "Save and continue");
}
function onFix(fix) {
	const href = fixRoute(fix, props.reference);
	if (href && href !== route.value.path) go(href);
}
async function contactUpdated() {
	updatingContact.value = false;
	await load();
}
watch(epoch, () => load());
onMounted(() => {
	portal.setTitle(__("Tender documents, clarifications and addenda"));
	if (!data.value) load();
});
</script>

<template>
	<div v-if="data" class="kt-page" data-testid="bds-documents-task">
		<TaskStepper v-if="data.step" :step="data.step" />
		<div class="kt-page-head">
			<div class="bds-head-main">
				<a :href="data.page.back_href" class="bds-back" data-testid="bds-documents-back"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5" /><path d="m12 19-7-7 7-7" /></svg>{{ __("Back to bid") }}</a>
				<div class="bds-title-row">
					<h1 class="kt-page-title">{{ __(data.page.title) }}</h1>
					<span v-if="data.badge" class="kt-status" :class="'is-' + data.badge.tone" data-testid="bds-documents-badge">{{ data.badge.label }}</span>
				</div>
				<p class="kt-page-desc">{{ __(data.page.description) }}</p>
			</div>
		</div>

		<PortalGuidance :journey="data.journey" :answer="data.next_step" :label="__('Bid journey')" @fix="onFix" />

		<NotifySignatory v-if="data.handover && data.bid" :handover="data.handover" :bid="data.bid" :organisation="route.query.organisation || ''" @sent="load" />

		<div class="kt-region">
			<h2>{{ __("Official Tender documents") }}</h2>
			<div class="bds-region-body">
				<table v-if="!narrow" class="table" data-testid="bds-task-documents-table">
					<thead><tr><th>{{ __("Document") }}</th><th>{{ __("Published") }}</th><th>{{ __("Action") }}</th></tr></thead>
					<tbody>
						<tr v-for="d in data.documents" :key="d.key">
							<td class="bds-strong">{{ d.label }}</td>
							<td>{{ d.published }}</td>
							<td><a :href="d.view_href" target="_blank" rel="noopener">{{ __("View") }}</a> · <a :href="d.download_href">{{ __("Download") }}</a></td>
						</tr>
					</tbody>
				</table>
				<div v-else data-testid="bds-task-documents-cards">
					<div v-for="d in data.documents" :key="d.key" class="bds-card">
						<div class="bds-card-title">{{ d.label }}</div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Published") }}</span><span>{{ d.published }}</span></div>
						<div class="bds-card-actions"><a :href="d.view_href" target="_blank" rel="noopener">{{ __("View") }}</a> · <a :href="d.download_href">{{ __("Download") }}</a></div>
					</div>
				</div>
			</div>
		</div>

		<div class="kt-region">
			<h2>{{ addendaHeading }}</h2>
			<div class="bds-region-body">
				<template v-if="data.addenda.length">
					<table v-if="!narrow" class="table" data-testid="bds-task-addenda-table">
						<thead><tr><th>{{ __("Addendum") }}</th><th>{{ __("Issued") }}</th><th>{{ __("Revised deadline") }}</th><th>{{ __("Action") }}</th></tr></thead>
						<tbody>
							<tr v-for="a in data.addenda" :key="a.reference">
								<td class="bds-strong">{{ a.label }}</td>
								<td>{{ a.issued }}</td>
								<td>{{ a.revised_deadline }}</td>
								<td><template v-if="a.view_href"><a :href="a.view_href" target="_blank" rel="noopener">{{ __("View") }}</a> · <a :href="a.download_href">{{ __("Download") }}</a></template></td>
							</tr>
						</tbody>
					</table>
					<div v-else data-testid="bds-task-addenda-cards">
						<div v-for="a in data.addenda" :key="a.reference" class="bds-card">
							<div class="bds-card-title">{{ a.label }}</div>
							<div class="bds-card-fact"><span class="kt-label">{{ __("Issued") }}</span><span>{{ a.issued }}</span></div>
							<div class="bds-card-fact"><span class="kt-label">{{ __("Revised deadline") }}</span><span>{{ a.revised_deadline }}</span></div>
							<div class="bds-card-actions"><template v-if="a.view_href"><a :href="a.view_href" target="_blank" rel="noopener">{{ __("View") }}</a> · <a :href="a.download_href">{{ __("Download") }}</a></template></div>
						</div>
					</div>
					<template v-for="a in data.addenda" :key="'ack-' + a.reference">
						<div v-if="a.notice" class="kt-group bds-notice-group" :data-testid="'bds-addendum-notice-' + a.reference">
							<div class="bds-notice-line"><span class="kt-label">{{ a.notice.destination }}</span><span class="kt-status" :class="'is-' + a.notice.tone">{{ a.notice.status }}</span></div>
							<p class="bds-muted">{{ a.notice.text }}</p>
							<div v-if="a.notice.can_update_contact"><button type="button" class="btn btn-secondary" :class="{ 'bds-btn-touch': narrow }" data-testid="bds-update-notice-email" @click="updatingContact = true">{{ __("Update notice email") }}</button></div>
						</div>
						<template v-if="a.acknowledgement">
							<label class="kt-checkbox bds-acknowledge" :data-testid="'bds-acknowledge-' + a.reference">
								<input type="checkbox" :checked="ticked(a)" :aria-invalid="!!errors[a.acknowledgement.handle]" @change="ticks = { ...ticks, [a.reference]: $event.target.checked }" />
								<span class="box"></span>
								<span>{{ a.acknowledgement.label }}</span>
							</label>
							<p v-if="errors[a.acknowledgement.handle]" class="kt-field-error">{{ errors[a.acknowledgement.handle] }}</p>
							<p v-if="a.acknowledgement.acknowledged_text && ticked(a)" class="bds-muted" data-testid="bds-acknowledged">{{ a.acknowledgement.acknowledged_text }}</p>
						</template>
					</template>
				</template>
				<p v-else class="bds-muted" data-testid="bds-task-no-addenda">{{ __("No addenda have been issued.") }}</p>
			</div>
		</div>

		<div class="kt-region">
			<div v-if="data.clarification.can_ask" class="bds-region-head">
				<h2>{{ __("Questions and answers") }}</h2>
				<div class="bds-region-actions"><button type="button" class="btn btn-secondary" :class="{ 'bds-btn-touch': narrow }" data-testid="bds-task-ask" @click="asking = true">{{ __("Ask a question") }}</button></div>
			</div>
			<h2 v-else>{{ __("Questions and answers") }}</h2>
			<div class="bds-region-body">
				<div v-for="q in data.answers" :key="q.key" class="kt-group bds-answer">
					<span class="bds-strong">{{ q.question }}</span>
					<span class="bds-answer-text">{{ q.answer }}</span>
					<div class="bds-notice-line"><span class="kt-label">{{ q.answered }}</span><span v-if="q.notice" class="kt-status" :class="'is-' + q.notice.tone">{{ q.notice.status }}</span></div>
				</div>
				<p v-if="!data.answers.length" class="bds-muted" data-testid="bds-task-no-answers">{{ __("No answers published yet.") }}</p>
				<MyQuestions :questions="data.my_questions" testid="bds-task-my-questions" />
				<p v-if="data.clarification.closed_text" class="bds-muted" data-testid="bds-task-clarifications-closed">{{ data.clarification.closed_text }}</p>
			</div>
		</div>

		<div v-if="failure" class="kt-notice is-critical bds-load-failure" role="alert" data-testid="bds-load-failure">
			<div class="kt-notice-body">{{ failure }}</div>
		</div>

		<div v-if="narrow" class="bds-footer-stack">
			<p v-if="waiting" class="bds-muted" data-testid="bds-documents-blocked">{{ data.footer.blocked_text || __("Acknowledge the addendum to continue.") }}</p>
			<button v-if="canEdit" type="button" class="btn btn-primary bds-btn-block" :disabled="waiting || pending" data-testid="bds-documents-save" @click="saveAndContinue">{{ pending ? __("Saving…") : __(data.footer.save_label) }}</button>
			<a :href="data.page.back_href" class="btn btn-secondary bds-btn-block">{{ __("Back to bid") }}</a>
		</div>
		<div v-else class="bds-footer">
			<a :href="data.page.back_href" class="btn btn-secondary">{{ __("Back to bid") }}</a>
			<div class="bds-footer-end">
				<p v-if="waiting" class="bds-muted" data-testid="bds-documents-blocked">{{ data.footer.blocked_text || __("Acknowledge the addendum to continue.") }}</p>
				<button v-if="canEdit" type="button" class="btn btn-primary" :disabled="waiting || pending" data-testid="bds-documents-save" @click="saveAndContinue">{{ pending ? __("Saving…") : __(data.footer.save_label) }}</button>
			</div>
		</div>

		<QuestionDialog v-if="asking" :tender="{ reference, title: (data.tender && data.tender.title) || '' }" :organisation="data.organisation" @close="asking = false" @sent="load" />
		<NoticeContactDialog v-if="updatingContact" :contact="data.notice_contact" @close="updatingContact = false" @saved="contactUpdated" />
	</div>
	<CommonState v-else-if="failure" state="load-failure" @action="load" />
	<div v-else class="kt-page" aria-hidden="true"><div class="bds-skeleton" data-testid="bds-documents-loading"></div></div>
</template>
