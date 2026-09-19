<!-- TPR-DES-09 Published Tender (every actor variant, no-addendum and
     submission-ended), ported class-for-class. It also serves as the plain
     record view for a reader on any other status (§10.4 "record"): the
     same head, facts, content sections and history — no business action. -->
<template>
	<div class="tnd-page" data-screen-label="TPR-DES-09 Published Tender">
		<BlueprintCard>
			<RecordHead :title="tender.title" :badge="tender.badge" :badge-tone="badgeTone" :refs="tender.tender_reference" :lede="lede">
				<template v-if="published" #aside>
					<button type="button" class="kt-btn kt-btn-secondary" style="flex-shrink: 0" data-testid="tnd-view-public" @click="$emit('view-document', 'Complete Tender', 'Public')">View public Tender</button>
				</template>
			</RecordHead>
			<div v-if="published" class="tnd-section tnd-grid-4" data-testid="tnd-published-facts">
				<div class="tnd-fact"><div class="kt-label">Published at</div><div class="tnd-fact-value">{{ tender.published_at_label }}</div></div>
				<div class="tnd-fact"><div class="kt-label">Current submission deadline</div><div class="tnd-fact-value">{{ tender.submission_deadline_label }}{{ ended ? " (ended)" : "" }}</div></div>
				<div class="tnd-fact"><div class="kt-label">Publication authorised by</div><div class="tnd-fact-value">{{ publication.authorised_by_name }}</div></div>
				<div class="tnd-fact"><div class="kt-label">Effective addenda</div><div class="tnd-fact-value" data-testid="tnd-effective-addenda">{{ openPeriod.effective_addenda_count || 0 }}</div></div>
			</div>
			<div v-else class="tnd-section tnd-grid-4" data-testid="tnd-record-facts">
				<div v-for="f in (record.key_facts || []).slice(0, 4)" :key="f.label" class="tnd-fact"><div class="kt-label">{{ f.label }}</div><div class="tnd-fact-value">{{ f.value || "—" }}</div></div>
			</div>
			<div v-if="documents.length" class="tnd-section tnd-section--tight tnd-actions">
				<button v-for="d in headlineDocuments" :key="d.digest" type="button" class="kt-btn kt-btn-secondary" :data-testid="`tnd-view-${d.kind === 'Invitation' ? 'invitation' : 'complete'}`" @click="$emit('view-document', d.kind)">View {{ d.kind === "Invitation" ? "Invitation" : "complete Tender" }}</button>
				<button v-if="openPeriod.current_addendum" type="button" class="kt-btn kt-btn-secondary" data-testid="tnd-view-current-addendum" @click="$emit('open-addendum', openPeriod.current_addendum.name)">View current addendum</button>
			</div>
			<div v-if="publication" class="tnd-section">
				<div class="kt-card-title" style="margin-bottom: 12px">Publication channels</div>
				<table class="kt-table" data-testid="tnd-published-channels">
					<thead><tr><th>Channel</th><th>Result</th><th>Available at</th><th>Confirmation</th></tr></thead>
					<tbody>
						<tr v-for="c in channels" :key="c.channel"><td>{{ c.channel_label }}</td><td><span class="kt-status" :class="c.status === 'Confirmed' ? 'is-live' : 'is-attention'">{{ c.result_label }}</span></td><td>{{ c.available_at_label || "—" }}</td><td><button v-if="c.status === 'Confirmed'" type="button" class="tnd-link-btn" @click="$emit('view-confirmation', c)">View confirmation</button><span v-else>—</span></td></tr>
					</tbody>
				</table>
			</div>
			<div v-if="publication" class="tnd-section">
				<div class="kt-card-title" style="margin-bottom: 12px">Changes and notices</div>
				<table v-if="addenda.length" class="kt-table" style="margin-bottom: 16px" data-testid="tnd-addenda-table">
					<thead><tr><th>Addendum</th><th>Change</th><th>Issued</th><th>Deadline</th><th></th></tr></thead>
					<tbody><tr v-for="a in addenda" :key="a.name" :data-status="a.status"><td>{{ a.addendum_reference }}</td><td>{{ a.change_summary }}<span v-if="a.status !== 'Issued'" class="tnd-sub">{{ a.status }}</span></td><td>{{ a.issued_at_label || "—" }}</td><td>{{ a.revised_submission_deadline_label || tender.submission_deadline_label }}</td><td><button type="button" class="tnd-link-btn" data-testid="tnd-open-addendum" @click="$emit('open-addendum', a.name)">View</button></td></tr></tbody>
				</table>
				<p v-else class="tnd-card-body" data-testid="tnd-no-addenda">{{ openPeriod.empty_addenda_text || "No addenda have been issued." }}</p>
				<table v-if="inquiries.length" class="kt-table" data-testid="tnd-inquiries-table">
					<thead><tr><th>Addendum</th><th>Question</th><th>Received</th><th>Response status</th><th></th></tr></thead>
					<tbody><tr v-for="q in inquiries" :key="q.name"><td>{{ q.addendum_reference }}</td><td>{{ q.question }}</td><td>{{ q.received_at_label }}</td><td><span class="kt-status" :class="q.response_status === 'Answered' ? 'is-live' : q.response_status === 'Late' ? 'is-critical' : 'is-attention'">{{ q.response_status }}</span></td><td><button type="button" class="tnd-link-btn" data-testid="tnd-open-inquiry" @click="$emit('open-inquiry', q.name)">View</button></td></tr></tbody>
				</table>
				<p v-else class="tnd-card-body" data-testid="tnd-no-inquiries">{{ openPeriod.empty_inquiries_text || "No addendum inquiries have been received." }}</p>
			</div>
			<div class="tnd-section tnd-section--content">
				<div class="kt-card-title tnd-content-title">Tender content</div>
				<ContentSections :sections="review.sections || []" :findings="[]" />
				<div class="kt-card-title tnd-content-title tnd-content-title--later">History and evidence</div>
				<div class="kt-disclosure" style="margin-top: 10px">
					<div class="kt-disclosure-head" role="button" tabindex="0" @click="historyOpen = !historyOpen" @keydown.enter.prevent="historyOpen = !historyOpen"><div class="kt-disclosure-title-row"><span class="kt-disclosure-title">Decisions and attempts</span></div><svg class="kt-disclosure-chevron" :class="{ 'is-open': historyOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m6 9 6 6 6-6"/></svg></div>
					<div v-if="historyOpen" class="kt-disclosure-body">
						<div class="kt-timeline" data-testid="tnd-timeline">
							<div v-for="(d, i) in timeline" :key="i" class="kt-timeline-row"><div class="kt-timeline-dot-col"><div class="kt-timeline-dot"></div><div v-if="i < timeline.length - 1" class="kt-timeline-line"></div></div><div class="kt-timeline-item"><div class="kt-timeline-item-title">{{ d.title }}</div><div class="kt-timeline-item-meta">{{ d.meta }}</div></div></div>
						</div>
						<button type="button" class="kt-btn kt-btn-ghost" style="padding: 8px 0 0" data-testid="tnd-view-history" @click="$emit('history')">View full history</button>
					</div>
				</div>
			</div>
		</BlueprintCard>
		<div class="tnd-footer tnd-footer--end" data-testid="tnd-published-footer">
			<template v-if="published && !ended">
				<button v-if="has('recommend_cancellation')" type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tnd-recommend-cancellation" @click="$emit('cancel-screen')">Recommend cancellation</button>
				<button v-if="has('prepare_addendum')" type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="tnd-prepare-addendum" @click="$emit('prepare-addendum')">Prepare addendum</button>
				<button v-if="has('cancel_tender')" type="button" class="kt-btn tnd-btn-danger" :disabled="pending" data-testid="tnd-cancel-tender" @click="$emit('cancel-screen')">Cancel Tender</button>
				<span v-if="!has('recommend_cancellation') && !has('prepare_addendum') && !has('cancel_tender')" class="tnd-status-text" data-testid="tnd-no-action">No business action available for this role.</span>
			</template>
			<template v-else>
				<button v-if="has('record_cancellation_evidence') || tender.overall_status === 'Cancelled'" type="button" class="kt-btn kt-btn-secondary" data-testid="tnd-open-cancellation" @click="$emit('cancel-screen')">View cancellation</button>
				<button v-if="has('reopen_tender')" type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tnd-reopen" @click="$emit('reopen')">Reopen for correction</button>
				<button v-if="has('request_requisition_correction')" type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tnd-request-correction" @click="$emit('request-correction')">Request requisition correction</button>
				<button v-if="has('view_publication')" type="button" class="kt-btn kt-btn-secondary" data-testid="tnd-view-publication" @click="$emit('publication')">View publication</button>
				<span v-if="!hasAnyAction" class="tnd-status-text" data-testid="tnd-no-action">No business action available for this role.</span>
			</template>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import BlueprintCard from "./BlueprintCard.vue";
import RecordHead from "./RecordHead.vue";
import ContentSections from "./ContentSections.vue";

const props = defineProps({
	record: { type: Object, default: () => ({ tender: {} }) },
	review: { type: Object, default: () => ({}) },
	pending: Boolean,
});
defineEmits(["view-document", "view-confirmation", "open-addendum", "open-inquiry", "prepare-addendum", "cancel-screen", "history", "reopen", "request-correction", "publication"]);

const historyOpen = ref(false);
const tender = computed(() => props.record.tender || {});
const publication = computed(() => props.record.publication || null);
const openPeriod = computed(() => props.record.open_period || {});
const published = computed(() => ["Published — open", "Submission period ended"].includes(tender.value.overall_status));
const ended = computed(() => tender.value.overall_status === "Submission period ended");
const badgeTone = computed(() => (ended.value ? "is-pending" : published.value ? "is-live" : ""));
const lede = computed(() => (ended.value ? "Supplier submission is closed. The proceeding has moved to the next procurement stage." : published.value ? "Published and open for supplier submissions." : ""));
const channels = computed(() => (publication.value || {}).channels || []);
const addenda = computed(() => openPeriod.value.addenda || []);
const inquiries = computed(() => openPeriod.value.inquiries || []);
const documents = computed(() => props.record.documents || []);
const headlineDocuments = computed(() => {
	const seen = new Set();
	return documents.value.filter((d) => ["Invitation", "Complete Tender"].includes(d.kind) && !seen.has(d.kind) && seen.add(d.kind));
});
const timeline = computed(() => {
	const out = (props.record.decisions || []).map((d) => ({ title: `${d.decision} by ${d.actor_name}`, meta: `${d.decided_at_label}${d.version_number ? " · Version " + d.version_number : ""}` }));
	if (publication.value && publication.value.published_at_label) out.push({ title: "Published", meta: publication.value.published_at_label });
	return out;
});
function has(action) {
	return (props.record.allowed_actions || []).includes(action);
}
const hasAnyAction = computed(() => ["record_cancellation_evidence", "reopen_tender", "request_requisition_correction", "view_publication"].some(has) || tender.value.overall_status === "Cancelled");
</script>
