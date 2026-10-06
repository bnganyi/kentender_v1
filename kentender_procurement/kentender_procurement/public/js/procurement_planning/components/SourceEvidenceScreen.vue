<!-- PLN-CHG-001 v1.24 §10.11 — Exact departmental evidence (U12), ported from
     Artboards-U12-U13.dc.html.

     One reviewed requirement, read in the order someone checking it would ask:
     what was asked for, who is paying for it, who certified and accepted it,
     and only then the record identifiers.

     Everything here is the snapshot the plan was actually reviewed on. A newer
     accepted requirement may exist, and when it does this page says so and
     offers to show it — but it never replaces a single value on this page,
     because the plan was not reviewed on the newer one. -->
<template>
	<div class="pln-evidence">
		<div class="kt-page">
			<a href="#" class="pln-evidence-back" data-testid="src-back-top" @click.prevent="$emit('navigate', evidence.back_route)">
				← Return to plan review
			</a>

			<!-- U12-UNAVAILABLE — a load failure is said plainly, with the two
			     things the reader can actually do. -->
			<template v-if="evidence.outcome === 'UNAVAILABLE'">
				<div class="kt-notice is-critical" data-testid="src-unavailable">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<path d="M18 6L6 18M6 6l12 12"></path>
					</svg>
					<div class="kt-notice-body">Departmental requirement evidence could not be loaded.</div>
				</div>
				<div class="pln-footer-right">
					<button type="button" class="btn btn-secondary" data-testid="src-retry" @click="$emit('reload')">Try again</button>
					<button type="button" class="btn btn-primary" data-testid="src-back-bottom" @click="$emit('navigate', evidence.back_route)">
						Return to plan review
					</button>
				</div>
			</template>

			<template v-else>
				<!-- U12-HISTORICAL-PLAN — the values stay the historical snapshot;
				     the notice explains why nothing here can be acted on. -->
				<div v-if="evidence.historical" class="kt-notice is-info pln-notice-split" data-testid="src-historical">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<circle cx="12" cy="12" r="9"></circle><path d="M12 8h.01M11 12h1v5h1"></path>
					</svg>
					<div class="kt-notice-body pln-notice-split">
						<span>Historical plan — read only</span>
						<button type="button" class="btn btn-secondary" data-testid="src-view-current" @click="$emit('navigate', evidence.current_plan_route)">
							View current plan
						</button>
					</div>
				</div>

				<!-- The board identifies the record with one scope line inside the
				     head. Built as a separate labelled fact row below it, the
				     identity read as the page's first section rather than as the
				     record's own (found live 24 Sep 2026). -->
				<div class="kt-page-head">
					<div>
						<h1 class="kt-page-title" data-testid="src-title">Departmental requirement</h1>
						<p class="kt-page-desc">{{ evidence.title }}</p>
						<div class="kt-page-scope" data-testid="src-context">
							<span>{{ evidence.need_reference || "Direct departmental requirement" }}</span>
							<span v-if="evidence.need_revision_number">· Revision {{ evidence.need_revision_number }}</span>
							<span class="kt-status is-live">Accepted for planning</span>
						</div>
					</div>
				</div>

				<!-- U12-NEWER-SOURCE — stated, and offered, but never substituted. -->
				<div v-if="evidence.has_newer_revision" class="kt-notice is-info" data-testid="src-newer-notice">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<circle cx="12" cy="12" r="9"></circle><path d="M12 8h.01M11 12h1v5h1"></path>
					</svg>
					<div class="kt-notice-body">
						A newer accepted requirement is available (Revision {{ evidence.newer_revision_number }}).
						The plan was reviewed on Revision {{ evidence.need_revision_number }}, which is what is shown below.
						<a href="#" data-testid="src-view-newer" @click.prevent="$emit('view-newer')">View the newer requirement</a>
					</div>
				</div>

				<div class="kt-region">
					<h2>Requirement details</h2>
					<div class="kt-meta-row is-tight" data-testid="src-requirement">
						<div>
							<span class="kt-label">Requirement title</span>
							<span class="kt-meta-value">{{ evidence.title }}</span>
						</div>
						<div>
							<span class="kt-label">Description</span>
							<span class="kt-meta-value">{{ evidence.description }}</span>
						</div>
						<div>
							<span class="kt-label">Expected result</span>
							<span class="kt-meta-value">{{ evidence.expected_operational_result }}</span>
						</div>
						<div>
							<span class="kt-label">Quantity</span>
							<span class="kt-meta-value">{{ evidence.quantity_number }}</span>
						</div>
						<div>
							<span class="kt-label">Unit</span>
							<span class="kt-meta-value">{{ evidence.unit_label }}</span>
						</div>
						<div>
							<span class="kt-label">Required by</span>
							<span class="kt-meta-value">{{ evidence.required_by_display }}</span>
						</div>
					</div>
				</div>

				<div class="kt-region is-secondary">
					<h2>Departmental funding</h2>
					<!-- The board binds these facts in a group rule under the heading. -->
					<div class="kt-group">
						<div class="kt-meta-row" data-testid="src-funding">
							<div>
								<span class="kt-label">Department</span>
								<span class="kt-meta-value">{{ evidence.department }}</span>
							</div>
							<div v-if="evidence.budget_line_name">
								<span class="kt-label">Budget line name</span>
								<span class="kt-meta-value">{{ evidence.budget_line_name }}</span>
							</div>
							<div>
								<span class="kt-label">Budget line</span>
								<span class="kt-meta-value">{{ evidence.budget_line_reference }}</span>
							</div>
							<div>
								<span class="kt-label">Amount</span>
								<span class="kt-meta-value">{{ evidence.planning_amount_display }}</span>
							</div>
						</div>
					</div>
				</div>

				<div class="kt-region is-secondary">
					<h2>Certification and Procurement review</h2>
					<!-- U12 — two facts, two groups: certification never reads as if
					     it proves procurement's own acceptance, or the reverse. The
					     department's own attestation words stay with what they
					     certify, not stranded below an unrelated fact. -->
					<div data-testid="src-certification">
						<div class="kt-group">
							<div class="kt-meta-row">
								<div>
									<span class="kt-label">Certification status</span>
									<span class="kt-meta-value">
										<span class="kt-status" :class="evidence.certified ? 'is-live' : 'is-attention'">{{ evidence.certification_status }}</span>
									</span>
								</div>
								<template v-if="evidence.certified">
									<div>
										<span class="kt-label">Certified by</span>
										<span class="kt-meta-value">{{ evidence.certified.actor_name }}</span>
									</div>
									<!-- The capacity is what makes the certification mean
									     something; it is omitted rather than guessed. -->
									<div v-if="evidence.certified.capacity">
										<span class="kt-label">Capacity</span>
										<span class="kt-meta-value">{{ evidence.certified.capacity }}</span>
									</div>
									<div>
										<span class="kt-label">Certified at</span>
										<span class="kt-meta-value">{{ evidence.certified.display }}</span>
									</div>
								</template>
							</div>
							<!-- The department's own words, where the owner supplied them. -->
							<p v-if="evidence.certified?.attestation_text" class="kt-muted" data-testid="src-attestation">
								{{ evidence.certified.attestation_text }}
							</p>
						</div>
						<div class="kt-group">
							<div class="kt-meta-row">
								<div>
									<span class="kt-label">Procurement disposition</span>
									<span class="kt-meta-value">{{ evidence.procurement_disposition }}</span>
								</div>
								<template v-if="evidence.accepted_for_planning">
									<div>
										<span class="kt-label">Accepted by</span>
										<span class="kt-meta-value">{{ evidence.accepted_for_planning.actor_name }}</span>
									</div>
									<div>
										<span class="kt-label">Accepted at</span>
										<span class="kt-meta-value">{{ evidence.accepted_for_planning.display }}</span>
									</div>
								</template>
							</div>
						</div>
					</div>
					<div v-if="evidence.need_accepted" class="kt-meta-row" data-testid="src-need-accepted">
						<div>
							<span class="kt-label">Need accepted by</span>
							<span class="kt-meta-value">{{ evidence.need_accepted.actor_name }} · {{ evidence.need_accepted.display }}</span>
						</div>
					</div>
				</div>

				<!-- The identifiers, closed: they answer "which record", not
				     "should this be in the plan". -->
				<details class="kt-disclosure" data-testid="src-record-details">
					<summary class="kt-disclosure-head">
						<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">Record details</span></div>
						<svg class="kt-disclosure-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9l6 6 6-6"></path></svg>
					</summary>
					<div class="kt-disclosure-body">
						<div class="kt-meta-row">
							<div>
								<span class="kt-label">Departmental plan</span>
								<span class="kt-meta-value">{{ evidence.departmental_plan_reference }}</span>
							</div>
							<div>
								<span class="kt-label">Submission</span>
								<span class="kt-meta-value">{{ evidence.submission_number }}</span>
							</div>
							<div>
								<span class="kt-label">DPP entry</span>
								<span class="kt-meta-value">{{ evidence.dpp_entry_id }}</span>
							</div>
							<div>
								<span class="kt-label">Plan item</span>
								<span class="kt-meta-value">{{ evidence.plan_item_id }}</span>
							</div>
							<div>
								<span class="kt-label">Plan version</span>
								<span class="kt-meta-value">{{ evidence.version_number }}</span>
							</div>
						</div>
					</div>
				</details>

				<div class="pln-footer" data-testid="src-footer">
					<span></span>
					<div class="pln-footer-right">
						<button type="button" class="btn btn-primary" data-testid="src-back-bottom" @click="$emit('navigate', evidence.back_route)">
							Return to plan review
						</button>
					</div>
				</div>
			</template>
		</div>
	</div>
</template>

<script setup>
defineProps({
	evidence: { type: Object, default: () => ({}) },
});

defineEmits(["navigate", "view-newer", "reload"]);
</script>
