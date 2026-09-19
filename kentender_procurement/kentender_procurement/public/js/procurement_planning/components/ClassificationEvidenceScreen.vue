<!-- PLN-CHG-001 v1.23 §10.5 — U06-ACCEPTED-CLASSIFICATION and
     U06-CORRECT-CLASSIFICATION, ported from U06.dc.html.

     This is the Procurement-owned classification record for an accepted
     submission, and the only lawful way to change it. Two things must stay
     unmistakable on this screen:

     1. Correcting a classification does not touch the departmental plan. The
        certified requirement, its quantities, dates and funding are the
        department's evidence and are not reopened here.
     2. The correction is appended. The earlier decision stays in history, and
        whatever already consumed the source has its own recovery route, named
        on the row rather than left for the Planner to work out. -->
<template>
	<div>
		<div class="pln-sheet">
			<div class="pln-masthead">
				<div>
					<h1 class="kt-page-title" data-testid="pln-class-title">View accepted requirement classifications</h1>
				</div>
			</div>

			<div class="kt-meta-row pln-context-row" data-testid="pln-class-context">
				<div>
					<span class="kt-label">Reference</span>
					<span class="kt-meta-value">{{ evidence.dpp_reference }}</span>
				</div>
				<div>
					<span class="kt-label">Submission</span>
					<span class="kt-meta-value">{{ evidence.submission_number }}</span>
				</div>
				<div>
					<span class="kt-label">Status</span>
					<span class="kt-meta-value"><span class="kt-status is-live">Accepted</span></span>
				</div>
			</div>

			<table class="kt-table" data-testid="pln-class-table">
				<thead>
					<tr>
						<th>Requirement</th>
						<th>Requirement type</th>
						<th>Category</th>
						<th>Classified by</th>
						<th>Classified at</th>
						<th>Action</th>
					</tr>
				</thead>
				<tbody>
					<template v-for="row in rows" :key="row.dpp_entry_id">
						<tr data-testid="pln-class-row">
							<td>{{ row.title }}</td>
							<td>{{ row.excluded ? "Not applicable" : row.classification.requirement_type }}</td>
							<td>{{ row.excluded ? "Not applicable" : row.classification.procurement_category }}</td>
							<td>{{ row.excluded ? "—" : row.classification.actor_name }}</td>
							<td>{{ row.excluded ? "—" : row.classification.at_display }}</td>
							<td>
								<a
									v-if="row.can_correct && evidence.can_correct"
									href="#"
									data-testid="pln-class-correct"
									@click.prevent="$emit('correct', row)"
								>Correct classification</a>
								<span v-else>—</span>
							</td>
						</tr>
						<!-- A corrected row shows what it was and why, in place: the
						     history is the point of the record. -->
						<tr v-if="!row.excluded && row.classification.corrected" class="pln-row-detail" data-testid="pln-class-history">
							<td colspan="6">
								<span class="kt-label">Corrected from</span>
								<span>
									{{ lastCorrection(row).previous_requirement_type }} /
									{{ lastCorrection(row).previous_procurement_category }}
									· {{ lastCorrection(row).reason }}
								</span>
							</td>
						</tr>
					</template>
				</tbody>
			</table>

			<p class="kt-muted" data-testid="pln-class-note">
				The certified departmental requirement will not change. A correction records a new procurement
				classification and keeps the earlier decision in history.
			</p>

			<!-- Whatever already consumed a corrected source, named with its own
			     recovery route rather than left implicit. -->
			<div
				v-for="notice in affectedNotices"
				:key="notice.key"
				class="kt-notice"
				:class="notice.kind"
				data-testid="pln-class-affected"
			>
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
				</svg>
				<div class="kt-notice-body">{{ notice.text }}</div>
			</div>

			<!-- U06-CORRECT-CLASSIFICATION — a focused panel over this screen. -->
			<div v-if="panel" class="kt-dialog-backdrop" data-testid="pln-class-panel">
				<div class="kt-dialog pln-class-dialog">
					<div class="kt-dialog-title">Correct requirement classification</div>
					<div class="pln-dialog-body">
						<p class="pln-class-subject">
							<strong>{{ panel.title }}</strong><br>
							<span class="kt-muted">{{ evidence.dpp_reference }} · Submission {{ evidence.submission_number }}</span>
						</p>

						<div class="kt-meta-row">
							<div>
								<span class="kt-label">Current requirement type</span>
								<span class="kt-meta-value">{{ panel.classification.requirement_type }}</span>
							</div>
							<div>
								<span class="kt-label">Current category</span>
								<span class="kt-meta-value">{{ panel.classification.procurement_category }}</span>
							</div>
						</div>

						<div class="kt-field">
							<label for="pln-class-new-type" class="kt-label">New requirement type</label>
							<select
								id="pln-class-new-type"
								class="kt-input"
								data-testid="pln-class-new-type"
								:value="newType"
								@change="$emit('update:newType', $event.target.value)"
							>
								<option value="">Select a requirement type</option>
								<option
									v-for="option in selectableTypes"
									:key="option.requirement_type"
									:value="option.requirement_type"
								>{{ option.requirement_type }}</option>
							</select>
						</div>

						<div class="pln-class-derived">
							<span class="kt-label">New category (derived)</span>
							<span class="kt-meta-value" data-testid="pln-class-new-category">{{ derivedCategory }}</span>
						</div>

						<div class="kt-field">
							<label for="pln-class-reason" class="kt-label">Reason for correction</label>
							<textarea
								id="pln-class-reason"
								class="kt-input"
								rows="3"
								data-testid="pln-class-reason"
								:value="reason"
								@input="$emit('update:reason', $event.target.value)"
							></textarea>
						</div>

						<p class="kt-muted" data-testid="pln-class-impact">{{ impactText }}</p>
						<p v-if="error" class="pln-error-summary" data-testid="pln-class-error">{{ error }}</p>
					</div>
					<div class="kt-dialog-actions">
						<button type="button" class="kt-btn kt-btn-secondary" data-testid="pln-class-cancel" @click="$emit('cancel')">
							Cancel
						</button>
						<button
							type="button"
							class="kt-btn kt-btn-primary"
							data-testid="pln-class-save"
							:disabled="pending || !canSave"
							@click="$emit('save')"
						>
							Save classification correction
						</button>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	evidence: { type: Object, default: () => ({}) },
	panel: { type: Object, default: null },
	newType: { type: String, default: "" },
	reason: { type: String, default: "" },
	error: { type: String, default: "" },
	pending: Boolean,
});

defineEmits(["correct", "cancel", "save", "update:newType", "update:reason"]);

const rows = computed(() => props.evidence.rows || []);

function lastCorrection(row) {
	const corrections = row.classification?.corrections || [];
	return corrections[corrections.length - 1] || {};
}

// A correction can only move the classification somewhere else, so the current
// type is not offered.
const selectableTypes = computed(() =>
	(props.evidence.requirement_types || []).filter(
		(option) => option.requirement_type !== props.panel?.classification?.requirement_type,
	),
);

const derivedCategory = computed(() => {
	if (!props.newType) return "—";
	const match = (props.evidence.requirement_types || []).find((o) => o.requirement_type === props.newType);
	return match ? match.procurement_category : "—";
});

const canSave = computed(() => Boolean(props.newType) && props.reason.trim().length >= 20);

// §5.1.6 items 6–8: what the Planner must do next depends entirely on what
// already consumed this source.
const RECOVERY_TEXT = {
	dissolve_and_reform:
		"This requirement is already in a draft purchase. The purchase will need to be rebuilt before the plan can continue. "
		+ "The accepted departmental submission will not change.",
	plan_successor:
		"This requirement is in a plan that is already under review or in force. That plan stays exactly as it is; "
		+ "the corrected classification is carried in through the applicable correction or plan update.",
	downstream_owner:
		"This purchase is already in procurement and cannot be reclassified through Planning. The correction is recorded, "
		+ "but it has not changed the existing procurement. Follow the correction or cancellation process shown for that procurement.",
	none: "Nothing has used this requirement yet, so it becomes available with the corrected classification. "
		+ "The accepted departmental submission will not change.",
};

const impactText = computed(() => RECOVERY_TEXT[props.panel?.affected?.recovery || "none"]);

const affectedNotices = computed(() =>
	rows.value
		.filter((row) => !row.excluded && row.classification?.corrected && row.affected?.recovery !== "none")
		.map((row) => ({
			key: row.dpp_entry_id,
			kind: row.affected.recovery === "downstream_owner" ? "is-critical" : "is-warning",
			text: noticeFor(row),
		})),
);

function noticeFor(row) {
	const affected = row.affected;
	if (affected.recovery === "downstream_owner") {
		const item = affected.locked_items[0];
		return `${row.title} is in purchase ${item.plan_item_id}, which already has an authorised requisition. `
			+ "Planning cannot reclassify it; follow the correction process for that procurement.";
	}
	if (affected.recovery === "dissolve_and_reform") {
		const item = affected.draft_items[0];
		return `${row.title} is in draft purchase ${item.plan_item_id}. Remove that purchase and add its requirements again `
			+ "so method, reservation and schedule checks use the corrected classification.";
	}
	const item = affected.governed_items[0];
	return `${row.title} is in purchase ${item.plan_item_id}, in a plan that is ${item.plan_version_status.toLowerCase()}. `
		+ "That plan stays in force; carry the correction in through a plan update.";
}
</script>
