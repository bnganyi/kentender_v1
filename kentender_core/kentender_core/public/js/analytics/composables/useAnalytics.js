import { reactive, ref } from "vue";
import { analyticsApi } from "../data/analyticsApi.js";

// ANL-CHG-001 v0.8 §7, §8, §9.1, §11. Everything the page says is made by the server: counts, percentages,
// labels, bands, dates, amounts, order and paging. This module keeps the page's state (what is loaded, what
// is retrying, the search text and the paging cursor, which never enter the URL) and nothing else.

/** Region ids a Try again can re-read: a strip column, the coverage region, the funding region, an area tab. */
export const regionId = {
	strip: (areaKey) => "strip:" + areaKey,
	coverage: "coverage",
	funding: "funding",
	area: "area",
};

function slice(payload, region) {
	if (!payload) return null;
	if (region === regionId.coverage) return payload.overview ? payload.overview.coverage : null;
	if (region === regionId.funding) return payload.overview ? payload.overview.funding : null;
	if (region === regionId.area) return payload.area || null;
	if (region.startsWith("strip:")) {
		const key = region.slice("strip:".length);
		return payload.overview ? (payload.overview.strip.columns || []).find((column) => column.key === key) || null : null;
	}
	return null;
}

// Put one freshly read region into the payload that is on screen; every other region keeps its own
// object, so it keeps its values (ANL §11 "Try again in one region").
function mergeRegion(current, fresh, region) {
	if (region === regionId.coverage) {
		current.overview.coverage = fresh.overview.coverage;
		// The Annual planning column's "Coverage unavailable" depends on the same read.
		const index = current.overview.strip.columns.findIndex((column) => column.key === "annual_planning");
		const column = slice(fresh, regionId.strip("annual_planning"));
		if (index >= 0 && column) current.overview.strip.columns[index] = column;
	} else if (region === regionId.funding) {
		current.overview.funding = fresh.overview.funding;
	} else if (region === regionId.area) {
		current.area = fresh.area;
	} else if (region.startsWith("strip:")) {
		const key = region.slice("strip:".length);
		const index = current.overview.strip.columns.findIndex((column) => column.key === key);
		const column = slice(fresh, region);
		if (index >= 0 && column) current.overview.strip.columns[index] = column;
	}
	// The definitions end with which area reads were unavailable; they follow the latest read.
	if (fresh.definitions) current.definitions = fresh.definitions;
}

export function useAnalytics({ getUrl, api = analyticsApi } = {}) {
	const phase = ref("loading"); // loading | ready | failed (the call itself failed)
	const data = ref(null);
	const loadedKey = ref("");
	const refreshing = ref(false);
	const busy = reactive({});
	const retryFailed = reactive({});
	const search = ref(""); // applied search text: component state, never in the URL
	const cursor = ref(null); // the cursor of the page of rows shown
	const cursorStack = ref([]); // cursors of the pages before this one, for Previous
	const guard = kentender_core.desk_page.createSequenceGuard();
	const cache = kentender_core.desk_page.createScreenCache();

	const identity = (url) => [url.tab, url.fy, url.dept, url.state, search.value, cursor.value || ""].join("|");
	const args = (url) => ({ tab: url.tab, fy: url.fy, dept: url.dept, state: url.state, search: search.value, cursor: cursor.value });

	function clear(map) {
		for (const key of Object.keys(map)) delete map[key];
	}

	// Read the route's tab and filters. A screen already loaded in this session renders its last payload at
	// once and refreshes in place (`refreshing`); a skeleton shows only when there is nothing to show yet
	// (AGENTS.md §6.4). Every loader carries a sequence token so a slower, older read never lands.
	async function load() {
		const url = getUrl();
		const key = identity(url);
		const mine = guard.next();
		const cached = cache.get(key);
		if (cached) {
			data.value = cached;
			loadedKey.value = key;
			phase.value = "ready";
			refreshing.value = true;
		} else if (data.value && phase.value === "ready" && data.value.tab === url.tab) {
			refreshing.value = true; // same tab, other filter, search or page: keep what is shown while it reads
		} else {
			data.value = null;
			phase.value = "loading";
			refreshing.value = false;
		}
		try {
			const response = await api.load(args(url));
			if (!guard.isCurrent(mine)) return false;
			if (!response || typeof response !== "object") throw new Error("no payload");
			data.value = response;
			loadedKey.value = key;
			phase.value = "ready";
			clear(retryFailed);
			if (response.verdict === "ok") cache.set(key, response);
			else cache.remove(key);
			return true;
		} catch (error) {
			if (!guard.isCurrent(mine)) return false;
			// A failed read never leaves stale facts labelled current (ANL §11 "Refresh / Try again").
			data.value = null;
			phase.value = "failed";
			cache.remove(key);
			return false;
		} finally {
			if (guard.isCurrent(mine)) refreshing.value = false;
		}
	}

	// Try again on one region: re-read the tab and put only that region's slice into what is shown.
	async function retry(region) {
		const url = getUrl();
		const key = identity(url);
		const mine = guard.next();
		busy[region] = true;
		retryFailed[region] = false;
		try {
			const response = await api.load(args(url));
			if (!guard.isCurrent(mine)) return false;
			if (!response || typeof response !== "object") throw new Error("no payload");
			if (data.value && loadedKey.value === key && response.verdict === "ok" && slice(response, region)) {
				mergeRegion(data.value, response, region);
				cache.set(key, data.value);
			} else {
				data.value = response;
				loadedKey.value = key;
				phase.value = "ready";
				if (response.verdict === "ok") cache.set(key, response);
			}
			return true;
		} catch (error) {
			if (guard.isCurrent(mine)) retryFailed[region] = true;
			return false;
		} finally {
			busy[region] = false;
		}
	}

	// ----- search and paging: component state; each re-reads the tab in place -------------------------

	function resetPaging() {
		cursor.value = null;
		cursorStack.value = [];
	}

	function submitSearch(text) {
		const next = String(text || "").trim();
		if (next === search.value) return Promise.resolve(false);
		search.value = next;
		resetPaging();
		return load();
	}

	function clearSearch() {
		search.value = "";
		resetPaging();
		return load();
	}

	function nextPage() {
		const area = data.value && data.value.area;
		const next = area && area.register && area.register.next_cursor;
		if (!next) return Promise.resolve(false);
		cursorStack.value = [...cursorStack.value, cursor.value];
		cursor.value = next;
		return load();
	}

	function previousPage() {
		if (!cursorStack.value.length) return Promise.resolve(false);
		const stack = [...cursorStack.value];
		cursor.value = stack.pop();
		cursorStack.value = stack;
		return load();
	}

	// A new tab starts clean; a changed filter or state keeps the search text and starts at the first page.
	function routeChanged(previous, next) {
		if (!previous || previous.tab !== next.tab) search.value = "";
		resetPaging();
	}

	return { phase, data, refreshing, busy, retryFailed, search, cursor, cursorStack, load, retry, submitSearch, clearSearch, nextPage, previousPage, routeChanged };
}
