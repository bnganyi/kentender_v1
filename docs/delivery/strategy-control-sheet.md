Good. Here is the **master implementation control sheet** for the Strategy module.

This is the document you use to control Windsurf, not just prompt it.

**📘 Strategy Module — Master Implementation Control Sheet**

|     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| **Phase** | **Objective** | **Windsurf Prompt Scope** | **Deliverable** | **Manual Check** | **Smoke Test** | **Pass/Fail** |
| **0\. Environment & Baseline** | Create clean Strategy module baseline | Module namespace, placeholder workspace, basic roles, clean boot only | Placeholder Strategy workspace opens without errors | Can log in and open Strategy placeholder from normal navigation | Open workspace successfully |     |
| **1\. Workspace & Navigation** | Make Strategy discoverable | Strategy Management workspace, menu/sidebar entry, New Strategic Plan button, empty plan list area | User can navigate to Strategy and see entry UI | No CTRL+K needed, no dead links, buttons visible | Workspace opens and New Strategic Plan button is clickable |     |
| **2\. Strategic Plan Core Entity** | Create and save Strategic Plan header | Strategic Plan model/DocType, create/save/edit Draft plan only | Draft Strategic Plan can be created and appears in list | Save works, reload works, list shows plan correctly | Create draft plan and reopen it |     |
| **3\. Step-Based Builder Skeleton** | Replace raw form with guided shell | Header, stepper, Next/Back, step-based builder shell; Plan Info functional, later steps placeholders | Opening a plan shows builder instead of long form | Stepper visible, no giant scroll form, Next/Back works | Open plan and navigate across builder steps |     |
| **4\. Program Layer** | Add Program CRUD | Program model, Programs step table, modal/panel create-edit-delete | Programs can be created, edited, deleted under plan | Persist after reload, unique code enforced, table updates correctly | Create one Program and verify reload |     |
| **5\. Sub-program Layer** | Add Sub-program CRUD | Sub-program model, Sub-program table, linked Program selector, optional filter | Sub-programs can be created under Programs | Cannot create without Program, linkage visible, reload works | Create Program + Sub-program and reopen |     |
| **6\. Indicator Layer** | Add Output Indicator CRUD | Indicator model, Indicators table, link to Sub-program, unit field required | Indicators can be created under Sub-programs | Unit required, hierarchy consistent, no orphan indicators | Create full chain through Indicator |     |
| **7\. Target Layer** | Complete hierarchy with Targets | Performance Target model, Targets table, link to Indicator, numeric target validation | Full hierarchy can be created end-to-end | Target requires Indicator, numeric validation works, duplicates blocked | Create full chain through Target |     |
| **8\. Review & Validation Engine** | Make structure self-checking before submit | Review step, counts, issue list, blocking validation | User sees summary and cannot submit incomplete plan | Missing levels shown clearly, clicking issue helps navigate, no bypass | Try submitting incomplete plan and confirm block |     |
| **9\. Workflow (Plan Only)** | Add lifecycle and locking | Draft → Submitted → Approved → Active → Archived, lock by state | Plan lifecycle works and child editing locks correctly | Workflow visible in header, no editing after Submitted, Active is read-only | Submit, approve, activate one valid plan |     |
| **10\. Selector APIs** | Expose active strategy for downstream modules | Lightweight selector endpoints for active Programs, Sub-programs, Indicators, Targets | Downstream modules can fetch only Active strategy | Draft/Submitted/Archived not exposed, labels readable, no duplicates | Call selector endpoints and confirm only Active data returned |     |
| **11\. Smoke Tests** | Automate Strategy MVP sanity | Small deterministic smoke suite only | Core MVP flow covered by tests | Tests are reliable, failures are actionable | Run suite: workspace, create plan, build hierarchy, validate submit, activate, selectors |     |
| **12\. UX Polish Only** | Improve clarity without logic change | Labels, spacing, helper text, empty states, readability only | UI feels cleaner with no behavioral drift | All previous behavior unchanged, no scope creep | Re-run full smoke suite unchanged |     |

**Hard gating rules**

Do not move to the next phase unless all are true:

|     |     |
| --- | --- |
| **Gate** | **Rule** |
| Scope Gate | Windsurf only changed the requested phase scope |
| Usability Gate | Current phase can be demoed in under 2 minutes |
| Stability Gate | Reload/save/navigation still work |
| Regression Gate | Previous phase still works |
| Smoke Gate | Current applicable smoke check passes |

**Recommended phase checkpoints**

**After Phase 2**

You should already be able to say:

Strategy exists in navigation, and a Draft Strategic Plan can be created and reopened.

If not, stop.

**After Phase 3**

You should be able to say:

Opening a plan no longer feels like a raw ERP form.

If not, stop.

**After Phase 7**

You should be able to say:

A complete strategy hierarchy can be built end-to-end.

If not, stop.

**After Phase 9**

You should be able to say:

The module is structurally complete and governed.

If not, stop.

**Minimal smoke suite progression**

You do not need all smoke tests on day one.

|     |     |
| --- | --- |
| **By End of Phase** | **Required Smoke Coverage** |
| Phase 1 | Workspace opens |
| Phase 2 | Create and reopen Draft plan |
| Phase 4 | Add Program |
| Phase 7 | Build full hierarchy |
| Phase 8 | Incomplete plan blocked |
| Phase 9 | Submit → Approve → Activate |
| Phase 10 | Active selectors only |

**Suggested working rhythm**

Use this exact loop:

1\. Run one Windsurf phase prompt

2\. Manual check

3\. Fix only defects in that phase

4\. Run relevant smoke test

5\. Mark pass/fail

6\. Proceed only if passed

**Pass/fail decision template**

Use this after every phase:

**Phase:**

e.g. Phase 4 — Program Layer

**Expected:**

Programs can be created, edited, deleted under a plan

**Observed:**

What actually happened

**Pass?**

Yes / No

**If No:**

- navigation issue
- save/reload issue
- validation issue
- scope creep
- regression
- other

**Next Action:**

- fix within same phase
- do not proceed

**My recommendation for your actual start**

Start with this batch only:

- Phase 0
- Phase 1
- Phase 2

Then pause and review.

That is enough to tell you whether the new approach is working.

If you want, I’ll next turn this into a **copy-paste execution tracker markdown file** you can keep beside Windsurf while implementing.