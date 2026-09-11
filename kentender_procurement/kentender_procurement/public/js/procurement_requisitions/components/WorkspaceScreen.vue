<!-- REQ-DES-01 Requisitions workspace (§13.3), ported class-for-class from
     the artboard: masthead with no eyebrow (only editor screens carry the
     PROCUREMENT REQUISITIONS eyebrow, per §13.1), the headline-plus-button
     "Ready to prepare" card (absent when nothing is eligible, one row per
     eligible Plan Item under a single count headline — never a table), and
     the one connected "Requisitions" list (originally retitled from the
     earlier "My Drafts"/"Tasks"/"Recent Requisitions" split per §13.3's own
     rationale; relabelled again from "Your Requisitions" to drop possessive
     framing for cross-module title consistency — product decision, not a
     §13.3 correction). No Procuring Entity selector, value dashboard or STD
     Library link exists anywhere on this screen. -->
<template>
	<div>
		<div class="req-masthead">
			<div>
				<h1 class="kt-page-title">Procurement Requisitions</h1>
				<p class="kt-page-lede">Prepare precise departmental requests from approved Plan Items.</p>
			</div>
		</div>

		<!-- loading skeleton -->
		<div v-if="loading" class="kt-card kt-blueprint" style="padding: 0; overflow: hidden" data-testid="req-loading">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div v-for="row in 3" :key="row" class="req-skel-row">
				<div class="kt-skel" style="width: 72%"></div>
				<div class="kt-skel" style="width: 52%"></div>
				<div class="kt-skel" style="width: 44%"></div>
			</div>
		</div>

		<!-- load error, with the generated support reference -->
		<div v-else-if="error" class="kt-card kt-blueprint req-state-card" data-testid="req-error">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>Procurement Requisitions could not be loaded.</h3>
			<p>Try again. If the problem continues, quote the support reference shown below.</p>
			<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('reload')">Try again</button>
			<p class="req-support-ref">Support reference: {{ supportRef }}</p>
		</div>

		<!-- the verdict resolved before anything else rendered: no control,
		     no strip, no table (KT-STD-001 §3A). -->
		<div v-else-if="workspace.outcome === 'FORBIDDEN'" class="kt-card kt-blueprint req-state-card" data-testid="req-forbidden">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>{{ forbidden.heading }}</h3>
			<p>{{ forbidden.text }}</p>
		</div>

		<template v-else>
			<!-- REQ-DES-01 "Ready to prepare" card: absent entirely (not shown
			     empty) when nothing is currently eligible. -->
			<div v-if="readyToPrepare" class="kt-card kt-blueprint req-card-pad" data-testid="req-ready-to-prepare">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="req-ready-headline" data-testid="req-ready-headline">{{ readyToPrepare.headline }}</div>
				<div
					v-for="(row, index) in readyToPrepare.rows"
					:key="row.plan_item_id"
					class="req-ready-row"
					data-testid="req-ready-row"
				>
					<div class="req-ready-sub">{{ row.supporting }}</div>
					<button
						type="button"
						class="kt-btn kt-btn-primary"
						:disabled="pending"
						:data-testid="`req-prepare-action-${index}`"
						@click="$emit('navigate', row.route)"
					>
						Prepare Requisition
					</button>
				</div>
			</div>

			<!-- REQ-DES-01 "Requisitions" — one connected list. -->
			<h2 class="req-section-title">Requisitions</h2>
			<table class="kt-table" data-testid="req-your-requisitions">
				<thead>
					<tr>
						<th>Requisition</th>
						<th>Plan Item</th>
						<th>Status</th>
						<th>Action</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in workspace.requisitions" :key="row.requisition">
						<td>{{ row.requisition_reference }}</td>
						<td>{{ row.plan_item_title }}</td>
						<td><span class="kt-status" :class="statusClass(row.status_kind)">{{ row.status }}</span></td>
						<td>
							<a v-if="row.action_label" href="#" @click.prevent="$emit('navigate', row.route)">{{ row.action_label }}</a>
						</td>
					</tr>
				</tbody>
			</table>
			<div class="req-table-caption" data-testid="req-count-label">{{ workspace.count_label }}</div>
		</template>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	loading: Boolean,
	error: String,
	supportRef: String,
	workspace: { type: Object, default: () => ({}) },
	pending: Boolean,
});

defineEmits(["reload", "navigate"]);

const forbidden = computed(() => props.workspace.forbidden || {});
const readyToPrepare = computed(() => props.workspace.ready_to_prepare || null);

const KIND_CLASS = { live: "is-live", attention: "is-attention", critical: "is-critical", draft: "is-draft" };

function statusClass(kind) {
	// the server already returns the exact "is-*" suffix (see read.py's
	// _STATE_STATUS table) — KIND_CLASS covers the plain-word form too, in
	// case a future caller passes one instead.
	if (!kind) return "is-draft";
	return kind.startsWith("is-") ? kind : KIND_CLASS[kind] || "is-draft";
}
</script>
