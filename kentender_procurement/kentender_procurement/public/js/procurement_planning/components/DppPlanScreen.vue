<!-- PLN-UI-02/05 Departmental Procurement Plan (§12.2/§12.5), rendering
     PLN-DES-02 v1.12 (Draft with readiness notice, three-column context strip)
     and PLN-DES-05 (ready + certification, Submit in the header) class-for-
     class, plus the returned-issue rows (§12.2). No Procuring Entity field. -->
<template>
	<div>
		<!-- header row -->
		<div class="pln-header-row">
			<div class="pln-header-left">
				<p class="kt-page-kicker">DEPARTMENTAL PROCUREMENT PLAN</p>
				<h1 class="kt-page-title">{{ plan.header?.title }}</h1>
				<p class="pln-quiet-ref">{{ plan.header?.reference_line }}</p>
				<span class="kt-status" :class="badgeClass" data-testid="dpp-badge">
					{{ plan.header?.badge }}
				</span>
			</div>
			<div class="pln-header-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('view-accepted-needs')">
					View accepted needs
				</button>
				<!-- PLN-DES-05: the HoD's ready plan carries Submit in the header;
				     PLN-DES-02: a mutable draft carries Add direct requirement. -->
				<button
					v-if="plan.certification?.show"
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="dpp-submit-header"
					:disabled="pending || !plan.can_submit || !certified"
					@click="$emit('submit')"
				>
					Submit departmental plan
				</button>
				<button
					v-else-if="plan.mutable"
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="dpp-add-direct"
					@click="$emit('add-direct')"
				>
					Add direct requirement
				</button>
			</div>
		</div>

		<!-- three-column context strip -->
		<div class="kt-card kt-blueprint pln-strip-grid pln-strip-grid-3" data-testid="dpp-context">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="pln-strip-field">
				<label>Department</label>
				<div class="pln-val">{{ plan.context?.department }}</div>
			</div>
			<div class="pln-strip-field">
				<label>Financial Year</label>
				<div class="pln-val">{{ plan.context?.financial_year }}</div>
			</div>
			<div class="pln-strip-field">
				<label>Submission window</label>
				<div class="pln-val">{{ plan.context?.window?.display }}</div>
			</div>
		</div>

		<!-- readiness notice (amber) -->
		<div v-if="plan.readiness" class="pln-notice" data-testid="dpp-readiness">
			<p class="pln-notice-title">{{ plan.readiness.title }}</p>
			<p>{{ plan.readiness.text }}</p>
		</div>

		<!-- error summary from a refused command -->
		<div v-if="errorSummary" class="pln-notice is-critical" data-testid="dpp-error" role="alert">
			<p class="pln-notice-title">This action could not be completed</p>
			<p>{{ errorSummary }}</p>
		</div>

		<!-- requirements table -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="dpp-entries">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<table class="pln-table">
				<thead>
					<tr>
						<th>Requirement</th>
						<th>Source</th>
						<th class="pln-num">Quantity</th>
						<th>Required by</th>
						<th>Procurement Budget Line</th>
						<th class="pln-num">Indicative amount</th>
						<th>Status</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
					<template v-for="row in plan.entries" :key="row.entry_id">
						<tr :data-testid="`dpp-entry-${row.entry_id}`">
							<td>{{ row.title }}</td>
							<td>{{ row.source_label }}</td>
							<td class="pln-num">{{ row.quantity_display }}</td>
							<td>{{ row.required_by_display }}</td>
							<td>{{ row.budget_line_display }}</td>
							<td class="pln-num">{{ row.amount_display }}</td>
							<td>
								<span class="kt-status" :class="statusClass(row.status_kind)">
									{{ row.status }}
								</span>
							</td>
							<td style="text-align: right">
								<button
									v-if="row.action"
									type="button"
									class="kt-btn kt-btn-ghost"
									:data-testid="`dpp-entry-action-${row.entry_id}`"
									@click="$emit('open-entry', row)"
								>
									{{ row.action }}
								</button>
							</td>
						</tr>
						<!-- §12.2 — each structured return issue next to its entry -->
						<tr v-for="(issue, i) in row.issues" :key="`${row.entry_id}-issue-${i}`">
							<td colspan="8">
								<div class="pln-issue" data-testid="dpp-issue">
									<strong>{{ issue.problem }}.</strong> {{ issue.correction }}
								</div>
							</td>
						</tr>
					</template>
				</tbody>
			</table>
			<p class="pln-table-caption" data-testid="dpp-totals">{{ plan.totals_caption }}</p>
		</div>

		<!-- PLN-DES-05 certification card -->
		<div v-if="plan.certification?.show" class="pln-cert-box" data-testid="dpp-certification">
			<div class="kt-card-title">{{ plan.certification.heading }}</div>
			<p>{{ plan.certification.text }}</p>
			<label class="pln-checkbox-row">
				<input
					type="checkbox"
					data-testid="dpp-certify"
					:checked="certified"
					@change="$emit('update:certified', $event.target.checked)"
				/>
				{{ plan.certification.checkbox_label }}
			</label>
		</div>

		<!-- sticky footer -->
		<div class="pln-footer-bar">
			<button type="button" class="kt-btn kt-btn-ghost" @click="$emit('back')">Back to workspace</button>
			<div class="pln-footer-actions">
				<button
					v-if="plan.mutable"
					type="button"
					class="kt-btn kt-btn-secondary"
					:disabled="pending"
					@click="$emit('save-draft')"
				>
					Save draft
				</button>
				<button
					v-if="plan.mutable"
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="dpp-submit"
					:disabled="pending || !plan.can_submit || !certified"
					@click="$emit('submit')"
				>
					Submit departmental plan
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	plan: { type: Object, default: () => ({}) },
	pending: Boolean,
	certified: Boolean,
	errorSummary: String,
});

defineEmits([
	"view-accepted-needs",
	"add-direct",
	"open-entry",
	"back",
	"save-draft",
	"submit",
	"update:certified",
]);

const KIND_CLASS = {
	live: "is-live",
	attention: "is-attention",
	critical: "is-critical",
	muted: "is-draft",
};

const badgeClass = computed(() => {
	const badge = props.plan.header?.badge;
	if (badge === "Draft") return "is-draft";
	return KIND_CLASS[props.plan.header?.badge_kind] || "is-draft";
});

function statusClass(kind) {
	return KIND_CLASS[kind] || "is-draft";
}
</script>
