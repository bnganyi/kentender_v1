// Dumps every Contract Management board as JSON, by running the design's own
// code through `cmKit` (tests/ui/fidelity/board.js). Nothing is counted by hand.
//
// Usage (from the repo root):
//   node docs/mvp-1-r1/21_contract_management/reconciliation/tools/extract_boards.mjs > /tmp/cm_boards.json
import { cmKit } from "../../../../../tests/ui/fidelity/board.js";

const walk = (blocks, out) => {
	for (const b of blocks || []) {
		if (b.k === "btns") out.buttons.push(...b.items.map(String));
		if (b.k === "links") out.links.push(...b.items.map((i) => (typeof i === "string" ? i : i.l || String(i))));
		if (b.k === "table") for (const r of b.rows || []) for (const c of r) if (typeof c === "string" && c[0] === "@") out.rowLinks.push(c.slice(1));
	}
};

const kit = cmKit();
const boards = kit.screens.map((s, i) => {
	const c = { buttons: [], links: [], rowLinks: [] };
	for (const rg of s.regions || []) walk(rg.b, c);
	if (s.dialog) walk(s.dialog.b, c);
	if (s.rows) for (const r of s.rows) for (const x of r) if (typeof x === "string" && x[0] === "@") c.rowLinks.push(x.slice(1));
	const fixes = s.next && s.next.k === "blk" ? s.next.fixes || [] : [];
	return {
		order: i + 1,
		id: s.id, design: s.d, group: s.g, name: s.name, designName: s.dn || "", variant: s.vl || "",
		page: s.page, tab: s.tab || "", who: s.who || "", at: s.at || "", subject: s.subj || "",
		ref: s.ref || "", status: s.st || "", title: s.title || "",
		next: s.next ? { kind: s.next.k, headline: s.next.h } : null,
		primary: s.p || "", secondary: s.s2 || [], headP: s.headP || "", emptyAct: s.emptyAct || "",
		dialog: s.dialog ? { title: s.dialog.t, primary: s.dialog.p || "", secondary: s.dialog.s2 || [] } : null,
		fixes, buttons: c.buttons, links: c.links, rowLinks: c.rowLinks,
		note: s.note || "",
	};
});
process.stdout.write(JSON.stringify({ files: kit.files, boards }, null, 1));
