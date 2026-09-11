<!-- TPR-DES-05 Tender approval (§13.7): the immutable submitted Version —
     Requisition summary (with the internal-only policy context, visible to
     the approver, never rendered), the task summaries, readiness, complete
     renders, the quiet release binding; Return for correction / Approve for
     publication. Nothing is editable. -->
<template>
	<div>
		<div style="margin-bottom: 24px">
			<div class="tpr-cap">{{ tender.tender_reference }} · Version {{ tender.version_number }}</div>
			<h1 class="kt-page-title" style="font-size: 28px; margin: 4px 0">{{ tender.requirement_title }}</h1>
			<span class="kt-status" :class="statusClass">{{ statusLabel }}</span>
		</div>
		<p v-if="error" class="tpr-error-banner" role="alert">{{ error }}</p>
		<div class="tpr-grid-2" style="margin-bottom: 24px">
			<div class="kt-card kt-blueprint tpr-card-pad"><i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="tpr-card-kicker">Requisition</div><div class="tpr-card-heading">{{ inherited.requisition_reference }}</div>
				<p class="tpr-card-body">{{ packageLine }} Authorised value {{ inherited.authorised_value }} (internal only).</p>
				<p class="tpr-card-body tpr-muted" style="margin-top: 8px" data-testid="tpr-approval-internal-context"><span class="tpr-tag is-outline" style="margin-right: 6px">Internal only — never rendered to bidders</span>{{ internalLine }}</p>
			</div>
			<div class="kt-card kt-blueprint tpr-card-pad"><i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="tpr-card-kicker">Task 1 — Tender details</div><div class="tpr-card-heading">{{ inherited.planned_method }} · KES {{ money(values.tender_security_amount) }} security</div>
				<p class="tpr-card-body">Submission {{ submissionLabel }} · Validity {{ values.tender_validity_days }} days · {{ values.pre_tender_meeting ? "Pre-tender meeting" : "No pre-tender meeting" }}.</p>
			</div>
			<div class="kt-card kt-blueprint tpr-card-pad"><i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="tpr-card-kicker">Task 2–3 — Requirements &amp; price</div><div class="tpr-card-heading">{{ (inherited.counts || {}).items }} item{{ (inherited.counts || {}).items === 1 ? "" : "s" }} · generated schedule</div>
				<p class="tpr-card-body">{{ goodsLine }} Price schedule generated, awaiting Tenderer response.</p>
			</div>
			<div class="kt-card kt-blueprint tpr-card-pad"><i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="tpr-card-kicker">Task 4–5 — Evaluation &amp; contract</div><div class="tpr-card-heading">{{ evidence.length }} evidence requirements · {{ values.payment_timing_days }}-day payment</div>
				<p class="tpr-card-body">Performance security {{ values.performance_security_required ? values.performance_security_percent + "%" : "not required" }} · Delay damages {{ values.delay_damages_per_week_percent }}%/week, max {{ values.maximum_delay_damages_percent }}% · {{ values.contract_contact_office }}.</p>
			</div>
		</div>
		<div class="tpr-section">
			<div class="kt-card-title">Readiness</div>
			<div class="tpr-statuses" data-testid="tpr-approval-readiness">
				<span class="kt-status" :class="readiness.blocking_count ? 'is-critical' : 'is-live'">{{ readiness.blocking_count || 0 }} Blocking</span>
				<span class="kt-status" :class="readiness.warning_count ? 'is-attention' : 'is-live'">{{ readiness.warning_count || 0 }} Warning{{ warningSuffix }}</span>
			</div>
		</div>
		<div class="tpr-section">
			<div class="kt-card-title">Complete renders</div>
			<div class="tpr-tags">
				<a href="#" class="tpr-tag is-outline" data-testid="tpr-approval-preview-invitation" @click.prevent="$emit('preview', 'invitation')">Invitation — digest {{ shortDigest(renders.invitation_digest) }}</a>
				<a href="#" class="tpr-tag is-outline" data-testid="tpr-approval-preview-tender" @click.prevent="$emit('preview', 'issued_tender')">Issued Tender — digest {{ shortDigest(renders.issued_tender_digest) }}</a>
			</div>
		</div>
		<div class="kt-card kt-blueprint tpr-card-pad tpr-card-narrow" style="margin-bottom: 24px"><i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="tpr-card-kicker">Release binding</div>
			<p class="tpr-card-body tpr-mono">template {{ (task.binding || {}).template_version }} · bundle digest {{ shortDigest((task.binding || {}).bundle_digest) }} · requisition digest {{ shortDigest((task.binding || {}).requisition_content_digest) }}</p>
		</div>
		<div class="tpr-actions">
			<button v-if="actions.can_return" type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tpr-return" @click="$emit('return')">Return for correction</button>
			<button v-if="actions.can_return" type="button" class="kt-btn kt-btn-primary" :disabled="pending || !actions.can_approve" data-testid="tpr-approve" @click="$emit('approve')">Approve for publication</button>
			<span v-if="actions.sod_blocked" class="tpr-muted" data-testid="tpr-sod-note">You prepared or submitted this Version; another Head of Procurement Function must approve it.</span>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { shortDigest } from "../data/format.js";

const props = defineProps({ task: { type: Object, default: () => ({}) }, pending: Boolean, error: { type: String, default: "" } });
defineEmits(["return", "approve", "preview"]);
const tender = computed(() => props.task.tender || {});
const inherited = computed(() => props.task.inherited || {});
const values = computed(() => props.task.officer_values || {});
const readiness = computed(() => props.task.readiness || {});
const renders = computed(() => props.task.renders || {});
const evidence = computed(() => props.task.evidence_requirements || []);
const actions = computed(() => props.task.permitted_actions || {});
const statusLabel = computed(() => (props.task.task_status === "Open" ? "Submitted for approval" : tender.value.state_label || tender.value.version_status));
const statusClass = computed(() => (props.task.task_status === "Open" ? "is-pending" : "is-draft"));
const packageLine = computed(() => {
	const c = inherited.value.counts || {};
	return `${c.items || 0} item${c.items === 1 ? "" : "s"} · ${c.related_services || 0} related services · ${c.acceptance_requirements || 0} acceptance rows.`;
});
const goodsLine = computed(() => (inherited.value.goods || []).map((g) => `${g.description} ×${g.quantity}, ${g.minimum_warranty} warranty`).join("; ") + ".");
const internalLine = computed(() => {
	const i = inherited.value.internal_context || {};
	return [i.strategic_objective_path, i.plan_horizon].filter(Boolean).join(" · ") || "—";
});
const submissionLabel = computed(() => String(values.value.submission_deadline || "").replace("T", " "));
const warningSuffix = computed(() => (findingsWarning.value ? ` — ${findingsWarning.value}` : ""));
const findingsWarning = computed(() => {
	const w = (readiness.value.findings || []).find((f) => f.severity === "Warning");
	return w && w.finding_code === "WARN_MANUFACTURER_AUTHORISATION" ? "manufacturer authorisation proportionality" : "";
});
function money(v) {
	return Number(v || 0).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}
</script>
