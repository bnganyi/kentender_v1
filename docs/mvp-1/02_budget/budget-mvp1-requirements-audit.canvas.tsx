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
 * Budget MVP-1 requirements audit (revised).
 * Plain-text Status/Severity/Verdict columns so summary counts stay traceable.
 * Cross-module work is tracked in:
 * apps/kentender_v1/docs/mvp-1/02_budget/04_Budget_Cross_Module_Lifecycle_Tracker.md
 */

type Tone = "neutral" | "success" | "warning" | "info" | "deleted";

const DELIVERY = {
  notStarted: "Not started",
  providerInProgress: "Provider in progress",
  providerDoneConsumerPending: "Provider complete — consumer pending",
  consumerWiredE2EPending: "Consumer wired — end-to-end proof pending",
  e2eComplete: "End-to-end complete",
  futureExternal: "Future external integration",
  blocked: "Blocked",
  outOfScope: "Out of scope",
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
    capability: "check_funding",
    conditionClass: "Provider present — consumer evidence",
    deliveryStatus: DELIVERY.consumerWiredE2EPending,
    tone: "warning",
    owner: "Budget / Demand",
    note: "Provider tests exist; Demand readiness calls check_available_budget — strengthen E2E proof",
  },
  {
    capability: "reserve_funding",
    conditionClass: "Provider present — consumer proof incomplete",
    deliveryStatus: DELIVERY.consumerWiredE2EPending,
    tone: "warning",
    owner: "Budget / Demand",
    note: "create_reservation invoked from Demand lifecycle; formal E2E still pending",
  },
  {
    capability: "release_reservation",
    conditionClass: "Budget-owned incomplete + consumer coverage",
    deliveryStatus: DELIVERY.providerInProgress,
    tone: "warning",
    owner: "Budget / Demand (+ later owners)",
    note: "DIA adapter + some Demand cancel paths; promote stable budget_api + non-Demand owners",
  },
  {
    capability: "revalidate_reservation",
    conditionClass: "Budget-owned capability missing",
    deliveryStatus: DELIVERY.notStarted,
    tone: "deleted",
    owner: "Budget → Planning / Tender / Award",
    note: "Provider missing; all consumers pending",
  },
  {
    capability: "convert_reservation",
    conditionClass: "Budget-owned capability missing",
    deliveryStatus: DELIVERY.notStarted,
    tone: "deleted",
    owner: "Budget → Contract Management",
    note: "Seeded Partially converted ≠ conversion workflow",
  },
  {
    capability: "adjust_commitment",
    conditionClass: "Budget-owned capability missing",
    deliveryStatus: DELIVERY.notStarted,
    tone: "deleted",
    owner: "Budget → Contract Management",
    note: "Variation consumer pending after provider exists",
  },
  {
    capability: "sync_expenditure (internal)",
    conditionClass: "Budget-owned capability missing",
    deliveryStatus: DELIVERY.notStarted,
    tone: "deleted",
    owner: "Budget",
    note: "Internal ingestion + stale/unavailable handling required in MVP 1 via fixtures",
  },
  {
    capability: "Live finance-system connector",
    conditionClass: "Future external integration",
    deliveryStatus: DELIVERY.futureExternal,
    tone: "info",
    owner: "Finance integration",
    note: "Out of MVP 1 live connector scope; do not block internal sync_expenditure contract",
  },
  {
    capability: "close_budget",
    conditionClass: "Budget-owned capability missing",
    deliveryStatus: DELIVERY.notStarted,
    tone: "deleted",
    owner: "Budget",
    note: "Closed seed row ≠ close workflow",
  },
  {
    capability: "Notifications and work queue",
    conditionClass: "Budget-owned capability missing",
    deliveryStatus: DELIVERY.notStarted,
    tone: "deleted",
    owner: "Budget",
    note: "REQ §14 workflow support",
  },
  {
    capability: "Role-based browser evidence",
    conditionClass: "Test gap",
    deliveryStatus: DELIVERY.notStarted,
    tone: "warning",
    owner: "Budget QA",
    note: "All budget-funding Playwright specs use Administrator",
  },
  {
    capability: "Parallel oversubscription protection",
    conditionClass: "Test / evidence gap",
    deliveryStatus: DELIVERY.providerDoneConsumerPending,
    tone: "info",
    owner: "Budget",
    note: "Idempotency covered; parallel stress matrix incomplete",
  },
  {
    capability: "Route registry and documentation hygiene",
    conditionClass: "Implementation hygiene",
    deliveryStatus: DELIVERY.notStarted,
    tone: "warning",
    owner: "Budget / platform",
    note: "kt_module_registry prefixes; teardown §6 text; cursor pack pointer",
  },
];

const OWNERSHIP: {
  event: string;
  trigger: string;
  budget: string;
  trackerId: string;
  deliveryStatus: string;
  tone: Tone;
}[] = [
  {
    event: "Check funding while preparing a Demand",
    trigger: "Demand",
    budget: "Validate funding without mutation",
    trackerId: "XMOD-BUD-001",
    deliveryStatus: DELIVERY.consumerWiredE2EPending,
    tone: "warning",
  },
  {
    event: "Approve a Demand",
    trigger: "Demand",
    budget: "Atomically create the reservation",
    trackerId: "XMOD-BUD-002",
    deliveryStatus: DELIVERY.consumerWiredE2EPending,
    tone: "warning",
  },
  {
    event: "Move into Planning",
    trigger: "Planning",
    budget: "Revalidate and inherit the same reservation",
    trackerId: "XMOD-BUD-004",
    deliveryStatus: DELIVERY.notStarted,
    tone: "deleted",
  },
  {
    event: "Create/configure a Tender",
    trigger: "Tender",
    budget: "Carry and revalidate the same reservation",
    trackerId: "XMOD-BUD-005",
    deliveryStatus: DELIVERY.notStarted,
    tone: "deleted",
  },
  {
    event: "Financially clear an Award",
    trigger: "Award",
    budget: "Revalidate funding against the proposed award",
    trackerId: "XMOD-BUD-006",
    deliveryStatus: DELIVERY.notStarted,
    tone: "deleted",
  },
  {
    event: "Activate a Contract",
    trigger: "Contract Management",
    budget: "Convert reservation into commitment",
    trackerId: "XMOD-BUD-007",
    deliveryStatus: DELIVERY.notStarted,
    tone: "deleted",
  },
  {
    event: "Approve a contract variation",
    trigger: "Contract Management",
    budget: "Adjust commitment after funding validation",
    trackerId: "XMOD-BUD-008",
    deliveryStatus: DELIVERY.notStarted,
    tone: "deleted",
  },
  {
    event: "Cancel or reduce downstream work",
    trigger: "Owning downstream module",
    budget: "Release the authorised amount",
    trackerId: "XMOD-BUD-003",
    deliveryStatus: DELIVERY.providerInProgress,
    tone: "warning",
  },
  {
    event: "Receive expenditure information",
    trigger: "Finance integration",
    budget: "Store read-only snapshot and detect exceptions",
    trackerId: "XMOD-BUD-009",
    deliveryStatus: DELIVERY.notStarted,
    tone: "deleted",
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
    id: "BUD-UI-01",
    surface: "Budget Portfolio",
    screenState: "Live Desk + gates",
    lifecycleImplication: "Does not prove reservation/commitment lifecycle",
    status: "Budget core — strong UI",
    tone: "success",
  },
  {
    id: "Register",
    surface: "Register Approved Budget",
    screenState: "Live Desk + gates",
    lifecycleImplication: "Baseline capture only",
    status: "Budget core — strong UI",
    tone: "success",
  },
  {
    id: "BUD-UI-02",
    surface: "Funding Performance",
    screenState: "Live Desk + export",
    lifecycleImplication: "Read model; sync_expenditure still missing",
    status: "Partial — UI ahead of ingestion",
    tone: "warning",
  },
  {
    id: "BUD-UI-03",
    surface: "Budget Overview",
    screenState: "Live + anti-flash chrome",
    lifecycleImplication: "Workspace shell only",
    status: "Budget core — strong UI",
    tone: "success",
  },
  {
    id: "BUD-UI-04/05",
    surface: "Lines + Line Editor",
    screenState: "Live Desk + gates",
    lifecycleImplication: "Active immutability is service-enforced",
    status: "Budget core — strong UI",
    tone: "success",
  },
  {
    id: "BUD-UI-06",
    surface: "Check & Reserve",
    screenState: "Modal + thin Desk host",
    lifecycleImplication: "Provider path exists; E2E Demand proof pending",
    status: "Partial — provider/consumer",
    tone: "warning",
  },
  {
    id: "BUD-UI-07",
    surface: "Funding Activity",
    screenState: "Live read projection",
    lifecycleImplication: "Seeded Partially converted ≠ convert_reservation",
    status: "Partial — projection only",
    tone: "warning",
  },
  {
    id: "BUD-UI-08/09",
    surface: "Revisions + Review",
    screenState: "Live Desk + gates",
    lifecycleImplication: "Budget-owned revision spine present",
    status: "Budget core — strong UI",
    tone: "success",
  },
  {
    id: "BUD-UI-10",
    surface: "Downstream Usage",
    screenState: "Live read projection",
    lifecycleImplication: "Lineage display ≠ Award/Contract mutations",
    status: "Partial — projection only",
    tone: "warning",
  },
  {
    id: "BUD-UI-11",
    surface: "Readiness / Review",
    screenState: "Live Desk + gates",
    lifecycleImplication: "Activation path present; close_budget missing",
    status: "Budget core — strong UI",
    tone: "success",
  },
  {
    id: "BUD-UI-12",
    surface: "Audit History",
    screenState: "Live read projection",
    lifecycleImplication: "Cannot audit events that have no runtime writer",
    status: "Partial — projection only",
    tone: "warning",
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
    severity: "Critical",
    conditionClass: "Hygiene / authority",
    finding:
      "prompts/budget tracker still claims B0–B6 Done for torn-down UX; teardown §6 still says rebuild not implemented",
    deliveryStatus: DELIVERY.notStarted,
    tone: "deleted",
    tracker: "BUD-SUP-006/007",
  },
  {
    id: "G-02",
    severity: "Critical",
    conditionClass: "Budget-owned capability missing",
    finding:
      "revalidate_reservation, convert_reservation, adjust_commitment, close_budget have no provider implementations",
    deliveryStatus: DELIVERY.notStarted,
    tone: "deleted",
    tracker: "XMOD-BUD-004…008, 010",
  },
  {
    id: "G-03",
    severity: "Critical",
    conditionClass: "Budget-owned capability missing",
    finding:
      "Internal sync_expenditure contract missing; do not confuse with future live finance connector",
    deliveryStatus: DELIVERY.notStarted,
    tone: "deleted",
    tracker: "XMOD-BUD-009",
  },
  {
    id: "G-04",
    severity: "High",
    conditionClass: "Provider present — consumer proof incomplete",
    finding:
      "Demand invokes check/create/release via DIA adapter; formal E2E and stable Budget API surface still incomplete",
    deliveryStatus: DELIVERY.consumerWiredE2EPending,
    tone: "warning",
    tracker: "XMOD-BUD-001…003",
  },
  {
    id: "G-05",
    severity: "High",
    conditionClass: "Budget-owned capability missing",
    finding: "Notifications / work queue (REQ §14) not present",
    deliveryStatus: DELIVERY.notStarted,
    tone: "warning",
    tracker: "BUD-SUP-001",
  },
  {
    id: "G-06",
    severity: "High",
    conditionClass: "Test gap",
    finding: "Role-based browser evidence missing (Administrator-only Playwright)",
    deliveryStatus: DELIVERY.notStarted,
    tone: "warning",
    tracker: "BUD-SUP-002",
  },
  {
    id: "G-07",
    severity: "Medium",
    conditionClass: "Fixture hygiene",
    finding:
      "Canonical working fixture settled as MOH-BUD-0001 family; REQ §15 aliases need a future doc reconcile",
    deliveryStatus: DELIVERY.notStarted,
    tone: "info",
    tracker: "Fixture note in tracker",
  },
  {
    id: "G-08",
    severity: "Medium",
    conditionClass: "Future external integration",
    finding: "Live IFMIS/finance connector intentionally unavailable in MVP 1",
    deliveryStatus: DELIVERY.futureExternal,
    tone: "info",
    tracker: "XMOD-BUD-009 (external half)",
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
    id: "BUD-AC-001",
    criterion: "Direct-capture Draft without calculated totals",
    verdict: "Likely met (Budget core)",
    tone: "success",
    note: "Register + domain tests — UI live ≠ full module Done",
  },
  {
    id: "BUD-AC-008/009/013",
    criterion: "Non-mutating check; idempotent reserve; insufficient blocks",
    verdict: "Provider likely met",
    tone: "success",
    note: "E2E Demand proof still pending",
  },
  {
    id: "BUD-AC-010/011/014",
    criterion: "Inheritance; partial multi-commit; variation adjust",
    verdict: "Not met",
    tone: "deleted",
    note: "Provider services missing — not a consumer-only gap",
  },
  {
    id: "BUD-AC-015–017",
    criterion: "Active immutability; revision floor; apply preserves identities",
    verdict: "Mostly met (Budget core)",
    tone: "success",
    note: "Service-level evidence",
  },
  {
    id: "BUD-AC-018/019",
    criterion: "Segregation + entity permissions",
    verdict: "Partial",
    tone: "warning",
    note: "Domain tests partial; role UI evidence missing",
  },
  {
    id: "BUD-AC-020",
    criterion: "Actual expenditure read-only; stale ≠ zero",
    verdict: "Partial",
    tone: "warning",
    note: "Display cues exist; internal sync contract missing",
  },
  {
    id: "BUD-AC-024–026",
    criterion: "MOH fixtures; no obsolete formulas; Stitch screens",
    verdict: "Partial / mostly met UI",
    tone: "info",
    note: "Screens ≠ lifecycle complete",
  },
];

export default function BudgetMvp1RequirementsAudit() {
  const coreStrong = SURFACES.filter((s) => s.tone === "success").length;
  const uiPartial = SURFACES.filter((s) => s.tone === "warning").length;
  const notStarted = CAPABILITIES.filter((c) => c.deliveryStatus === DELIVERY.notStarted).length;
  const e2ePending = CAPABILITIES.filter(
    (c) => c.deliveryStatus === DELIVERY.consumerWiredE2EPending,
  ).length;
  const futureExt = CAPABILITIES.filter((c) => c.deliveryStatus === DELIVERY.futureExternal).length;
  const criticalGaps = GAP_REGISTER.filter((g) => g.severity === "Critical").length;

  return (
    <Stack gap={24} style={{ padding: 24, maxWidth: 1240 }}>
      <Stack gap={8}>
        <H1>Budget & Funding — MVP-1 audit (revised)</H1>
        <Text tone="secondary">
          Screens are substantially implemented; the Budget lifecycle is not yet complete. Three
          conditions are tracked separately: Budget-owned missing, provider present but consumer
          incomplete, and future external integration.
        </Text>
        <Text tone="secondary" size="small">
          Authority: docs/mvp-1/02_budget · Durable tracker:
          04_Budget_Cross_Module_Lifecycle_Tracker.md · Fixture canonical: MOH-BUD-0001 · Updated 6
          Aug 2026
        </Text>
      </Stack>

      <Callout tone="warning" title="Central conclusion">
        Budget core UI/services are largely present, but MVP-1 is not Integration Ready or
        End-to-End Complete. Do not treat a live screen, a seeded status (e.g. Partially converted),
        or a historical prompts/budget “Done” row as lifecycle completion.
      </Callout>

      <Grid columns={4} gap={16}>
        <Stat value={String(coreStrong)} label="Screens strong (UI/core)" tone="success" />
        <Stat value={String(uiPartial)} label="Screens partial (projection)" tone="warning" />
        <Stat value={String(notStarted)} label="Capabilities not started" tone="danger" />
        <Stat value={String(criticalGaps)} label="Critical gap rows" tone="danger" />
      </Grid>

      <Row gap={8} wrap>
        <Pill tone="warning">E2E proof pending: {e2ePending}</Pill>
        <Pill tone="info">Future external: {futureExt}</Pill>
        <Pill tone="neutral">No single “Implemented” flag</Pill>
      </Row>

      <Divider />

      <Stack gap={12}>
        <H2>Completion levels</H2>
        <Table
          headers={["Level", "Meaning", "Current verdict"]}
          columnAlign={["left", "left", "left"]}
          rows={[
            [
              "1. Budget Core Complete",
              "Budget-owned screens, rules, and services work",
              "Substantially approaching — not signed off",
            ],
            [
              "2. Integration Ready",
              "Stable, tested contracts for downstream callers",
              "Not ready",
            ],
            [
              "3. End-to-End Complete",
              "Demand / Planning / Tender / Award / Contract triggers wired and proven",
              "Not complete",
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
              Budget-owned missing
            </CardHeader>
            <CardBody>
              <Text size="small">
                Provider service/rules absent in Budget (revalidate, convert, adjust, close,
                internal sync_expenditure, notifications).
              </Text>
            </CardBody>
          </Card>
          <Card>
            <CardHeader trailing={<Pill tone="warning">Class B</Pill>}>
              Provider present — consumer incomplete
            </CardHeader>
            <CardBody>
              <Text size="small">
                Budget contract exists; trigger module not fully wired or E2E-proven (check/reserve
                Demand path today).
              </Text>
            </CardBody>
          </Card>
          <Card>
            <CardHeader trailing={<Pill tone="info">Class C</Pill>}>
              Future external integration
            </CardHeader>
            <CardBody>
              <Text size="small">
                Intentionally unavailable in MVP 1 (live finance connector). Internal snapshot
                contract remains in-scope.
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
          headers={[
            "Capability",
            "Condition class",
            "Delivery status",
            "Owner",
            "Notes",
          ]}
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
          Every requirement has a trigger owner and a Budget provider responsibility. Tracker IDs
          live in 04_Budget_Cross_Module_Lifecycle_Tracker.md for later completion.
        </Text>
        <Table
          headers={[
            "Tracker ID",
            "Business event",
            "Trigger owner",
            "Budget responsibility",
            "Delivery status",
          ]}
          columnAlign={["left", "left", "left", "left", "left"]}
          rows={OWNERSHIP.map((o) => [
            o.trackerId,
            o.event,
            o.trigger,
            o.budget,
            o.deliveryStatus,
          ])}
        />
      </Stack>

      <Divider />

      <Stack gap={12}>
        <H2>Durable tracker (do not forget)</H2>
        <Callout tone="info" title="Where to continue this work">
          Cross-module rows XMOD-BUD-001…010 and support gaps BUD-SUP-* are maintained in
          apps/kentender_v1/docs/mvp-1/02_budget/04_Budget_Cross_Module_Lifecycle_Tracker.md. Each
          row includes service contract, idempotency, audit event, provider/consumer/E2E tests, and
          delivery status. Update that file when wiring lands — do not rely on chat memory.
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
          headers={[
            "ID",
            "Surface",
            "Screen state",
            "Lifecycle implication",
            "Status",
          ]}
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
          <CardHeader>Single Funding Activity lifecycle journal</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text size="small">
                Record correlation/idempotency key, Budget/Line, downstream reference, event type,
                amount/currency, previous→resulting state, triggering module, actor/system,
                timestamp, success/rejection/exception, reason and approval reference.
              </Text>
              <Text size="small">
                Funding Activity, Downstream Usage, and Audit History must be projections of this
                journal — not separate truth stores.
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
            1. Lifecycle service spine (provider): revalidate, stable release, convert, adjust,
            internal sync_expenditure, close_budget
          </Text>
          <Text size="small">
            2. Wire each owning downstream module and update XMOD delivery statuses in the durable
            tracker
          </Text>
          <Text size="small">
            3. Add provider + consumer + end-to-end evidence; keep live finance connector tagged
            Future external integration
          </Text>
        </Stack>
      </Stack>

      <Callout tone="neutral" title="Delivery status vocabulary">
        Not started · Provider in progress · Provider complete — consumer pending · Consumer wired —
        end-to-end proof pending · End-to-end complete · Future external integration · Blocked · Out
        of scope
      </Callout>
    </Stack>
  );
}
