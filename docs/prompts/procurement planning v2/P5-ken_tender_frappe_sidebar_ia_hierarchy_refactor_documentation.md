# KenTender Frappe Sidebar IA Hierarchy Refactor Documentation

This document captures the full research-based recommendation for implementing the Procurement Planning information architecture inside the Frappe / ERPNext Desk sidebar.

The target IA is:

```text
Procurement
├── Procurement Home
├── Procurement Journeys
├── Strategy Alignment
├── Budget & Funding
├── Demand Intake & Approval
├── Procurement Planning
│   ├── Planning Home
│   ├── Approved Demands
│   ├── Packages
│   ├── Released to Tender
│   └── Planning Evidence
├── STD / Tender Document Readiness
├── Tender Management
├── Supplier Participation & Bid Submission
├── Tender Closing
├── Bid Opening
├── Evaluation & Award
├── Contract Management
└── Evidence & Audit
```

The screenshots show that Procurement Planning has been implemented functionally as an expandable parent with child entries. However, the visual hierarchy is weak. The child items are present, but they do not read strongly enough as subordinate items because the default Frappe / ERPNext sidebar styling gives limited nested navigation affordance.

---

# 1. Research Conclusion

Frappe has partial native support for hierarchy, but not enough visual hierarchy control for the desired KenTender IA.

The recommended approach is:

```text
Native Frappe workspace hierarchy for structure and routing
+
KenTender sidebar enhancement layer for visual hierarchy
```

Do not fake the hierarchy only with CSS. The parent/child relationship should exist in the Frappe Workspace configuration. Then custom CSS/JS should improve how that hierarchy appears in the Desk sidebar.

---

# 2. Use Native Frappe Workspace Hierarchy as the Source of Truth

Frappe supports creating child workspaces. Its Workspace customization model allows sidebar items to be arranged as parent/child workspaces.

Therefore, Procurement Planning should be implemented as a real parent workspace/sidebar group, with the child items below it.

Required structure:

```text
Procurement Planning
├── Planning Home
├── Approved Demands
├── Packages
├── Released to Tender
└── Planning Evidence
```

## Cursor Instruction

```text
Keep Procurement Planning as a parent workspace/sidebar group.
Create Planning Home, Approved Demands, Packages, Released to Tender, and Planning Evidence as child workspaces/items under Procurement Planning.
Do not flatten them as peer top-level modules.
Do not duplicate them under Configuration.
```

## Important Rule

The hierarchy should be data-backed through Workspace configuration, not only represented by visual indentation.

---

# 3. Accept the Native Frappe Sidebar Limitation

Frappe / ERPNext’s Desk sidebar is designed around Workspace entries. It supports workspace organization, but it does not provide enough built-in visual controls for:

- tree connector lines
- strong nested indentation
- child item typography
- parent group visual emphasis
- active child group expansion behavior
- depth-specific styling
- custom per-group hierarchy treatment

This explains why the implementation works structurally but still looks visually flat.

The practical conclusion is:

```text
Do not fight Frappe by replacing the entire Desk sidebar immediately.
Enhance the native sidebar with small KenTender-specific styling and behavior.
```

---

# 4. Recommended Implementation Pattern

Use:

```text
Frappe native Workspace hierarchy
+
KenTender sidebar CSS
+
small JS class enhancer if needed
```

This gives the correct behavior and avoids building a completely separate navigation shell.

Do not rebuild the whole sidebar unless native Desk rendering cannot be styled reliably.

---

# 5. Desired Visual Result

The sidebar should visually read as:

```text
Procurement Planning       chevron
  Planning Home
  Approved Demands
  Packages
  Released to Tender
  Planning Evidence
```

The child items should have:

```text
smaller text
left indentation
subtle vertical rail
lighter icon weight
clear active state
less visual weight than top-level modules
```

The parent item should remain visually stronger than its children.

---

# 6. Recommended Visual Rules

## Parent Workspace

`Procurement Planning` should behave like a group heading plus navigation item.

Recommended treatment:

```text
- standard top-level item size
- normal or semi-bold text
- chevron clearly aligned to the right
- active group state if any child is active
```

## Child Workspace Items

Child items should be visually subordinate.

Recommended treatment:

```text
- indented under Procurement Planning
- slightly smaller or lighter text
- lower visual weight than top-level modules
- subtle left rail or guide line
- active child item has a visible selected state
```

## Active Child State

When a child route is active, both should be clear:

```text
- the child item is selected
- the Procurement Planning group is expanded and visibly active as the parent context
```

---

# 7. Recommended CSS Concept

Create a KenTender sidebar stylesheet.

Suggested file:

```text
kentender/public/css/kentender_sidebar.css
```

Suggested CSS:

```css
/* KenTender nested workspace sidebar */
.kt-sidebar-group {
  margin-top: 4px;
}

.kt-sidebar-group-label {
  font-weight: 600;
  color: var(--text-color);
}

.kt-sidebar-child {
  margin-left: 28px;
  padding-left: 12px;
  font-size: 13px;
  color: var(--text-muted);
  position: relative;
}

.kt-sidebar-child::before {
  content: "";
  position: absolute;
  left: 0;
  top: -6px;
  bottom: -6px;
  width: 1px;
  background: var(--border-color);
}

.kt-sidebar-child.is-active {
  color: var(--text-color);
  font-weight: 600;
  background: var(--control-bg);
  border-radius: 8px;
}

.kt-sidebar-child.is-active::before {
  background: var(--primary);
  width: 2px;
}
```

The exact selectors may need adjustment depending on the rendered Frappe version. Cursor should inspect the actual DOM classes produced by the current Desk sidebar.

---

# 8. Recommended JS Enhancer

Frappe may not expose stable per-depth classes on sidebar items. If native classes are insufficient, add a small JS enhancer that applies KenTender classes after the Desk sidebar renders.

Suggested file:

```text
kentender/public/js/kentender_sidebar.js
```

Suggested implementation:

```javascript
// kentender/public/js/kentender_sidebar.js

(function () {
  const PLANNING_LABELS = new Set([
    "Planning Home",
    "Approved Demands",
    "Packages",
    "Released to Tender",
    "Planning Evidence",
  ]);

  const PLANNING_PARENT_LABEL = "Procurement Planning";

  function normalizeText(value) {
    return (value || "").replace(/\s+/g, " ").trim();
  }

  function enhanceProcurementPlanningSidebar() {
    const sidebar = document.querySelector(".standard-sidebar, .desk-sidebar, aside");
    if (!sidebar) return;

    const links = Array.from(sidebar.querySelectorAll("a"));

    links.forEach((link) => {
      const text = normalizeText(link.textContent);
      const href = link.getAttribute("href") || "";

      if (text.includes(PLANNING_PARENT_LABEL) || href.includes("procurement-planning")) {
        link.classList.add("kt-sidebar-group-label");
        const row = link.closest("li, .sidebar-item, .standard-sidebar-item") || link;
        row.classList.add("kt-sidebar-group");
      }

      if (PLANNING_LABELS.has(text)) {
        link.classList.add("kt-sidebar-child");
        const row = link.closest("li, .sidebar-item, .standard-sidebar-item") || link;
        row.classList.add("kt-sidebar-child-row");
      }
    });
  }

  function installObserver() {
    const observer = new MutationObserver(() => {
      enhanceProcurementPlanningSidebar();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    enhanceProcurementPlanningSidebar();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", installObserver);
  } else {
    installObserver();
  }
})();
```

## Implementation Caution

Prefer stable route metadata or known hrefs over text matching if possible.

Text matching is acceptable as a first workaround but can break if labels are renamed or translated.

Better long-term options:

```text
- add data attributes when rendering the sidebar if possible
- match workspace route names
- match known workspace IDs
- centralize menu configuration in one KenTender nav registry
```

---

# 9. Add CSS and JS Through hooks.py

Cursor should include the CSS and JS through the app hooks.

Suggested configuration:

```python
# hooks.py

app_include_css = [
    "/assets/kentender/css/kentender_sidebar.css",
]

app_include_js = [
    "/assets/kentender/js/kentender_sidebar.js",
]
```

If the project already has global Desk assets configured, add these files to the existing list rather than replacing it.

---

# 10. Keep Group Expanded When a Child Is Active

The Procurement Planning group should remain expanded when the user is inside any child route.

Routes that should keep the group open:

```text
/desk/procurement-planning
/desk/planning-home
/desk/approved-demands
/desk/packages
/desk/released-to-tender
/desk/planning-evidence
```

If the project uses different route slugs, map them explicitly.

Suggested route map:

```javascript
const PROCUREMENT_PLANNING_ROUTES = [
  "/desk/procurement-planning",
  "/desk/planning-home",
  "/desk/approved-demands",
  "/desk/packages",
  "/desk/released-to-tender",
  "/desk/planning-evidence",
];
```

When any of these routes is active:

```text
- expand Procurement Planning
- mark Procurement Planning as active parent context
- mark exact child as active
```

---

# 11. Frappe v16 Workspace Sidebar Note

If the project is on Frappe v16, there may be additional Workspace Sidebar / Desktop Icon behavior available.

Community discussion suggests Frappe v16 introduced or changed concepts around `Workspace Sidebar` and desktop icons. Some users describe creating a parent desktop icon and adding sidebar links with `Link type = Workspace sidebar`.

However, the documentation and community guidance appear sparse and inconsistent. Do not rely on undocumented v16 behavior without testing.

## Cursor Instruction

```text
If the project is on Frappe v16 and Workspace Sidebar is available, test native Workspace Sidebar first.
If it cannot produce clear visual nesting, keep native hierarchy but apply KenTender sidebar CSS classes.
Do not rely on undocumented v16 behavior without a fallback.
```

---

# 12. Do Not Replace the Whole Sidebar Unless Necessary

Frappe UI has a standalone Sidebar component with support for sections and collapsible groups, but that is not automatically the same as ERPNext Desk’s workspace sidebar.

It becomes relevant only if KenTender later moves to a custom app shell or Vue-based shell.

For now, do not rebuild the entire sidebar.

Use the lowest-risk route:

```text
Native Frappe workspace hierarchy
+
custom KenTender CSS/JS hierarchy enhancer
```

Only consider a full custom sidebar if:

```text
- Desk sidebar DOM cannot be reliably styled
- Workspace hierarchy cannot support the IA
- route context cannot be preserved
- active state cannot be controlled
- nested modules expand/collapse inconsistently
```

---

# 13. Recommended Acceptance Criteria

The implementation is acceptable when all of the following are true:

1. `Procurement Planning` appears as a parent group in the main Procurement navigation.
2. The following items appear under it as child items:
   - Planning Home
   - Approved Demands
   - Packages
   - Released to Tender
   - Planning Evidence
3. Child items are visually indented.
4. Child items are visually lighter than top-level modules.
5. A subtle rail or equivalent visual cue shows the child group.
6. The active child item is clearly highlighted.
7. The Procurement Planning group remains expanded when a child route is active.
8. Procurement Planning children are not duplicated elsewhere as top-level modules.
9. The global left menu remains stable across child routes.
10. The solution uses native Frappe Workspace hierarchy as the source of truth.
11. Custom CSS/JS is limited to visual hierarchy enhancement, not a full replacement sidebar.

---

# 14. Final Cursor Handoff

Use this implementation instruction directly:

```text
Implement Procurement Planning as a true parent workspace with child workspaces/items:
- Planning Home
- Approved Demands
- Packages
- Released to Tender
- Planning Evidence

Use Frappe’s native parent/child workspace configuration as the source of truth.

Then add a KenTender sidebar enhancement layer:
- indent Procurement Planning children
- add a subtle vertical rail
- reduce child item text weight/size
- keep parent label visually stronger
- preserve active child highlighting
- keep the group expanded when any child route is active

Do not create a second custom navigation model unless native Desk sidebar rendering cannot be styled reliably.
Do not flatten Procurement Planning children as peer top-level modules.
```

---

# 15. Final Recommendation

The correct strategy is not to abandon Frappe’s sidebar, and not to accept a flat-looking hierarchy.

Use Frappe for structure:

```text
Workspace parent-child hierarchy
```

Use KenTender for presentation:

```text
CSS/JS v