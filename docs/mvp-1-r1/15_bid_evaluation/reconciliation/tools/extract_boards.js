// Extracts the EVL artboard registry (window.EVL.boards) as JSON.
// Usage: node extract_boards.js > boards.json   (run from any directory)
const fs = require("fs");
const path = require("path");
const dir = path.join(__dirname, "..", "..", "design", "evl");
global.window = global;
for (const f of ["evl-kit.js", "boards-1.js", "boards-2.js", "boards-3.js", "boards-4.js", "boards-5.js"]) {
  eval(fs.readFileSync(path.join(dir, f), "utf8"));
}
const E = window.EVL;
if (Array.isArray(window.EVL_Q)) window.EVL_Q.forEach((fn) => fn(E)); // the kit drains the queue itself once loaded
const out = E.sorted().map((b) => ({
  id: b.id, group: b.g, name: b.name, actor: b.actor ? (E.P[b.actor] || [b.actor])[0] : "",
  at: b.at || "", state: b.state || "", spec: b.spec || "", arch: b.arch || "",
  size: b.size === "m" ? "390x844" : b.size === "c" ? "1024x768" : "1440x1024",
  dialog: !!b.dlg, after: b.after || "", note: b.note || "",
}));
process.stdout.write(JSON.stringify(out, null, 1));
