// A bid's commands (save an answer, upload, replace, remove or link a file) each carry the version of
// the bid they were made against, and every one of them moves that version on. A person who uploads a
// file and goes straight on to Save, or whose re-read is still on its way, would otherwise send the
// version the page held before the upload and be told "Another person changed this bid".
//
// So, per bid: the commands run one at a time, each takes the newest version known when it starts
// (the page's own, or what the last command or refusal reported), and each reports the version it
// produced. Keyed by the portal runtime, so a test mounts with a clean slate.
const stores = new WeakMap();

function slot(portal, reference) {
	let bids = stores.get(portal);
	if (!bids) stores.set(portal, (bids = new Map()));
	let entry = bids.get(reference);
	if (!entry) bids.set(reference, (entry = { version: 0, tail: Promise.resolve() }));
	return entry;
}

export function noteVersion(portal, reference, version) {
	const next = Number(version);
	const entry = slot(portal, reference);
	if (Number.isFinite(next) && next > entry.version) entry.version = next;
}

// What a command should send: the newest of the page's own version and the last one a command reported.
export function expectedVersion(portal, reference, pageVersion) {
	return Math.max(slot(portal, reference).version, Number(pageVersion) || 0);
}

// Run `fn` after every earlier command on this bid has finished, whatever its outcome.
export function runExclusive(portal, reference, fn) {
	const entry = slot(portal, reference);
	const run = entry.tail.then(() => fn());
	entry.tail = run.then(() => undefined, () => undefined);
	return run;
}

// Remember what a command's answer or refusal says the bid's version now is.
export function noteResult(portal, reference, result) {
	if (result && result.record_version != null) noteVersion(portal, reference, result.record_version);
}

export function noteRefusal(portal, reference, error) {
	if (error && error.code === "BDS_STALE_VERSION" && error.detail) noteVersion(portal, reference, error.detail.record_version);
}

export function isStale(error) {
	return !!error && error.code === "BDS_STALE_VERSION";
}

// One command on a bid: after the earlier ones, against the newest version known, reporting what it produced.
// `send(version)` makes the call and returns its answer.
export function sendCommand(portal, reference, pageVersion, send) {
	return runExclusive(portal, reference, async () => {
		const result = await send(expectedVersion(portal, reference, pageVersion));
		noteResult(portal, reference, result);
		return result;
	});
}
