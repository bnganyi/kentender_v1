/**
 * The structural half of design fidelity: what containers a screen is built
 * out of, and how they nest.
 *
 * The existing instrument in `../helpers/designFidelity.ts` compares the
 * artboard's ordered landmark *texts* against the live page's. That cannot see
 * a container, because no container is in its selector list; it cannot see an
 * element demoted to another element, because the text is the same either way;
 * and it cannot see anything without text at all. Every one of those has
 * shipped:
 *
 *   - `.kt-group` dropped from Plan checks — a wrapper with no text of its own,
 *     invisible to a text comparison by construction (found live 24 Sep 2026).
 *   - "Approval" built as a `.kt-label` where the board titles a region with
 *     `h2` — same string, same position, subsequence still matched.
 *   - A disclosure head with no title row and no chevron — the chevron is an
 *     SVG, so it has no text to compare (8 more instances across Planning).
 *   - Editable controls built inside `.kt-meta-row`, the read-only fact
 *     primitive, on the U09 purchase editor: ten defects, every fidelity
 *     assertion green (`cf968ac9`, and AGENTS.md §6.6).
 *
 * This module answers the other question: does the screen use the containers
 * the board draws, nested the way the board nests them?
 *
 * It deliberately does NOT compare trees for equality. A build is free to add
 * layout wrappers the board had no need of — an element that is not a landmark
 * is transparent, and its children are hoisted to the nearest landmark
 * ancestor. What must hold is the landmark contract: every container the board
 * draws is present, in order, under the same chain of landmark ancestors.
 *
 * Runs in Node over HTML strings, so one implementation serves both the
 * component tests (a mounted component's `outerHTML`) and the browser gates
 * (the live page's and the artboard's `outerHTML`).
 */
import { DESIGN_SYSTEM_OMISSIONS } from "./departures/design-system.js";

/**
 * The design system's structural vocabulary.
 *
 * `classes` lists every class that means the same landmark. The aliases are
 * not sloppiness — the artboard exports and the live stylesheet genuinely use
 * different names for the same thing, and the difference is a porting
 * convention, not a defect:
 *
 *   - Planning's boards draw `.field` and `table.table`; the live app uses the
 *     Industry `.field` and `.table` (0 occurrences of `field` or
 *     `table` across all ten Planning boards).
 *   - The boards' `.dialog` is a design-tool class the live code deliberately
 *     never ports, rendering `.dialog` instead — stated at
 *     `ConfirmDialog.vue` and `ReasonDialog.vue` in Departmental Needs.
 *
 * Two things are deliberately NOT in this vocabulary, for the same reason:
 *
 *   - `.kt-facts`/`.kt-fact-value`, which Budget's boards draw, have no rule in
 *     `kt_industry_tokens.css` at all. The board carries their layout inline as
 *     `grid-template-columns:repeat(2,1fr)`. A name the design system does not
 *     define is a design-tool artefact, not a container the build owes anyone.
 *   - `.kt-grid-2`/`.kt-grid-3`/`.kt-editor-grid` are real, but they are layout,
 *     and layout wrappers are exactly what this instrument lets a build add or
 *     leave out. Making the grid a landmark buried every field one level deeper
 *     than the board draws it and reported all of them missing.
 *
 * Both are transparent, so their children hoist and the two sides line up.
 */
const LANDMARKS = [
	{ name: "page", classes: ["kt-page"] },
	{ name: "page-head", classes: ["kt-page-head"] },
	{ name: "page-scope", classes: ["kt-page-scope"] },
	{ name: "page-actions", classes: ["kt-page-actions"] },
	{ name: "region", classes: ["kt-region"] },
	{ name: "group", classes: ["kt-group"] },
	{ name: "task-row", classes: ["kt-task-row"] },
	{ name: "decision", classes: ["kt-decision"] },
	{ name: "filter-bar", classes: ["kt-filter-bar"] },
	{ name: "meta-row", classes: ["kt-meta-row"] },
	{ name: "field", classes: ["field"] },
	{ name: "table", classes: ["table"] },
	{ name: "notice", classes: ["kt-notice"] },
	// Part of the notice primitive, not decoration: `kt_industry_tokens.css`
	// colours `.kt-notice.is-warning .kt-notice-icon` and its siblings per
	// severity, so the icon is how a warning reads as a warning. Every board
	// in every module draws one. An SVG has no text, so this is invisible to
	// the landmark gate — the same blind spot that let eight disclosure heads
	// ship without their chevrons.
	{ name: "notice-icon", classes: ["kt-notice-icon"] },
	{ name: "disclosure", classes: ["kt-disclosure"] },
	{ name: "disclosure-head", classes: ["kt-disclosure-head"] },
	{ name: "disclosure-title-row", classes: ["kt-disclosure-title-row"] },
	{ name: "disclosure-chevron", classes: ["kt-disclosure-chevron"] },
	{ name: "disclosure-body", classes: ["kt-disclosure-body"] },
	{ name: "timeline", classes: ["kt-timeline"] },
	{ name: "empty", classes: ["kt-empty"] },
	{ name: "card", classes: ["card"] },
	{ name: "card-title", classes: ["kt-card-title"] },
	{ name: "factstack", classes: ["kt-factstack"] },
	// Strategy and Budget frame content with `.blueprint` + `.card`
	// rather than `.kt-page` + `.kt-region` + `.kt-group`. Neither module uses
	// a single one of the Planning containers; both boards and both live
	// screens are built from these. AGENTS.md §6.6 already records a shipped
	// defect of exactly this shape — real content in a bare `.card` with
	// the `.blueprint`/`.corner` frame dropped.
	{ name: "blueprint", classes: ["blueprint"] },
	{ name: "corner", classes: ["corner"] },
	{ name: "kpi-row", classes: ["kt-kpi-row"] },
	{ name: "kpi-card", classes: ["kt-kpi-card"] },
	{ name: "tabs", classes: ["kt-tabs"] },
	// The Budget boards draw each allocation, approval line and revision as an
	// expandable `.kt-record`: a `main` row with a toggle, and a `detail` the
	// toggle reveals. Flattening the detail, or rendering the record with no
	// way to open it, leaves every word on the screen unchanged.
	{ name: "record", classes: ["kt-record"] },
	{ name: "record-main", classes: ["kt-record-main"] },
	{ name: "record-title", classes: ["kt-record-title"] },
	{ name: "record-toggle", classes: ["kt-record-toggle"] },
	{ name: "record-body", classes: ["kt-record-body"] },
	{ name: "record-detail", classes: ["kt-record-detail"] },
	{ name: "record-footer", classes: ["kt-record-footer"] },
	{ name: "bar", classes: ["kt-bar"] },
	{ name: "dialog", classes: ["dialog"] },
	{ name: "dialog-actions", classes: ["dialog-actions"] },
];

/**
 * Modifiers that change what a container *is*, not merely how it looks, so a
 * board drawing one and a build omitting it are saying different things:
 * `is-secondary` demotes a region's heading, `is-tight` turns a fact grid into
 * a wrapping row, and a notice's severity is its whole meaning.
 */
const MODIFIERS = ["is-secondary", "is-tight", "is-warning", "is-critical", "is-info", "is-live", "is-attention"];

/**
 * Landmarks whose severity modifier is a reading of their own data rather than
 * a choice about the container. `BudgetDetailScreen` colours its Available KPI
 * from `available > 0`; the board hardcodes whichever one its fixture happened
 * to show. That is the same thing a status pill's severity is, and status is
 * already excluded from this instrument for exactly that reason. A notice is
 * the opposite case and stays strict: there the severity IS the message.
 */
const DATA_SEVERITY = new Set(["kpi-card", "bar"]);

/** Attribute-marked landmarks (see `landmarkOf`). */
const GUIDANCE = ["journey", "next-step"];

/** Headings are landmarks in their own right: a region titled by an `h2` and a
 *  region titled by a styled `div` are not the same structure, and only the
 *  first survives a stylesheet change. */
const HEADING_TAGS = ["H1", "H2", "H3"];

function classesOf(el) {
	const raw = el.getAttribute && el.getAttribute("class");
	return raw ? String(raw).trim().split(/\s+/) : [];
}

/**
 * A status pill is deliberately NOT a landmark. This instrument answers one
 * question — what containers is the screen built from, and how do they nest —
 * and a badge is a leaf marker, not a container. Its severity is row data, and
 * whether it sits directly in a group or inside that group's fact row says
 * nothing about the screen's structure. Its text is already compared by the
 * landmark gate in `../helpers/designFidelity.ts`.
 *
 * `.kt-tab` is excluded for the same reason, and only `.kt-tabs` — the bar that
 * holds them — is a landmark. A tab is a button, its label is already compared
 * as a landmark text by that same gate, and Budget's and Strategy's fidelity
 * specs both strip tab texts deliberately because they carry live counts.
 */
function landmarkOf(el) {
	if (HEADING_TAGS.includes(el.tagName)) return { names: [el.tagName.toLowerCase()], mods: [] };
	const classes = classesOf(el);
	// KT-STD-001 v1.8 §2.9 — the boards draw the journey tracker and the
	// next-step block only as `data-kt="journey"` / `data-kt="next-step"`
	// (inline-styled, no class), and the shared components carry the same
	// attribute. Without this both would be transparent, and a screen that
	// dropped its tracker or put the blocked block in the wrong place would
	// still pass.
	const guidance = (el.getAttribute && el.getAttribute("data-kt")) || "";
	const guidanceNames = GUIDANCE.includes(guidance) ? [guidance] : [];
	if (!classes.length && !guidanceNames.length) return null;
	// An element is usually several landmarks at once — the frame in both
	// Strategy and Budget is a single element carrying `card blueprint`,
	// and an empty state is `card blueprint kt-empty`. Taking only the
	// first match in this list's order made that panel read as an `empty` with
	// no card, and reported the board's card as missing. Collect them all, in
	// the vocabulary's own order so the rendered path is stable.
	const names = LANDMARKS.filter((landmark) => landmark.classes.some((candidate) => classes.includes(candidate))).map(
		(landmark) => landmark.name
	).concat(guidanceNames);
	if (!names.length) return null;
	const mods = names.some((name) => DATA_SEVERITY.has(name)) ? [] : MODIFIERS.filter((mod) => classes.includes(mod));
	return { names, mods };
}

/**
 * A board draws one row per entry in its own fixture; how many entries a live
 * world holds is fixture content. Identical repeated siblings collapse to one
 * requirement, so the structure is still compared in full, exactly once — the
 * same rule the landmark gate's own `onceEach` applies.
 */
function signature(node) {
	return `${describe(node)}(${node.children.map(signature).join(",")})`;
}

function collapseRepeats(nodes) {
	const seen = new Set();
	return nodes.filter((node) => {
		const key = signature(node);
		if (seen.has(key)) return false;
		seen.add(key);
		return true;
	});
}

/**
 * Reduce an element to its landmark skeleton. Non-landmark elements are
 * transparent — their children are hoisted — which is what makes an
 * implementation-only wrapper legal.
 */
export function skeletonOf(root) {
	function walk(el, into) {
		for (const child of Array.from(el.children || [])) {
			const landmark = landmarkOf(child);
			if (landmark) {
				const node = {
					names: landmark.names,
					mods: landmark.mods,
					tag: child.tagName.toLowerCase(),
					testid: (child.getAttribute && child.getAttribute("data-testid")) || "",
					children: [],
				};
				into.push(node);
				walk(child, node.children);
			} else {
				walk(child, into);
			}
		}
		return into;
	}
	return walk(root, []);
}

/** `region > h2` reads better in a failure message than `region > h2` buried
 *  in JSON, so paths are rendered as a breadcrumb. */
function pathOf(trail, node) {
	return [...trail, describe(node)].join(" > ");
}

function describe(node) {
	const name = node.names.join("+");
	return node.mods.length ? `${name}.${node.mods.join(".")}` : name;
}

function matches(boardNode, builtNode) {
	// Every landmark the board's element is must also be one the build's
	// element is; the build may be more besides. So a board `card+blueprint`
	// is satisfied by a built `card+blueprint+empty`, and a build that drops
	// the blueprint frame from a card is not.
	if (!boardNode.names.every((name) => builtNode.names.includes(name))) return false;
	// The board's modifiers are a floor, not an exact set: a build may add
	// `is-live` to a notice the board drew plain, but may not drop the
	// severity the board chose.
	return boardNode.mods.every((mod) => builtNode.mods.includes(mod));
}

/**
 * Compare a board skeleton against a built one.
 *
 * Ordered subsequence with ancestry: each board node must appear among the
 * built children of its matched parent, at or after the previous match. Built
 * nodes nothing consumed are reported as additions — legal only when the
 * departures registry names them.
 */
/**
 * How well a built node satisfies a board node, counting the board's children
 * it can account for. Used to choose between several candidates of the same
 * kind: three plain `region`s in a row are indistinguishable by name, and
 * first-fit picked the wrong one — the board's Plan-checks region matched the
 * build's Requirements region and its `group` was then reported missing.
 */
function affinity(boardNode, builtNode) {
	if (!boardNode.children.length) return 1;
	let score = 0;
	let cursor = 0;
	for (const wanted of boardNode.children) {
		for (let i = cursor; i < builtNode.children.length; i += 1) {
			if (matches(wanted, builtNode.children[i])) {
				score += 1 + affinity(wanted, builtNode.children[i]);
				cursor = i + 1;
				break;
			}
		}
	}
	return score;
}

// Revisions of the design system that the module artboards pre-date (departures/design-system.js).
function omittedBySystem(path) {
	return DESIGN_SYSTEM_OMISSIONS.some((entry) => path === entry.endsWith || path.endsWith(` > ${entry.endsWith}`));
}

export function compareSkeletons(board, built, { departures = [] } = {}) {
	const missing = [];
	const extra = [];
	const allowed = new Set(departures.map((entry) => entry.testid).filter(Boolean));
	const allowedPaths = new Set(departures.map((entry) => entry.path).filter(Boolean));
	// Board containers the build deliberately does not require: either
	// replaced by something else (`replaces`) or not carried at all (`omits`),
	// each with its own recorded reason.
	const replaced = new Set(departures.flatMap((entry) => [...(entry.replaces || []), ...(entry.omits || [])]));

	function walk(rawBoardNodes, builtNodes, trail) {
		const boardNodes = collapseRepeats(rawBoardNodes);
		const consumed = new Set();
		let cursor = 0;
		for (const wanted of boardNodes) {
			let found = -1;
			let best = -1;
			for (let i = cursor; i < builtNodes.length; i += 1) {
				if (consumed.has(i) || !matches(wanted, builtNodes[i])) continue;
				const score = affinity(wanted, builtNodes[i]);
				if (score > best) {
					best = score;
					found = i;
				}
			}
			if (found === -1) {
				const path = pathOf(trail, wanted);
				// A board container the build deliberately replaces with
				// something else — recorded, with the replacement named, so
				// "we chose differently" cannot be confused with "we dropped it".
				if (replaced.has(path)) continue;
				if (omittedBySystem(path)) continue;
				const elsewhere = builtNodes.some((node) => wanted.names.every((name) => node.names.includes(name)));
				missing.push({
					path,
					why: elsewhere ? "OUT OF ORDER or missing a required modifier" : "MISSING",
					built: builtNodes.map(describe),
				});
				continue;
			}
			consumed.add(found);
			cursor = found + 1;
			// The board draws one row per entry in its own fixture and the live
			// world holds however many it holds. Having matched this board node,
			// any later sibling that is structurally identical to the built node
			// that satisfied it is another of the same thing — fixture content,
			// not an addition. Which entries are shown is already compared, by
			// text, by the landmark gate; only a sibling that is a DIFFERENT
			// container, or the same container with different insides, is
			// reported. This is the built-side half of `collapseRepeats`, which
			// has always done the same on the board side.
			const repeat = signature(builtNodes[found]);
			for (let i = found + 1; i < builtNodes.length; i += 1) {
				if (!consumed.has(i) && signature(builtNodes[i]) === repeat) consumed.add(i);
			}
			walk(wanted.children, builtNodes[found].children, [...trail, describe(wanted)]);
		}
		builtNodes.forEach((node, index) => {
			if (consumed.has(index)) return;
			const path = pathOf(trail, node);
			if (allowed.has(node.testid) || allowedPaths.has(path)) return;
			extra.push({ path, testid: node.testid });
		});
	}

	walk(board, built, []);
	return { missing, extra };
}

/**
 * Fail with the whole picture at once, the way the landmark gate already does:
 * naming one difference at a time turns a re-port into a dozen round trips.
 */
export function formatMismatch(label, { missing, extra }) {
	const lines = [];
	if (missing.length) {
		lines.push(`${label}: ${missing.length} container(s) the artboard draws are not in the built screen.`);
		for (const item of missing) {
			lines.push(`  ${item.why}: ${item.path}`);
			lines.push(`    built at that level: ${item.built.join(", ") || "(nothing)"}`);
		}
	}
	if (extra.length) {
		lines.push(
			`${label}: ${extra.length} container(s) the artboard does not draw are present and unregistered.`,
			"  Register each in tests/ui/fidelity/departures/ with a reason and an authority, or remove it.",
		);
		for (const item of extra) {
			lines.push(`  UNREGISTERED: ${item.path}${item.testid ? ` [data-testid="${item.testid}"]` : ""}`);
		}
	}
	return lines.join("\n");
}
