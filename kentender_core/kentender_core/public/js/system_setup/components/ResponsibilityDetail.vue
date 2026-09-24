<script setup>
// AUTH-DES-06, ported from C06 #auth-des-06 (Active) and
// #auth-des-06-scheduled: the reference as eyebrow, the title with its
// status, the Assignment facts beside the Audit group, the collapsed Access
// diagnostics, the Administrative history (a change made before the start is
// one event with a line per changed field, #auth-changed-history) and the
// sticky footer.
//
// An assignment already in force is never edited: an incorrect one is
// revoked and replaced so historical authority is never rewritten. One that
// has not started yet may still be changed (owner decision 21 Sep 2026) —
// Edit, like Revoke, appears only because the server said so (`can_edit` /
// `can_revoke`). No Procuring Entity row exists (AUTH §13.7).
import { ref } from "vue";

defineProps({
	assignment: { type: Object, required: true },
});
const emit = defineEmits(["revoke", "edit"]);

const diagnosticsOpen = ref(false);

const STATUS_KIND = {
	Active: "is-live",
	Scheduled: "is-draft",
	Expired: "is-pending",
	Revoked: "is-critical",
};
</script>

<template>
	<div class="kt-ura-detail" data-testid="kt-ura-detail">
		<div class="kt-eyebrow">{{ assignment.assignment }}</div>
		<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:4px 0 24px">
			<h2 style="margin:0">{{ assignment.user_full_name }} — {{ assignment.business_role }}</h2>
			<span class="kt-status" :class="STATUS_KIND[assignment.status]" data-testid="kt-ura-detail-status">{{ assignment.status }}</span>
		</div>

		<div class="kt-ura-detail-grid">
			<div>
				<h3 style="margin:0 0 10px">{{ __("Assignment") }}</h3>
				<dl class="kt-setup-facts is-wide">
					<dt class="kt-label">{{ __("User") }}</dt>
					<dd>{{ assignment.user_full_name }} · {{ assignment.user }}</dd>
					<dt class="kt-label">{{ __("Responsibility") }}</dt>
					<dd>{{ assignment.business_role }}</dd>
					<dt class="kt-label">{{ __("Scope classification") }}</dt>
					<dd>{{ assignment.scope_type }}</dd>
					<dt class="kt-label">{{ __("Organisation Unit") }}</dt>
					<dd>{{ assignment.organisation_unit_path || __("Site-wide") }}</dd>
					<dt class="kt-label">{{ __("Included units") }}</dt>
					<dd>{{ assignment.coverage }}</dd>
					<dt class="kt-label">{{ __("Appointment") }}</dt>
					<dd>{{ assignment.appointment_type }}</dd>
					<dt class="kt-label">{{ __("Effective period") }}</dt>
					<dd>{{ assignment.effective_label }}</dd>
					<template v-if="assignment.authority_reference">
						<dt class="kt-label">{{ __("Authority reference") }}</dt>
						<dd>{{ assignment.authority_reference }}</dd>
					</template>
				</dl>
			</div>
			<div class="kt-group">
				<h4 style="margin:0 0 10px">{{ __("Audit") }}</h4>
				<dl class="kt-setup-facts is-plain">
					<dt class="kt-label">{{ __("Assigned by") }}</dt>
					<dd>{{ assignment.assigned_by || "—" }}</dd>
					<dt class="kt-label">{{ __("Assigned at") }}</dt>
					<dd>{{ assignment.assigned_at_label || "—" }}</dd>
					<template v-if="assignment.revoked_by">
						<dt class="kt-label">{{ __("Revoked by") }}</dt>
						<dd>{{ assignment.revoked_by }}</dd>
						<dt class="kt-label">{{ __("Revoked at") }}</dt>
						<dd>{{ assignment.revoked_at_label }}</dd>
						<dt class="kt-label">{{ __("Revocation reason") }}</dt>
						<dd>{{ assignment.revocation_reason }}</dd>
					</template>
					<dt class="kt-label">{{ __("Frappe role projection") }}</dt>
					<dd>{{ assignment.diagnostics.projection_present ? __("Synchronised") : assignment.status === "Scheduled" ? __("Not yet required") : __("Missing") }}</dd>
				</dl>
			</div>
		</div>

		<!-- §14.4 — read-only; never repairs or broadens, and never shows a
		     protected record's content. -->
		<div class="kt-disclosure" style="margin-top:24px">
			<div
				class="kt-disclosure-head"
				role="button"
				tabindex="0"
				:aria-expanded="diagnosticsOpen ? 'true' : 'false'"
				data-testid="kt-ura-diagnostics-toggle"
				@click="diagnosticsOpen = !diagnosticsOpen"
				@keydown.enter.prevent="diagnosticsOpen = !diagnosticsOpen"
				@keydown.space.prevent="diagnosticsOpen = !diagnosticsOpen"
			>
				<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">{{ __("Access diagnostics") }}</span></div>
				<svg class="kt-disclosure-chevron" :class="{ 'is-open': diagnosticsOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M6 9l6 6 6-6" /></svg>
			</div>
			<div v-if="diagnosticsOpen" class="kt-disclosure-body" data-testid="kt-ura-diagnostics">
				<dl class="kt-setup-facts is-plain">
					<dt class="kt-label">{{ __("Required Frappe Role projection") }}</dt>
					<dd>
						{{ assignment.diagnostics.required_projection.join(", ") }} —
						{{ assignment.diagnostics.projection_present ? __("present") : __("missing") }}
					</dd>
					<dt class="kt-label">{{ __("Resolved organisational coverage") }}</dt>
					<dd>{{ assignment.diagnostics.coverage }}</dd>
					<dt class="kt-label">{{ __("Configuration conflicts or overlaps") }}</dt>
					<dd>{{ assignment.diagnostics.overlapping.length ? assignment.diagnostics.overlapping.length : __("None found") }}</dd>
					<dt class="kt-label">{{ __("Orphan Frappe Roles") }}</dt>
					<dd>{{ assignment.diagnostics.projection_orphaned.length ? assignment.diagnostics.projection_orphaned.join(", ") : __("None") }}</dd>
					<dt class="kt-label">{{ __("Obsolete records awaiting migration") }}</dt>
					<dd>
						{{ Object.values(assignment.diagnostics.obsolete_rows || {}).some((n) => n)
							? Object.entries(assignment.diagnostics.obsolete_rows).filter(([, n]) => n).map(([k, n]) => k + ": " + n).join(" · ")
							: __("None") }}
					</dd>
				</dl>
			</div>
		</div>

		<h3 style="margin:24px 0 10px;font-size:17px">{{ __("Administrative history") }}</h3>
		<div class="kt-table-scroll" data-testid="kt-ura-history">
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
						<td style="vertical-align:top">{{ event.when }}</td>
						<td style="vertical-align:top">{{ event.actor }}</td>
						<td>
							<template v-if="(event.changes || []).length">
								<div style="font-weight:600">{{ event.event }}</div>
								<div v-for="change in event.changes" :key="change" class="kt-ura-change">{{ change }}</div>
							</template>
							<template v-else>{{ event.event }}</template>
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div v-if="assignment.can_revoke || assignment.can_edit" class="kt-sticky-footer kt-ura-footer">
			<button
				v-if="assignment.can_edit"
				type="button"
				class="kt-btn kt-btn-secondary"
				data-testid="kt-ura-open-edit"
				@click="emit('edit')"
			>{{ __("Edit scheduled assignment") }}</button>
			<button
				v-if="assignment.can_revoke"
				type="button"
				class="kt-btn kt-btn-primary kt-danger"
				data-testid="kt-ura-open-revoke"
				@click="emit('revoke')"
			>{{ __("Revoke responsibility") }}</button>
		</div>
	</div>
</template>
