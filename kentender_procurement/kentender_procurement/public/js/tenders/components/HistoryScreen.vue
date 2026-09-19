<!-- /app/tenders/{ref}/history — plan D22: no board (fidelity-exempt). The
     GetTenderHistory projection as plain tables: versions, decisions,
     documents (by digest), publication + confirmations, addenda, inquiries,
     cancellation, and the event log (payloads for oversight readers only). -->
<template>
	<div class="tnd-page" data-screen-label="Tender history">
		<BlueprintCard>
			<div class="tnd-head">
				<div class="tnd-title-row"><h1 class="tnd-h1" data-testid="tnd-record-title">History</h1><span class="kt-status is-pending">{{ data.tender.overall_status }}</span></div>
				<p class="tnd-refs">{{ data.tender.tender_reference }} · {{ data.tender.requirement_title }}</p>
				<p class="tnd-lede">Every Version, decision, document and event of this Tender, in order.</p>
			</div>
			<div class="tnd-section">
				<div class="kt-card-title" style="margin-bottom: 12px">Versions</div>
				<table class="kt-table tnd-history-table" data-testid="tnd-history-versions">
					<thead><tr><th>Version</th><th>Status</th><th>Prepared</th><th>Submitted</th><th>Approved</th><th>Returned / stopped</th></tr></thead>
					<tbody><tr v-for="v in data.versions || []" :key="v.name"><td>Version {{ v.version_number }}</td><td><span class="kt-status is-pending">{{ v.status }}</span></td><td>{{ v.prepared_by_name }}<div class="tnd-sub">{{ v.prepared_at_label }}</div></td><td>{{ v.submitted_by_name }}<div class="tnd-sub">{{ v.submitted_at_label }}</div></td><td>{{ v.approved_by_name }}<div class="tnd-sub">{{ v.approved_at_label }}</div></td><td>{{ v.return_reason || v.stop_reason || v.reopen_reason || "—" }}<div v-if="v.returned_by_name" class="tnd-sub">{{ v.returned_by_name }} · {{ v.returned_at_label }}</div></td></tr></tbody>
				</table>
			</div>
			<div v-if="(data.decisions || []).length" class="tnd-section">
				<div class="kt-card-title" style="margin-bottom: 12px">Decisions</div>
				<table class="kt-table tnd-history-table" data-testid="tnd-history-decisions">
					<thead><tr><th>Decision</th><th>By</th><th>Role</th><th>When</th><th>Reason</th></tr></thead>
					<tbody><tr v-for="d in data.decisions" :key="d.name"><td>{{ d.decision }}<div v-if="d.version_number" class="tnd-sub">Version {{ d.version_number }}</div></td><td>{{ d.actor_name }}</td><td>{{ d.business_role }}</td><td>{{ d.decided_at_label }}</td><td>{{ d.reason || "—" }}<div v-if="d.affected_task" class="tnd-sub">{{ d.affected_task }}</div></td></tr></tbody>
				</table>
			</div>
			<div v-if="(data.documents || []).length" class="tnd-section">
				<div class="kt-card-title" style="margin-bottom: 12px">Documents</div>
				<table class="kt-table" data-testid="tnd-history-documents">
					<thead><tr><th>Document</th><th>Generated</th><th>Reference</th><th></th></tr></thead>
					<tbody><tr v-for="d in data.documents" :key="d.document"><td>{{ d.kind }}<div v-if="d.addendum || d.cancellation" class="tnd-sub">{{ d.addendum || d.cancellation }}</div></td><td>{{ d.generated_at_label }}</td><td class="tnd-xs tnd-muted">{{ d.digest.slice(0, 16) }}</td><td><button type="button" class="tnd-link-btn" @click="$emit('view-digest', d)">View</button></td></tr></tbody>
				</table>
			</div>
			<div v-if="data.publication" class="tnd-section">
				<div class="kt-card-title" style="margin-bottom: 12px">Publication</div>
				<p class="tnd-card-body" style="margin: 0 0 10px">{{ data.publication.publication_status }} · authorised by {{ data.publication.authorised_by_name }}, {{ data.publication.authorised_at_label }}<span v-if="data.publication.published_at_label"> · published {{ data.publication.published_at_label }}</span> · rule {{ data.publication.rule_snapshot_id }}</p>
				<table class="kt-table" data-testid="tnd-history-channels"><thead><tr><th>Channel</th><th>Result</th><th>Available at</th><th>Attested by</th></tr></thead><tbody><tr v-for="c in data.publication.channels || []" :key="c.channel"><td>{{ c.channel_label }}</td><td>{{ c.result_label }}</td><td>{{ c.available_at_label || "—" }}</td><td>{{ c.attested_by_name || "—" }}<div class="tnd-sub">{{ c.attested_at_label }}</div></td></tr></tbody></table>
			</div>
			<div v-if="openPeriod && ((openPeriod.addenda || []).length || (openPeriod.inquiries || []).length || openPeriod.cancellation)" class="tnd-section">
				<div class="kt-card-title" style="margin-bottom: 12px">Open period</div>
				<table v-if="(openPeriod.addenda || []).length" class="kt-table" style="margin-bottom: 12px" data-testid="tnd-history-addenda"><thead><tr><th>Addendum</th><th>Status</th><th>Change</th><th>Issued</th><th>Effective</th></tr></thead><tbody><tr v-for="a in openPeriod.addenda" :key="a.name"><td>{{ a.addendum_reference }}</td><td>{{ a.status }}</td><td>{{ a.change_summary }}</td><td>{{ a.issued_at_label || "—" }}</td><td>{{ a.effective_at_label || "—" }}</td></tr></tbody></table>
				<table v-if="(openPeriod.inquiries || []).length" class="kt-table" style="margin-bottom: 12px" data-testid="tnd-history-inquiries"><thead><tr><th>Inquiry</th><th>Received</th><th>Status</th><th>Responded</th></tr></thead><tbody><tr v-for="q in openPeriod.inquiries" :key="q.name"><td>{{ q.question }}</td><td>{{ q.received_at_label }}</td><td>{{ q.response_status }}</td><td>{{ q.responded_by_name || "—" }}<div class="tnd-sub">{{ q.responded_at_label }}</div></td></tr></tbody></table>
				<p v-if="openPeriod.cancellation" class="tnd-card-body" data-testid="tnd-history-cancellation">Cancelled by {{ openPeriod.cancellation.decided_by_name }}, {{ openPeriod.cancellation.decided_at_label }} — {{ openPeriod.cancellation.ground_label }}: {{ openPeriod.cancellation.reason }}</p>
			</div>
			<div class="tnd-section tnd-section--last">
				<div class="kt-card-title" style="margin-bottom: 12px">Events</div>
				<table class="kt-table tnd-history-table" data-testid="tnd-history-events">
					<thead><tr><th>When</th><th>Event</th><th>Subject</th><th>Delivery</th><th v-if="oversight">Detail</th></tr></thead>
					<tbody><tr v-for="e in data.events || []" :key="e.name || e.event_id"><td>{{ e.occurred_at_label }}</td><td>{{ e.event_type }}<div class="tnd-sub">#{{ e.sequence }}</div></td><td>{{ e.subject_type }}<div class="tnd-sub">{{ e.subject_id }}</div></td><td>{{ e.status }}<div v-if="e.consumer" class="tnd-sub">{{ e.consumer }}</div></td><td v-if="oversight" class="tnd-xs tnd-muted"><pre style="margin: 0; white-space: pre-wrap; font: inherit">{{ JSON.stringify(e.payload || {}, null, 0).slice(0, 400) }}</pre></td></tr></tbody>
				</table>
			</div>
		</BlueprintCard>
		<div class="tnd-footer"><a href="#" class="tnd-footer-back" data-testid="tnd-back" @click.prevent="$emit('back')">Back to Tender</a></div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import BlueprintCard from "./BlueprintCard.vue";

const props = defineProps({ data: { type: Object, default: () => ({ tender: {} }) } });
defineEmits(["back", "view-digest"]);
const openPeriod = computed(() => props.data.open_period || null);
const oversight = computed(() => !!props.data.protected);
</script>
