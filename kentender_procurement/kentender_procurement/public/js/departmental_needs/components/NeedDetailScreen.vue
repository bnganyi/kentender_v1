<!-- NDS-UI-04 / NDS-UI-06 need detail (§12.4), ported class-for-class from
     NDS Artboards.dc.html — NDS-DES-05 submitted, NDS-DES-07 accepted + the
     Planning-status variants derivable from the existing usage/disposition
     projections (NONE/PROCEEDING/EXCLUDED/STILL-ACTIVE/RESTORED),
     NDS-DES-08-DRAFT/SUBMITTED/RETURNED/OTHER-AUTHOR (an open successor's own
     status, not the Need's root state), NDS-DES-11-REQUESTED/OPEN-UPDATE (the
     withdrawal-blocking facts shown on this same detail page, not the
     withdrawal review screen), and NDS-DES-TERMINAL (decline/
     withdrawal) — the decision-reason/withdrawn-by block, content and
     structure ported from NDS Artboards.dc.html using the live
     `.kt-notice`/`.kt-meta-row`/`.kt-label` vocabulary rather than the
     mockup's own inline styles. The screen shows the exact revision it was
     asked for and never rewrites the requested one. -->
<template>
	<div class="kt-page">
		<div class="kt-page-head">
			<div>
				<h1 class="kt-page-title">{{ shownRevision.title }}</h1>
				<div style="display: flex; align-items: center; gap: 12px; margin-top: 8px">
					<span class="text-muted" style="font-size: 13px">{{ need.need_reference }}</span>
					<span class="kt-status" :class="statusClass">{{ statusLabel }}</span>
					<span class="text-muted" style="font-size: 12px">Revision {{ shownRevision.revision_number }}</span>
				</div>
				<div class="kt-page-scope">
					<span>{{ orientationLine }}</span>
				</div>
			</div>
			<div v-if="ownerActions.length" class="kt-page-actions">
				<button
					v-for="action in ownerActions"
					:key="action.code"
					class="kt-btn kt-btn-secondary"
					data-testid="nds-owner-action"
					:data-action="action.code"
					@click="$emit(action.code)"
				>
					<svg
						v-if="action.code === 'create-update'"
						width="15"
						height="15"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.5"
						stroke-linecap="round"
						stroke-linejoin="round"
					><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" /><path d="M14 2v4a2 2 0 0 0 2 2h4" /><path d="m11 17 4-4-1.5-1.5L9.5 15.5V17z" /></svg>
					<svg
						v-else-if="action.code === 'request-withdrawal'"
						width="15"
						height="15"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.5"
						stroke-linecap="round"
						stroke-linejoin="round"
					><rect width="20" height="5" x="2" y="3" rx="1" /><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8" /><path d="M10 12h4" /></svg
					>{{ action.label }}
				</button>
			</div>
		</div>

		<!-- NDS-DES-TERMINAL (decline/withdrawal) — "Decision reason" +
		     Decided by/at for a declined Need, or Withdrawn by/at (no reason:
		     §5.1's self-service withdrawal collects none) for a self-withdrawn
		     one. Neither `editAction` nor `reviewAction` nor `showPlanning`
		     apply to either terminal state, so this always renders directly
		     under the header when present. -->
		<div v-if="terminalDecision" class="kt-notice is-critical" data-testid="nds-terminal-decision">
			<div class="kt-notice-body">
				<template v-if="terminalDecision.reason">
					<span class="kt-label">Decision reason</span>
					<p class="kt-factstack-value" style="margin: 8px 0 16px">{{ terminalDecision.reason }}</p>
				</template>
				<div class="kt-meta-row">
					<div><span class="kt-label">{{ decidedByLabel }}</span><span class="kt-meta-value" style="font-size: 15px">{{ terminalDecision.actor_label }}</span></div>
					<div><span class="kt-label">{{ decidedAtLabel }}</span><span class="kt-meta-value" style="font-size: 15px">{{ terminalDecision.occurred_label }}</span></div>
				</div>
			</div>
		</div>

		<!-- NDS-DES-14 MASKED-DETAIL is rendered by the parent (access denied
		     before this component mounts); a superseded pinned revision stays
		     readable and says so. -->
		<div v-if="isHistoricalRevision" class="kt-notice is-info">
			<div class="kt-notice-body">
				This revision has been superseded. Revision {{ currentAcceptedNumber }} is now the
				current accepted revision of this need.
			</div>
		</div>

		<div v-if="editAction" class="kt-notice is-warning" data-testid="nds-detail-editable">
			<div class="kt-notice-body">
				<template v-if="isReturned && latestReturn">
					<strong>What needs to change</strong><br />
					{{ latestReturn.reason }}
					<div style="display: flex; gap: var(--kt-space-6); margin-top: var(--kt-space-3); font-size: 12px">
						<div><strong style="color: var(--kt-color-text)">Returned by</strong> {{ latestReturn.actor_label }}</div>
						<div><strong style="color: var(--kt-color-text)">Returned at</strong> {{ latestReturn.occurred_label }}</div>
					</div>
				</template>
				<template v-else>This need has not been submitted for departmental review yet.</template>
			</div>
			<button class="kt-btn kt-btn-primary" style="margin-top: var(--kt-space-3)" data-testid="nds-detail-edit" @click="$emit('edit')">
				{{ editAction.label }}
			</button>
		</div>

		<div v-if="need.current_state === 'Submitted'" class="kt-notice is-info">
			<div class="kt-notice-body">
				Submitted for review. Your Head of Department must decide whether this requirement
				should be available to Procurement Planning. The details cannot be edited while
				review is pending.
			</div>
		</div>
		<div v-if="reviewAction">
			<button class="kt-btn kt-btn-primary" data-testid="nds-detail-review" @click="$emit('review', reviewAction)">
				{{ reviewAction.label }}
			</button>
		</div>

		<!-- NDS-DES-08-DRAFT/SUBMITTED/OTHER-AUTHOR — an open successor's own
		     revision status decides the notice, never the Need's root
		     `current_state` (§5.2 holds that at "Accepted for planning" for
		     the whole successor lifecycle). The action link is the maker's
		     alone (`canOpenSuccessor` — accessProfile === owner); any other
		     reader (OTHER-AUTHOR) sees the same fact with no link.
		     NDS-DES-08-RETURNED (a successor sent back for correction) is not
		     distinguishable from a fresh Draft with today's read contract — a
		     returned successor's `current_revision` is immediately repointed
		     to a brand-new correction copy (services/lifecycle.py
		     `review_need`, same "preserve the snapshot, copy for editing"
		     mechanism the primary-Need return path uses), so no field says
		     "this Draft exists because of a return" the way the primary
		     Need's own `current_state === 'Returned'` does. FOLLOW_UPS FU-38. -->
		<div v-if="openSuccessor" class="kt-notice">
			<div class="kt-notice-body">
				<template v-if="successorSubmitted">
					<div style="font-weight: 600; color: var(--kt-color-text)">Your changes are awaiting review</div>
					<p v-if="canOpenSuccessor && submittedAt" class="text-muted" style="margin: 6px 0 0; font-size: 12px">
						Submitted at {{ formatInstant(submittedAt) }}
					</p>
					<button
						v-if="canOpenSuccessor"
						type="button"
						class="kt-action-link"
						style="margin-top: 8px"
						data-testid="nds-open-successor"
						@click="$emit('open-successor')"
					>
						View proposed changes
					</button>
				</template>
				<template v-else>
					<div style="font-weight: 600; color: var(--kt-color-text)">Update in progress</div>
					<button
						v-if="canOpenSuccessor"
						type="button"
						class="kt-action-link"
						style="margin-top: 8px"
						data-testid="nds-open-successor"
						@click="$emit('open-successor')"
					>
						Continue update
					</button>
					<!-- NDS-DES-11-OPEN-UPDATE — names the reason Request withdrawal is
					     absent from the header while an update is open (ownerActions
					     already omits it, §5.3); relevant to the maker alone. -->
					<p v-if="canOpenSuccessor" style="margin: 12px 0 0">
						An update is already in progress. Complete or cancel it before requesting withdrawal.
					</p>
				</template>
			</div>
		</div>

		<!-- NDS-DES-11-REQUESTED — a withdrawal already open against a
		     STILL-ACTIVE requirement leads with this headline instead of the
		     inline "Where this requirement stands" warning below (which stays
		     for the no-open-withdrawal STILL-ACTIVE case, NDS-DES-07A), so the
		     same fact is never shown twice on one page. -->
		<div v-if="withdrawalOpen && stillActive" class="kt-notice is-warning" data-testid="nds-withdrawal-waiting">
			<div class="kt-notice-body">
				<div style="font-weight: 600; color: var(--kt-color-text)">Waiting for a Planning change</div>
				<p style="margin: 6px 0 0">
					The annual plan has not yet been updated. Withdrawal cannot be approved while
					this requirement remains included.
				</p>
			</div>
		</div>

		<!-- §11.8 "Where this requirement stands" — Departmental plan and
		     Current annual plan as two sibling .kt-group facts, never merged
		     into one status. §11.8A REFRESHING/UNAVAILABLE (their own,
		     independently-retriable check) sit above the pair; a material
		     mixed-state warning (STILL-ACTIVE/OLDER) sits immediately after,
		     before "Accepted requirement" — NDS-DES-07A's own placement rule. -->
		<div v-if="showPlanning" class="kt-region">
			<h2>Where this requirement stands</h2>
			<div v-if="planningRefreshing" class="text-muted" style="font-size: 12.5px; margin-bottom: var(--kt-space-2)">
				Updating Planning information…
			</div>
			<div v-if="planningUnavailable" class="kt-notice is-critical" style="margin-bottom: var(--kt-space-3)">
				<div class="kt-notice-body" style="font-size: 12px">
					Planning information is temporarily unavailable.<br />
					Withdrawal cannot be approved until the required check succeeds.
					<div>
						<button
							type="button"
							class="kt-action-link"
							data-testid="nds-retry-planning"
							style="font-size: 12px; margin-top: 6px"
							@click="$emit('retry-planning')"
						>
							Try again
						</button>
					</div>
				</div>
			</div>
			<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; max-width: 900px">
				<div v-if="departmentalPlanStatus" class="kt-group">
					<span class="kt-label">Departmental plan</span>
					<div style="display: flex; align-items: center; gap: 10px; margin-top: 8px">
						<span class="kt-status" :class="departmentalPlanStatus.cls">{{ departmentalPlanStatus.label }}</span>
					</div>
					<!-- NDS-DES-07A-EXCLUDED/STILL-ACTIVE — a not-proceeding exclusion
					     names its own reason under a "Reason" label, set off by a
					     divider; every other outcome keeps the plain unlabelled
					     sentence (NDS-DES-07/07-PLANNER/07-AUDITOR/07A-PROCEEDING/
					     RESTORED's "Included" explanation). -->
					<div
						v-if="departmentalPlanStatus.cls === 'is-attention'"
						style="margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--kt-color-divider)"
					>
						<span class="kt-label">Reason</span>
						<p style="margin: 6px 0 0; font-size: 13px; color: var(--kt-color-neutral-800)">{{ departmentalPlanStatus.explanation }}</p>
					</div>
					<p v-else style="margin: 12px 0 0; font-size: 13px; color: var(--kt-color-neutral-800)">{{ departmentalPlanStatus.explanation }}</p>
				</div>
				<div class="kt-group">
					<span class="kt-label">Current annual plan</span>
					<div style="display: flex; align-items: center; gap: 10px; margin-top: 8px">
						<span class="kt-status" :class="annualPlanStatus.cls">{{ annualPlanStatus.label }}</span>
					</div>
					<p style="margin: 12px 0 0; font-size: 13px; color: var(--kt-color-neutral-800)">{{ annualPlanStatus.explanation }}</p>
					<!-- NDS-DES-07A-STILL-ACTIVE/RESTORED — the concrete Plan Item
					     an Active projection names is one click away here too, not
					     only inside the "Planning decisions and history" disclosure. -->
					<button
						v-if="usage.active_plan_item"
						type="button"
						class="kt-action-link"
						style="margin-top: 10px"
						data-testid="nds-view-plan-item-inline"
						@click="$emit('view-plan-item')"
					>
						View annual plan item
					</button>
				</div>
			</div>
			<p class="text-muted" style="margin: 12px 0 0; font-size: 12px">
				These statuses do not confirm that the requirement has been purchased or delivered.
			</p>
			<div
				v-if="(planningRefreshing || planningUnavailableWithSnapshot) && planningCheckedAt"
				class="text-muted"
				style="font-size: 12px; margin-top: var(--kt-space-2)"
			>
				Last confirmed: {{ formatInstant(planningCheckedAt) }}
			</div>
			<!-- NDS-DES-07A STILL-ACTIVE — a not-proceeding departmental
			     disposition with the requirement still Fully included blocks
			     withdrawal until Planning clears it. Absent while a withdrawal
			     request is already open (NDS-DES-11-REQUESTED) — the top-level
			     "Waiting for a Planning change" notice above says the same thing
			     once, not twice. -->
			<div v-if="stillActive && !withdrawalOpen" class="kt-notice is-warning" style="margin-top: var(--kt-space-4)">
				<div class="kt-notice-body" style="font-size: 12px">
					The annual plan has not yet been updated. Withdrawal cannot be approved while
					this requirement remains included.
				</div>
			</div>
			<!-- NDS-DES-07A OLDER — the current accepted revision has never itself
			     been projected, but Planning is still using an earlier accepted
			     revision's inclusion. -->
			<div v-if="olderUsageFact" class="kt-notice is-info" style="margin-top: var(--kt-space-4)">
				<div class="kt-notice-body" style="font-size: 12px">
					The current annual plan still uses the previously accepted details.
					<div style="display: flex; gap: var(--kt-space-6); margin-top: var(--kt-space-3)">
						<div><strong style="color: var(--kt-color-text)">Included requirement revision</strong> {{ olderUsageFact.revision_number }}</div>
						<div v-if="olderUsageFact.required_by_date"><strong style="color: var(--kt-color-text)">Earlier required-by date</strong> {{ formatDate(olderUsageFact.required_by_date) }}</div>
					</div>
					<div style="display: flex; gap: var(--kt-space-4); margin-top: 6px">
						<button
							type="button"
							class="kt-action-link"
							data-testid="nds-view-earlier-requirement"
							style="font-size: 12px"
							@click="olderRequirementOpen = !olderRequirementOpen"
						>
							{{ olderRequirementOpen ? "Hide earlier requirement" : "View earlier requirement" }}
						</button>
						<button
							v-if="olderUsageFact.active_plan_item"
							type="button"
							class="kt-action-link"
							style="font-size: 12px"
							@click="$emit('view-plan-item')"
						>
							View annual plan item
						</button>
					</div>
					<RequirementCard v-if="olderRequirementOpen" :revision="olderUsageFact.content" />
				</div>
			</div>
		</div>

		<!-- A titled section is a `.kt-region`: that is what puts its heading
		     in the section typeface and its content on the section rhythm.
		     Five headings in this module stood in bare divs, so they were
		     styled by nothing and drifted from the sections beside them
		     (found live 24 Sep 2026). -->
		<div class="kt-region">
			<h2>{{ isAccepted ? "Accepted requirement" : "Requirement" }}</h2>
			<div style="max-width: 900px">
				<RequirementCard :revision="shownRevision" />
			</div>
		</div>

		<div v-if="showPlanning && planningHistory.length" class="kt-disclosure" style="max-width: 900px">
			<div class="kt-disclosure-head" @click="planningHistoryOpen = !planningHistoryOpen">
				<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">Planning decisions and history</span></div>
				<svg
					class="kt-disclosure-chevron"
					:class="{ 'is-open': planningHistoryOpen }"
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
				><path d="M6 9l6 6 6-6" /></svg>
			</div>
			<div v-if="planningHistoryOpen" class="kt-disclosure-body">
				<div class="kt-timeline">
					<div v-for="(item, index) in planningHistory" :key="index" class="kt-timeline-row">
						<div class="kt-timeline-dot-col">
							<i class="kt-timeline-dot" :class="item.dotClass"></i>
							<i v-if="index < planningHistory.length - 1" class="kt-timeline-line"></i>
						</div>
						<div class="kt-timeline-item">
							<div class="kt-timeline-item-title">{{ item.title }}</div>
							<div class="kt-timeline-item-meta">{{ item.meta }}</div>
							<div v-if="item.meta2" class="kt-timeline-item-meta">{{ item.meta2 }}</div>
							<button
								v-if="item.action"
								type="button"
								class="kt-action-link"
								style="font-size: 12px"
								@click="$emit(item.action)"
							>
								{{ item.actionLabel }}
							</button>
						</div>
					</div>
				</div>
			</div>
		</div>

		<div v-else-if="!showPlanning && history.length" class="kt-disclosure" style="max-width: 900px">
			<div class="kt-disclosure-head" @click="planningHistoryOpen = !planningHistoryOpen">
				<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">History</span></div>
				<svg
					class="kt-disclosure-chevron"
					:class="{ 'is-open': planningHistoryOpen }"
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
				><path d="M6 9l6 6 6-6" /></svg>
			</div>
			<div v-if="planningHistoryOpen" class="kt-disclosure-body">
				<div class="kt-timeline">
					<div v-for="(item, index) in history" :key="index" class="kt-timeline-row">
						<div class="kt-timeline-dot-col">
							<i class="kt-timeline-dot" :class="item.dot_class"></i>
							<i v-if="index < history.length - 1" class="kt-timeline-line"></i>
						</div>
						<div class="kt-timeline-item">
							<div class="kt-timeline-item-title">{{ item.title }}</div>
							<div class="kt-timeline-item-meta">{{ item.meta }}</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import RequirementCard from "./RequirementCard.vue";
import { formatDate, formatInstant } from "../data/format.js";

const props = defineProps({
	need: { type: Object, default: () => ({}) },
	scopeLabels: { type: Object, default: () => ({}) },
	revision: { type: Object, default: () => ({}) },
	acceptedRevision: { type: Object, default: () => ({}) },
	usage: { type: Object, default: () => ({}) },
	// get_departmental_need().planning_disposition — Planning information only.
	disposition: { type: Object, default: null },
	// §11.8A — the dedicated Planning-status re-check's own state (NDS-CHG-001
	// v1.14 Phase 2), separate from this screen's own load.
	olderUsage: { type: Object, default: null },
	planningChecking: Boolean,
	planningUnavailable: Boolean,
	planningCheckedAt: { type: String, default: "" },
	authorLabel: { type: String, default: "" },
	accessProfile: { type: String, default: "" },
	actions: { type: Array, default: () => [] },
	latestReturn: { type: Object, default: null },
	// NDS-DES-TERMINAL — { reason, actor_label, occurred_label }. `reason` is
	// empty for a self-service withdrawal (§5.1 collects none); always
	// present for a decline.
	terminalDecision: { type: Object, default: null },
	acceptedByLabel: { type: String, default: "" },
	acceptedAt: { type: String, default: "" },
	acceptedCapacity: { type: String, default: "" },
	submittedAt: { type: String, default: "" },
	withdrawalOpen: Boolean,
	pinnedRevision: { type: Object, default: null },
	history: { type: Array, default: () => [] },
});
defineEmits([
	"create-update",
	"request-withdrawal",
	"view-plan-item",
	"open-successor",
	"edit",
	"review",
	"retry-planning",
]);

const olderRequirementOpen = ref(false);

const planningHistoryOpen = ref(false);

const isReturned = computed(() => props.need.current_state === "Returned");
const isAccepted = computed(() => props.need.current_state === "Accepted for planning");
const editAction = computed(() => (props.actions || []).find((a) => a.code === "edit") || null);
const reviewAction = computed(
	() => (props.actions || []).find((a) => a.code === "review" || a.code === "withdrawal") || null
);

const shownRevision = computed(
	() => props.pinnedRevision || (props.acceptedRevision?.name && props.acceptedRevision) || props.revision || {}
);

const isHistoricalRevision = computed(
	() =>
		!!props.pinnedRevision &&
		!!props.acceptedRevision?.name &&
		props.pinnedRevision.name !== props.acceptedRevision.name
);

const currentAcceptedNumber = computed(() => props.acceptedRevision?.revision_number || "");

const STATUS_LABELS = {
	Draft: ["is-draft", "Draft"],
	Submitted: ["is-pending", "Awaiting Head of Department review"],
	Returned: ["is-attention", "Changes requested"],
	"Accepted for planning": ["is-live", "Accepted for planning"],
	"Not taken forward": ["is-critical", "Not taken forward"],
	Withdrawn: ["is-critical", "Withdrawn"],
};
const statusClass = computed(() => STATUS_LABELS[props.need.current_state]?.[0] || "is-draft");
const statusLabel = computed(() => STATUS_LABELS[props.need.current_state]?.[1] || props.need.current_state || "");

// NDS-DES-TERMINAL — "Decided by/at" for a decline, "Withdrawn by/at" for a
// self-withdrawal; the same two facts, labelled for which one actually
// happened.
const decidedByLabel = computed(() => (props.need.current_state === "Withdrawn" ? "Withdrawn by" : "Decided by"));
const decidedAtLabel = computed(() => (props.need.current_state === "Withdrawn" ? "Withdrawn at" : "Decided at"));

const openSuccessor = computed(
	() =>
		isAccepted.value &&
		props.need.current_revision &&
		props.need.current_accepted_revision &&
		props.need.current_revision !== props.need.current_accepted_revision
);

const canOpenSuccessor = computed(() => props.accessProfile === "owner");

// NDS-DES-08-SUBMITTED — the open successor's own revision status, read only
// while a successor is actually open so a plain accepted Need (no successor)
// never falls into this branch by accident. "Draft" is the fallback for
// every other successor state, including one just returned for correction
// (FOLLOW_UPS FU-38 — not distinguishable from a fresh Draft today).
const successorSubmitted = computed(
	() => openSuccessor.value && props.revision?.revision_status === "Submitted"
);

const ownerActions = computed(() => {
	if (props.accessProfile !== "owner" || !isAccepted.value || isHistoricalRevision.value) return [];
	const available = [];
	if (!openSuccessor.value) available.push({ code: "create-update", label: "Create update" });
	// NDS-DES-11-OPEN-UPDATE — an open successor and an open withdrawal
	// request are mutually exclusive (§5.3); Request withdrawal is absent
	// while an update is already in progress, not just while one is open.
	if (!props.withdrawalOpen && !openSuccessor.value)
		available.push({ code: "request-withdrawal", label: "Request withdrawal" });
	return available;
});

function label(field) {
	return props.scopeLabels[field] || props.need[field] || "";
}

// §11.5/§11.8 — one orientation sentence beneath the header, replacing the
// four separately labelled Department/Financial year/Submitted-or-Accepted
// facts: "{department} · {FY} · Submitted by {author} on {date}" or
// "… · Accepted by {actor}[ as {capacity}] on {date}".
const orientationLine = computed(() => {
	const parts = [label("organisation_unit"), label("financial_year")];
	if (isAccepted.value) {
		const actor = props.acceptedByLabel || props.authorLabel;
		const capacity = props.acceptedCapacity ? ` as ${props.acceptedCapacity}` : "";
		const when = props.acceptedAt ? ` on ${formatInstant(props.acceptedAt)}` : "";
		if (actor) parts.push(`Accepted by ${actor}${capacity}${when}`);
	} else if (props.authorLabel) {
		const when = props.submittedAt ? ` on ${formatInstant(props.submittedAt)}` : "";
		parts.push(`Submitted by ${props.authorLabel}${when}`);
	}
	return parts.filter(Boolean).join(" · ");
});

const showPlanning = computed(() => isAccepted.value);

// §11.8A — whether there is any recorded Planning fact at all to fall back
// on while a check is in flight or has failed. Absent this, a failure is
// UNAVAILABLE-NO-SNAPSHOT rather than UNAVAILABLE.
const hasPlanningSnapshot = computed(
	() => Boolean(props.disposition?.recorded) || Boolean(props.usage?.recorded) || Boolean(props.olderUsage)
);
const planningRefreshing = computed(() => props.planningChecking && hasPlanningSnapshot.value);
const planningUnavailableWithSnapshot = computed(() => props.planningUnavailable && hasPlanningSnapshot.value);
const planningUnavailableNoSnapshot = computed(() => props.planningUnavailable && !hasPlanningSnapshot.value);
const olderUsageFact = computed(() => (!props.usage?.recorded ? props.olderUsage : null));

// §11.8/§11.8A — Departmental plan reads the accepted DPP disposition;
// Current annual plan reads Active usage. The two are independent facts,
// never merged into one status. REFRESHING/UNAVAILABLE keep the
// last-confirmed labels with their own suffix rather than showing a new
// (unconfirmed) result; UNAVAILABLE-NO-SNAPSHOT shows neither.
const statusSuffix = computed(() =>
	planningRefreshing.value || planningUnavailableWithSnapshot.value ? " — last confirmed" : ""
);
const departmentalPlanStatus = computed(() => {
	if (planningUnavailableNoSnapshot.value)
		return { cls: "is-critical", label: "Unavailable", explanation: "" };
	// Owner instruction, 23 September 2026: say nothing about the departmental
	// plan until there is a departmental decision to report. Accepting a Need
	// now starts the department's Draft plan, so "No accepted departmental
	// decision recorded" sat beside a plan that demonstrably existed and read
	// as if nothing had happened. The fact returns the moment Procurement
	// accepts the departmental plan, as Included or Not included this year.
	if (!props.disposition?.recorded) return null;
	return props.disposition.disposition === "Not proceeding"
		? {
				cls: "is-attention",
				label: `Not included this year${statusSuffix.value}`,
				explanation: props.disposition.reason || "",
			}
		: {
				cls: "is-live",
				label: `Included${statusSuffix.value}`,
				explanation: "The accepted departmental plan includes this requirement.",
			};
});
const annualPlanStatus = computed(() => {
	if (planningUnavailableNoSnapshot.value)
		return { cls: "is-critical", label: "Unavailable", explanation: "" };
	if (props.usage?.usage !== "Fully included")
		return { cls: "is-pending", label: `Not included${statusSuffix.value}`, explanation: "" };
	// STILL-ACTIVE — a not-proceeding departmental disposition, but the
	// requirement remains represented in the current annual plan.
	return stillActive.value
		? { cls: "is-live", label: `Still included${statusSuffix.value}`, explanation: "" }
		: {
				cls: "is-live",
				label: `Included${statusSuffix.value}`,
				explanation: "The current annual procurement plan includes this requirement.",
			};
});
const stillActive = computed(
	() => props.disposition?.recorded && props.disposition.disposition === "Not proceeding" && props.usage?.usage === "Fully included"
);

const planningHistory = computed(() => {
	const items = [];
	for (const row of props.disposition?.history || []) {
		items.push({
			title: "Departmental decision",
			meta: `Requirement revision ${(row.need_revision || "").split("-V").pop()?.replace(/^0+/, "") || ""} · ${row.dpp_submission || ""}`,
			meta2: row.actor_label || row.decision_at ? `Accepted by Procurement${row.actor_label ? " " + row.actor_label : ""}${row.decision_at ? " · " + formatInstant(row.decision_at) : ""}` : "",
			dotClass: row.disposition === "Not proceeding" ? "is-attention" : "is-live",
		});
	}
	if (props.usage?.active_plan_item) {
		items.push({
			title: "Annual plan",
			meta: props.usage.active_plan || "",
			meta2: props.usage.active_plan_item || "",
			dotClass: "is-live",
			action: "view-plan-item",
			actionLabel: "View annual plan item",
		});
	}
	return items;
});
</script>
