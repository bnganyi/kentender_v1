#!/usr/bin/env bash
# Contract Management release evidence (CM-CHG-001 v0.8 plan Phase 12, tracker CM-G12): every Contract Management gate, once, in the order that keeps one
# gate's leftovers out of the next, with each result written to artifacts/cm-release-evidence.md next to the commit it was run on and the proof level it can
# give. A failing gate does not stop the run: the report must show every gate, so the whole picture is read at once. The exit status is non-zero if any failed.
#
#   scripts/test-site.sh run make ui-cm-release-evidence-gate
#
# What this proves is exactly what each row says. It does not cover Phase 13 (document approvals, the legal questions, the production Trust provider and
# channels, the production rule profile, a security review): those are owner-gated and the report ends by listing them as not run.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${CM_EVIDENCE_FILE:-$ROOT/artifacts/cm-release-evidence.md}"
mkdir -p "$(dirname "$OUT")"
cd "$ROOT"

# target | proof level it gives | what it covers
GATES=(
	"cm-services-gate|L1 synthetic upstreams, real ERPNext where the module says so|every service and board module, then the shared signing facade"
	"cm-seams-gate|L2 real owners|Award's source material, the core seams, Budget's funding provider and its principal guard"
	"cm-native-gate|L2 real ERPNext|the native adapter, the payment bypass guards, a two-process claim race, the readiness check"
	"cm-leakage-gate|L1 + L2|who may read what; the technical and audit readers can never act; adversarial authority"
	"cm-dead-end-gate|L1|no reader stranded on any stage; every command safe to send twice; holds and recovery"
	"cm-regression-gate|L2 regression|Award's seams, Budget's funding provider, the signing facade, the supplier-account provider and Home's structural comparison"
	"ui-cm-fidelity-gate|structural|every board of the design compared with its artboard, or recorded as not compared with its reason"
	"cm-ui-gate|L2 browser|the shell, the ordinary thread, formation, an existing contract, delivery and acceptance, finance, changes, close-out; then the world is cleaned"
	"cm-demo-gate|L2 browser|the demonstration profiles walked as real people from the sidebar, My work and the bell"
	"cm-persona-gate|L2 browser|each named person on the accepted contract, as that person, with no native-form redirect"
	"cm-independence-gate|L2 independence site|the service modules on a site that holds only ERPNext, core, supplier accounts and the app"
)

# The browser gates must not be cut off by the server restarting whenever a Python file in the shared checkout changes
# (an earlier run lost four specs and a persona to "net::ERR_EMPTY_RESPONSE" for exactly that): serve without the watcher for the run, normally again after.
scripts/test-site.sh stop >/dev/null 2>&1 || true
TEST_SERVE_NORELOAD=1 scripts/test-site.sh serve >/dev/null 2>&1 || true
trap 'scripts/test-site.sh stop >/dev/null 2>&1 || true; scripts/test-site.sh serve >/dev/null 2>&1 || true' EXIT

now() { date '+%Y-%m-%d %H:%M:%S %z'; }
commit="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
dirty="$(git status --porcelain 2>/dev/null | grep -c . || true)"
started="$(now)"
rows=""
failed=0

for gate in "${GATES[@]}"; do
	IFS='|' read -r target level covers <<<"$gate"
	echo "=== $target ($(now))"
	begin=$SECONDS
	make "$target" SITE="${SITE:-kentender-test.local}"
	code=$?
	took=$((SECONDS - begin))
	verdict="Passed"
	if [ "$code" -ne 0 ]; then verdict="**FAILED** (exit $code)"; failed=$((failed + 1)); fi
	rows+="| \`make $target\` | $verdict | $((took / 60)) min $((took % 60)) s | $level | $covers |"$'\n'
done

{
	echo "# Contract Management release evidence"
	echo
	echo "| | |"
	echo "|---|---|"
	echo "| Commit | \`$commit\` ($dirty uncommitted paths at the start of the run) |"
	echo "| Site | \`${SITE:-kentender-test.local}\` (the test site; never the dev site) |"
	echo "| Started | $started |"
	echo "| Finished | $(now) |"
	echo "| Gates failed | $failed of ${#GATES[@]} |"
	if [ -n "${CM_LOCK_HELD:-}" ]; then
		echo "| Shared test-site lock | held for the whole run (\`${CM_LOCK_HELD}\`) |"
	else
		echo "| Shared test-site lock | **not held**: the script was run directly, so other work could have used the site during the run |"
	fi
	echo "| Preflight | run first by every gate (\`cm-preflight\`: refuses a live Playwright run and the development site) |"
	echo
	echo "| Gate | Result | Took | Proof level | What it covers |"
	echo "|---|---|---|---|---|"
	printf '%s' "$rows"
	echo
	echo "## Platform"
	echo
	"$ROOT/scripts/cm-platform-manifest.sh" | sed 1,2d
	echo
	echo "## Not run, and why"
	echo
	echo "* **Phase 13** is owner-gated and has no gate: the approval of the proposed successor documents, the legal questions (LQ-01 to LQ-06), the production rule profile, the production Trust provider, the execution and witnessing method, real notice and report channels, Finance policy confirmations, and a security review. Until they are done, the proofs above are development proofs: the signing provider, the rule profile, the Award source provider and the funding owner may be simulated, and no screen says so."
	echo "* **A contract closed against the real Budget on the canonical award** is not proved (FU-CM-118): Budget's own provider is proved and Contract Management's close-out is proved against the simulated funding owner."
	echo "* **The canonical seed world** carries no contract (FU-CM-122); the demonstration profiles stand in for it."
	echo "* **Home's browser specs** (\`make ui-home-gate\`) are not run as evidence: they read the canonical world as it was seeded on 5 October, and the test site's canonical world has drifted from it (the head of procurement's Home reads 2 actions, 1 waiting item and 2 oversight records where the specs expect 9, 2 and 6, because Tenders, Bid opening and Requisitions rows are missing; none of that is Contract Management's). Contract work on Home is proved by \`test_cm_home_provider\` and the demonstration walk. Rebuilding the world with \`make seed-canonical SITE=kentender-test.local REBUILD=True\` makes them an oracle again."
	echo "* **The rest of the platform's gates** (each other module's own services and browser gates) are not re-run: the regression gate above covers what Contract Management reaches into or changed in another app's world, and nothing else."
} >"$OUT"

echo
echo "Release evidence written to $OUT ($failed gate(s) failed)"
[ "$failed" -eq 0 ]
