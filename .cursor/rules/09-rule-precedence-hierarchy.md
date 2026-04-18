---
trigger: always_on
---

## Rule Precedence Hierarchy (Highest to Lowest Priority)

### 1. User's Explicit Instructions in Current Conversation
- Any direct instruction from user in current conversation
- Commands containing "DO NOT", "NEVER", "ONLY", "MUST"
- Explicit override statements
- Specific implementation permissions or denials

### 2. Execution Discipline Rules
- Rules in `06-execution-gatekeeper.md`
- No-autonomous-coding restrictions
- Implementation gate requirements
- Permission-based execution rules

### 3. Framework Generator Rules  
- Rules in `07-framework-generators-first.md`
- Command vs code policy (`08-command-vs-code.md`)
- Frappe scaffold generation requirements
- Framework-managed artifact handling

### 4. Planning Workflow Guidance
- Planning guidance instructions
- Workflow automation rules
- Standard development patterns
- Phase progression rules

### 5. General Architecture Rules
- App structure and ownership rules
- Dependency direction rules  
- Implementation pattern rules
- UX and workflow rules

## Conflict Resolution

When rules conflict:
1. Higher priority rule ALWAYS wins
2. STOP execution immediately
3. Notify user of conflict
4. Wait for explicit resolution

## Examples

**Scenario**: User says "DO NOT implement" but planning guidance says to proceed
- **Winner**: User instruction (#1)
- **Action**: STOP, do not implement

**Scenario**: Execution discipline says no autonomous coding, but planning guidance auto-proceeds
- **Winner**: Execution discipline (#2)  
- **Action**: STOP, require explicit trigger

**Scenario**: Framework rules require command, but architecture rules allow code edits
- **Winner**: Framework rules (#3)
- **Action**: Use framework command first
