import { computed, reactive, ref } from "vue";
import { homeApi } from "../data/homeApi.js";

// HOME-CHG-001 v0.6 §5.1, §8, §10B.1. Everything the page says is made by the server:
// counts, labels, relative times, order, paging and the "Show n more" number. This
// module keeps the page's state (what is loaded, what is retrying) and applies the
// composition rules that are about *placement*, not content (which regions show, where).

export const REGION_IDS = {
	my_work: "my-work",
	coming_up: "coming-up",
	waiting: "waiting",
	oversight: "oversee",
	completed: "completed",
};

const COUNTED = ["my_work", "waiting", "oversight"];
const MAIN = ["my_work", "coming_up"];
const RAIL = ["waiting", "oversight", "completed"];

function heading(region) {
	return {
		my_work: __("My work"),
		coming_up: __("Coming up"),
		waiting: __("Waiting on others"),
		oversight: __("Records you oversee"),
		completed: __("Recently completed actions"),
	}[region];
}
export { heading as regionHeading };

function isFailed(region, failed) {
	return !!region && (region.coverage === "partial" || region.coverage === "unavailable" || !!failed[region.name]);
}

/**
 * Where each region goes. A region with no entries after a successful read is omitted;
 * a failed one stays, to show its own message and Try again (§5.1 item 7, §8).
 * - Both main regions empty: "Nothing needs your action right now." leads the main
 *   column, and Records you oversee moves from the rail into it (§5.1 item 8, §10B.1 item 5).
 * - No rail regions left: the main column spans all 12 columns (§10B.1 item 4A).
 */
export function layoutOf(data, failed = {}) {
	const regions = {};
	for (const [name, region] of Object.entries(data.regions || {})) regions[name] = { ...region, name };
	const showable = (name) => {
		const region = regions[name];
		return !!region && (region.entries.length > 0 || isFailed(region, failed));
	};
	const viewer = data.viewer || {};

	if (data.empty) {
		return { panel: viewer.technical ? "technical" : "empty", columns: [], main: [], rail: [], mainEmpty: false, railEmpty: true };
	}

	const columns = data.summary_visible
		? COUNTED.filter((name) => regions[name] && regions[name].applicable).map((name) => ({
				region: name,
				anchor: REGION_IDS[name],
				heading: heading(name),
				accent: name === "my_work",
				figure: regions[name].count,
				unavailable: regions[name].count === null || regions[name].count === undefined,
				label: regions[name].label,
		  }))
		: [];

	const main = MAIN.filter(showable);
	let rail = RAIL.filter(showable);
	const mainEmpty = main.length === 0;
	if (mainEmpty && rail.includes("oversight")) {
		main.push("oversight");
		rail = rail.filter((name) => name !== "oversight");
	}
	return { panel: "", columns, main, rail, mainEmpty, railEmpty: rail.length === 0 };
}

export function useHomeWorkspace(api = homeApi) {
	const phase = ref("loading"); // loading | ready | denied | failed
	const data = ref(null);
	const busy = reactive({});
	const failed = reactive({}); // a region whose retry could not be read
	const moreFailed = reactive({}); // a region whose Show more could not be read
	const focusKey = ref("");
	const announcement = ref("");
	let token = 0;

	function clear(map) {
		for (const key of Object.keys(map)) delete map[key];
	}

	// Every loader carries a sequence token (AGENTS.md §6.4): a slow earlier read can never
	// overwrite a later one. `quiet` revalidates in place and keeps what is shown (a skeleton
	// only when there is nothing to show yet).
	async function load({ quiet = false } = {}) {
		const mine = ++token;
		if (!quiet || !data.value) phase.value = "loading";
		try {
			const response = await api.load();
			if (mine !== token) return false;
			if (!response || response.state === "denied") {
				data.value = null;
				phase.value = "denied";
				return true;
			}
			if (response.state === "failed") {
				data.value = null;
				phase.value = "failed";
				return true;
			}
			data.value = response;
			phase.value = "ready";
			clear(failed);
			clear(moreFailed);
			return true;
		} catch (error) {
			if (mine !== token) return false;
			if (quiet && data.value) return false;
			data.value = null;
			phase.value = "failed";
			return false;
		}
	}

	// Try again on one region: read everything quietly (counts, the empty rules and the
	// rail all depend on the whole read) and keep the page as it is meanwhile.
	async function retry(region) {
		busy[region] = true;
		failed[region] = false;
		try {
			const ok = await load({ quiet: true });
			if (!ok && phase.value === "ready") failed[region] = true;
		} finally {
			busy[region] = false;
		}
	}

	// Show more: append the next cursor's rows in place, leave the count alone, and put
	// focus on the first appended row (§5.1 item 5, HOME-AC-12).
	async function showMore(region) {
		const current = data.value && data.value.regions && data.value.regions[region];
		if (!current || !current.next_cursor || busy[region]) return;
		const snapshot = data.value;
		busy[region] = true;
		moreFailed[region] = false;
		try {
			const response = await api.load([region], { [region]: current.next_cursor });
			if (data.value !== snapshot) return; // a fuller read replaced this data meanwhile
			const next = response && response.regions && response.regions[region];
			if (!next) throw new Error("no region in the response");
			current.entries.push(...next.entries);
			Object.assign(current, {
				coverage: next.coverage,
				shown: next.shown,
				remaining: next.remaining,
				next_cursor: next.next_cursor,
				next_count: next.next_count,
				total: next.total,
			});
			focusKey.value = next.entries.length ? next.entries[0].key : "";
			announcement.value = current.total === null || current.total === undefined
				? __("Showing {0}", [current.shown])
				: __("Showing {0} of {1}", [current.shown, current.total]);
		} catch (error) {
			if (data.value === snapshot) moreFailed[region] = true;
		} finally {
			busy[region] = false;
		}
	}

	const layout = computed(() => (data.value ? layoutOf(data.value, failed) : null));
	return { phase, data, busy, failed, moreFailed, focusKey, announcement, layout, load, retry, showMore };
}
