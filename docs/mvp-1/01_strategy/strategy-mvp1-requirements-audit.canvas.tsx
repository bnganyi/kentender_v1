import {
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  H3,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
} from "cursor/canvas";

/**
 * Strategy Alignment MVP-1 requirements audit.
 * Plain-text Status/Severity/Verdict columns so summary counts stay traceable.
 * Cross-module work is tracked in:
 * apps/kentender_v1/docs/mvp-1/01_strategy/08_Strategy_Cross_Module_Lifecycle_Tracker.md
 */

type Tone = "neutral" | "success" | "warning" | "info" | "deleted";

const DELIVERY = {
  notStarted: "Not started",
  providerInProgress: "Provider in progress",
  providerDeskProven: "Provider complete — Desk proven",
  providerDoneConsumerPending: "Provider complete — consumer pending",
  consumerWiredE2EPending: "Consumer wired — end-to-end proof pending",
  e2eComplete: "End-to-end complete",
  futureExternal: "Future external integration",
  blocked: "Blocked",
  outOfScope: "Out of scope",
  closedHygiene: "Closed (hygiene)",
} as const;

const CAPABILITIES: {
  capability: string;
  conditionClass: string;
  deliveryStatus: string;
  tone: Tone;
  owner: string;
  note: string;
}[] = [
  {
    capability: "list_active_targets",
    conditionClass: "End-to-end complete (Budget + Demand + Planning display)",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
    owner: "Strategy → Budget / Demand / Planning",
    note: "Budget Desk + create-demand load Active targets; Budget save validates (Playwright); Planning wizard shows Name (CODE)",
  },
  {
    capability: "validate_strategy_reference",
    conditionClass: "End-to-end complete (Budget save path)",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
    owner: "Strategy → Demand / Planning / Budget",
    note: "Budget drawer ktFormErrors + Active save E2E; Demand + package inherit use strategy_consumer",
  },
  {
    capability: "list_applicable_value_commitments",
    conditionClass: "End-to-end complete (Demand PVC)",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
    owner: "Strategy → Demand (Value Case)",
    note: "Demand Value Treatment + create-demand Review; evidence create-demand-pvc-xmod-str-003 / make ui-create-demand-strategy-gate",
  },
  {
    capability: "get_strategy_usage",
    conditionClass: "End-to-end complete (Budget/Demand/Planning)",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
    owner: "Strategy",
    note: "Budget primary_* + Demand/Planning strategy_*; Tender/Contract/Asset/Disposal empty stubs",
  },
  {
    capability: "get_strategy_performance",
    conditionClass: "End-to-end complete (Budget/Demand/Planning contribution)",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
    owner: "Strategy",
    note: "Budget primary_* + Demand Value Treatment adoption + Planning estimated_value; Tender/Contract stubs",
  },
  {
    capability: "Demand primary alignment on Value Case",
    conditionClass: "End-to-end complete",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
    owner: "Demand",
    note: "strategy_target required in readiness; create-demand Active target empty-Next; evidence create-demand-strategy-xmod-str-002",
  },
  {
    capability: "Planning inherit Strategy Reference",
    conditionClass: "End-to-end complete",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
    owner: "Planning",
    note: "Package strategy_* inherit + wizard kt-pw-demand-strategy Name (CODE); Playwright strategy-display + pw12 Step 1",
  },
  {
    capability: "Tender / Contract / Asset / Disposal usage",
    conditionClass: "Provider present — consumer not invoked (XMOD-STR-005)",
    deliveryStatus: DELIVERY.providerDoneConsumerPending,
    tone: "info",
    owner: "Tender / Award (+ later Contract)",
    note: "Strategy usage/performance stubs ready; does not block Strategy Core move-on",
  },
  {
    capability: "Notifications and work queue (§17)",
    conditionClass: "Provider complete (transition events; due/overdue parked)",
    deliveryStatus: DELIVERY.providerDeskProven,
    tone: "success",
    owner: "Strategy",
    note: "strategy_notification_service + transition wiring; due/overdue cron parked under XMOD-STR-009",
  },
  {
    capability: "Role-based browser evidence",
    conditionClass: "Provider complete — Desk proven (wave 2)",
    deliveryStatus: DELIVERY.providerDeskProven,
    tone: "success",
    owner: "Strategy QA",
    note: "Viewer create deny + Officer/Manager export + wrong-PE Performance; make ui-strategy-role-gate — full §12 residual",
  },
  {
    capability: "Full STR-AC-001–030 automated matrix",
    conditionClass: "Provider complete — Desk proven (wave 2; residual polish)",
    deliveryStatus: DELIVERY.providerDeskProven,
    tone: "success",
    owner: "Strategy QA",
    note: "Waves 1+2 AC samples + coverage map; 002/023 stitch/nav-gated; not every 001–030 Closed",
  },
  {
    capability: "Python module_registry route_prefixes",
    conditionClass: "Closed (hygiene)",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
    owner: "Strategy / platform",
    note: "STR-SUP-003 — all page_js slugs in Python + JS registries",
  },
  {
    capability: "National plan import / AI / formula engine",
    conditionClass: "Future external / out of scope",
    deliveryStatus: DELIVERY.outOfScope,
    tone: "info",
    owner: "—",
    note: "REQ §4.2 / §24 exclusions — do not block Strategy Core",
  },
];

const OWNERSHIP: {
  event: string;
  trigger: string;
  strategy: string;
  trackerId: string;
  deliveryStatus: string;
  tone: Tone;
}[] = [
  {
    event: "Select Active Performance Target on Budget Line",
    trigger: "Budget",
    strategy: "Expose Active targets; validate Strategy Reference",
    trackerId: "XMOD-STR-001",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
  },
  {
    event: "Require primary alignment on Demand Value Case",
    trigger: "Demand",
    strategy: "validate_strategy_reference + Active-only selection",
    trackerId: "XMOD-STR-002",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
  },
  {
    event: "Apply Required / Recommended Plan Value Commitments",
    trigger: "Demand",
    strategy: "list_applicable_value_commitments",
    trackerId: "XMOD-STR-003",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
  },
  {
    event: "Inherit Strategy Reference into Planning package",
    trigger: "Planning",
    strategy: "Re-validate / carry same reference snapshot",
    trackerId: "XMOD-STR-004",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
  },
  {
    event: "Carry Strategy Reference through Tender / Award",
    trigger: "Tender / Award",
    strategy: "Historical resolvable; Active-only for new picks",
    trackerId: "XMOD-STR-005",
    deliveryStatus: DELIVERY.providerDoneConsumerPending,
    tone: "info",
  },
  {
    event: "Show Budget / Demand / Planning usage on plan",
    trigger: "Strategy (read)",
    strategy: "get_strategy_usage projection",
    trackerId: "XMOD-STR-006",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
  },
  {
    event: "Strategy Performance contribution stages",
    trigger: "Strategy (read) + consumers",
    strategy: "get_strategy_performance from authoritative refs",
    trackerId: "XMOD-STR-007",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
  },
  {
    event: "Correct invalid / superseded downstream refs",
    trigger: "Strategy admin + owning module",
    strategy: "correct_strategy_reference + portfolio flags",
    trackerId: "XMOD-STR-008",
    deliveryStatus: DELIVERY.providerDoneConsumerPending,
    tone: "warning",
  },
  {
    event: "Notify measurement / readiness / CA work items",
    trigger: "Strategy workflows",
    strategy: "Notification Log adapters (§17)",
    trackerId: "XMOD-STR-009",
    deliveryStatus: DELIVERY.providerDoneConsumerPending,
    tone: "success",
  },
];

const SURFACES: {
  id: string;
  surface: string;
  screenState: string;
  lifecycleImplication: string;
  status: string;
  tone: Tone;
}[] = [
  {
    id: "STR-UI-01",
    surface: "Strategy Portfolio",
    screenState: "Live Desk + Playwright",
    lifecycleImplication: "Does not prove consumer alignment enforcement",
    status: "Strategy core — strong UI",
    tone: "success",
  },
  {
    id: "Create",
    surface: "Create Plan",
    screenState: "Live Desk + tests",
    lifecycleImplication: "Plan identity only",
    status: "Strategy core — strong UI",
    tone: "success",
  },
  {
    id: "STR-UI-02",
    surface: "Plan Overview",
    screenState: "Live Desk + tests",
    lifecycleImplication: "Successor / scope display",
    status: "Strategy core — strong UI",
    tone: "success",
  },
  {
    id: "STR-UI-03/04",
    surface: "Plan Structure + Target drawer",
    screenState: "Live Desk + Stitch gates",
    lifecycleImplication: "Clean hierarchy present; not Objective=Indicator",
    status: "Strategy core — strong UI",
    tone: "success",
  },
  {
    id: "STR-UI-05/06",
    surface: "PVO Catalogue + Editor",
    screenState: "Live Desk + gates",
    lifecycleImplication: "Catalogue ≠ Demand PVC treatment",
    status: "Strategy core — strong UI",
    tone: "success",
  },
  {
    id: "STR-UI-07",
    surface: "Plan Value Commitments",
    screenState: "Live Desk + tests",
    lifecycleImplication: "Adoption on plan; downstream application pending",
    status: "Strategy core — strong UI",
    tone: "success",
  },
  {
    id: "STR-UI-08–10",
    surface: "Measurements + Submit + Verify",
    screenState: "Live Desk + segregation tests",
    lifecycleImplication: "Strategy-owned measurement spine present",
    status: "Strategy core — strong UI",
    tone: "success",
  },
  {
    id: "STR-UI-11",
    surface: "Corrective Actions",
    screenState: "Live Desk + MOH CA seed",
    lifecycleImplication: "Underperformance workflow present",
    status: "Strategy core — strong UI",
    tone: "success",
  },
  {
    id: "STR-UI-12",
    surface: "Downstream Usage",
    screenState: "Live read projection",
    lifecycleImplication: "Budget/Demand/Planning projected; Tender/Contract/Asset/Disposal empty stubs until consumers",
    status: "B/D/P proven — Tender stubs OK",
    tone: "success",
  },
  {
    id: "STR-UI-13",
    surface: "Review / Readiness",
    screenState: "Live Desk + blocker groups",
    lifecycleImplication: "Plan activation path present",
    status: "Strategy core — strong UI",
    tone: "success",
  },
  {
    id: "STR-UI-14",
    surface: "Audit",
    screenState: "Live read projection",
    lifecycleImplication: "Cannot audit consumer events that never wrote Strategy Audit Event",
    status: "Strategy core — strong UI",
    tone: "success",
  },
  {
    id: "STR-UI-15",
    surface: "Strategy Performance",
    screenState: "Live + export + Viewer default",
    lifecycleImplication: "Budget/Demand/Planning contribution proven; Tender/Contract stubs until XMOD-STR-005",
    status: "B/D/P proven — Tender stubs OK",
    tone: "success",
  },
];

const GAP_REGISTER: {
  id: string;
  severity: string;
  conditionClass: string;
  finding: string;
  deliveryStatus: string;
  tone: Tone;
  tracker: string;
}[] = [
  {
    id: "G-01",
    severity: "Low",
    conditionClass: "End-to-end complete",
    finding:
      "create-demand Active target empty-Next error + Name (CODE) select proven (create-demand-strategy-xmod-str-002); full Stitch Value Case redesign remains out of scope",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
    tracker: "XMOD-STR-002",
  },
  {
    id: "G-02",
    severity: "Low",
    conditionClass: "End-to-end complete",
    finding:
      "get_strategy_usage projects Budget + Demand + Planning (PKG-MOH-2026-001); Downstream Usage Desk proven; Tender/Contract/Asset/Disposal remain empty stubs",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
    tracker: "XMOD-STR-006",
  },
  {
    id: "G-03",
    severity: "Low",
    conditionClass: "End-to-end complete",
    finding:
      "PVC Review treatments refresh readiness (Included / N/A+rationale) proven (create-demand-pvc-xmod-str-003); full Stitch Value Case redesign remains out of scope",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
    tracker: "XMOD-STR-003",
  },
  {
    id: "G-04",
    severity: "Low",
    conditionClass: "End-to-end complete",
    finding:
      "Budget drawer ktFormErrors + Active primary save proven (budget-funding-line-strategy-xmod-str-001); non-Active reject remains domain-only",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
    tracker: "XMOD-STR-001",
  },
  {
    id: "G-05",
    severity: "Low",
    conditionClass: "Provider complete — Desk proven",
    finding:
      "Strategy Notification Log adapters for plan/measurement/CA/PVO transitions (due/overdue cron parked)",
    deliveryStatus: DELIVERY.providerDeskProven,
    tone: "success",
    tracker: "XMOD-STR-009 / STR-SUP-002",
  },
  {
    id: "G-06",
    severity: "Low",
    conditionClass: "End-to-end complete",
    finding:
      "Planning wizard demand card shows Name (CODE) (procurement-planning-strategy-display-xmod-str-004); package inherit domain-proven",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
    tracker: "XMOD-STR-004",
  },
  {
    id: "G-07",
    severity: "Low",
    conditionClass: "Closed (hygiene)",
    finding:
      "Strategy route_prefixes synced to all page_js (incl. strategy-plan-create); teardown inventory §6 refreshed; ticket-doc-read-gate lists MVP-1 Strategy pack",
    deliveryStatus: DELIVERY.e2eComplete,
    tone: "success",
    tracker: "STR-SUP-003 / STR-SUP-004 / STR-SUP-006",
  },
  {
    id: "G-08",
    severity: "Low",
    conditionClass: "Provider complete — Desk proven (wave 2)",
    finding:
      "AC waves 1+2 + role PW create/export/wrong-PE green; backlog (full §12 / AC polish) not on active queue — does not block Strategy move-on",
    deliveryStatus: DELIVERY.providerDeskProven,
    tone: "success",
    tracker: "STR-SUP-005",
  },
  {
    id: "G-09",
    severity: "Medium",
    conditionClass: "Future external / out of scope",
    finding:
      "National plan import, AI, formula engine, public portal, causal savings claims excluded from MVP 1",
    deliveryStatus: DELIVERY.outOfScope,
    tone: "info",
    tracker: "REQ §4.2 / §24",
  },
];

const AC_SNAPSHOT: {
  id: string;
  criterion: string;
  verdict: string;
  tone: Tone;
  note: string;
}[] = [
  {
    id: "STR-AC-001–004",
    criterion: "Create plan; clean hierarchy; readiness blockers; no Objective=Indicator",
    verdict: "Met (Desk proven samples)",
    tone: "success",
    note: "AC-001 Sub-programme + create/structure/readiness domain tests",
  },
  {
    id: "STR-AC-005–007",
    criterion: "Segregation; immutability; activate supersedes previous",
    verdict: "Met (Strategy core)",
    tone: "success",
    note: "Transitions + concurrency + AC matrix samples",
  },
  {
    id: "STR-AC-008/009",
    criterion: "Historical refs resolvable; Active-only for new selection",
    verdict: "Met for B/D/P; Tender pending",
    tone: "success",
    note: "Budget/Demand/Planning E2E; XMOD-STR-005 for Tender/Award",
  },
  {
    id: "STR-AC-010–030",
    criterion: "PVO / PVC / measurements / CA / audit / performance / export samples",
    verdict: "Desk proven (wave 2 matrix)",
    tone: "success",
    note: "Coverage map in test_strategy_mvp1_ac_matrix; residual polish backlog only",
  },
  {
    id: "STR-AC-028",
    criterion: "Public-value reporting: consideration vs achievement",
    verdict: "Met for Demand treatments + Performance",
    tone: "success",
    note: "XMOD-STR-003 + XMOD-STR-007; Tender contribution still stub",
  },
  {
    id: "Downstream usage ACs",
    criterion: "Budget + Demand + Planning usage visible",
    verdict: "Met for B/D/P",
    tone: "success",
    note: "Tender/Contract/Asset/Disposal stubs until consumers store refs",
  },
];

export default function StrategyMvp1RequirementsAudit() {
  const coreStrong = SURFACES.filter((s) => s.tone === "success").length;
  const uiPartial = SURFACES.filter((s) => s.tone === "warning").length;
  const deskProven = CAPABILITIES.filter(
    (c) => c.deliveryStatus === DELIVERY.providerDeskProven,
  ).length;
  const consumerPending = CAPABILITIES.filter(
    (c) => c.deliveryStatus === DELIVERY.providerDoneConsumerPending,
  ).length;
  const outOfScope = CAPABILITIES.filter((c) => c.deliveryStatus === DELIVERY.outOfScope).length;
  const criticalGaps = GAP_REGISTER.filter((g) => g.severity === "Critical").length;

  return (
    <Stack gap={24} style={{ padding: 24, maxWidth: 1240 }}>
      <Stack gap={8}>
        <H1>Strategy Alignment — MVP-1 audit</H1>
        <Text tone="secondary">
          Strategy Core Complete + Integration Ready for Budget / Demand / Planning. Remaining work
          is consumer/TM (XMOD-STR-005+). Track provider-present/consumer-pending gaps separately —
          they do not reopen Strategy Core.
        </Text>
        <Text tone="secondary" size="small">
          Authority: docs/mvp-1/01_strategy · Durable tracker:
          08_Strategy_Cross_Module_Lifecycle_Tracker.md · Fixture canonical: MOH-SP-0001 · Updated 6
          Aug 2026 (handoff)
        </Text>
      </Stack>

      <Callout tone="success" title="Central conclusion — move on from Strategy Core">
        Strategy Core Complete and Integration Ready (Budget/Demand/Planning E2E). Safe to leave
        Strategy-owned waves. Tender/Award (XMOD-STR-005) and remediation UX (XMOD-STR-008) are
        consumer-owned next work. Parked: due/overdue cron, full §12 residual — not on the active
        Strategy queue.
      </Callout>

      <Grid columns={4} gap={16}>
        <Stat value={String(coreStrong)} label="Screens strong (UI/core)" tone="success" />
        <Stat value={String(uiPartial)} label="Screens partial (projection)" tone="warning" />
        <Stat value={String(deskProven)} label="Desk-proven capabilities" tone="success" />
        <Stat value={String(criticalGaps)} label="Critical gap rows" tone="neutral" />
      </Grid>

      <Row gap={8} wrap>
        <Pill tone="success">Strategy Core Complete</Pill>
        <Pill tone="success">Integration Ready (B/D/P)</Pill>
        <Pill tone="warning">Consumer pending (TM+): {consumerPending}</Pill>
        <Pill tone="info">Out of scope: {outOfScope}</Pill>
      </Row>

      <Divider />

      <Stack gap={12}>
        <H2>Completion levels</H2>
        <Table
          headers={["Level", "Meaning", "Current verdict"]}
          columnAlign={["left", "left", "left"]}
          rows={[
            [
              "1. Strategy Core Complete",
              "Strategy-owned screens, rules, and services work with provider tests",
              "Met — Desk proven (STR-SUP-005)",
            ],
            [
              "2. Integration Ready",
              "Stable, tested contracts for Budget / Demand / Planning callers",
              "Met for Budget / Demand / Planning",
            ],
            [
              "3a. End-to-End Complete (B/D/P)",
              "Demand / Budget / Planning triggers wired and proven",
              "Met — XMOD-STR-001–004 / 006 / 007",
            ],
            [
              "3b. End-to-End Complete (+ Tender)",
              "Tender / Award carry Strategy Reference",
              "Not met — XMOD-STR-005 (consumer; does not block Strategy Core)",
            ],
          ]}
        />
      </Stack>

      <Divider />

      <Stack gap={12}>
        <H2>Condition classes (must stay separate)</H2>
        <Grid columns={3} gap={16}>
          <Card>
            <CardHeader trailing={<Pill tone="deleted">Class A</Pill>}>
              Strategy-owned missing
            </CardHeader>
            <CardBody>
              <Text size="small">
                Strategy-owned gaps that would reopen Core. Currently empty for MVP-1 handoff —
                residual AC/§12 polish is backlog only, not Class A blockers.
              </Text>
            </CardBody>
          </Card>
          <Card>
            <CardHeader trailing={<Pill tone="warning">Class B</Pill>}>
              Provider present — consumer incomplete
            </CardHeader>
            <CardBody>
              <Text size="small">
                Strategy contract exists; trigger module not yet wired (Tender/Award XMOD-STR-005,
                remediation UX XMOD-STR-008). Does not block Strategy Core move-on.
              </Text>
            </CardBody>
          </Card>
          <Card>
            <CardHeader trailing={<Pill tone="info">Class C</Pill>}>
              Future / out of scope
            </CardHeader>
            <CardBody>
              <Text size="small">
                National plan import, AI, formula engine, public portal, causal savings — intentionally
                excluded from MVP 1.
              </Text>
            </CardBody>
          </Card>
        </Grid>
      </Stack>

      <Divider />

      <Stack gap={12}>
        <H2>Capability classification (provider vs consumer vs external)</H2>
        <Text size="small" tone="secondary">
          Status column uses the mandatory delivery vocabulary. Counts above are derived from these
          rows.
        </Text>
        <Table
          headers={["Capability", "Condition class", "Delivery status", "Owner", "Notes"]}
          columnAlign={["left", "left", "left", "left", "left"]}
          rows={CAPABILITIES.map((c) => [
            c.capability,
            c.conditionClass,
            c.deliveryStatus,
            c.owner,
            c.note,
          ])}
        />
      </Stack>

      <Divider />

      <Stack gap={12}>
        <H2>Cross-module ownership model</H2>
        <Text size="small" tone="secondary">
          Every requirement has a trigger owner and a Strategy provider responsibility. Tracker IDs
          live in 08_Strategy_Cross_Module_Lifecycle_Tracker.md for later completion.
        </Text>
        <Table
          headers={[
            "Tracker ID",
            "Business event",
            "Trigger owner",
            "Strategy responsibility",
            "Delivery status",
          ]}
          columnAlign={["left", "left", "left", "left", "left"]}
          rows={OWNERSHIP.map((o) => [
            o.trackerId,
            o.event,
            o.trigger,
            o.strategy,
            o.deliveryStatus,
          ])}
        />
      </Stack>

      <Divider />

      <Stack gap={12}>
        <H2>Durable tracker (do not forget)</H2>
        <Callout tone="info" title="Where to continue this work">
          Cross-module rows XMOD-STR-001…009 and support gaps STR-SUP-* are maintained in
          apps/kentender_v1/docs/mvp-1/01_strategy/08_Strategy_Cross_Module_Lifecycle_Tracker.md.
          Each row includes service contract, preconditions, audit event, provider/consumer/E2E
          tests, and delivery status. Update that file when wiring lands — do not rely on chat
          memory.
        </Callout>
        <H3>Required fields per XMOD row</H3>
        <Text size="small">
          Requirement ID · Business event · Trigger module · Provider module · Service contract ·
          Preconditions · Idempotency key · Expected mutation · Failure result · Audit event ·
          Provider test · Consumer test · End-to-end test · Delivery status
        </Text>
      </Stack>

      <Divider />

      <Stack gap={12}>
        <H2>Screens vs lifecycle (UI live ≠ Done)</H2>
        <Table
          headers={["ID", "Surface", "Screen state", "Lifecycle implication", "Status"]}
          columnAlign={["left", "left", "left", "left", "left"]}
          rows={SURFACES.map((s) => [
            s.id,
            s.surface,
            s.screenState,
            s.lifecycleImplication,
            s.status,
          ])}
        />
      </Stack>

      <Divider />

      <Stack gap={12}>
        <H2>Gap register</H2>
        <Table
          headers={[
            "ID",
            "Severity",
            "Condition class",
            "Finding",
            "Delivery status",
            "Tracker",
          ]}
          columnAlign={["left", "left", "left", "left", "left", "left"]}
          rows={GAP_REGISTER.map((g) => [
            g.id,
            g.severity,
            g.conditionClass,
            g.finding,
            g.deliveryStatus,
            g.tracker,
          ])}
        />
      </Stack>

      <Divider />

      <Stack gap={12}>
        <H2>Acceptance criteria snapshot</H2>
        <Table
          headers={["ID", "Criterion", "Verdict", "Note"]}
          columnAlign={["left", "left", "left", "left"]}
          rows={AC_SNAPSHOT.map((a) => [a.id, a.criterion, a.verdict, a.note])}
        />
      </Stack>

      <Divider />

      <Stack gap={12}>
        <H2>Runtime tracking target</H2>
        <Card>
          <CardHeader>Strategy Reference + Audit + Usage read model</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text size="small">
                Authority remains Strategic Plan hierarchy, Plan Value Commitments, Performance
                Measurements, Strategy Corrective Actions, and Strategy Audit Event — not a separate
                journal DocType.
              </Text>
              <Text size="small">
                Downstream Usage and Strategy Performance must project from authoritative Strategy
                References stored by consumers (aligned field names), plus Strategy Audit Event for
                governance evidence. Seeded measurements/CAs ≠ consumer wiring.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Stack>

      <Divider />

      <Stack gap={12}>
        <H2>Next priorities</H2>
        <Stack gap={6}>
          <Text size="small">
            Forward-only until each row is End-to-end complete or Blocked. STR-SUP-005 is Desk proven — do
            not re-queue it.
          </Text>
          <Text size="small">1. XMOD-STR-005 Tender / Award Strategy Reference carry when TM consumers ready</Text>
          <Text size="small">
            2. Extend Downstream Usage / Performance for Tender/Contract/Asset/Disposal when those modules
            store Strategy Reference
          </Text>
          <Text size="small">3. XMOD-STR-008 consumer remediation UX for invalid / superseded refs</Text>
          <Text size="small">
            Parked: due/overdue job (XMOD-STR-009); STR-SUP-005 backlog stays on that tracker row only.
          </Text>
        </Stack>
      </Stack>

      <Callout tone="neutral" title="Delivery status vocabulary">
        Not started · Provider in progress · Provider complete — Desk proven · Provider complete —
        consumer pending · Consumer wired — end-to-end proof pending · End-to-end complete · Future
        external integration · Blocked · Out of scope · Closed (hygiene)
      </Callout>
    </Stack>
  );
}
