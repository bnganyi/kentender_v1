Kentender Dropdown & Reference Display Standard (v1.0)

**1\. Golden Rule (Non-negotiable)**

Users must NEVER see internal database IDs.

These are strictly forbidden in UI:

-   5clnp2b7p
-   ffs40q1jhh
-   UUIDs
-   internal primary keys
-   internal IDs in secondary lines/tooltips/helper text

These belong only to:

-   backend
-   API payloads
-   logs

**2\. Every Selectable Entity Must Have 3 Fields**

For ANY entity used in a dropdown:

| **Field** | **Purpose** |
| --- | --- |
| id | internal (hidden) |
| code | stable business identifier |
| name | human-readable label |

**Example: Program**

{

"id": "5clnp2b7p",

"code": "PRG-MOH-001",

"name": "Healthcare Access"

}

**3\. Dropdown Display Format**

**Required format (standard across system):**

Primary: Name

Secondary: Code (muted)

**Example:**

Healthcare Access

PRG-MOH-001

**4\. Selected Value Display (Collapsed State)**

When a value is selected, show:

Healthcare Access (PRG-MOH-001)

OR if space constrained:

Healthcare Access

BUT:

-   code must be accessible (tooltip or secondary line)

**5\. Search Behavior**

Search must match:

-   name
-   code

Example:  
User types:

-   "health" → finds Healthcare Access
-   "PRG-001" → finds same record

**6\. Dropdown Item Layout (Required)**

Each option must be rendered as:

\[Primary line: Name\]

\[Secondary line: Code or short context\]

Secondary line must NEVER include `id` / `name` primary key.

NOT:

5clnp2b7p

Healthcare Access

**7\. Context Enrichment (Where Needed)**

For hierarchical entities (like your case):

**Program dropdown**

Healthcare Access

PRG-MOH-001

**Sub-program dropdown**

Primary Care Infrastructure

Under: Healthcare Access

**Output Indicator dropdown**

Increase rural healthcare coverage

Target: 65%

**8\. Cascading Behavior (Critical Fix for Your UI)**

Right now users:

-   pick Program
-   then see ALL Sub-programs
-   then ALL Indicators

That’s wrong.

**Required:**

| **Selection** | **Filters** |
| --- | --- |
| Program | filters Sub-program |
| Sub-program | filters Output Indicator |
| Output Indicator | filters Performance Target |

**9\. API Contract for Dropdowns**

Backend must return structured objects:

**Example: Program API**

\[

{

"id": "5clnp2b7p",

"code": "PRG-MOH-001",

"name": "Healthcare Access"

}

\]

**Frontend must:**

-   store id
-   display name + code

**10\. DO NOT USE THESE PATTERNS**

**❌ Raw IDs**

5clnp2b7p

**❌ Mixed secondary line with ID + code**

5clnp2b7p, PRG-001

**❌ Code-only**

PRG-MOH-001

**❌ Name-only (for critical entities)**

Healthcare Access

(acceptable only in very tight UI, but not ideal)

**11\. Performance Target Dropdown Fix (Your Screenshot)**

Right now:

5cl53463f

Improve service delivery metrics

**Must become:**

Improve service delivery metrics

TGT-MOH-2026-001

**12\. Advanced Rule — When to Show Codes**

| **Context** | **Show Code?** |
| --- | --- |
| Dropdown list | YES |
| Selected value | YES (inline or tooltip) |
| Display rows | YES |
| Cards | Optional |
| Headers | Optional |

**13\. Special Case: Free Text vs Reference**

If a field:

-   references another entity → use dropdown with name+code
-   is user-entered → do NOT show code

**13.1 Auto-generated code fields (UX rule)**

If a code value is system-generated:

- do not show it as an editable input in create modal/form
- do not allow user-supplied values in standard create/edit UX
- show it read-only after creation
- allow manual override only where policy permits

**14\. Cursor Fix Prompt (Critical)**

Fix all dropdowns and reference selectors to follow the Kentender Dropdown Display Standard.

Requirements:

1.  NEVER display internal database IDs (e.g., 5clnp2b7p)
2.  Each dropdown option must show:
    -   Primary: name
    -   Secondary: code (muted)
3.  Selected value must display:
    -   name + code (or name with code accessible)
4.  API responses must include:
    -   id (internal)
    -   code (business identifier)
    -   name (display)
5.  UI must:
    -   store id
    -   display name + code
6.  Implement cascading filters:
    -   Program → Sub-program → Output Indicator → Performance Target
7.  Update all dropdowns:
    -   Program
    -   Sub-program
    -   Output Indicator
    -   Performance Target
    -   Budget Line (if applicable)
8.  Search must match:
    -   name
    -   code

Do NOT:

-   expose internal IDs
-   show code-only or name-only for critical entities
-   leave dropdowns unfiltered when parent is selected

At the end report:

1.  all dropdowns updated
2.  APIs modified
3.  cascading logic implemented
4.  any entities missing code field

**Final point (important)**

This is one of those small things that has outsized impact.

If you fix this:

-   system immediately feels **government-grade**
-   users trust it
-   traceability improves
-   debugging becomes easier

If you don’t:

-   it will always feel like an internal tool

If you want next, I can define:  
👉 a **code generation standard (PRG-, SUB-, BL-, DIA-, etc.)** so all entities are consistent system-wide