<!-- PLN-CHG-001 v1.18 §10.5 (U12) — Source evidence within review: one
     reviewed allocation's full origin chain, reached only from its own
     Review task's Sources/Plan Items tables. Read-only; "Return to Plan
     review" both above and below the content. A Need-origin source shows
     its exact Need/Revision and the department's own acceptance; a
     direct-origin source shows "Direct departmental requirement" instead,
     never an empty Need field or a bypass reason. -->
<template>
	<div>
		<div style="margin-bottom: 16px">
			<a data-testid="src-back-top" @click="$emit('navigate', evidence.back_route)">&larr; Return to Plan review</a>
		</div>
		<p class="pln-quiet-ref">{{ evidence.plan_reference }} · Version {{ evidence.version_number }}</p>
		<h1 class="kt-page-title">Source evidence</h1>

		<div v-if="evidence.has_newer_revision" class="kt-card kt-blueprint pln-card-pad" data-testid="src-newer-notice" style="margin: 16px 0">
			<p style="margin: 0 0 8px">You are viewing the source revision used in this Plan. A newer accepted revision exists.</p>
			<div style="display: flex; gap: 16px">
				<a data-testid="src-view-newer">View newer accepted revision</a>
				<a data-testid="src-view-reviewed">Return to reviewed revision</a>
			</div>
		</div>

		<div class="kt-card kt-blueprint pln-card-pad" data-testid="src-detail" style="margin: 16px 0">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">{{ evidence.title }}</div>
			<div class="pln-facts-row" style="margin: 12px 0">
				<div class="pln-fact"><span class="kt-label">Quantity</span><span class="pln-fact-val">{{ evidence.quantity_display }}</span></div>
				<div class="pln-fact"><span class="kt-label">Required by</span><span class="pln-fact-val">{{ evidence.required_by_display }}</span></div>
				<div class="pln-fact"><span class="kt-label">Amount</span><span class="pln-fact-val">{{ evidence.amount_display }}</span></div>
			</div>
			<p style="margin: 0 0 12px">{{ evidence.description }}</p>
			<div class="pln-fact" style="margin-bottom: 12px">
				<span class="kt-label">Expected operational result</span><span class="pln-fact-val">{{ evidence.expected_operational_result }}</span>
			</div>

			<div class="pln-facts-row" style="margin-bottom: 12px">
				<template v-if="evidence.source_origin === 'Accepted Departmental Need'">
					<div class="pln-fact"><span class="kt-label">Reference</span><span class="pln-fact-val">{{ evidence.need_reference }}</span></div>
					<div class="pln-fact"><span class="kt-label">Revision</span><span class="pln-fact-val">{{ evidence.need_revision_number }}{{ evidence.has_newer_revision ? " (as reviewed)" : "" }}</span></div>
				</template>
				<div v-else class="pln-fact" data-testid="src-origin-direct"><span class="kt-label">Source origin</span><span class="pln-fact-val">Direct departmental requirement</span></div>
				<div class="pln-fact"><span class="kt-label">Department</span><span class="pln-fact-val">{{ evidence.department }}</span></div>
			</div>
			<div class="pln-facts-row">
				<div class="pln-fact"><span class="kt-label">Departmental Plan</span><span class="pln-fact-val">{{ evidence.departmental_plan_reference }}</span></div>
				<div class="pln-fact"><span class="kt-label">Submission</span><span class="pln-fact-val">{{ evidence.submission_number }}</span></div>
				<div v-if="evidence.source_origin === 'Accepted Departmental Need'" class="pln-fact"><span class="kt-label">DPP entry</span><span class="pln-fact-val">{{ evidence.dpp_entry_id }}</span></div>
				<div class="pln-fact"><span class="kt-label">Budget Line</span><span class="pln-fact-val">{{ evidence.budget_line_display }}</span></div>
				<div class="pln-fact"><span class="kt-label">Planning amount</span><span class="pln-fact-val">{{ evidence.planning_amount_display }}</span></div>
			</div>
		</div>

		<div class="kt-card kt-blueprint pln-card-pad" data-testid="src-evidence">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Evidence</div>
			<div style="display: flex; flex-direction: column; gap: 6px; font-size: 13px">
				<div v-if="evidence.need_accepted" data-testid="src-need-accepted">
					Need accepted by <strong>{{ evidence.need_accepted.actor_name }}</strong> — {{ evidence.need_accepted.display }}
				</div>
				<div v-if="evidence.certified" data-testid="src-certified">
					Certified by <strong>{{ evidence.certified.actor_name }}</strong> — {{ evidence.certified.display }}
				</div>
				<div v-if="evidence.accepted_for_planning" data-testid="src-accepted-for-planning">
					Accepted for Planning by <strong>{{ evidence.accepted_for_planning.actor_name }}</strong> — {{ evidence.accepted_for_planning.display }}
				</div>
			</div>
		</div>

		<div style="margin-top: 24px">
			<a data-testid="src-back-bottom" @click="$emit('navigate', evidence.back_route)">&larr; Return to Plan review</a>
		</div>
	</div>
</template>

<script setup>
defineProps({
	evidence: { type: Object, default: () => ({}) },
});

defineEmits(["navigate"]);
</script>
