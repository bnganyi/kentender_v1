<script setup>
// AUTH-ADR-001 v1.6 §13.7/§14.4, ported from AUTH-DES-06: eyebrow + title
// with the status badge inline, then an Assignment card of labelled rows, an
// Audit card, the collapsed Access-diagnostics row, the Administrative
// history table, and the destructive command alone in the bottom action bar.
//
// There is deliberately no Edit action: an incorrect assignment is revoked
// and replaced so historical authority is never rewritten. Revoke itself
// appears only because the server said so (`can_revoke`). No Procuring
// Entity row exists (§13.7).
import { ref } from "vue";

defineProps({
	assignment: { type: Object, required: true },
});
const emit = defineEmits(["revoke", "back"]);

const diagnosticsOpen = ref(false);

const STATUS_KIND = {
	Active: "is-live",
	Scheduled: "is-draft",
	Expired: "is-pending",
	Revoked: "is-critical",
};
</script>

<template>
	<div class="kt-detail-stack" data-testid="kt-ura-detail">
		<div>
			<a href="#" class="kt-back" data-testid="kt-ura-back-to-register" @click.prevent="emit('back')">
				← {{ __("Users and responsibilities") }}
			</a>
			<div class="kt-detail-head">
				<div class="kt-eyebrow">{{ assignment.assignment }}</div>
				<h2 class="kt-detail-title">
					{{ assignment.user_full_name }} — {{ assignment.business_role }}
					<span class="kt-status" :class="STATUS_KIND[assignment.status]">{{ assignment.status }}</span>
				</h2>
			</div>
		</div>

		<!-- AUTH-DES-06 — Assignment card -->
		<div class="kt-card kt-blueprint">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<div class="kt-card-title">{{ __("Assignment") }}</div>
			<div class="kt-detail-rows">
				<div class="kt-detail-row">
					<span class="kt-label">{{ __("User") }}</span>
					<span>{{ assignment.user_full_name }} · {{ assignment.user }}</span>
				</div>
				<div class="kt-detail-row">
					<span class="kt-label">{{ __("Responsibility") }}</span>
					<span>{{ assignment.business_role }}</span>
				</div>
				<div class="kt-detail-row">
					<span class="kt-label">{{ __("Scope classification") }}</span>
					<span>{{ assignment.scope_type }}</span>
				</div>
				<div class="kt-detail-row">
					<span class="kt-label">{{ __("Organisation Unit") }}</span>
					<span>{{ assignment.organisation_unit_path || __("Site-wide") }}</span>
				</div>
				<div class="kt-detail-row">
					<span class="kt-label">{{ __("Included units") }}</span>
					<span>{{ assignment.coverage }}</span>
				</div>
				<div class="kt-detail-row">
					<span class="kt-label">{{ __("Appointment") }}</span>
					<span>{{ assignment.appointment_type }}</span>
				</div>
				<div v-if="assignment.authority_reference" class="kt-detail-row">
					<span class="kt-label">{{ __("Authority reference") }}</span>
					<span>{{ assignment.authority_reference }}</span>
				</div>
				<div class="kt-detail-row">
					<span class="kt-label">{{ __("Effective period") }}</span>
					<span>{{ assignment.effective_label }}</span>
				</div>
			</div>
		</div>

		<!-- AUTH-DES-06 — Audit card -->
		<div class="kt-card kt-blueprint">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<div class="kt-card-title">{{ __("Audit") }}</div>
			<div class="kt-detail-rows">
				<div class="kt-detail-row">
					<span class="kt-label">{{ __("Assigned by") }}</span>
					<span>{{ assignment.assigned_by || "—" }}</span>
				</div>
				<div class="kt-detail-row">
					<span class="kt-label">{{ __("Assigned at") }}</span>
					<span>{{ assignment.assigned_at_label || "—" }}</span>
				</div>
				<div v-if="assignment.revoked_by" class="kt-detail-row">
					<span class="kt-label">{{ __("Revoked by") }}</span>
					<span>{{ assignment.revoked_by }}</span>
				</div>
				<div v-if="assignment.revoked_by" class="kt-detail-row">
					<span class="kt-label">{{ __("Revoked at") }}</span>
					<span>{{ assignment.revoked_at_label }}</span>
				</div>
				<div v-if="assignment.revoked_by" class="kt-detail-row">
					<span class="kt-label">{{ __("Revocation reason") }}</span>
					<span>{{ assignment.revocation_reason }}</span>
				</div>
				<div class="kt-detail-row">
					<span class="kt-label">{{ __("Frappe role projection") }}</span>
					<span>{{ assignment.diagnostics.projection_present ? __("Synchronised") : __("Missing") }}</span>
				</div>
			</div>
		</div>

		<!-- AUTH-DES-06 — Access diagnostics, collapsed as a row-card -->
		<button
			type="button"
			class="kt-card kt-blueprint kt-diag-card"
			:aria-expanded="diagnosticsOpen"
			data-testid="kt-ura-diagnostics-toggle"
			@click="diagnosticsOpen = !diagnosticsOpen"
		>
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<span class="kt-diag-card-title">{{ __("Access diagnostics") }}</span>
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m9 6 6 6-6 6" /></svg>
		</button>

		<!-- §14.4 — read-only; never repairs or broadens, and never shows a
		     protected record's content. -->
		<div v-if="diagnosticsOpen" class="kt-card kt-blueprint" data-testid="kt-ura-diagnostics">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<div class="kt-diagnostics">
				<div class="kt-diag-row">
					<span class="kt-muted">{{ __("Required & present Frappe Role projection") }}</span>
					<span>
						{{ assignment.diagnostics.required_projection.join(", ") }} —
						{{ assignment.diagnostics.projection_present ? __("present") : __("missing") }}
					</span>
				</div>
				<div class="kt-diag-row">
					<span class="kt-muted">{{ __("Resolved organisational coverage") }}</span>
					<span>{{ assignment.diagnostics.coverage }}</span>
				</div>
				<div class="kt-diag-row">
					<span class="kt-muted">{{ __("Configuration conflicts or overlaps") }}</span>
					<span>{{ assignment.diagnostics.overlapping.length ? assignment.diagnostics.overlapping.length : __("None found") }}</span>
				</div>
				<div class="kt-diag-row">
					<span class="kt-muted">{{ __("Orphan Frappe Roles") }}</span>
					<span>{{ assignment.diagnostics.projection_orphaned.length ? assignment.diagnostics.projection_orphaned.join(", ") : __("None") }}</span>
				</div>
				<div class="kt-diag-row">
					<span class="kt-muted">{{ __("Obsolete records awaiting migration") }}</span>
					<span>
						{{ Object.values(assignment.diagnostics.obsolete_rows || {}).some((n) => n)
							? Object.entries(assignment.diagnostics.obsolete_rows).filter(([, n]) => n).map(([k, n]) => k + ": " + n).join(" · ")
							: __("None") }}
					</span>
				</div>
			</div>
		</div>

		<!-- AUTH-DES-06 — Administrative history -->
		<div class="kt-card kt-blueprint kt-history-card" data-testid="kt-ura-history">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<div class="kt-card-title">{{ __("Administrative history") }}</div>
			<div class="kt-table-scroll">
				<table class="kt-table">
					<thead>
						<tr>
							<th>{{ __("When") }}</th>
							<th>{{ __("Actor") }}</th>
							<th>{{ __("Event") }}</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="event in assignment.history" :key="event.event + event.when">
							<td>{{ event.when }}</td>
							<td>{{ event.actor }}</td>
							<td>{{ event.event }}</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>

		<div v-if="assignment.can_revoke" class="kt-action-bar">
			<button
				type="button"
				class="kt-btn kt-btn-primary kt-danger"
				data-testid="kt-ura-open-revoke"
				@click="emit('revoke')"
			>{{ __("Revoke responsibility") }}</button>
		</div>
	</div>
</template>
