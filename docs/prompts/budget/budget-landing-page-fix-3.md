Budget Landing Page Fix

Good catch. This is exactly where most systems quietly fail — you built the workflow, but not the *work surface*.

Right now your page is **record-centric** (select a budget → view details).  
What you’re missing is **task-centric entry points**.

Let’s fix that cleanly without bloating the UI.

**🔴 The Gap (Plainly)**

An approver currently has to:

-   scan the list manually
-   guess which ones need action

That does not scale. It will break immediately in real use.

**✅ Correct Pattern (ERP-grade)**

You need **two parallel views in the same page**:

**1\. Records (what you already have)**

**2\. Work (what needs action)**

**🎯 Minimal, Production-Ready Solution**

**1\. Add “Work Tabs” above the list**

Replace:

Budgets

With:

\[ All \] \[ My Work \] \[ Draft \] \[ Submitted \] \[ Approved \]

**Behavior:**

-   **All** → current behavior
-   **My Work** → critical
-   **Submitted** → all pending approvals
-   **Draft** → editable budgets
-   **Approved** → locked

**2\. Define “My Work” (this is the key)**

**For Strategy Manager:**

-   Draft budgets they created → “Continue work”
-   Rejected budgets (future)
-   Possibly “needs revision” (later)

**For Planning Authority (Approver):**

-   **Submitted budgets ONLY**

👉 This becomes their *inbox*

**3\. Add Visual Priority Cues**

Right now status is visible but passive.

Make it actionable:

**In list:**

FY2027 Budget \[SUBMITTED\] 🔴 Needs Approval

FY2026 Budget \[DRAFT\] 🟡 In Progress

OR cleaner:

-   Submitted → **blue badge + bold border**
-   Add subtle “Requires action” label

**4\. Add KPI for Work (Top Row)**

Right now:

Active | Draft | Total | Allocation

Add:

Pending Approval (for approver)

My Drafts (for manager)

Example:

**For Planning Authority:**

Pending Approval: 3 ← THIS becomes primary

**5\. Auto-default behavior by role**

This is important:

-   Strategy Manager lands on → **Draft tab**
-   Planning Authority lands on → **My Work tab**

👉 No thinking required.

**6\. Action Reinforcement (You already did part of this well)**

You have:

\[ View Budget Builder \] \[ Approve Budget \]

Good. Now tighten logic:

**If user is Approver AND status = Submitted:**

-   Show:
    -   ✅ Approve
    -   ❌ Reject (add this soon)

**If not:**

-   Hide Approve entirely

**7\. Optional but High-Value (still minimal)**

Add a tiny banner in summary panel:

🔔 This budget requires your approval

Only for approvers.

**🧠 What You Just Introduced**

Without adding complexity, you now have:

-   **Inbox model** (My Work)
-   **Filtering model** (tabs)
-   **Role-aware UX**
-   **Action-driven UI**

That’s exactly what makes ERPNext modules feel “professional”.

**⚖️ Keep It Minimal Rule**

Do NOT:

-   build a separate “Tasks module”
-   add notifications yet
-   create dashboards

This tab system is enough for MVP.

**🔥 Final Verdict**

Your current UI:

Good record viewer

After this change:

Becomes a **working system**