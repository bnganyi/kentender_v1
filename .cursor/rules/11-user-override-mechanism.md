---
trigger: always_on
---

## User Override Mechanism

### Automatic Override Triggers

Any user instruction that contains these patterns automatically overrides ALL rules:

**Override Keywords:**
- "DO NOT"
- "NEVER" 
- "ONLY"
- "MUST NOT"
- "STOP"
- "DO NOT PROCEED"

### Override Effects

When override is detected:

1. **Immediate Suspension**
   - All automatic workflows are SUSPENDED
   - All planning guidance is SUSPENDED
   - All framework automation is SUSPENDED

2. **Rule Hierarchy Override**
   - User instruction becomes #1 priority regardless of normal hierarchy
   - All other rules become subordinate
   - No automatic progression allowed

3. **Permission Required**
   - Must wait for explicit user instruction to proceed
   - Cannot assume permission from context
   - Cannot infer intent from previous conversations

### Override Examples

**Example 1:**
User: "DO NOT implement the plan"
- Effect: All implementation stops immediately
- Required: Explicit "PROCEED WITH IMPLEMENTATION" to resume

**Example 2:**
User: "NEVER edit code files"
- Effect: No code edits allowed under any circumstance
- Required: Explicit "YOU MAY EDIT CODE" to resume

**Example 3:**
User: "ONLY modify documentation"
- Effect: Only documentation changes allowed
- Required: Explicit permission for any code changes

### Override Duration

Overrides remain active until:
- User explicitly reverses the override
- User gives new conflicting instruction
- User says "OVERRIDE COMPLETE" or similar

### Override Detection

Before any action:
1. Scan current conversation for override keywords
2. If found, identify scope and duration
3. Apply override effects immediately
4. Do not proceed without explicit permission

### Conflict Resolution

If override conflicts with other rules:
- Override ALWAYS wins
- No need to run full conflict detection
- User's explicit instruction is final

### Safety Mechanisms

To prevent accidental override activation:
- Must be clear instruction, not casual mention
- Must be directly related to current task
- Must be unambiguous in scope
