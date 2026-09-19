# KenTender monorepo helpers — bench root: /home/midasuser/frappe-bench
# Default site matches sites/common_site_config.json → default_site

SITE ?= kentender.midas.com
BENCH_ROOT ?= /home/midasuser/frappe-bench
KENTENDER_APPS := kentender_core,kentender_strategy,kentender_budget,kentender_procurement,kentender_suppliers,kentender_governance,kentender_compliance,kentender_stores,kentender_assets,kentender_integrations,kentender_transparency,frontend,
INSTALL_ORDER := kentender_core kentender_strategy kentender_budget kentender_procurement kentender_suppliers kentender_governance kentender_compliance kentender_stores kentender_assets kentender_integrations kentender_transparency frontend

.PHONY: tenders-schema-gate tenders-services-gate ui-tenders-workspace-gate ui-tenders-start-gate ui-tenders-details-gate ui-tenders-requirements-gate ui-tenders-review-gate ui-tenders-approval-gate ui-tenders-authorisation-gate ui-tenders-publication-gate ui-tenders-published-gate ui-tenders-addendum-gate ui-tenders-cancel-gate ui-tenders-history-gate ui-tenders-fidelity-gate ui-tenders-release-evidence-gate ui-system-setup-procurement-settings-gate ui-system-setup-fiscal-years-gate ui-system-setup-access-gate help install install-one migrate build build-kentender clear restart doctor list symlinks validate-links smoke seed-canonical seed-canonical-dry-run seed-canonical-validate ui-smoke tender-templates-bundle-gate ui-workspace-pattern-gate ui-strategy-gate ui-strategy-fidelity-gate ui-stitch-desk-chrome-gate ui-industry-design-gate ui-system-setup-fidelity-gate ui-budget-fidelity-gate ui-budget-gate ui-create-demand-strategy-gate ui-civic-ledger-queue-gate ui-civic-ledger-ui01-gate ui-civic-ledger-cfg01-gate ui-civic-ledger-cfg02-gate ui-civic-ledger-cfg03-gate ui-civic-ledger-cfg04-gate ui-civic-ledger-cfg05-gate ui-civic-ledger-cfg06-gate ui-civic-ledger-cfg07-gate ui-civic-ledger-cfg08-gate ui-civic-ledger-cfg09-gate ui-civic-ledger-wg01-gate ui-civic-ledger-wg02-gate ui-civic-ledger-wg03-gate pub-domain-gate ui-publications-gate ui-demands-workspace-gate ui-planning-workspace-gate ui-planning-departmental-gate ui-planning-fidelity-gate ui-planning-release-evidence-gate ui-planning-annual-plan-gate ui-planning-item-gate ui-planning-finance-gate ui-planning-governance-gate ui-planning-publication-gate planning-requisition-gate planning-seed-gate ui-req-workspace-gate ui-req-start-gate ui-req-editor-a-gate ui-req-editor-b-gate ui-req-department-gate ui-req-procurement-gate ui-req-authorised-gate ui-req-fidelity-gate ui-req-release-evidence-gate ui-demands-form-gate ui-demands-review-gate ui-demands-detail-gate ui-demands-performance-gate demands-abs-gate bw-domain-gate bw-a0-domain-gate bw-a2-domain-gate bw-a3-domain-gate bw-a4-domain-gate bw-manifest-phase1-gate bw-manifest-phase2-gate bw-manifest-phase3-gate bw-manifest-phase4-gate bw-manifest-phase5-gate bw-manifest-phase2-reset bw-manifest-phase2-reseed ui-bidder-a0-gate ui-bidder-a1-gate ui-bidder-a2-gate ui-bidder-a3-gate ui-bidder-a4-gate bw-x100-domain-gate bw-s300-domain-gate ui-bidder-s300-cbq-gate bw-fot-domain-gate ui-bidder-fot-gate bw-statutory-domain-gate ui-bidder-statutory-gate bw-tender-security-domain-gate ui-bidder-tender-security-gate bw-preliminary-domain-gate ui-bidder-preliminary-gate tm2-v1-contamination-audit p11-04-tm2-surface-gate p11-05-tm2-surface-legacy-literal-gate p12-01-scenario-harness x-01-planning-std-poc-gate x-02-no-plain-bench-build-gate x-03-doc9-acceptance-sequence-gate vue-desk-bundle-translation-binding-gate e1-nssf-seed-gate e1-nssf-poc-gate seed-stable-platform seed-stable-platform-reset seed-stable-platform-validate seed-demand-to-bidder-journey
.PHONY:

help:
	@echo "Targets:"
	@echo "  make install SITE=$(SITE)     — install-app all KenTender apps in order"
	@echo "  make install-one APP=...      — install-app single app"
	@echo "  make migrate SITE=$(SITE)"
	@echo "  make build — desk assets via the bench-root scripts/bench-with-node.sh (Node ≥24; see AGENTS.md §4.1)"
	@echo "  make build-kentender — all KenTender apps via the same wrapper"
	@echo "  make clear SITE=$(SITE)"
	@echo "  make restart"
	@echo "  make doctor"
	@echo "  make list SITE=$(SITE)"
	@echo "  make symlinks"
	@echo "  make validate-links"
	@echo "  make smoke SITE=$(SITE) — guard_frappe_scaffolds + Wave 0 smoke tests"
	@echo "  make tm2-v1-contamination-audit SITE=$(SITE) — P11-03 static scan + catalogue (kentender_procurement)"
	@echo "  make p11-04-tm2-surface-gate SITE=$(SITE) — P11-04 TM2 paths must not get_doc/new_doc Procurement Tender"
	@echo "  make p11-05-tm2-surface-legacy-literal-gate SITE=$(SITE) — P11-05 TM2 paths + v2 desk JS must not quote Procurement Tender"
	@echo "  make p12-01-scenario-harness SITE=$(SITE) — P12-01 doc 7 §2 scenario catalog + S01–S13 stub test modules"
	@echo "  make x-01-planning-std-poc-gate SITE=$(SITE) — X-01 planning + STD POC regression slice (tender-management §X)"
	@echo "  make x-02-no-plain-bench-build-gate — X-02 tender-management prompts must not document bare bench asset build (doc 9 §3.1)"
	@echo "  make x-03-doc9-acceptance-sequence-gate — X-03 doc 9 §23.4 KenTender acceptance runbook markers (doc + audit)"
	@echo "  make vue-desk-bundle-translation-binding-gate SITE=$(SITE) — every Vue-in-Desk bundle using __() in templates binds globalProperties.__ (AGENTS.md §6.1)"
	@echo "  make ui-queue-check [FIX=1] — background-job queue depth; a full queue breaks every fixture reset and teardown and reports it as a misleading NameError (AGENTS.md §8.1)"
	@echo "  make ui-smoke — Phase La: npm run test:ui:smoke (needs Node, running site, apps/kentender_v1/.env.ui)"
	@echo "  make ui-workspace-pattern-gate — workspace contract tests (selection, scroll, anti-flicker)"
	@echo "  make ui-strategy-gate — STR-CHG-001 v1.8 §16.2 browser journeys (author, approver, access states) on the §14 profiles"
	@echo "  make ui-strategy-fidelity-gate — Strategy screens match the v1.8 STR-DES artboards: landmark order measured from the artboard render (FU-01)"
	@echo "  make ui-stitch-desk-chrome-gate — Shared Stitch Desk chrome baseline (Win98/select/Espresso) — required before Stitch Desk UI Done"
	@echo "  make ui-industry-design-gate — Industry design system is canonical (AGENTS.md §6.6): kt-industry root class + no forked token files + computed-style parity"
	@echo "  make ui-system-setup-fidelity-gate — System setup screens match their .dc.html artboards: landmark order + geometry measured from the artboard render"
	@echo "  make ui-system-setup-procurement-settings-gate — PLN-CHG-001 v1.18 C01–C04: System setup component tests + the Procurement settings browser spec (Administrator + refused business user), test funding source purged after"
	@echo "  make ui-system-setup-fiscal-years-gate — CFG-CHG-002 v0.11 C02: Financial years cross-year replacement, expiry and stale-write recovery browser specs"
	@echo "  make ui-system-setup-access-gate — CFG-CHG-002 v0.11 §6/§11.1: who may use System setup, the refusal state, sub-path durability, narrow/200% and keyboard focus"
	@echo "  make ui-budget-fidelity-gate — BUD-CHG-001 v1.9: Budget & Funding screens match their reconciled .dc.html boards, state by state (landmark order)"
	@echo "  make ui-budget-gate — BUD-CHG-001 v1.9: the five Budget browser journeys (workspace, officer, approver, closure, access), single worker"
	@echo "  make ui-create-demand-strategy-gate — (retired) DIA create-demand gate; no-op until Demands MVP-1"
	@echo "  make ui-civic-ledger-queue-gate — Civic Ledger queue/list contract (chrome, filters, table footer)"
	@echo "  make ui-civic-ledger-ui01-gate — UI-01 home structural layout + mockup states"
	@echo "  make ui-civic-ledger-cfg01-gate — CFG-01 Tender Profile strip/form/Continue gate"
	@echo "  make ui-civic-ledger-cfg02-gate — CFG-02 Tender Data Sheet strip/form/Continue gate"
	@echo "  make ui-civic-ledger-cfg03-gate — CFG-03 IT Requirements table/drawer/Continue gate"
	@echo "  make ui-civic-ledger-cfg04-gate — CFG-04 Implementation Schedule approach/table/Continue gate"
	@echo "  make ui-civic-ledger-cfg05-gate — CFG-05 System Inventory table/drawer/Continue gate"
	@echo "  make ui-civic-ledger-cfg06-gate — CFG-06 Price Schedule tabs/table/drawer/Continue gate"
	@echo "  make ui-civic-ledger-cfg07-gate — CFG-07 Evaluation Setup tabs/table/drawer/Continue gate"
	@echo "  make ui-civic-ledger-cfg08-gate — CFG-08 Forms & Evidence filters/table/drawer/Continue gate"
	@echo "  make ui-civic-ledger-cfg09-gate — CFG-09 Contract Values tabs/table/drawer/Run Check gate"
	@echo "  make ui-civic-ledger-wg01-gate — WG-01 Readiness Check summary/findings/submit gate"
	@echo "  make ui-civic-ledger-wg02-gate — WG-02 Review & Approval checklist/decision gate"
	@echo "  make ui-civic-ledger-wg03-gate — WG-03 Document Preview (document artifact path) gate"
	@echo "  make pub-domain-gate SITE=$(SITE) — Tender Publications domain API tests"
	@echo "  make ui-publications-gate — Publications A1/A2/A3 Playwright smoke"
	@echo "  make ui-demands-workspace-gate — Demands workspace (DEM-UI-01) API + Playwright"
	@echo "  make ui-planning-workspace-gate — PLN-CHG-001 v1.18 PLN18-302: U01 workspace domain + vitest + Playwright (D13 world)"
	@echo "  make ui-planning-departmental-gate — PLN-CHG-001 v1.18 PLN18-303: U02-U06 Departmental preparation/certification/validation domain + vitest + Playwright"
	@echo "  make ui-planning-annual-plan-gate — PLN-CHG-001 v1.18 PLN18-304: U07 Annual Plan (5-tab) + U08 Form Plan Items domain + vitest + Playwright"
	@echo "  make ui-planning-item-gate — PLN-CHG-001 v1.18 PLN18-305: U09 Plan Item editor domain + vitest + Playwright (incl. stale-save race)"
	@echo "  make ui-planning-fidelity-gate — PLN-CHG-001 v1.12 D14: artboard landmark fidelity on the live screens"
	@echo "  make ui-planning-release-evidence-gate — PLN-CHG-001 v1.12 Phase 8: every Planning browser spec + fidelity + §14 persona pass, single-worker"
	@echo "  make ui-planning-plan-workbench-gate — PLN-CHG-001 v1.2 Slice D: Annual Plan workbench + formation + Plan Item editor"
	@echo "  make ui-planning-finance-gate — PLN-CHG-001 v1.18 PLN18-306: U10 Finance task (confirm/return/reassess/history) domain + vitest + Playwright"
	@echo "  make ui-planning-governance-gate — PLN-CHG-001 v1.2 Slice F: Annual Plan governance (adopt/approve/return)"
	@echo "  make ui-planning-publication-gate — PLN-CHG-001 v1.2 Slice G: Publication, Active and successor (BeginPlanUpdate/RemovePlanItemInSuccessor/CancelPlanUpdate)"
	@echo "  make planning-requisition-gate — PLN-CHG-001 v1.2 Slice H: §7.4 Requisition eligibility + drawdown consumption (API-only)"
	@echo "  make planning-seed-gate — PLN-CHG-001 v1.2 §14: deterministic seed contract (baseline + profiles + boundary guard)"
	@echo "  make tenders-services-gate SITE=$(SITE) — TPR-CHG-001 v0.8 Phases 4–6: every Tenders service test module"
	@echo "  make tenders-schema-gate SITE=$(SITE) — TPR-CHG-001 v0.8 Phase 2: Tenders schema, envelope, authorization, gateway-contract and core file-integrity tests"
	@echo "  make ui-tenders-<slice>-gate — TPR-CHG-001 v0.8 Phase 7 slice gates: workspace start details requirements review approval authorisation publication published addendum cancel history (vitest project tenders + the slice's Playwright spec on the Tenders Playwright world, then restore_site)"
	@echo "  make ui-tenders-fidelity-gate — TPR-CHG-001 v0.8: every TPR-DES board's landmarks in order on the live screen"
	@echo "  make ui-tenders-release-evidence-gate — TPR-CHG-001 v0.8 Phase 9: every Tenders browser spec + fidelity + persona pass"
	@echo "  make tender-templates-bundle-gate SITE=$(SITE) — TPR-CHG-001 v0.6 Phase 3: IT-EQUIPMENT-OPEN-V1 1.1 bundle loader, registry and renderer tests"
	@echo "  make ui-req-workspace-gate — REQ-CHG-001 v1.6 Slice 3a: Requisitions workspace (REQ-DES-01) + Playwright (REQ-402 world)"
	@echo "  make ui-req-start-gate — REQ-CHG-001 v1.6 Slice 3b: Start Requisition (REQ-DES-02)"
	@echo "  make ui-req-editor-a-gate — REQ-CHG-001 v1.6 Slice 3c-i: Editor steps 1-2 (REQ-DES-03/04)"
	@echo "  make ui-req-editor-b-gate — REQ-CHG-001 v1.6 Slice 3c-ii: Editor steps 3-5 (REQ-DES-05/06/07)"
	@echo "  make ui-req-department-gate — REQ-CHG-001 v1.6 Slice 3d: Department approval task (REQ-DES-08)"
	@echo "  make ui-req-procurement-gate — REQ-CHG-001 v1.6 Slice 3e: Procurement authorisation task (REQ-DES-09)"
	@echo "  make ui-req-authorised-gate — REQ-CHG-001 v1.6 Slice 3f: Authorised Requisition + revoke (REQ-DES-10)"
	@echo "  make ui-req-fidelity-gate — REQ-CHG-001 v1.6: artboard landmark fidelity on the live screens"
	@echo "  make ui-req-release-evidence-gate — REQ-CHG-001 v1.6 Phase 5: every Requisitions browser spec + fidelity + §16 persona pass, single-worker"
	@echo "  make — PLN-GATE-C01 scope + task authority + route denial"
	@echo "  make ui-demands-form-gate — Demand form (DEM-UI-02/03) API + Playwright"
	@echo "  make ui-demands-review-gate ui-demands-detail-gate — Demand review chrome gate + DEM-UI-04…08 API + Playwright"
	@echo "  make ui-demands-detail-gate — Approved Demand detail (DEM-UI-09…09D) API + Playwright"
	@echo "  make ui-demands-performance-gate — Demand performance (DEM-UI-10) API + Playwright"
	@echo "  make demands-abs-gate — DEM-ABS-001…012 legacy absence evidence"
	@echo "  make bw-domain-gate SITE=$(SITE) — Bidder workspace A1 domain API tests"
	@echo "  make bw-a0-domain-gate SITE=$(SITE) — Available Tenders (A0) domain tests"
	@echo "  make bw-a2-domain-gate SITE=$(SITE) — Submission Checklist (A2) domain + web route tests"
	@echo "  make bw-a3-domain-gate SITE=$(SITE) — Tender Documents & Addenda (A3) domain + web route tests"
	@echo "  make bw-a4-domain-gate SITE=$(SITE) — Requirement Matrix (A4) domain + web route tests"
	@echo "  make bw-manifest-phase1-gate SITE=$(SITE) — G1 Phase 1 BWMF schemas + NSSF fixture errata"
	@echo "  make bw-manifest-phase2-gate SITE=$(SITE) — G1 Phase 2 schema preflight + persistence"
	@echo "  make bw-manifest-phase3-gate SITE=$(SITE) — G1 Phase 3 deterministic BWMF compiler"
	@echo "  make bw-manifest-phase4-gate SITE=$(SITE) — G1 Phase 4 content-addressed resources"
	@echo "  make bw-manifest-phase5-gate SITE=$(SITE) — G1 Phase 5 governance and atomic publication"
	@echo "  make bw-manifest-phase2-reset SITE=$(SITE) — clear BWMF persistence rows"
	@echo "  make bw-manifest-phase2-reseed SITE=$(SITE) — clear + seed BWMF canonical fixture"
	@echo "  make ui-bidder-a0-gate — A0 Available Tenders Website Playwright smoke"
	@echo "  make ui-bidder-a1-gate — Bidder A1 Published Tender Overview Playwright smoke"
	@echo "  make ui-bidder-a2-gate — A2 Submission Checklist Website Playwright smoke"
	@echo "  make ui-bidder-a3-gate — A3 Tender Documents & Addenda Website Playwright smoke"
	@echo "  make ui-bidder-a4-gate — A4 Requirement Matrix Website Playwright smoke"
	@echo "  make bw-fot-domain-gate SITE=$(SITE) — FoT Review-and-Certify domain + order tests"
	@echo "  make ui-bidder-fot-gate — FoT Review-and-Certify Website Playwright smoke"
	@echo "  make bw-statutory-domain-gate SITE=$(SITE) — Statutory Declarations domain + web tests"
	@echo "  make ui-bidder-statutory-gate — Statutory Declarations Website Playwright smoke"
	@echo "  make bw-tender-security-domain-gate SITE=$(SITE) — Tender Security domain tests"
	@echo "  make ui-bidder-tender-security-gate — Tender Security Website Playwright smoke"
	@echo "  make bw-preliminary-domain-gate SITE=$(SITE) — Preliminary Requirements domain tests"
	@echo "  make ui-bidder-preliminary-gate — Preliminary Requirements Website Playwright smoke"
	@echo "  make bw-qualification-domain-gate SITE=$(SITE) — Qualification and Capability domain tests"
	@echo "  make ui-bidder-qualification-gate — Qualification and Capability Website Playwright smoke"
	@echo "  make bw-technical-proposal-domain-gate SITE=$(SITE) — Technical Proposal domain + layout guard"
	@echo "  make ui-bidder-technical-proposal-gate — Technical Proposal Website Playwright smoke"
	@echo "  make bw-requirements-compliance-domain-gate SITE=$(SITE) — Requirements Compliance domain + layout guard"
	@echo "  make ui-bidder-requirements-compliance-gate — Requirements Compliance Website Playwright smoke"
	@echo "  make bw-price-schedule-domain-gate SITE=$(SITE) — Price Schedule domain + layout guard"
	@echo "  make ui-bidder-price-schedule-gate — Price Schedule Website Playwright smoke"
	@echo "  make bw-final-submission-domain-gate SITE=$(SITE) — Final Submission domain + layout + stitch contracts"
	@echo "  make bw-final-submission-stitch-contract-gate SITE=$(SITE) — Final Submission per-Stitch-file UI contracts (01–05)"
	@echo "  make ui-bidder-final-submission-gate — Final Submission Website Playwright smoke (modal structure)"
	@echo "  make e1-nssf-seed-gate SITE=$(SITE) — E1 NSSF seed mapper + preview (subset)"
	@echo "  make e1-nssf-poc-gate SITE=$(SITE) — full E1 PoC: seed + bid APIs + Playwright bidder workspace"
	@echo "  make seed-canonical SITE=$(SITE) [THROUGH=requisitions] [WIPE=True] [FORCE=True] — clear every non-canonical row, then reseed KT-STD-001 §8 configuration + SEED-001 modules progressively (site → strategy → budget → needs → planning → requisitions) and validate; WIPE=True also drops and rebuilds the site stage itself (needs FORCE=True outside developer_mode)"
	@echo "  make seed-canonical-dry-run SITE=$(SITE) — report what seed-canonical would remove, delete nothing"
	@echo "  make seed-canonical-validate SITE=$(SITE) [THROUGH=requisitions] — validate the canonical world only"
	@echo "  make seed-kentender-mvp-v1 SITE=$(SITE) — fixture-scoped reset + full KENTENDER_MVP_V1 seed + Playwright purge + validate"
	@echo "  make seed-kentender-mvp-v1-validate SITE=$(SITE) — validate full KENTENDER_MVP_V1 stack"
	@echo "  make purge-kentender-playwright-data SITE=$(SITE) — remove owned Playwright/Gate fixtures without deleting canonical or business records"
	@echo "  make purge-erpnext-test-fixtures SITE=$(SITE) — remove ERPNext's own _Test Fiscal Year residue (not KenTender seed data)"
	@echo "  make seed-moh-mvp-v1 SITE=$(SITE) — deprecated alias → seed-kentender-mvp-v1"
	@echo "  make seed-stable-platform SITE=$(SITE) — load MOH stable platform seed (Works + IT STD)"
	@echo "  make seed-stable-platform-reset SITE=$(SITE) — clear + reload stable platform seed"
	@echo "  make seed-demand-to-bidder-journey SITE=$(SITE) — quiet Demand→CFG→bidder sample"
	@echo "  make seed-stable-platform-validate SITE=$(SITE) — validate stable platform seed only"
	@echo "  make seed-demo-platform-reset SITE=$(SITE) — clean PEs + linked IT STD demo platform seed"
	@echo "  make seed-demo-platform-validate SITE=$(SITE) — validate demo platform seed only"

install:
	@for app in $(INSTALL_ORDER); do \
		echo "Installing $$app on $(SITE)"; \
		cd $(BENCH_ROOT) && bench --site $(SITE) install-app $$app || exit 1; \
	done

install-one:
	@test -n "$(APP)" || (echo "Usage: make install-one APP=kentender_core SITE=..." && exit 1)
	cd $(BENCH_ROOT) && bench --site $(SITE) install-app $(APP)

migrate:
	cd $(BENCH_ROOT) && bench --site $(SITE) migrate

build:
	cd $(BENCH_ROOT) && ./scripts/bench-with-node.sh build

build-kentender:
	cd $(BENCH_ROOT) && ./scripts/bench-with-node.sh build --apps $(KENTENDER_APPS)

clear:
	cd $(BENCH_ROOT) && bench --site $(SITE) clear-cache && bench --site $(SITE) clear-website-cache

restart:
	cd $(BENCH_ROOT) && bench restart

doctor:
	cd $(BENCH_ROOT) && bench doctor

# The background-job queue this bench never drains on its own. Every fixture
# reset enqueues jobs; past Frappe's ceiling every reset and teardown fails,
# and `bench execute` reports that as a misleading NameError. The UI suites
# check this automatically (tests/ui/globalSetup.ts); this is the same check
# by hand, and `FIX=1` drains it.
ui-queue-check:
	node tests/ui/helpers/queueCheck.cjs $(if $(FIX),--fix,)

list:
	cd $(BENCH_ROOT) && bench --site $(SITE) list-apps

symlinks:
	cd $(BENCH_ROOT)/apps && \
	ln -sfn kentender_v1/kentender_core kentender_core && \
	ln -sfn kentender_v1/kentender_strategy kentender_strategy && \
	ln -sfn kentender_v1/kentender_budget kentender_budget && \
	ln -sfn kentender_v1/kentender_procurement kentender_procurement && \
	ln -sfn kentender_v1/kentender_governance kentender_governance && \
	ln -sfn kentender_v1/kentender_compliance kentender_compliance && \
	ln -sfn kentender_v1/kentender_stores kentender_stores && \
	ln -sfn kentender_v1/kentender_assets kentender_assets && \
	ln -sfn kentender_v1/kentender_integrations kentender_integrations && \
	ln -sfn kentender_v1/kentender_suppliers kentender_suppliers && \
	ln -sfn kentender_v1/kentender_transparency kentender_transparency && \
	ln -sfn kentender_v1/apps/frontend frontend

validate-links:
	@test -L $(BENCH_ROOT)/apps/kentender_core
	@test -L $(BENCH_ROOT)/apps/kentender_strategy
	@test -L $(BENCH_ROOT)/apps/kentender_budget
	@test -L $(BENCH_ROOT)/apps/kentender_procurement
	@test -L $(BENCH_ROOT)/apps/kentender_governance
	@test -L $(BENCH_ROOT)/apps/kentender_compliance
	@test -L $(BENCH_ROOT)/apps/kentender_stores
	@test -L $(BENCH_ROOT)/apps/kentender_assets
	@test -L $(BENCH_ROOT)/apps/kentender_integrations
	@test -L $(BENCH_ROOT)/apps/kentender_suppliers
	@test -L $(BENCH_ROOT)/apps/kentender_transparency
	@test -L $(BENCH_ROOT)/apps/frontend
	@echo "All KenTender symlinks look present."

smoke:
	cd $(BENCH_ROOT) && python3 apps/kentender_v1/scripts/guard_frappe_scaffolds.py
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_core --module kentender_core.tests.test_wave0_smoke

ui-smoke:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npm run test:ui:smoke

# DIA workspace pattern lock retired with Demand Intake teardown (Demands MVP-1 pending).
# Civic Ledger queue pattern is covered by ui-civic-ledger-queue-gate.
ui-workspace-pattern-gate:
	@echo "ui-workspace-pattern-gate: DIA pattern lock retired — no-op (see Demands MVP-1 teardown inventory)."

# Fast gate for Strategy CSS/chrome/typography work (Desk Espresso bleed, shared plan header).
ui-strategy-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/strategy/strategy-author.spec.ts \
		tests/ui/smoke/strategy/strategy-approver.spec.ts \
		tests/ui/smoke/strategy/strategy-access.spec.ts

# FU-01 — the Strategy screens against the v1.8 STR-DES artboards.
ui-strategy-fidelity-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/strategy/strategy-fidelity.spec.ts

# Shared Stitch Desk chrome baseline — must stay green for Strategy/Budget/… canvases.
ui-stitch-desk-chrome-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_core.tests.test_stitch_desk_chrome_gate
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/stitch-desk/stitch-desk-chrome.spec.ts

# Industry design system is canonical (AGENTS.md §6.6) — every Vue-in-Desk page
# root wraps class="kt-industry" (or is on the gate's own legacy allowlist), no
# app forks a competing token file, and pages that claim .kt-industry actually
# render identical computed tokens (not just a same-named class).
ui-industry-design-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_core.tests.test_industry_design_gate
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/industry-design/industry-design-gate.spec.ts

# Design fidelity (AGENTS.md §6.6 enforcement) — every System setup screen is
# diffed against its .dc.html artboard rendered in the same browser: the
# artboard's ordered structural landmarks must appear in order in the live
# page, and geometry measured off the artboard (column ratios, row heights,
# 520px dialogs, grid label columns, truncation of named fixture text) must
# match within tolerance. Seeds the KT-STD §8 world first (idempotent).
ui-system-setup-fidelity-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.site_setup.run
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/design-fidelity/system-setup-fidelity.spec.ts

# PLN-CHG-001 v1.18 §10.11 C01–C04 (tracker PLN18-106) — the System setup
# component suite plus the Procurement settings browser journey; the spec's
# one test funding source is purged afterwards.
ui-system-setup-procurement-settings-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project system-setup
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.site_setup.run
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/system_setup/procurement-settings.spec.ts; status=$$?; \
		cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.services.procurement_settings.purge_playwright_funding_sources; exit $$status

# CFG-CHG-002 v0.11 §10.3 (tracker CFG11-302) — the Financial years browser
# journeys not covered by the fidelity gate: cross-year replacement (reads
# the live canonical years, submits nothing), expiry and a stale-write
# recovery (both on isolated far-future years via reset_fiscal_year_edge_cases,
# never the canonical open year every other module's fixtures depend on).
ui-system-setup-fiscal-years-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.site_setup.run
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.playwright_ui_fixtures.reset_fiscal_year_edge_cases
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/system_setup/system-setup-fiscal-years.spec.ts; status=$$?; \
		cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.tests.responsibility_test_cleanup.purge; exit $$status

# CFG-CHG-002 v0.11 §6/§11.1 (tracker CFG11-308) — access and the shared
# states: a business user is refused with an explanation, every tab resolves
# to content, a sub-path survives reload and back, all three intake
# activities stay readable at 400px and 200% text scale, and the keyboard
# reaches the primary action. Read-only; nothing is written.
ui-system-setup-access-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.site_setup.run
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/system_setup/system-setup-access.spec.ts

# BUD-CHG-001 v1.3 Phase 8 (BUD-802) — Budget & Funding screens match their
# .dc.html artboards. Seeds via a piped `exec(open(...).read())` rather than
# raw stdin: budget_fidelity_seed.py lives under tests/ui/smoke/design-
# fidelity/ (not inside any installed app's Python package, so `bench
# execute <dotted.path>` cannot import it), and plain `bench console < file`
# silently mishandles multi-statement scripts with blank lines inside
# indented blocks (IPython's own stdin cell-splitting) — see that file's own
# top comment.
ui-budget-fidelity-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/design-fidelity/budget-fidelity.spec.ts

# BUD-CHG-001 v1.9 — the five Budget browser journeys (workspace states, Officer
# register/edit/submit, Approver decision-first review, year-end closure,
# access/technical read). Fixtures reset per spec through
# kentender_budget.seeds.playwright_ui_fixtures; single worker — every spec
# mutates the one canonical budget.
ui-budget-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/budget/budget-workspace.spec.ts \
		tests/ui/smoke/budget/budget-officer.spec.ts \
		tests/ui/smoke/budget/budget-approver.spec.ts \
		tests/ui/smoke/budget/budget-closure.spec.ts \
		tests/ui/smoke/budget/budget-access.spec.ts

# XMOD-STR-002 / 003 — create-demand Strategy target + PVC Review E2E.
# Retired with DIA preparatory teardown; Demands MVP-1 will restore a successor gate.
ui-create-demand-strategy-gate:
	@echo "ui-create-demand-strategy-gate: create-demand / DIA retired — no-op (Demands MVP-1 pending)."

ui-civic-ledger-queue-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/kt-cl-queue-pattern-lock.spec.ts \
		tests/ui/smoke/publications/a2-publications-queue.spec.ts

ui-civic-ledger-ui01-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/ui01-layout-contract.spec.ts \
		tests/ui/smoke/it-std-wizard/ui01-home.spec.ts \
		tests/ui/smoke/it-std-wizard/ui01-mockup-states.spec.ts

ui-civic-ledger-cfg01-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/cfg01-tender-profile.spec.ts

ui-civic-ledger-cfg02-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/cfg02-tender-data-sheet.spec.ts

ui-civic-ledger-cfg03-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/cfg03-it-requirements.spec.ts

ui-civic-ledger-cfg04-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/cfg04-implementation-schedule.spec.ts

ui-civic-ledger-cfg05-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/cfg05-system-inventory.spec.ts

ui-civic-ledger-cfg06-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/cfg06-price-schedule.spec.ts

ui-civic-ledger-cfg07-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/cfg07-evaluation-setup.spec.ts

ui-civic-ledger-cfg08-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/cfg08-forms-and-evidence.spec.ts

ui-civic-ledger-cfg09-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/cfg09-contract-values.spec.ts

ui-civic-ledger-wg01-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/wg01-readiness.spec.ts

ui-civic-ledger-wg02-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/wg02-review.spec.ts

ui-civic-ledger-wg03-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/wg03-document-preview.spec.ts

pub-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_publication_setup_api

ui-publications-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/publications/a1-package-review.spec.ts \
		tests/ui/smoke/publications/a2-publications-queue.spec.ts \
		tests/ui/smoke/publications/a3-publication-setup.spec.ts

ui-demands-workspace-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_procurement.demands.tests.test_demands_workspace_api
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/demands/demands-workspace.spec.ts

# PLN-CHG-001 v1.18 — Phase 2 exit (PLN18-213): the whole Planning-owned
# Python domain suite (every services/schema test, discovered dynamically —
# new test files are picked up without editing this target), including the
# rule-3 removed-concept scan (test_planning_v123_schema). Each test class's
# own addClassCleanup(fx.restore_site) restores intake flags and wipes test
# rows; the cross-module checkpoint (core, budget, NDS, strategy, REQ, TPR)
# has no single shared gate across apps and is run as the sibling modules'
# own suites (see the tracker's PLN18-213 evidence for the exact list).
# test_planning_seed is included again: PLN-CHG-001 v1.23 repaired the seed
# onto the asynchronous publication pipeline, so it is an ordinary regression.
planning-domain-gate:
	cd $(BENCH_ROOT) && for m in $$(cd apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/tests && ls test_*.py | sed 's/\.py$$//'); do \
		bench --site $(SITE) run-tests --app kentender_procurement --module kentender_procurement.procurement_planning.tests.$$m || exit 1; done

# PLN18-302 — U01 Workspace + U21 Common States (PLN-CHG-001 v1.18 Phase 3A).
# Supersedes the v1.12 gate of the same name: `planning-workspace.spec.ts` is
# retired for `pln-workspace.spec.ts` (this row's own testids); fidelity for
# U01/U21 lives in the shared `ui-planning-fidelity-gate`, not duplicated here.
ui-planning-workspace-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.procurement_planning.tests.test_planning_workspace
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project procurement-planning
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/planning/pln-workspace.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures.restore_site

# PLN18-303 (PLN-CHG-001 v1.18 Phase 3B) — U02-U06 Departmental preparation,
# certification and validation. Supersedes the v1.12 ui-planning-dpp-gate and
# ui-planning-dpp-review-gate (both retired with this row, same as the v1.12
# planning-dpp.spec.ts / planning-dpp-review.spec.ts they ran): one gate
# across all three DPP domain modules and the one dedicated spec that
# replaces both retired Playwright files.
ui-planning-departmental-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.procurement_planning.tests.test_dpp_lifecycle
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.procurement_planning.tests.test_dpp_read
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.procurement_planning.tests.test_dpp_validation
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project procurement-planning
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/planning/pln-departmental.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures.restore_site

# PLN-CHG-001 v1.12 Phase 8 — release evidence: every Planning browser spec
# single-worker on the D13 world, the fidelity spec, and the §14 persona pass
# (which skips itself with the exact missing prerequisite while FU-10/FU-11
# are open), then the intake flags restored.
ui-planning-release-evidence-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project procurement-planning
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/planning \
		tests/ui/smoke/design-fidelity/planning-fidelity.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures.restore_site

# PLN-CHG-001 v1.23 — every artboard panel's landmarks, in order, on the live
# screen (AGENTS.md §6.6), on the Playwright world. Rewritten for v1.23: the
# design files are one labelled panel per variant, indexed by `openPanel`.
ui-planning-fidelity-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/design-fidelity/planning-fidelity.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures.restore_site

# PLN18-304 (PLN-CHG-001 v1.18 Phase 3C) — U07 Annual Plan (5-tab screen:
# overview/items/funding/governance/changes) and U08 Form Plan Items.
# Supersedes the v1.12 ui-planning-plan-workbench-gate (retired with this row,
# same as the planning-plan-workbench.spec.ts it ran): the Plan Item editor
# (U09) is PLN18-305's own row, not this one.
ui-planning-annual-plan-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.procurement_planning.tests.test_plan_workbench
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project procurement-planning
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/planning/pln-annual-plan.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures.restore_site

# PLN18-305 (PLN-CHG-001 v1.18 Phase 3D) — U09 Plan Item editor: five
# sections ported from the frame, method-condition Declaration evidence, the
# live baseline recalculation. Supersedes no dedicated v1.12 gate (the old
# stale-save spec ran only inside `ui-planning-release-evidence-gate`'s own
# directory-wide glob); `planning-plan-item-stale-save.spec.ts` is retired
# for `pln-item.spec.ts`, which carries that same regression test forward.
ui-planning-item-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.procurement_planning.tests.test_plan_workbench
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project procurement-planning
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/planning/pln-item.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures.restore_site

# PLN18-306 (PLN-CHG-001 v1.18 Phase 3E) — U10 Finance task: plan funding
# confirmation over Budget's real affordability contract (no reservation),
# the funding evidence history (U10-history) and Active-Version reassessment
# (U10-reassess-return — the same U10 route, §9's own table names only one).
# Supersedes the v1.12 gate of the same name: `planning-finance.spec.ts` is
# retired for `pln-finance.spec.ts` (this row's own testids and the two new
# reassessment/history-carrying tests).
ui-planning-finance-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.procurement_planning.tests.test_plan_finance
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project procurement-planning
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/planning/pln-finance.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures.restore_site

# PLN-CHG-001 v1.12 Slice C — Annual Plan governance (PLN-UI-11/12).
ui-planning-governance-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.procurement_planning.tests.test_plan_governance
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project procurement-planning
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/planning/planning-governance.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures.restore_site

# PLN-CHG-001 v1.12 Slice D — Active plan, cascade reforecast and publication
# (PLN-UI-13/14).
ui-planning-publication-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.procurement_planning.tests.test_plan_publication
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project procurement-planning
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/planning/planning-publication.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures.restore_site

# PLN-CHG-001 v1.2 Slice H — §7.4 Requisition eligibility (API-only, no UI):
# GetRequisitionEligiblePlanItem.v2 + drawdown/reversal consumption, incl.
# the request-shaped journey; contract tests only per the tracker.
planning-requisition-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.procurement_planning.tests.test_plan_requisition
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.procurement_planning.tests.test_planning_v118_schema

# PLN-CHG-001 v1.2 §14 (Phase 11) — the deterministic Planning seed:
# prerequisites, actors, the integrated baseline through real commands,
# isolated profiles, idempotent rerun, and the boundary guard that keeps the
# seed itself on the published Needs contracts.
planning-seed-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.procurement_planning.tests.test_planning_seed
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.departmental_needs.tests.test_departmental_needs_architecture

# TPR-CHG-001 v0.6 — Tender Preparation Python gates.
tenders-schema-gate:
	cd $(BENCH_ROOT) && for m in test_tender_schema test_envelope test_tender_authorization test_gateway_contracts; do \
		bench --site $(SITE) run-tests --app kentender_procurement --module kentender_procurement.tenders.tests.$$m || exit 1; done
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_core --module kentender_core.tests.test_file_integrity

tenders-services-gate:
	cd $(BENCH_ROOT) && for m in $$(cd apps/kentender_v1/kentender_procurement/kentender_procurement/tenders/tests && ls test_*.py | sed 's/\.py$$//'); do \
		bench --site $(SITE) run-tests --app kentender_procurement --module kentender_procurement.tenders.tests.$$m || exit 1; done

tender-templates-bundle-gate:
	cd $(BENCH_ROOT) && for m in test_loader test_registry test_renderer; do \
		bench --site $(SITE) run-tests --app kentender_procurement --module kentender_procurement.tender_templates.tests.$$m || exit 1; done

# REQ-CHG-001 v1.6 — Procurement Requisitions slice gates (tracker rule 6).
# Each gate runs the shared vitest project (component tests aren't split per
# screen), the slice's own Playwright spec on the REQ-402 world, and restores
# the site's DPP intake flag afterward. The Python service suite (REQ-G02) is
# proven once, module by module, not repeated per UI slice.
ui-req-workspace-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project procurement-requisitions
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/requisitions/requisitions-workspace.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.procurement_requisitions.seeds.playwright_ui_fixtures.restore_site

ui-req-start-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project procurement-requisitions
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/requisitions/requisitions-start.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.procurement_requisitions.seeds.playwright_ui_fixtures.restore_site

ui-req-editor-a-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project procurement-requisitions
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/requisitions/requisitions-editor-drawdown-items.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.procurement_requisitions.seeds.playwright_ui_fixtures.restore_site

ui-req-editor-b-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project procurement-requisitions
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/requisitions/requisitions-editor-review.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.procurement_requisitions.seeds.playwright_ui_fixtures.restore_site

ui-req-department-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project procurement-requisitions
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/requisitions/requisitions-department-task.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.procurement_requisitions.seeds.playwright_ui_fixtures.restore_site

ui-req-procurement-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project procurement-requisitions
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/requisitions/requisitions-procurement-task.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.procurement_requisitions.seeds.playwright_ui_fixtures.restore_site

ui-req-authorised-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project procurement-requisitions
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/requisitions/requisitions-authorised.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.procurement_requisitions.seeds.playwright_ui_fixtures.restore_site

# REQ-CHG-001 v1.6 — every artboard's landmarks in order on the live screen
# (AGENTS.md §6.6), on the REQ-402 world.
ui-req-fidelity-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/design-fidelity/requisitions-fidelity.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.procurement_requisitions.seeds.playwright_ui_fixtures.restore_site

# REQ-CHG-001 v1.6 Phase 5 — release evidence: every Requisitions browser
# spec single-worker on the REQ-402 world, the fidelity spec, and the §16
# persona pass (skips itself with the exact missing prerequisite if the
# canonical MOH seed is not built), then the intake flag restored.
ui-req-release-evidence-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project procurement-requisitions
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/requisitions \
		tests/ui/smoke/design-fidelity/requisitions-fidelity.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.procurement_requisitions.seeds.playwright_ui_fixtures.restore_site


# TPR-CHG-001 v0.8 — Tenders slice gates (tracker rule 6 / plan §8). Each
# gate runs the vitest project, the slice's Playwright spec single-worker on
# the Tenders Playwright world (which extends the Requisitions one), and
# restores the site afterward. Python gates are proven once per module.
ui-tenders-workspace-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project tenders
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/tenders/tnd-workspace.spec.ts tests/ui/smoke/tenders/tnd-common-states.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.tenders.seeds.playwright_ui_fixtures.restore_site

ui-tenders-start-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project tenders
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/tenders/tnd-start.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.tenders.seeds.playwright_ui_fixtures.restore_site

ui-tenders-details-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project tenders
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/tenders/tnd-editor-details.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.tenders.seeds.playwright_ui_fixtures.restore_site

ui-tenders-requirements-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project tenders
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/tenders/tnd-editor-requirements.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.tenders.seeds.playwright_ui_fixtures.restore_site

ui-tenders-review-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project tenders
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/tenders/tnd-review.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.tenders.seeds.playwright_ui_fixtures.restore_site

ui-tenders-approval-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project tenders
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/tenders/tnd-approval.spec.ts tests/ui/smoke/tenders/tnd-correction.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.tenders.seeds.playwright_ui_fixtures.restore_site

ui-tenders-authorisation-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project tenders
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/tenders/tnd-authorisation.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.tenders.seeds.playwright_ui_fixtures.restore_site

ui-tenders-publication-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project tenders
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/tenders/tnd-publication.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.tenders.seeds.playwright_ui_fixtures.restore_site

ui-tenders-published-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project tenders
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/tenders/tnd-published.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.tenders.seeds.playwright_ui_fixtures.restore_site

ui-tenders-addendum-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project tenders
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/tenders/tnd-addendum.spec.ts tests/ui/smoke/tenders/tnd-inquiry.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.tenders.seeds.playwright_ui_fixtures.restore_site

ui-tenders-cancel-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project tenders
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/tenders/tnd-cancel.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.tenders.seeds.playwright_ui_fixtures.restore_site

ui-tenders-history-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project tenders
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/tenders/tnd-history.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.tenders.seeds.playwright_ui_fixtures.restore_site

ui-tenders-fidelity-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/design-fidelity/tenders-fidelity.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.tenders.seeds.playwright_ui_fixtures.restore_site

ui-tenders-release-evidence-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx vitest run --project tenders
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/tenders \
		tests/ui/smoke/design-fidelity/tenders-fidelity.spec.ts
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_procurement.tenders.seeds.playwright_ui_fixtures.restore_site

ui-demands-form-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_procurement.demands.tests.test_demands_form_api
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/demands/demand-form.spec.ts

ui-demands-review-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_procurement.demands.tests.test_demands_review_chrome_gate
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_procurement.demands.tests.test_demands_review_api
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_procurement.demands.tests.test_demands_enrichment_api
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_procurement.demands.tests.test_demands_budget_api
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_procurement.demands.tests.test_demands_final_approval_api
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/demands/business-review.spec.ts \
		tests/ui/smoke/demands/procurement-enrichment.spec.ts \
		tests/ui/smoke/demands/budget-confirm.spec.ts \
		tests/ui/smoke/demands/budget-exception.spec.ts \
		tests/ui/smoke/demands/final-approval.spec.ts

ui-demands-detail-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_procurement.demands.tests.test_demands_detail_api
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/demands/approved-detail.spec.ts

ui-demands-performance-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_procurement.demands.tests.test_demand_performance
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/demands/demand-performance.spec.ts

demands-abs-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_procurement.demands.tests.test_demands_mvp1_legacy_absence

bid-submissions-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bid_submissions_api

ui-bid-submissions-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bid-submissions/officer-bid-submissions.spec.ts

bw-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_published_tender_overview_api

bw-a0-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_available_tenders_api
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_published_tender_overview_web

ui-bidder-a0-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/a0-available-tenders.spec.ts

ui-bidder-a1-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/a1-published-tender-overview.spec.ts

bw-a2-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_submission_checklist_api
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_submission_checklist_web

ui-bidder-a2-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/a2-submission-checklist.spec.ts

bw-a3-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_tender_documents_addenda_api
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_tender_documents_addenda_web
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bidder_presentation_boundary

ui-bidder-a3-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/a3-documents-addenda.spec.ts

bw-x100-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_x100_evidence_and_issues

bw-s300-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_s300_confidential_business_questionnaire

ui-bidder-s300-cbq-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/s300-cbq.spec.ts

bw-fot-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_fot_review_certify
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_f0_foundation

ui-bidder-fot-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/fot-review-certify.spec.ts

bw-statutory-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_statutory_declarations

ui-bidder-statutory-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/statutory-declarations.spec.ts

bw-tender-security-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_tender_security

ui-bidder-tender-security-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/tender-security.spec.ts

bw-preliminary-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_preliminary_requirements

ui-bidder-preliminary-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/preliminary-requirements.spec.ts

bw-qualification-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_qualification_and_capability
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_qualification_stitch_layout_guard

ui-bidder-qualification-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 --retries=0 \
		tests/ui/smoke/bidder-workspace/qualification-and-capability.spec.ts

bw-technical-proposal-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_technical_proposal
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_technical_proposal_stitch_layout_guard

ui-bidder-technical-proposal-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 --retries=0 \
		tests/ui/smoke/bidder-workspace/technical-proposal.spec.ts

bw-requirements-compliance-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_requirements_compliance
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_requirements_compliance_stitch_layout_guard

ui-bidder-requirements-compliance-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 --retries=0 \
		tests/ui/smoke/bidder-workspace/requirements-compliance.spec.ts

bw-price-schedule-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_price_schedule
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_price_schedule_stitch_layout_guard

ui-bidder-price-schedule-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 --retries=0 \
		tests/ui/smoke/bidder-workspace/price-schedule.spec.ts

bw-final-submission-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_final_submission_readiness
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_final_submission_stitch_layout_guard
	$(MAKE) bw-final-submission-stitch-contract-gate SITE=$(SITE)

.PHONY: bw-final-submission-stitch-contract-gate
bw-final-submission-stitch-contract-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bidder_stitch_contract_gate

ui-bidder-final-submission-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 --retries=0 \
		tests/ui/smoke/bidder-workspace/final-submission.spec.ts

bw-a4-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_requirement_matrix_api
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_requirement_matrix_web

ui-bidder-a4-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/a4-requirement-matrix.spec.ts

bw-manifest-phase1-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_schema_conformance_phase1
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_nssf_fixture_errata_phase1

bw-manifest-phase2-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_schema_preflight_phase2
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_persistence_phase2
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_persistence_phase2b
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_persistence_phase2c

bw-manifest-phase3-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_compiler_phase3
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_compile_service_phase3

bw-manifest-phase4-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_resource_oracle_phase4
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_resource_verifier_phase4a
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_materialize_phase4

bw-manifest-phase5-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_governance_phase5

bw-manifest-phase2-reset:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_procurement.tender_configurations.seed.bwmf_canonical_fixture.clear_bwmf_canonical_fixture

bw-manifest-phase2-reseed:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_procurement.tender_configurations.seed.bwmf_canonical_fixture.seed_bwmf_canonical_fixture

ui-std-config-gate:
	@echo "STD Module POC archived (2026-07). Use: make verify-std-archived && npm run test:ui:smoke:std-module-retired"
	@exit 1

verify-std-archived:
	chmod +x $(BENCH_ROOT)/apps/kentender_v1/scripts/verify-std-archived.sh
	$(BENCH_ROOT)/apps/kentender_v1/scripts/verify-std-archived.sh

ui-std-module-retired-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npm run test:ui:smoke:std-module-retired

tm2-v1-contamination-audit:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_management.tests.test_p11_03_tm2_v1_contamination_audit

p11-04-tm2-surface-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_management.tests.test_p11_04_tm2_surface_no_procurement_tender

p11-05-tm2-surface-legacy-literal-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_management.tests.test_p11_05_tm2_surface_no_procurement_tender_literal

p12-01-scenario-harness:
	SITE=$(SITE) $(BENCH_ROOT)/scripts/p12_01_tm2_works_scenario_harness.sh

x-01-planning-std-poc-gate:
	SITE=$(SITE) $(BENCH_ROOT)/scripts/x_01_planning_std_poc_regression_gate.sh

x-02-no-plain-bench-build-gate:
	$(BENCH_ROOT)/scripts/x_02_tender_management_docs_no_plain_bench_build_gate.sh

x-03-doc9-acceptance-sequence-gate:
	$(BENCH_ROOT)/scripts/x_03_doc9_section_23_4_acceptance_sequence_gate.sh

vue-desk-bundle-translation-binding-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_core \
		--module kentender_core.tests.test_vue_desk_bundle_translation_binding_gate

e1-nssf-seed-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_e1_nssf_fixture_mapper
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_e1_nssf_seed

e1-nssf-poc-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_preview_presentation
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_e1_nssf_fixture_mapper
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_schema_compiler
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_e1_nssf_seed
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_electronic_bid_submission
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/e1-bidder-workspace.spec.ts

# Canonical world (KT-STD-001 §8 + SEED-001), progressive by module stage.
# THROUGH: site | strategy | budget | needs | planning | requisitions (later stages are added as they land).
# WIPE=True also drops the site stage itself (Procuring Entity, Organisation
# Units, Fiscal Years, actors) before rebuilding from nothing — see
# docs/mvp-1-r1/00_common/KenTender_SEED-OPS-001_*.md §4. FORCE=True bypasses
# every module seed's own developer_mode/allow_tests guard, required for WIPE
# outside developer_mode. RESEED defaults to None (Python-literal, not a
# string) so canonical.run() picks its own default: reseed immediately for
# a plain reset/rebuild, but WIPE=True alone now means what "wipe" says —
# clear and stop, empty database. Pass RESEED=True to also force the old
# "wipe then immediately rebuild everything" behaviour. All three must stay
# Python-literal True/False/None, not JSON true/false/null.
THROUGH ?= requisitions
WIPE ?= False
FORCE ?= False
RESEED ?= None
# Make variables are case-sensitive: `force=True`/`wipe=True`/`through=budget`
# on the command line silently set a DIFFERENT variable from FORCE/WIPE/
# THROUGH above and are otherwise ignored - a very natural mistake since
# it matches the Python kwarg names exactly. Accept the lowercase spelling
# as an alias, command-line value wins either way.
ifdef through
THROUGH := $(through)
endif
ifdef wipe
WIPE := $(wipe)
endif
ifdef force
FORCE := $(force)
endif
ifdef reseed
RESEED := $(reseed)
endif
seed-canonical:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_core.seeds.canonical.run \
		--kwargs '{"through": "$(THROUGH)", "reset": True, "wipe": $(WIPE), "reseed": $(RESEED), "force": $(FORCE), "validate": True}'

seed-canonical-dry-run:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_core.seeds.canonical.dry_run

seed-canonical-validate:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_core.seeds.canonical.validate --kwargs '{"through": "$(THROUGH)"}'

seed-kentender-mvp-v1:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_core.seeds.kentender_mvp_v1.orchestrator.run_kentender_mvp_v1 \
		--kwargs '{"reset": True, "force": True, "validate": True}'

seed-kentender-mvp-v1-validate:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_core.seeds.kentender_mvp_v1.orchestrator.validate_kentender_mvp_v1

purge-kentender-playwright-data:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_core.seeds.kentender_mvp_v1.clear.purge_kentender_playwright_data

# Not KenTender seed data — ERPNext's own `_Test Fiscal Year %` residue from
# running ERPNext's Python test suite on this site. canonical.py's wipe
# deliberately never touches these (SEED-OPS-001 §3.2); this is separate.
purge-erpnext-test-fixtures:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_core.tests.erpnext_test_fixture_cleanup.purge

# Deprecated aliases (one cycle).
seed-moh-mvp-v1: seed-kentender-mvp-v1

seed-moh-mvp-v1-validate: seed-kentender-mvp-v1-validate

seed-stable-platform:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.seed_stable_platform.run

seed-stable-platform-reset:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.seed_stable_platform.run --kwargs '{"reset": true}'

seed-stable-platform-validate:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.seed_stable_platform.validate

seed-demand-to-bidder-journey:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_procurement.tender_configurations.seed.demand_to_bidder_journey_sample.run

seed-demo-platform:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.seed_demo_platform.run --kwargs '{"reset": false}'

seed-demo-platform-reset:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.seed_demo_platform.run --kwargs '{"reset": true}'

seed-demo-platform-validate:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.seed_demo_platform.validate
