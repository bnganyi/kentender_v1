<script setup>
import { ref, watch, onMounted, onUnmounted } from "vue";
import ConfirmActionDialog from "./ConfirmActionDialog.vue";
import StatusTag from "./StatusTag.vue";

const props = defineProps({
	code: { type: String, required: true },
});
const emit = defineEmits(["close", "after-action"]);

const METHOD = "kentender_strategy.api.strategy_api.get_plan_readiness_api";
const TRANSITION_METHOD = "kentender_strategy.api.strategy_api.transition_plan";
const POLL_MS = 15000;
const REASON_ACTIONS = new Set(["Return for correction"]);

const loading = ref(true);
const error = ref(null);
const readiness = ref(null); // { plan, status, ready, issues, grouped, allowed_actions, ... }
const dialogOpen = ref(false);
const pendingAction = ref(null);
const submitting = ref(false);

async function load() {
	loading.value = true;
	error.value = null;
	try {
		const response = await frappe.call({ method: METHOD, args: { plan_code: props.code }, freeze: false });
		readiness.value = response.message;
	} catch (err) {
		error.value = err;
	} finally {
		loading.value = false;
	}
}

function openConfirm(action) {
	pendingAction.value = action;
	dialogOpen.value = true;
}

function cancelConfirm() {
	dialogOpen.value = false;
	pendingAction.value = null;
}

async function confirmAction(reason) {
	const action = pendingAction.value;
	const planVersion = readiness.value?.plan?.id;
	submitting.value = true;
	try {
		await frappe.call({
			method: TRANSITION_METHOD,
			args: { plan_version: planVersion, action, reason },
			freeze: false,
		});
		dialogOpen.value = false;
		pendingAction.value = null;
		frappe.show_alert({ message: `${action} succeeded`, indicator: "green" });
		// Authoritative refresh — never mutate status/allowed_actions locally.
		await load();
		emit("after-action");
	} catch (err) {
		dialogOpen.value = false;
		pendingAction.value = null;
		frappe.show_alert({
			message: err?.message || `${action} failed`,
			indicator: "red",
		});
	} finally {
		submitting.value = false;
	}
}

watch(() => props.code, load, { immediate: true });

let pollId = null;
onMounted(() => {
	pollId = window.setInterval(load, POLL_MS);
});
onUnmounted(() => {
	window.clearInterval(pollId);
});
</script>

<template>
	<div class="kt-pp-drawer-backdrop" @click.self="$emit('close')">
		<aside class="kt-pp-drawer" data-testid="kt-pp-drawer">
			<div class="kt-pp-drawer__header">
				<div>
					<div class="kt-pp-drawer__code">{{ code }}</div>
					<h2 v-if="readiness">{{ readiness.plan.name }}</h2>
				</div>
				<button type="button" class="kt-pp-dialog__close" aria-label="Close" @click="$emit('close')">
					×
				</button>
			</div>

			<div v-if="loading && !readiness" class="kt-pp-drawer__loading">Loading plan…</div>

			<div v-else-if="error" class="kt-pp-drawer__error">
				<p>
					{{
						error.exc_type === "PermissionError"
							? "You don't have access to this plan."
							: "Couldn't load this plan. Try again."
					}}
				</p>
				<button type="button" class="kt-pp-btn kt-pp-btn--secondary" @click="load">Retry</button>
			</div>

			<div v-else-if="readiness" class="kt-pp-drawer__body">
				<div class="kt-pp-drawer__status">
					<StatusTag :status="readiness.status" tone="outline" />
					<span v-if="readiness.blocker_count" class="kt-pp-drawer__blockers">
						{{ readiness.blocker_count }} blocker(s)
					</span>
				</div>

				<ul v-if="readiness.issues && readiness.issues.length" class="kt-pp-drawer__issues">
					<li v-for="issue in readiness.issues" :key="issue.title">{{ issue.description }}</li>
				</ul>

				<div class="kt-pp-drawer__actions">
					<template v-if="readiness.allowed_actions && readiness.allowed_actions.length">
						<button
							v-for="action in readiness.allowed_actions"
							:key="action"
							type="button"
							class="kt-pp-btn kt-pp-btn--primary"
							data-testid="kt-pp-drawer-action"
							:disabled="submitting"
							@click="openConfirm(action)"
						>
							{{ action }}
						</button>
					</template>
					<p v-else class="kt-pp-drawer__no-actions">
						No actions available to you for this plan in its current state.
					</p>
				</div>
			</div>

			<ConfirmActionDialog
				:open="dialogOpen"
				:action="pendingAction || ''"
				:needs-reason="REASON_ACTIONS.has(pendingAction)"
				@confirm="confirmAction"
				@cancel="cancelConfirm"
			/>
		</aside>
	</div>
</template>

<style scoped>
.kt-pp-drawer-backdrop {
	position: fixed;
	inset: 0;
	z-index: 1000;
	display: flex;
	justify-content: flex-end;
	background: color-mix(in srgb, #2b2b2d 35%, transparent);
}
.kt-pp-drawer {
	width: min(420px, 100vw);
	height: 100%;
	background: var(--ktpp-color-bg);
	border-left: 1px solid var(--ktpp-color-divider);
	box-shadow: var(--ktpp-shadow-sm);
	padding: var(--ktpp-space-4);
	overflow-y: auto;
	display: flex;
	flex-direction: column;
	gap: var(--ktpp-space-3);
}
.kt-pp-drawer__header {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	gap: var(--ktpp-space-2);
}
.kt-pp-drawer__code {
	font-family: var(--ktpp-font-heading);
	font-size: 12px;
	letter-spacing: 0.08em;
	color: var(--ktpp-color-accent-700);
}
.kt-pp-drawer__header h2 {
	font-size: 19px;
}
.kt-pp-dialog__close {
	background: none;
	border: 0;
	font-size: 20px;
	line-height: 1;
	cursor: pointer;
	color: var(--ktpp-color-text);
}
.kt-pp-drawer__loading,
.kt-pp-drawer__error {
	padding: 24px 0;
	text-align: center;
	font-size: 14px;
}
.kt-pp-drawer__status {
	display: flex;
	align-items: center;
	gap: 10px;
}
.kt-pp-drawer__blockers {
	font-size: 12px;
	color: #b3261e;
}
.kt-pp-drawer__issues {
	margin: 0;
	padding-left: 18px;
	font-size: 13px;
	color: color-mix(in srgb, var(--ktpp-color-text) 80%, transparent);
}
.kt-pp-drawer__actions {
	display: flex;
	flex-wrap: wrap;
	gap: 8px;
	margin-top: 6px;
}
.kt-pp-drawer__no-actions {
	font-size: 13px;
	color: color-mix(in srgb, var(--ktpp-color-text) 60%, transparent);
}
.kt-pp-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	font-family: var(--ktpp-font-heading);
	font-weight: var(--ktpp-font-heading-weight);
	font-size: 14px;
	padding: 7px 14px;
	border-radius: var(--ktpp-radius-md);
	border: 1px solid transparent;
}
.kt-pp-btn:disabled {
	opacity: 0.45;
	cursor: not-allowed;
}
.kt-pp-btn--secondary {
	border-color: var(--ktpp-color-divider);
	background: transparent;
	color: var(--ktpp-color-text);
}
.kt-pp-btn--primary {
	background: var(--ktpp-color-accent);
	color: var(--ktpp-color-bg);
	border-color: var(--ktpp-color-accent);
}
.kt-pp-btn--primary:hover:not(:disabled) {
	background: var(--ktpp-color-accent-600);
}
</style>
