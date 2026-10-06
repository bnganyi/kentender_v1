<!-- REQ-DES-11 "Returned reviewed Version" — the exact earlier Version as a
     complete read-only review, with an authorised link to the current copied
     Draft. No edit, route or decision action. -->
<template>
	<div class="kt-panel-lg req-page" data-testid="req-version">
		<div class="req-title-row">
			<h3>{{ view.header.title }}</h3>
			<span class="kt-status" :class="view.header.badge.tone" data-testid="req-badge">{{ view.header.badge.label }}</span>
		</div>
		<div class="kt-label req-reference">{{ view.header.reference }} · Version {{ view.header.version_number }}</div>

		<template v-if="view.decision">
			<div class="kt-meta-row" style="margin-top: var(--kt-space-4)" data-testid="req-version-decision">
				<div><span class="kt-label">Decided by</span><span class="kt-meta-value" style="font-size: 14px">{{ view.decision.by }}</span></div>
				<div><span class="kt-label">Decided at</span><span class="kt-meta-value" style="font-size: 14px">{{ view.decision.at }}</span></div>
				<div v-if="view.decision.affected_section"><span class="kt-label">Affected section</span><span class="kt-meta-value" style="font-size: 14px">{{ view.decision.affected_section }}</span></div>
			</div>
			<div class="kt-meta-row" style="margin-top: 12px"><div><span class="kt-label">Correction reason</span><span class="kt-meta-value" style="font-size: 14px">{{ view.decision.reason }}</span></div></div>
		</template>
		<div v-if="view.current_draft_route" style="margin: 12px 0 var(--kt-space-6)">
			<a :href="view.current_draft_route" style="font-size: 13px" data-testid="req-open-current-draft" @click.stop.prevent="ctx.goPath(view.current_draft_route)">Open current copied Draft</a>
		</div>

		<ReviewSections :sections="view.sections || []" />
		<Disclosure title="Record details" testid="req-record-details">
			<div class="kt-meta-row" style="flex-wrap: wrap">
				<div v-for="fact in view.record_details || []" :key="fact.label"><span class="kt-label">{{ fact.label }}</span><span class="kt-meta-value" style="font-size: 14px">{{ fact.value }}</span></div>
			</div>
		</Disclosure>

		<div class="req-footer">
			<button type="button" class="btn btn-ghost" data-testid="req-back" @click="ctx.go()">Back to Requisitions</button>
			<button v-if="(view.actions || {}).export" type="button" class="btn btn-secondary" :disabled="ctx.pending.value" data-testid="req-export" @click="downloadExport(ctx, view.requisition, view.header.version)">Export</button>
		</div>
	</div>
</template>

<script setup>
import { useReq } from "../data/context.js";
import { downloadExport } from "../data/export.js";
import Disclosure from "./shared/Disclosure.vue";
import ReviewSections from "./shared/ReviewSections.vue";

defineProps({ view: { type: Object, required: true } });
const ctx = useReq();
</script>
