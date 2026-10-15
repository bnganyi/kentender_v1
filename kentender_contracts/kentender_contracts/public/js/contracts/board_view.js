// The design's board model, drawn (CM-CHG-001 v0.8 section 10; `design/CM Artboards.dc.html`). These are the template's own helper functions (`stCls`, `cell`, `table`, `field`, `block`, `view`)
// ported as pure functions, so a live screen and the design's board are built from the same decisions and only data differs.

const STATUS = {
	Preparing: "is-draft", Draft: "is-draft", "Awaiting signatures": "is-pending", Active: "is-live", Closed: "is-critical", Terminated: "is-critical", "Did not proceed": "is-critical",
	"Needs review": "is-attention", Meets: "is-live", "Does not meet": "is-critical", Signed: "is-live", "Awaiting signature": "is-pending", Confirmed: "is-live", Reversed: "is-critical",
	"Not verified": "is-attention", Verified: "is-live", Operative: "is-live", Paid: "is-live", Certified: "is-live", Held: "is-attention", Submitted: "is-pending", "Partly paid": "is-pending",
	Recorded: "is-live", Succeeded: "is-live", Reconciled: "is-live", Failed: "is-critical", Uncertain: "is-attention", Attempting: "is-pending",
};

export function statusClass(label) {
	return STATUS[label] || "is-pending";
}

// "id|label" is how a select option carries a value that differs from what the reader sees.
export function optionParts(option) {
	const text = String(option);
	const at = text.indexOf("|");
	return at < 0 ? { value: text, label: text } : { value: text.slice(0, at), label: text.slice(at + 1) };
}

// A table cell's prefix says what it is: `@` link, `!` status pill, `#` or `~` input, `^value|a,b,c` select, anything else text.
export function parseCell(value, index, num) {
	const text = String(value);
	const cell = { cls: num.includes(index) ? "is-num" : "", isT: false, isL: false, isS: false, isI: false, isSel: false, v: text, opts: [] };
	const mark = text[0];
	if (mark === "@") Object.assign(cell, { isL: true, v: text.slice(1) });
	else if (mark === "!") Object.assign(cell, { isS: true, v: text.slice(1), sc: statusClass(text.slice(1)) });
	else if (mark === "#" || mark === "~") Object.assign(cell, { isI: true, v: text.slice(1) });
	else if (mark === "^") {
		const [current, options] = text.slice(1).split("|");
		Object.assign(cell, { isSel: true, v: current, opts: (options || current).split(",") });
	} else cell.isT = true;
	return cell;
}

export function tableView(block) {
	const num = block.num || [];
	return {
		head: block.cols.map((v, i) => ({ v, cls: num.includes(i) ? "is-num" : "" })),
		body: block.rows.map((row, r) => ({ cells: row.map((v, i) => ({ ...parseCell(v, i, num), name: (block.inputs || {})[`${r},${i}`] || "", live: (block.live || {})[`${r},${i}`] || "" })) })),
	};
}

export function fieldView(field, key, i) {
	const t = field.t;
	return {
		...field,
		span: field.wide || t === "ta" || t === "rad" ? "1 / -1" : "auto",
		rows: (field.o && field.o.rows) || 3,
		name: field.name || `${key}-f${i}`,
		radioName: `${key}-f${i}`,
		options: t === "rad" ? field.opts.map((label, j) => ({ label, index: j })) : (field.opts || []).map(optionParts),
	};
}

export function blockView(block, key, index) {
	const out = { ...block, isFacts: block.k === "facts", isRows: block.k === "rows", isTable: block.k === "table", isFields: block.k === "fields", isText: block.k === "text", isStrong: block.k === "strong", isHelp: block.k === "help", isLinks: block.k === "links", isBtns: block.k === "btns", isPreview: block.k === "preview", items: [] };
	if (out.isFacts || out.isRows || out.isPreview) out.items = block.items.map(([l, v]) => ({ l, v }));
	if (out.isLinks || out.isBtns) out.items = block.items;
	if (out.isTable) Object.assign(out, tableView(block), { gcols: `repeat(${block.cols.length}, minmax(0, 1fr))` });
	if (out.isTable) out.flat = out.body.flatMap((r) => r.cells);
	if (out.isFields) out.items = block.items.map((f, i) => fieldView(f, `${key}-${index}`, i));
	if (out.isPreview) out.chev = block.open ? "is-open" : "";
	return out;
}

// The next step in the design's four kinds, with the sentence(s) the template draws.
export function nextView(next) {
	if (!next) return null;
	return {
		kind: next.k,
		turn: next.k === "turn",
		wait: next.k === "wait",
		done: next.k === "done",
		blk: next.k === "blk",
		h: next.h,
		s: next.s || "",
		s2: next.s2 || "",
		fixes: (next.fixes || []).map((l, i) => ({ l, primary: i === 0, sec: i > 0 })),
	};
}

// "A–B" for a long run of unit references typed one per line, the list itself for a short one.
export function unitRange(text) {
	const units = String(text || "").split("\n").map((u) => u.trim()).filter(Boolean);
	if (!units.length) return "—";
	return units.length === 1 ? units[0] : units.length > 3 ? `${units[0]}–${units[units.length - 1]}` : units.join(", ");
}

// Every field a board or one of its dialogs asks for, with the value it starts at: what a command is sent with.
export function initialValues(scope) {
	const values = {};
	const fields = (blocks) => {
		for (const block of blocks || []) {
			if (block.k === "fields") {
				for (const f of block.items) if (f.name) values[f.name] = f.t === "rad" ? (f.si >= 0 ? f.si : "") : f.v ?? "";
			} else if (block.k === "table") {
				block.rows.forEach((row, r) =>
					row.forEach((cell, i) => {
						const name = (block.inputs || {})[`${r},${i}`];
						if (!name) return;
						const text = String(cell);
						const mark = text[0];
						values[name] = mark === "^" ? text.slice(1).split("|")[0] : mark === "#" || mark === "~" ? text.slice(1) : text;
					})
				);
			}
		}
	};
	for (const region of scope.regions || []) fields(region.b);
	return values;
}
