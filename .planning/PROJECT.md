# Constraint Manager v2.0

## What This Is

A Fusion (Autodesk Fusion 360) desktop add-in that gives users a comprehensive constraint management interface for sketches. v1.1 shipped a command-based tool for viewing and selectively deleting constraints on selected entities. v2.0 evolves the UI into a three-tab interface that adds sketch-wide constraint type summaries with bulk deletion, and a full constraint list with type filtering — filling the largest unmet needs in the Fusion constraint management space.

## Core Value

Users can see and manage every constraint in a sketch without guessing, clicking blindly, or relying on Fusion's all-or-nothing deletion.

## Requirements

### Validated

- ✓ Per-entity constraint listing in a table — v1.0
- ✓ Multi-entity selection with unified constraint table — v1.0
- ✓ Selective deletion of individual constraints via checkboxes — v1.0
- ✓ Non-deletable constraint protection (lock emoji, disabled checkbox) — v1.0
- ✓ Related entity display for each constraint — v1.0
- ✓ Toolbar button in DESIGN workspace with proper lifecycle — v1.0
- ✓ Entity token re-resolution for safe deletion across event boundaries — v1.1

### Active

- [ ] Three-tab command dialog (Selected Entities, Constraint Types, All Constraints)
- [ ] **Constraint Types tab**: Summary table showing each constraint type, count, and "Delete All" action for the active sketch
- [ ] **All Constraints tab**: Full list of every constraint in the active sketch with explicit "Load" button
- [ ] **All Constraints tab**: Type column (sortable) for each constraint row
- [ ] **All Constraints tab**: Dropdown filter by constraint type
- [ ] **All Constraints tab**: Checkbox selection + delete for individual constraints
- [ ] **Selected Entities tab**: Preserve current v1 behavior exactly

### Out of Scope

- Dimension constraints — deferred to future release (v2.x), geometric constraints only for now
- Viewport highlighting of constraint geometry — deferred to future release
- Under-constrained diagnostics — deferred to future release
- Auto-constraint interception — Fusion API doesn't support intercepting constraints as they're created
- Constraint replacement (e.g., swap perpendicular → H/V) — complex, defer to future

## Context

**Competitive landscape is empty.** No other Fusion add-in provides a constraint list/table, selective deletion by type, or bulk operations. The only adjacent tools are a 23-star GitHub highlighting add-in and a hidden text command. This is the #1 most-requested feature on Autodesk IdeaStation.

**Primary audience for v2 features:** CNC/laser users who import DXF/SVG files and get hundreds of Fix constraints applied automatically. The Constraint Types tab with "Delete All Fix" is the killer feature for this group. Secondary audience: anyone debugging over-constrained sketches.

**Existing architecture:** Python add-in with clean separation between command/UI layer (`command.py`) and pure constraint logic (`constraint_engine.py`). Event-driven lifecycle (CommandCreated → InputChanged → PreSelect → Execute → Destroy). Module-level state management for handler references. The constraint engine is testable outside Fusion via mock objects.

**Key technical consideration:** The "All Constraints" tab needs an explicit Load button because sketch-wide enumeration could be expensive on large sketches (hundreds of entities, thousands of constraints). The Constraint Types tab should be lightweight — just counting, not listing.

**Existing codebase map:** `.planning/codebase/` contains detailed architecture, stack, and convention analysis from v1.1.

## Constraints

- **Platform**: Autodesk Fusion 360 Python API (`adsk.core`, `adsk.fusion`) — all UI must use Fusion's command input system (`TabCommandInput`, `TableCommandInput`, `DropDownCommandInput`)
- **Runtime**: Python 3.x as provided by Fusion's embedded interpreter — no external dependencies allowed in production
- **Installation**: Folder copy to `%APPDATA%/Autodesk/Autodesk Fusion 360/API/AddIns/ConstraintManager/` — no build step
- **Compatibility**: Must work on Windows and macOS
- **Performance**: Sketch-wide operations must handle sketches with 500+ entities without hanging the UI
- **Backward compatibility**: Selected Entities tab must behave identically to v1.1

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Three-tab UI (Selected Entities / Constraint Types / All Constraints) | Covers three distinct workflows: surgical precision, bulk type ops, and full sketch audit | — Pending |
| Explicit Load button on All Constraints tab | Prevents UI hang on massive sketches — user opts in to expensive enumeration | — Pending |
| Constraint Types tab uses count + Delete All per type | Lightweight summary is more useful than listing every constraint for bulk ops (DXF import cleanup) | — Pending |
| v2.0 version bump | Three-tab UI is a fundamentally different UX, not an incremental patch | — Pending |
| Incremental release strategy going forward | Ship features as ready (v2.1, v2.2) rather than bundling everything | — Pending |
| Geometric constraints only in v2.0 | Dimensions deferred to keep scope focused — validate tab UI first | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-22 after initialization*
