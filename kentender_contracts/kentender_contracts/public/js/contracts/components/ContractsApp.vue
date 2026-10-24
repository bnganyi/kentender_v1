<!-- ContractsApp — the Contract Management screens, one component for both surfaces (CM-CHG-001 v0.8 §9, §10.3): the Desk page /app/contracts and the supplier portal /supplier/contracts.
     The surface hands it where it is in the route (`target`), how to move (`go`) and when the page comes back into view (`epoch`); everything else is the same screens drawn from the same server
     answers. The Desk page ("contracts"): the contracts list (/app/contracts) and one contract (/app/contracts/<contract>/<tab>/<subject...>). The app stays mounted
     across navigations (AGENTS.md §6.1); the route is the only place a screen's identity lives (a reload, Back and Forward and a copied link land on the same screen). One loader with a sequence
     guard (a slower, older answer never overwrites a newer one); a screen already shown refreshes in place and the skeleton is only for a screen with nothing to show yet (§6.4).
     The server decides what a viewer may read and do, and every rule; this screen draws its answer: the list, a contract's board, the stable denial (D-DENIED) or the load failure (D-ERR).
     A refusal comes back as data and is drawn where it belongs: a form value beside its field, any other refusal in a notice, with what the person typed kept. -->
<template>
	<div class="kt-cm-app">
		<div class="kt-shell" data-testid="cm-root" :data-screen="screen" :data-loading="loading ? 'true' : 'false'" :data-refreshing="refreshing ? 'true' : 'false'" :data-busy="busy ? 'true' : 'false'">
			<div class="kt-page" v-if="screen === 'workspace-forbidden' || screen === 'error' || screen === 'contract-forbidden' || screen === 'loading'">
				<AccessDenied
					v-if="screen === 'workspace-forbidden'"
					heading="You do not have access to Contracts"
					:text="['This area needs a contract responsibility, a supplier account or a technical reader role.', 'Ask your KenTender administrator to check your assignment in System setup.']"
				/>
				<StatePage v-else-if="screen === 'contract-forbidden'" tone="lock" message="You do not have access to this contract." :secondary="['Back to contracts']" testid="cm-denied" @secondary="backToContracts" />
				<StatePage v-else-if="screen === 'error'" tone="error" message="This record could not be loaded." primary="Retry" :secondary="['Back to contracts']" :busy="loading" testid="cm-load-error" @primary="load()" @secondary="backToContracts" />
				<div v-else class="kt-skel" data-testid="cm-skeleton" style="width: 100%" aria-busy="true"></div>
			</div>
			<BoardList
				v-else-if="screen === 'workspace'"
				:board="payload.board"
				@filter="onFilter"
				@view="onView"
				@open="openContract"
				@page="onPage"
				@size="onSize"
				@head="goTo(['register'])"
			/>
			<CmBoard
				v-else-if="screen === 'board'"
				ref="boardRef"
				:board="payload.board"
				:busy="busy || refreshing"
				:errors="errors"
				:refusal="refusal"
				@run="run"
				@route="goTo"
				@tab="goTab"
				@back="backToContracts"
			/>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from "vue";
import * as api from "../data/api.js";
import AccessDenied from "../../access_shared/AccessDenied.vue";
import StatePage from "./StatePage.vue";
import BoardList from "./BoardList.vue";
import CmBoard from "./CmBoard.vue";
import { savePageSize, savedPageSize } from "../../pager_shared/pageSize.js";

const props = defineProps({
	target: { type: Object, required: true }, // { contract, tab, subject } read from the route
	epoch: { type: Number, default: 0 }, // ticks when the page comes back into view on the same route
	go: { type: Function, required: true }, // (segments) -> move to a contract screen, [] is the list
});
const emit = defineEmits(["title"]);

const boardRef = ref(null);
const payload = ref(null);
const loading = ref(false);
const busy = ref(false);
const failed = ref(false);
const errors = ref({});
const refusal = ref(null);
let seq = 0; // a slower, older response must never overwrite a newer one (AGENTS.md §6.4)
let pendingKey = ""; // the operation key of a command whose answer never arrived: a retry is the same operation

// The list's own state lives in the root so a visit to a contract and back keeps it (AGENTS.md §6.11).
const view = ref("My work");
const filters = ref({ search: "", status: "", source: "", responsible: "", unit: "" });
const page = ref(1);
const pageSize = ref(savedPageSize("contracts-list"));

const target = computed(() => props.target);
const key = computed(() => `${target.value.contract}|${target.value.tab}|${target.value.subject.join("/")}`);
const screen = computed(() => (failed.value && !payload.value ? "error" : payload.value ? payload.value.screen : "loading"));
const refreshing = computed(() => loading.value && !!payload.value);

async function load() {
	const token = ++seq;
	loading.value = true;
	try {
		const t = target.value;
		const answer = t.contract
			? await api.getBoard({ contract: t.contract, tab: t.tab, subject: t.subject })
			: await api.getWorkspace({ page: page.value, pageSize: pageSize.value, view: view.value, search: filters.value.search, status: filters.value.status, source: filters.value.source, responsible: filters.value.responsible, unit: filters.value.unit });
		if (token !== seq) return;
		if (answer && answer.ok === false) throw new Error(answer.message || "failed");
		payload.value = answer;
		failed.value = false;
	} catch (error) {
		if (token !== seq) return;
		failed.value = true;
	} finally {
		if (token === seq) loading.value = false;
	}
}

// The screen drawn follows the route: a different contract (or the list) starts from nothing, the same contract on another tab refreshes in place.
let lastContract = "\u0000";
watch(
	key,
	() => {
		if (target.value.contract !== lastContract) payload.value = null;
		lastContract = target.value.contract;
		errors.value = {};
		refusal.value = null;
		load();
	},
	{ immediate: true }
);
// The page coming back into view on the same route revalidates what it already shows, quietly.
watch(() => props.epoch, () => load());

function goTo(segments) {
	props.go(segments);
}
function openContract(segments) {
	goTo(segments);
}
function goTab(tab) {
	goTo([target.value.contract, tab.toLowerCase()]);
}
function backToContracts() {
	props.go([]);
}

// The reader's own filter actions reset the page; nothing a load can change does (AGENTS.md §6.11).
function onFilter(next) {
	filters.value = next;
	page.value = 1;
	load();
}
function onView(next) {
	view.value = next;
	page.value = 1;
	load();
}
function onPage(n) {
	page.value = n;
	load();
}
function onSize(n) {
	pageSize.value = n;
	savePageSize("contracts-list", n);
	page.value = 1;
	load();
}

function mintKey() {
	if (pendingKey) return pendingKey;
	pendingKey = globalThis.crypto && crypto.randomUUID ? crypto.randomUUID() : `k-${Date.now()}-${Math.random().toString(16).slice(2)}`;
	return pendingKey;
}

async function send(command, args, values, version) {
	const operationKey = mintKey();
	const answer = await api.runCommand({ command, contract: target.value.contract, expectedVersion: version, key: operationKey, args, values });
	pendingKey = ""; // an answer arrived: the next click is a new operation
	return answer;
}

function fail(answer) {
	if (answer.screen === "contract-forbidden") {
		payload.value = answer;
		return;
	}
	if (answer.code === "CM_INPUT") errors.value = answer.fields || {};
	else refusal.value = answer;
}

// A command is awaited together with the reload of what it changed, inside the busy window, so the revision the next click reads is the one just saved (§6.4).
async function run({ spec, values }) {
	if (busy.value) return;
	busy.value = true;
	errors.value = {};
	refusal.value = null;
	const typed = { ...(boardRef.value ? boardRef.value.form : {}) };
	try {
		let version = payload.value.board.version;
		let answer = await send(spec.command, spec.args || {}, values, version);
		if (answer.ok && spec.then) {
			const args = { ...(spec.then.args || {}) };
			for (const name of spec.then.carry || []) args[name] = answer[name];
			version = answer.record_version ?? version;
			answer = await send(spec.then.command, args, {}, version);
		}
		if (!answer.ok) {
			fail(answer);
			if (answer.code === "CM_CHANGED") {
				await load();
				await nextTick();
				if (boardRef.value) Object.assign(boardRef.value.form, Object.fromEntries(Object.entries(typed).filter(([k]) => k in boardRef.value.form))); // the latest version, with what was typed kept
			}
			return;
		}
		if (answer.open) {  // a contract that did not exist before this command: go to it
			props.go([answer.open, "agreement"]);
			return;
		}
		const leaving = target.value.subject.length > 0; // a form opened from a tab (record delivery, submit invoice) is done once it is saved: back to the tab
		if (leaving) {
			props.go([target.value.contract, (payload.value.board.tab || target.value.tab || "").toLowerCase()]);
			return;
		}
		await load();
		await nextTick();
		if (boardRef.value) boardRef.value.closeDialog();
	} catch (error) {
		refusal.value = { message: "This could not be completed. Check your connection and try again.", reasons: [] };
	} finally {
		busy.value = false;
	}
}

// What the Desk page's rail needs to name the screen: the contract's reference once its board is drawn.
watch(() => payload.value && payload.value.board && payload.value.board.ref, (ref) => emit("title", ref || ""));
</script>
