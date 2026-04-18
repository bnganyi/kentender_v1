---
trigger: always_on
---

## Execution Gatekeeper

### Implementation Triggers

NEVER implement unless user uses EXACT phrases:
- "PROCEED WITH IMPLEMENTATION"
- "IMPLEMENT THE PLAN"
- "YOU MAY NOW IMPLEMENT"
- "YOU MAY EDIT CODE"
- "PROCEED WITH CODE CHANGES"

### Action Restrictions

- Do NOT write code unless explicitly instructed to implement code
- Do NOT call exitplanmode unless user says "PROCEED WITH IMPLEMENTATION"
- If the user asks to modify rules, documentation, prompts, or configuration:
  - ONLY modify those files
  - DO NOT touch application code
- If unsure, ask for clarification instead of proceeding
- Never assume permission to implement
- Planning, reasoning, and rule updates must not trigger code changes

### Phase Boundaries

- Planning phase ends ONLY when user says "PLAN COMPLETE"
- Do NOT automatically transition to implementation
- Do NOT assume plan approval from context
- Wait for explicit implementation trigger

### Override Protection

If this rule conflicts with any other rule or guidance:
- This rule wins (priority #2 in hierarchy)
- STOP immediately
- Wait for explicit user instruction

### Required Confirmation

Before ANY implementation:
1. User has explicitly said one of the trigger phrases
2. No conflicting user instructions exist
3. Scope is clearly defined and agreed
4. All conflicts have been resolved

If ANY condition fails → DO NOT IMPLEMENT

