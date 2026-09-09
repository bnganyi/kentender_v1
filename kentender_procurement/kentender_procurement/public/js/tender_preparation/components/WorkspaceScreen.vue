<!-- TPR-DES-01 Tender Preparation workspace (§13.3), ported class-for-class
     from the artboard: title + subtitle, "Ready to prepare" table with the
     Prepare Tender action, "My Tenders" table, and "Approval tasks" (the
     table only for the Head of Procurement Function; the artboard's own
     note for everyone else). No value dashboard, STD Library link, Procuring
     Entity selector or create-without-Requisition action. -->
<template>
	<div>
		<div class="tpr-masthead">
			<h1 class="kt-page-title">Tender Preparation</h1>
			<p class="kt-page-lede">Prepare Tenders from authorised Procurement Requisitions.</p>
		</div>
		<StateCard :loading="loading" :error="error" :support-ref="supportRef" :forbidden="forbidden" prefix="tpr" @reload="$emit('reload')" />
		<template v-if="!loading && !error && !forbidden">
			<div class="tpr-section" data-testid="tpr-ready-to-prepare">
				<div class="kt-card-title">Ready to prepare</div>
				<table v-if="ready.length" class="kt-table">
					<thead><tr><th>Requisition</th><th>Method</th><th>Items</th><th>Required by</th><th></th></tr></thead>
					<tbody>
						<tr v-for="(row, index) in ready" :key="row.handoff" data-testid="tpr-ready-row">
							<td>{{ row.requisition_reference }}</td>
							<td>{{ row.planned_method }}</td>
							<td class="tpr-num">{{ row.item_count }}</td>
							<td>{{ row.latest_delivery_date_label }}</td>
							<td class="tpr-table-action">
								<button v-if="row.can_prepare" type="button" class="kt-btn kt-btn-primary" :disabled="pending" :data-testid="`tpr-prepare-action-${index}`" @click="$emit('navigate', ['tender-preparation', 'new', row.handoff])">Prepare Tender</button>
							</td>
						</tr>
					</tbody>
				</table>
				<p v-else class="tpr-muted" data-testid="tpr-no-eligible">No authorised Requisitions are ready for Tender Preparation.</p>
			</div>

			<div class="tpr-section" data-testid="tpr-my-tenders">
				<div class="kt-card-title">My Tenders</div>
				<table class="kt-table">
					<thead><tr><th>Tender</th><th>Requisition</th><th>Version</th><th>Status</th></tr></thead>
					<tbody>
						<tr v-for="row in tenders" :key="row.tender" data-testid="tpr-tender-row">
							<td><a href="#" @click.prevent="$emit('navigate', row.route)">{{ row.tender_reference }}</a></td>
							<td>{{ row.requisition_reference }}</td>
							<td class="tpr-num">{{ row.version_number }}</td>
							<td><span class="kt-status" :class="statusClass(row.current_state)">{{ row.state_label }}</span></td>
						</tr>
						<tr v-if="!tenders.length"><td colspan="4" class="tpr-muted">No Tenders yet.</td></tr>
					</tbody>
				</table>
			</div>

			<div class="tpr-section" data-testid="tpr-approval-tasks">
				<div class="kt-card-title">Approval tasks</div>
				<table v-if="workspace.show_approval_tasks" class="kt-table">
					<thead><tr><th>Tender</th><th>Requisition</th><th>Received</th><th></th></tr></thead>
					<tbody>
						<tr v-for="row in approvalTasks" :key="row.task" data-testid="tpr-approval-task-row">
							<td>{{ row.tender_reference }}</td>
							<td>{{ row.requisition_reference }}</td>
							<td>{{ row.received_at }}</td>
							<td class="tpr-table-action"><button type="button" class="kt-btn kt-btn-primary" @click="$emit('navigate', row.route)">Open approval task</button></td>
						</tr>
						<tr v-if="!approvalTasks.length"><td colspan="4" class="tpr-muted">No Tenders are awaiting your approval.</td></tr>
					</tbody>
				</table>
				<p v-else class="tpr-muted">Visible only to the Head of Procurement Function.</p>
			</div>
		</template>
	</div>
</template>

<script setup>
import { computed } from "vue";
import StateCard from "./StateCard.vue";

const props = defineProps({ loading: Boolean, error: String, supportRef: String, workspace: { type: Object, default: () => ({}) }, pending: Boolean });
defineEmits(["reload", "navigate"]);

const forbidden = computed(() => (props.workspace.outcome === "FORBIDDEN" ? props.workspace.forbidden : null));
const ready = computed(() => props.workspace.ready_to_prepare || []);
const tenders = computed(() => props.workspace.tenders || []);
const approvalTasks = computed(() => props.workspace.approval_tasks || []);

const STATE_CLASS = { Draft: "is-draft", "Submitted for approval": "is-pending", "Approved for publication": "is-live", "Upstream correction required": "is-attention" };
function statusClass(state) {
	return STATE_CLASS[state] || "is-draft";
}
</script>
