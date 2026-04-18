---
trigger: always_on
---

## Rule Conflict Detection

### Pre-Action Checklist

Before taking ANY action, check for conflicts:

1. **User Instruction Check**
   - Does this violate user's explicit instructions?
   - Did user say "DO NOT" or "NEVER" about this action?
   - Is there a specific override statement?

2. **Execution Discipline Check**
   - Does this violate no-autonomous-coding rules?
   - Am I assuming permission to implement?
   - Is this planning vs implementation boundary crossed?

3. **Framework Rules Check**
   - Should this use framework command vs code edit?
   - Am I trying to manually create framework scaffolds?

4. **Architecture Rules Check**
   - Does this violate app ownership or dependency rules?
   - Is this mixing domain responsibilities?

### Conflict Detection Process

If ANY conflict detected:

1. **STOP IMMEDIATELY**
   - Do not proceed with the action
   - Do not attempt to resolve automatically

2. **IDENTIFY CONFLICT**
   - Which rules are conflicting?
   - What is the priority hierarchy?
   - What is the higher priority rule?

3. **NOTIFY USER**
   - State the conflict clearly
   - Reference the specific rules involved
   - Ask for explicit resolution

4. **WAIT FOR RESOLUTION**
   - Do not proceed until user resolves
   - Follow user's explicit instruction

### Common Conflict Scenarios

**Scenario A**: Planning guidance auto-proceeds vs user said "DO NOT"
- Conflict: Planning workflow (#4) vs User instruction (#1)
- Resolution: User instruction wins
- Action: STOP, wait for explicit "PROCEED"

**Scenario B**: Framework suggests code edit vs generator rule requires command
- Conflict: Architecture (#5) vs Framework (#3)  
- Resolution: Framework rule wins
- Action: Use framework command

**Scenario C**: Quick fix vs execution discipline
- Conflict: Convenience vs Execution discipline (#2)
- Resolution: Execution discipline wins
- Action: STOP, ask for permission

### Implementation

This rule must be checked BEFORE:
- Any file creation/edit
- Any command execution
- Any tool call that modifies state
- Any automatic progression

### Error Recovery

If conflict detection fails:
1. Acknowledge the failure
2. Revert the action if possible
3. Re-run conflict detection
4. Follow proper resolution process
