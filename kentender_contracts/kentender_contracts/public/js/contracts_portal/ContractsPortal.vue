<!-- ContractsPortal — the supplier's Contract Management screens at /supplier/contracts (CM-CHG-001 v0.8 section 9): the same `ContractsApp` the Desk page hosts, fed by the portal's route and transport. The
     supplier sees what the server projects for a supplier (their own side of the agreement, deliveries, invoices and obligations) and acts only through the commands it offers them. The app stays
     mounted while the supplier moves between the list, a contract and its tabs (AGENTS.md section 6.1). -->
<template>
	<ContractsApp :target="target" :epoch="epoch" :go="go" />
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import ContractsApp from "../contracts/components/ContractsApp.vue";

const props = defineProps({ initial: { type: Object, default: () => ({}) }, portal: { type: Object, required: true } });
const { route, go: goPath, epoch } = props.portal.useRoute({ ref, onMounted, onUnmounted });

const BASE = "/supplier/contracts";
// /supplier/contracts/<contract>/<tab>/<subject...>
const target = computed(() => {
	const rest = route.value.segments.slice(2).map((s) => decodeURIComponent(s));
	return { contract: rest[0] || "", tab: rest[1] || "", subject: rest.slice(2) };
});
const go = (segments) => goPath([BASE, ...segments.map((s) => encodeURIComponent(s))].join("/"));
</script>
