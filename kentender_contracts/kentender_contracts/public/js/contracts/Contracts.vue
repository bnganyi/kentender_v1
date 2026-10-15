<!-- Contracts — the Desk Page "contracts" (CM-CHG-001 v0.8 §9.0, §10.3): the contracts list at /app/contracts and one contract at /app/contracts/<contract>/<tab>/<subject...>. It owns what is
     Desk's: the route (a contract is a path segment, so a reload, Back and Forward and a copied link land on the same screen), the shared page rail and the app staying mounted across
     navigations (AGENTS.md §6.1). The screens themselves are `ContractsApp`, shared with the supplier portal. -->
<template>
	<div class="kt-industry kt-cm">
		<div ref="railEl" class="kt-rail-mount"></div>
		<ContractsApp :target="target" :epoch="epoch" :go="go" @title="reference = $event" />
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { parseRoute, useRouteState } from "./composables/useRouteState.js";
import { usePageRail } from "./composables/usePageRail.js";
import ContractsApp from "./components/ContractsApp.vue";

const PAGE = "contracts";
const { route, epoch } = useRouteState(PAGE);
const railEl = ref(null);
const reference = ref("");

const target = computed(() => parseRoute(route.value, PAGE));
const go = (segments) => frappe.set_route(PAGE, ...segments);

const railTrail = computed(() => {
	const trail = [{ label: __("Home"), route: ["home"] }, { label: __("Contracts"), route: target.value.contract ? [PAGE] : undefined }];
	if (target.value.contract) trail.push({ label: reference.value || target.value.contract });
	return trail;
});
usePageRail(railEl, railTrail, { showPeSwitcher: false });
</script>
