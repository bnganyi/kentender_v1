<!-- NDS-UI-07 withdrawal review (§12.6) — NDS-DES-12a blocked / 12b cleared.
     The dependency is always the fresh server result, never a cached button
     state. -->
<template>
	<div style="padding-bottom: 24px">
		<div style="margin-bottom: 20px">
			<div class="kt-page-kicker" style="letter-spacing: 0.06em">
				WITHDRAWAL REVIEW · {{ request.name }}
			</div>
			<div style="display: flex; align-items: center; gap: 12px; margin-top: 4px">
				<h1 class="kt-record-title">{{ version.title }}</h1>
				<StatusPill :label="request.status || 'Awaiting review'" />
			</div>
		</div>

		<div v-if="errorSummary" data-testid="nds-error-summary" class="kt-error-summary" role="alert" tabindex="-1">
			{{ errorSummary }}
		</div>

		<div class="kt-card kt-blueprint" style="margin-bottom: 16px; padding: 20px 24px">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title" style="margin-bottom: 16px">Request</div>
			<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px">
				<ReadonlyRow label="Requested by" :value="requesterLabel" strong style="margin-top: 0" />
				<ReadonlyRow label="Requested" :value="requestedLabel" strong volatile style="margin-top: 0" />
			</div>
			<ReadonlyRow label="Reason" :value="request.reason" style="margin-top: 0" />
		</div>

		<RequirementCard :version="version" title="Accepted Need" />

		<div class="kt-card kt-blueprint" style="padding: 20px 24px">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px">
				<div class="kt-card-title" style="margin-bottom: 0">
					{{ dependency.included ? "Active Plan inclusion must be cleared" : "No Active Plan inclusion" }}
				</div>
				<StatusPill :label="dependency.included ? 'Fully included' : 'Not included'" />
			</div>
			<p style="margin: 0 0 10px; font-size: 14.5px">
				{{
					dependency.included
						? "The accepted Need is represented by the following Active Plan Item."
						: "This accepted Need is not represented in an Active Plan."
				}}
			</p>
			<!-- §12.6 — View Plan Item navigates only; clearing happens in Planning. -->
			<div
				v-if="dependency.included && dependency.active_plan_item"
				style="display: flex; align-items: center; justify-content: space-between"
			>
				<div style="font-size: 14px; color: var(--color-neutral-700)">
					{{ dependency.active_plan_item }}
				</div>
				<button class="kt-btn kt-btn-secondary" data-testid="nds-view-plan-item" @click="$emit('view-plan-item')">
					View Plan Item
				</button>
			</div>
		</div>

		<div class="kt-page-footer" :style="dependency.included ? 'justify-content: flex-end' : ''">
			<template v-if="dependency.included">
				<button class="kt-btn kt-btn-secondary" data-testid="nds-withdrawal-close" :disabled="pending" @click="$emit('close')">
					Close
				</button>
			</template>
			<template v-else-if="!makerCheckerBlocked">
				<span></span>
				<div style="display: flex; gap: 12px">
					<button class="kt-btn-destructive" data-testid="nds-withdrawal-decline" :disabled="pending" @click="$emit('decline')">
						Decline withdrawal
					</button>
					<button class="kt-btn kt-btn-primary" data-testid="nds-withdrawal-approve" :disabled="pending" @click="$emit('approve')">
						Approve withdrawal
					</button>
				</div>
			</template>
		</div>

		<p
			v-if="makerCheckerBlocked"
			style="margin: 12px 0 0; font-size: 14.5px; color: var(--color-neutral-700)"
		>
			You requested this withdrawal, so it must be decided by another Head of User
			Department.
		</p>
	</div>
</template>

<script setup>
import { computed } from "vue";
import ReadonlyRow from "./ReadonlyRow.vue";
import RequirementCard from "./RequirementCard.vue";
import StatusPill from "./StatusPill.vue";
import { formatInstant } from "../data/format.js";

const props = defineProps({
	request: { type: Object, default: () => ({}) },
	version: { type: Object, default: () => ({}) },
	dependency: { type: Object, default: () => ({}) },
	requesterLabel: { type: String, default: "" },
	requestedAt: { type: String, default: "" },
	makerCheckerBlocked: Boolean,
	errorSummary: { type: String, default: "" },
	pending: Boolean,
});
defineEmits(["approve", "decline", "close", "view-plan-item"]);

const requestedLabel = computed(() => formatInstant(props.requestedAt));
</script>
