# Phase 1: Engine and Tab Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-22
**Phase:** 1-Engine and Tab Foundation
**Areas discussed:** Tab behavior, State management, Engine API design, Migration safety

---

## Tab Behavior

### Tab Labels

| Option | Description | Selected |
|--------|-------------|----------|
| Selected / Types / All | Short labels | ✓ |
| Full names | 'Selected Entities', 'Constraint Types', 'All Constraints' | |
| You decide | Claude picks labels | |

**User's choice:** Short labels: "Selected", "Types", "All"
**Notes:** None

### Empty Tabs (Phase 1)

| Option | Description | Selected |
|--------|-------------|----------|
| Coming soon message | Static text about future update | |
| Hide until ready | Only show Selected tab in Phase 1 | |
| Placeholder UI | Show tab with empty table structure | ✓ |

**User's choice:** Placeholder UI
**Notes:** Validates tab infrastructure before content is built

---

## State Management

### State Organization

| Option | Description | Selected |
|--------|-------------|----------|
| Dict per tab | Single module-level dict keyed by tab name | |
| Separate globals | Three separate module-level lists | |
| You decide | Claude picks best fit | ✓ |

**User's choice:** You decide — but keep plugin lightweight, only load entities when user explicitly asks. Types and All tabs both need a "load entities" button.
**Notes:** User emphasized no background loading. This led to D-04 (lazy-loading across all tabs).

### Handler Utility

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, utility func | wire_handler() helper | ✓ |
| Keep manual | Continue existing append pattern | |

**User's choice:** Yes, after clarification that it's a code organization helper with zero runtime overhead, not a background process.
**Notes:** User initially concerned about performance — asked what the utility actually does. After explanation that it's just wrapping the existing append pattern into one call, approved it.

---

## Engine API Design

### Build Timing

| Option | Description | Selected |
|--------|-------------|----------|
| Build and test now | Full implementation + pytest in Phase 1 | ✓ |
| Stub now, build later | Define signatures only | |
| You decide | Claude picks | |

**User's choice:** Build and test now
**Notes:** De-risks Phase 2/3

### Return Format

| Option | Description | Selected |
|--------|-------------|----------|
| Same dicts | Reuse existing constraint info dict format | |
| You decide | Claude designs per-tab return formats | ✓ |

**User's choice:** You decide
**Notes:** None

---

## Migration Safety

### Test Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Manual test in Fusion | Run add-in, test by hand | ✓ |
| Manual + unit tests | Expand pytest + manual Fusion testing | |
| You decide | Claude picks | |

**User's choice:** Manual test in Fusion
**Notes:** UI layer can't be automated outside Fusion

### Rollback Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Git revert | Revert to v1.1 if broken | |
| Feature flag | Toggle between old and new UI | |
| You decide | Claude picks safest approach | ✓ |

**User's choice:** You decide
**Notes:** None

---

## Claude's Discretion

- State organization pattern (dict vs separate globals)
- Engine return formats per tab
- Rollback approach

## Deferred Ideas

None — discussion stayed within phase scope
