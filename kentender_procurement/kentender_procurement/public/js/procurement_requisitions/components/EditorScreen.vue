<!-- The Draft editor (REQ-DES-03 / 05 / 06): one route, three visible tasks
     over the five internal validation groups (§6.1). The server decides the
     task statuses, the blockers and what this actor may change; the selected
     task is this page's own navigation state. -->
<template>
	<div class="kt-panel-lg req-page" data-testid="req-editor" :data-mode="view.mode">
		<div class="req-title-row">
			<h3>{{ header.title }}</h3>
			<span class="kt-status" :class="header.badge.tone" data-testid="req-badge">{{ header.badge.label }}</span>
		</div>
		<div class="req-reference"><span class="kt-label">{{ header.reference }}</span></div>
		<p class="kt-muted req-lede">{{ header.description }}</p>

		<ProgressRow :tasks="view.tasks" :selected="selected" @select="select" />

		<div v-if="view.returned" class="req-section" data-testid="req-returned">
			<div class="req-actions" style="margin-bottom: var(--kt-space-4)"><span class="kt-status is-attention">Correction requested</span></div>
			<Notice tone="warning">
				<strong>{{ view.returned.reason }}</strong><br />
				Returned by {{ view.returned.returned_by }} · {{ view.returned.returned_at }}<template v-if="view.returned.affected_section">
					· <a href="#" data-testid="req-go-affected" @click.stop.prevent="goAffected">Go to affected section</a> ({{ view.returned.affected_section }})</template>
			</Notice>
			<template v-if="view.returned.new_lead">
				<p style="font-size: 14px; margin: var(--kt-space-4) 0 0" data-testid="req-new-lead">This requisition was returned for certification by the new submitting department.</p>
				<div class="kt-meta-row" style="margin-top: var(--kt-space-4)">
					<div><span class="kt-label">Earlier certified department</span><span class="kt-meta-value" style="font-size: 14px">{{ view.returned.earlier_lead }}</span></div>
					<div><span class="kt-label">New submitting department</span><span class="kt-meta-value" style="font-size: 14px">{{ view.returned.new_lead }}</span></div>
				</div>
			</template>
			<p class="kt-muted" style="font-size: 13px; margin: 12px 0 0">
				Earlier decision evidence is preserved in the <a :href="view.returned.earlier_version_route" data-testid="req-earlier-version" @click.stop.prevent="ctx.goPath(view.returned.earlier_version_route)">returned Version</a>.
			</p>
		</div>

		<template v-if="stale">
			<Notice tone="warning">This requisition changed after you opened it. Review the latest version before saving.</Notice>
			<div class="req-actions" style="margin: var(--kt-space-4) 0 var(--kt-space-6)">
				<button type="button" class="kt-btn kt-btn-primary" data-testid="req-review-latest" @click="reviewLatest">Review latest version</button>
			</div>
		</template>

		<RequestDetailsTask v-if="selected === 'request_details'" ref="taskRef" :view="view" :locked="stale" :focus-section="focusSection" @continue="select('requirements')" />
		<RequirementsTask v-else-if="selected === 'requirements'" ref="taskRef" :view="view" :locked="stale" :focus-section="focusSection" @continue="select('review_submit')" @back="select('request_details')" />
		<ReviewTask v-else :view="view" @select="select" />
	</div>
</template>

<script setup>
import { computed, nextTick, ref } from "vue";
import { useReq } from "../data/context.js";
import Notice from "./shared/Notice.vue";
import ProgressRow from "./shared/ProgressRow.vue";
import RequestDetailsTask from "./RequestDetailsTask.vue";
import RequirementsTask from "./RequirementsTask.vue";
import ReviewTask from "./ReviewTask.vue";

const props = defineProps({ view: { type: Object, required: true } });
const ctx = useReq();
const header = computed(() => props.view.header || { badge: {} });
const taskRef = ref(null);

// A returned Draft opens at the governed affected section; otherwise at the
// first task that is not complete (§13.4 Returned variant).
function initialTask() {
	if (props.view.returned && props.view.returned.task) return props.view.returned.task;
	const pending = (props.view.tasks || []).find((t) => t.key !== "review_submit" && t.status !== "Complete");
	return pending ? pending.key : "review_submit";
}
// The chosen task survives a reload and back/forward (AGENTS.md §6.4); it is
// this viewer's navigation only, so session storage is enough.
const TASK_KEY = `kt-req-task:${props.view.header.requisition}`;
function rememberedTask() {
	try {
		const saved = window.sessionStorage.getItem(TASK_KEY);
		return (props.view.tasks || []).some((t) => t.key === saved) ? saved : "";
	} catch (e) {
		return "";
	}
}
function remember(key) {
	try {
		window.sessionStorage.setItem(TASK_KEY, key);
	} catch (e) {
		/* storage unavailable: the task still switches for this view */
	}
}
const selected = ref(rememberedTask() || initialTask());
remember(selected.value);
const focusSection = ref(props.view.returned ? props.view.returned.section : "");

function select(key) {
	selected.value = key;
	remember(key);
	focusSection.value = "";
	nextTick(() => window.scrollTo({ top: 0 }));
}

function goAffected() {
	selected.value = props.view.returned.task;
	remember(selected.value);
	focusSection.value = props.view.returned.section;
	nextTick(() => {
		const el = document.querySelector(`[data-section="${props.view.returned.section}"]`);
		if (el) {
			el.scrollIntoView({ block: "start" });
			el.focus({ preventScroll: true });
		}
	});
}

const stale = computed(() => !!(ctx.commandError.value && ctx.commandError.value.code === "REQ_STALE_VERSION"));
async function reviewLatest() {
	ctx.clearError();
	await ctx.reload();
	if (taskRef.value && taskRef.value.resetFromServer) taskRef.value.resetFromServer();
}
</script>
