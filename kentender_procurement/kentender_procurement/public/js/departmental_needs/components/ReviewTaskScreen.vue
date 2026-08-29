<!-- NDS-UI-05 review task (§12.5) — NDS-DES-06. Renders the exact immutable
     submitted version identified by the task, then the decision area. -->
<template>
	<div style="padding-bottom: 24px">
		<div style="margin-bottom: 20px">
			<div class="kt-page-kicker" style="letter-spacing: 0.06em">{{ kicker }}</div>
			<div style="display: flex; align-items: center; gap: 12px; margin-top: 4px">
				<h1 class="kt-record-title">{{ version.title }}</h1>
				<StatusPill :label="version.version_status || 'Submitted'" />
			</div>
		</div>

		<div v-if="errorSummary" class="kt-error-summary" role="alert" tabindex="-1">
			{{ errorSummary }}
		</div>

		<ContextCard :items="contextItems" />
		<RequirementCard :version="version" />

		<div class="kt-card kt-blueprint" style="padding: 20px 24px">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title" style="margin-bottom: 8px">Departmental decision</div>
			<p style="margin: 0; font-size: 15px">
				Should this requirement be made available to Procurement Planning?
			</p>
			<!-- §12.5 / NDS-BR-006 — the maker never sees a usable decision. -->
			<p
				v-if="makerCheckerBlocked"
				style="margin: 12px 0 0; font-size: 14.5px; color: var(--color-neutral-700)"
			>
				You submitted this version, so it must be decided by another Head of User
				Department.
			</p>
		</div>

		<div v-if="!makerCheckerBlocked && permitted.length" class="kt-page-footer">
			<button
				class="kt-btn kt-btn-secondary"
				:disabled="pending"
				@click="$emit('return')"
			>
				Return for correction
			</button>
			<div style="display: flex; gap: 12px">
				<button class="kt-btn-destructive" :disabled="pending" @click="$emit('decline')">
					Do not take forward
				</button>
				<button class="kt-btn kt-btn-primary" :disabled="pending" @click="$emit('accept')">
					{{ acceptLabel }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import ContextCard from "./ContextCard.vue";
import RequirementCard from "./RequirementCard.vue";
import StatusPill from "./StatusPill.vue";
import { formatInstant, versionKicker } from "../data/format.js";

const props = defineProps({
	need: { type: Object, default: () => ({}) },
	version: { type: Object, default: () => ({}) },
	scope: { type: Object, default: () => ({}) },
	requesterLabel: { type: String, default: "" },
	openedAt: { type: String, default: "" },
	taskType: { type: String, default: "Initial acceptance" },
	permitted: { type: Array, default: () => [] },
	makerCheckerBlocked: Boolean,
	errorSummary: { type: String, default: "" },
	pending: Boolean,
});
defineEmits(["return", "accept", "decline"]);

const isSuccessor = computed(() => props.taskType === "Successor acceptance");

const kicker = computed(() =>
	versionKicker(
		props.need.need_reference,
		props.version,
		isSuccessor.value ? "ACCEPTED NEED UPDATE" : "DEPARTMENTAL REVIEW"
	)
);

const acceptLabel = computed(() =>
	isSuccessor.value ? "Accept update" : "Accept for planning"
);

const contextItems = computed(() => [
	{ label: "Submitted by", value: props.requesterLabel },
	{ label: "Submitted", value: formatInstant(props.openedAt) },
	{ label: "Department", value: props.scope.organisation_unit || "" },
	{ label: "Financial Year", value: props.scope.financial_year || "" },
]);
</script>
