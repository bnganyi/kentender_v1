# KenTender v1 - Windsurf Development Rules

## Overview
This file governs the implementation of the KenTender v1 Frappe app, ensuring consistency with architectural principles and Frappe best practices.

## Pre-requisite Reading
Before making any changes, read:
- `docs/architecture/kentender-architecture-rules.md`
- `docs/architecture/global-architecture-v2.md`
- `AGENTS.md` (app root)

## Core Architectural Rules

### 1. App Structure & Ownership
- **Respect app ownership and dependency direction**
- **Do not create new apps** - work within kentender_v1 boundaries
- **Keep business logic in services/**, not DocType controllers
- **Maintain clean separation** between UI, business logic, and data layers

### 2. Frappe-Specific Guidelines
- **DocType controllers** should only handle Frappe lifecycle hooks
- **Service layer** contains all business logic and workflow orchestration
- **APIs must be explicit and minimal** - no hidden endpoints
- **Use workspace-first UX**, not raw DocType-first UX

### 3. Workflow & State Management
- **Do not invent hidden workflow states**
- **Do not mix unrelated phases**
- **Do not implement future phases**
- **Stop exactly at the requested phase boundary**

### 4. Code Quality Standards
- Follow Frappe naming conventions for DocTypes, fields, and methods
- Use proper error handling and logging
- Implement comprehensive validation in services layer
- Maintain backward compatibility when possible

## Required Development Process

### Before Coding
Provide:
- **Summary** of what will be implemented
- **Impacted apps** (usually just kentender_v1)
- **Impacted files** with full paths
- **Scope boundaries** - what's in vs out
- **Tests to run** before and after changes

### After Coding
Provide:
- **Files changed** with brief descriptions
- **What changed** - technical summary
- **What was intentionally not changed** - rationale
- **Manual checks** needed
- **Smoke tests to run**

## Frappe Development Specifics

### DocType Development
- Place custom scripts in appropriate `public/js` folders
- Use `frappe.call()` for server communication
- Follow Frappe permission patterns
- Implement proper field dependencies and validations

### Service Layer
- All business logic goes in `kentender_strategy/services/`
- Use shared assertion helpers for workflow actions
- Implement proper transaction handling
- Follow Frappe database transaction patterns

### UI/UX Development
- Build workspace-based navigation, not DocType lists
- Use Frappe's desk framework components
- Implement proper user feedback and loading states
- Follow responsive design principles

### Testing
- Write unit tests for service layer functions
- Test DocType controllers with Frappe test framework
- Include integration tests for critical workflows
- Test with different user roles and permissions

## Commands & Build Process

### After Python Changes
```bash
bench migrate
bench clear-cache
```

### After Frontend Changes
```bash
./scripts/bench-with-node.sh build --app kentender_v1
```

### Testing
```bash
bench run-tests --app kentender_v1
```

## Security & Permissions
- All workflow actions must go through whitelisted controller methods
- Use shared assertion helpers for authorization checks
- Implement proper role-based access controls
- Validate all user inputs in service layer

## File Organization
```
kentender_v1/
├── .windsurf/rules.md          # This file
├── AGENTS.md                   # High-level agent rules
├── docs/                       # Architecture documentation
├── kentender_strategy/
│   ├── doctype/               # Custom DocTypes
│   ├── services/              # Business logic layer
│   ├── api/                   # Explicit API endpoints
│   └── public/
│       ├── js/                # Client scripts
│       └── css/               # Stylesheets
└── hooks.py                   # Frappe app hooks
```

## Remember
- Always verify changes in browser with hard refresh
- Test with different user roles
- Check console for errors after UI changes
- Run migration after DocType changes
- Clear cache when in doubt
