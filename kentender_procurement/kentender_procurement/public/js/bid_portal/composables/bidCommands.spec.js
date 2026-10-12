// The commands of one bid run one at a time, each against the newest version known when it starts, so a Save
// that follows an upload carries the version the upload left the bid at, never the one the page held before.
import { describe, expect, it } from "vitest";
import { expectedVersion, isStale, noteRefusal, noteResult, runExclusive, sendCommand } from "./bidCommands.js";

const bid = "BID-1";
const fresh = () => ({});

describe("a bid's commands", () => {
	it("send the newest version known, never an older one the page still holds", () => {
		const portal = fresh();
		expect(expectedVersion(portal, bid, 30)).toBe(30);
		noteResult(portal, bid, { ok: true, record_version: 31 });
		expect(expectedVersion(portal, bid, 30)).toBe(31); // the page has not re-read yet
		expect(expectedVersion(portal, bid, 33)).toBe(33); // a newer read wins
		noteResult(portal, bid, { ok: true, record_version: 32 });
		expect(expectedVersion(portal, bid, 33)).toBe(33); // a version never goes back
	});

	it("keep each bid, and each portal, to itself", () => {
		const a = fresh();
		noteResult(a, bid, { record_version: 40 });
		expect(expectedVersion(a, "BID-2", 5)).toBe(5);
		expect(expectedVersion(fresh(), bid, 5)).toBe(5);
	});

	it("run one at a time in the order given, and a failure does not stop the next", async () => {
		const portal = fresh();
		const log = [];
		const slow = runExclusive(portal, bid, async () => {
			log.push("upload starts");
			await new Promise((r) => setTimeout(r, 20));
			log.push("upload ends");
			throw new Error("refused");
		});
		const next = runExclusive(portal, bid, async () => log.push("save starts"));
		await expect(slow).rejects.toThrow("refused");
		await next;
		expect(log).toEqual(["upload starts", "upload ends", "save starts"]);
	});

	it("make a command that follows another use the version the first one produced", async () => {
		const portal = fresh();
		const sent = [];
		const upload = sendCommand(portal, bid, 30, async (version) => (sent.push(version), { ok: true, record_version: 31 }));
		const save = sendCommand(portal, bid, 30, async (version) => (sent.push(version), { ok: true, record_version: 32 }));
		await Promise.all([upload, save]);
		expect(sent).toEqual([30, 31]);
		expect(expectedVersion(portal, bid, 30)).toBe(32);
	});

	it("learn the current version from a stale refusal, so the next try succeeds", () => {
		const portal = fresh();
		const refusal = Object.assign(new Error("Another person changed this bid."), { code: "BDS_STALE_VERSION", detail: { record_version: 35 } });
		expect(isStale(refusal)).toBe(true);
		expect(isStale(new Error("x"))).toBe(false);
		noteRefusal(portal, bid, refusal);
		expect(expectedVersion(portal, bid, 30)).toBe(35);
	});
});
