# Fusion Sketch Constraint Manager — Design Spec

**Date:** 2026-03-20
**Status:** Draft (revised per Codex review)
**Author:** Matthew Mees + Claude

---

## Problem

Managing sketch constraints in Autodesk Fusion is painful in complex sketches. There's no way to see a clean list of constraints attached to a specific entity, and selectively deleting one often means hunting through overlapping constraint icons in the viewport and hoping you click the right thing.

## Solution

A Fusion add-in that provides a command-based constraint manager. The user selects a sketch entity, sees its geometric constraints in a structured table (with dimensions added once validated — see Open Question #3), and can selectively delete them — all without leaving the sketch. Constraint types not yet mapped in the resolver appear as `Unknown` rows (visible but non-deletable).

## User Workflow

1. User is editing a sketch in Fusion (**must be in active sketch edit mode**)
2. User clicks the **Constraint Manager** button in the toolbar
3. A command dialog opens with a selection input prompting "Select sketch entity"
4. User clicks a line, arc, circle, or point in the viewport
5. The dialog table populates with geometric constraints referencing that entity (unrecognized types shown as `Unknown`):
   - Constraint type (e.g., "Coincident", "Horizontal", "Parallel")
   - Related entity (e.g., "Line #2", "Arc #1", "Point #4")
   - Whether it's deletable (grayed out with lock indicator if not)
6. User checks one or more constraints in the table
7. User clicks "Delete Selected" in the table toolbar — constraints are deleted, table refreshes
8. User can change entity selection at any time — table refreshes
9. User can repeat select/delete as many times as needed
10. User clicks **Close** to dismiss the dialog

## Architecture: Approach A — Command + TableCommandInput

A standard Fusion command dialog using native `CommandInputs`. Chosen over HTML Palette (too complex) and Hybrid/BrowserCommandInput (less documented, quirky) approaches.

### Why Command-Based

- Native Fusion UI — feels like a built-in tool
- Potential undo integration via the command context (must be validated — see Undo Contract below)
- Selection filtering built in via `SelectionCommandInput`
- Simpler to build and maintain
- Sufficient for the core use case; can upgrade to richer UI later if needed

## Dialog Layout

Single-panel, compact layout:

```
+------------------------------------------+
|  CONSTRAINT MANAGER                       |
+------------------------------------------+
|  Select Entity:                           |
|  [ Line #1 (SketchLine)            ]      |
+------------------------------------------+
|  CONSTRAINTS (5 found)     [Delete Selected]
|  +----+---------------+----------------+  |
|  | [] | Type          | Related To     |  |
|  +----+---------------+----------------+  |
|  | [x]| Coincident    | Point #3       |  |
|  | [] | Horizontal    | --             |  |
|  | [] | Parallel      | Line #3        |  |
|  | [] | Equal         | Line #5        |  |
|  | lock| Tangent      | Arc #2 (locked)|  |
|  +----+---------------+----------------+  |
+------------------------------------------+
|                              [ Close ]    |
+------------------------------------------+
```

**Note on Close vs OK/Cancel:** Since deletions happen immediately when the user clicks "Delete Selected" (not on OK), the traditional OK/Cancel pattern is misleading. We use a single **Close** button. This design assumes undo works for `inputChanged`-driven deletions — **if validation shows it doesn't, the interaction model must be restructured** (see Undo Contract section). Undo would then be available via Fusion's native Ctrl+Z after closing.

### Command Inputs

| Input | Type | Purpose |
|-------|------|---------|
| `entitySelect` | `SelectionCommandInput` | User picks a sketch entity. Filters: `SketchCurves`, `SketchPoints` (SketchCurves covers lines, arcs, circles, ellipses, splines). Limit: 1. Set `isUseCurrentSelections = False` to avoid inheriting stale selections. |
| `constraintTable` | `TableCommandInput` | Displays constraints. 3 columns: checkbox (`BoolValueCommandInput` per row), type (`StringValueCommandInput`), related entity (`StringValueCommandInput`). "Delete Selected" action placed via `addToolbarCommandInput` on the table's native toolbar. See **Table Checkbox Strategy** below. |

### Highlighting (v1: Deferred)

Live viewport highlighting of related entities when checking table rows is **deferred to a future version**. The dual-`SelectionCommandInput` approach originally proposed has known issues: hidden selection inputs clear their selections, and separate selection sets only display while that input is active (unless `Command.hasDistinctSelectionSets` is changed, which introduces its own complications).

For v1, the "Related To" column provides sufficient context for the user to identify which entity a constraint connects to. If highlighting is added later, `ui.activeSelections.add()` with strict cleanup in `destroy` is the recommended approach — not a second `SelectionCommandInput`.

### Table Checkbox Strategy

The v1 UX depends on per-row checkboxes in a `TableCommandInput`. The intended approach is to add a `BoolValueCommandInput` (checkbox style, not button style) into column 0 of each row via `tableInput.addCommandInput()`.

**This must be validated as a first implementation step** — build a minimal test command with a `TableCommandInput` containing `BoolValueCommandInput` cells before building the full constraint manager. If checkboxes don't work in table cells:

- **Fallback A:** Use `TableCommandInput`'s built-in row selection (`tableInput.selectedRow`) instead of explicit checkboxes. This changes the interaction model to single-select, delete-one-at-a-time:
  - User clicks a row to select it (no checkbox column needed)
  - "Delete Selected" deletes the single selected constraint
  - Table refreshes; user selects next constraint to delete
  - State rules simplify: "some checked" becomes "a row is selected"
  - Batch deletion in reverse order is no longer needed — single `deleteMe()` call per action
- **Fallback B:** Use `DropDownCommandInput` per row as a check/uncheck toggle (known to work in tables but clunky).

## Constraint Enumeration Engine

### API: Direct Per-Entity Query

The Fusion API provides direct access to constraints on any sketch entity:

- **`SketchEntity.geometricConstraints`** — returns a `GeometricConstraintList` of all geometric constraints referencing that entity
- **`SketchEntity.sketchDimensions`** — returns a `SketchDimensionList` of all dimensions referencing that entity

This eliminates the need for a full-sketch scan or cache. **v1 default: geometric constraints only** via `geometricConstraints`. Dimension support via `sketchDimensions` is enabled only after its property mapping is verified during implementation (see Open Question #3). The engine should be structured to make adding dimension enumeration a single-flag addition, but it ships disabled until validated.

### Resolving the "Related Entity"

For each constraint returned, we need to identify the *other* entity (i.e., not the selected one). Each constraint type has different property names:

| Constraint Type | Properties to Check |
|----------------|-------------------|
| Horizontal, Vertical | `line` |
| Parallel, Perpendicular, Collinear | `lineOne`, `lineTwo` |
| Coincident | `point`, `entity` |
| Equal, Tangent, Smooth | `curveOne`, `curveTwo` |
| Concentric | `entityOne`, `entityTwo` |
| Symmetry | `entityOne`, `entityTwo`, `symmetryLine` |
| MidPoint | `point`, `midPointCurve` |
| HorizontalPoints, VerticalPoints | `pointOne`, `pointTwo` |
| Fix | `entity` |
| Offset | `parentCurves`, `childCurves` (collections — different pattern) |

**Resolution rules:**

- **Single-entity constraints** (Horizontal, Vertical, Fix): "Related To" shows `--`.
- **Two-entity constraints** (Parallel, Equal, Coincident, etc.): Read both properties, return the one that isn't the selected entity.
- **Three-entity constraints** (Symmetry): The selected entity may match `entityOne`, `entityTwo`, or `symmetryLine`. Show all *other* members comma-separated, e.g. `Line #2, Line #5`. Role annotations (e.g., `(sym)`) deferred to a future version.
- **Collection constraints** (Offset): `parentCurves` and `childCurves` are `ObjectCollection`s. Show comma-separated labels of the *other* collection's members, e.g. `Line #3, Arc #1`. If > 3 entities, truncate: `Line #3, Arc #1, +2 more`.

Dimension constraint subclass properties need verification during implementation — the geometric constraint types above are confirmed.

**Graceful handling of unknown types:** Unrecognized constraint types must be shown in the table as `Unknown (<raw objectType>)` with "Related To" set to `--`. They should be displayed as non-deletable (lock indicator) since we can't safely resolve their properties. This ensures the constraint list remains complete even when encountering new or undocumented types from future Fusion versions. Log the unknown type for debugging.

### Entity Display Names

`SketchEntity` does not expose a generic `name` property. The implementation must construct display labels deterministically:

| Entity Type | Label Format | Example |
|-------------|-------------|---------|
| `SketchLine` | `Line #N` | `Line #12` |
| `SketchArc` | `Arc #N` | `Arc #3` |
| `SketchCircle` | `Circle #N` | `Circle #1` |
| `SketchEllipse` | `Ellipse #N` | `Ellipse #1` |
| `SketchFittedSpline` | `Spline #N` | `Spline #2` |
| `SketchPoint` | `Point #N` | `Point #4` |
| Construction variants | Prefix with `Constr.` | `Constr. Line #2` |

**Deriving N (v1):** Use the entity's index within its parent collection (e.g., `sketch.sketchCurves.sketchLines` for lines). This is the sole labeling strategy for v1 — do not attempt to read browser tree names (not reliably exposed via API). If index stability proves problematic during implementation (see Open Question #5), switch to `entityToken`-based hashing for a stable short ID.

**Constraint type display:** Strip namespace from `objectType` (e.g., `adsk::fusion::HorizontalConstraint` → "Horizontal").

### Performance

- Direct per-entity enumeration is fast — no full-sketch scan needed
- Even complex sketches typically have 50–200 constraints total; per-entity counts are much smaller
- Enumeration is read-only — does not trigger sketch recomputation

## Non-Deletable Constraints

Non-deletable constraints (where `isDeletable` returns `False`) are shown in the table but grayed out with a lock indicator and are not checkable. They provide context — the user can see that a constraint exists without being able to accidentally select it for deletion.

## Deletion

- **Trigger:** "Delete Selected" toolbar action on the `TableCommandInput` (via `addToolbarCommandInput`)
- **Mechanism:** `inputChanged` handler detects the toolbar button, iterates checked constraints in reverse index order, calls `deleteMe()` on each
- **Safety:** Check `isDeletable` before each call (defense in depth — UI already prevents checking non-deletable rows). Check `constraint.isValid` as well (earlier deletions in the batch may cascade).
- **On failure:** Log and continue — don't abort the batch for one failed delete
- **After deletion:** Let Fusion's normal sketch solver update automatically. Do **not** use `sketch.isComputeDeferred` — Autodesk warns it can cause bad results with dependent features on existing sketches. Re-enumerate constraints for the currently selected entity and refresh the table.
- **Dialog stays open** — user can continue selecting entities and deleting constraints until they close

### Undo Contract (v1)

Undo behavior for deletions triggered inside `inputChanged` is underdocumented in the Fusion API. The v1 contract:

- **Acceptable:** One undo step per `deleteMe()` call (user presses Ctrl+Z multiple times to undo a batch). This is the most likely default behavior.
- **Acceptable:** One undo step per `inputChanged` invocation (entire batch undone at once). This would be ideal.
- **Not acceptable:** No undo at all. If testing reveals this, move deletion logic into the `execute` handler with a queued-deletion model.

This must be tested early in implementation. The Close-only dialog design depends on undo working — without it, users have no way to recover from accidental deletions.

### Command State Rules

| State | Behavior |
|-------|----------|
| No entity selected | Table is empty. Delete action is disabled (always present, never hidden). |
| Entity selected, zero constraints | Table shows "No constraints found" message row. Delete action disabled. |
| Entity selected, constraints listed, none checked | Delete action disabled. |
| Entity selected, constraints listed, some checked | Delete action enabled. |
| Selected entity becomes invalid after deletion | Clear table, clear `entitySelect`, prompt for new selection. Check `entity.isValid` before re-enumeration. |
| User exits sketch edit mode while dialog is open | The `destroy` handler fires (Fusion closes commands when leaving sketch edit). Clean up gracefully. |
| Delete button clicked with no checked rows | No-op (button should already be disabled, but guard defensively). |

## Add-in Structure

```
ConstraintManager/
├── ConstraintManager.py          # Entry point (run/stop)
├── ConstraintManager.manifest    # Add-in metadata
├── commands/
│   └── constraint_manager/
│       ├── __init__.py
│       ├── command.py            # Command definition, event handlers
│       └── constraint_engine.py  # Constraint enumeration, name resolution, deletion
└── resources/
    └── constraint_manager/
        └── 16x16.png             # Toolbar icon
```

### Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `ConstraintManager.py` | Registers command in DESIGN workspace toolbar. Handles add-in lifecycle (run/stop). |
| `command.py` | Command creation, event handlers (commandCreated, inputChanged, preSelect, execute, destroy). Builds UI, wires table to engine. |
| `constraint_engine.py` | Pure logic: enumerate constraints via `geometricConstraints` (and `sketchDimensions` when enabled), resolve related entities and display names, perform deletions. No Fusion UI dependencies. |

### Installation

User copies the `ConstraintManager/` folder to:
```
%APPDATA%/Autodesk/Autodesk Fusion/API/AddIns/
```
Then enables it via **Tools → Scripts & Add-Ins → Add-Ins** tab.

## Event Handler Flow

```
commandCreated
  ├── Verify active sketch edit mode — abort with message if not
  ├── Create entitySelect (SelectionCommandInput, isUseCurrentSelections=False)
  ├── Create constraintTable (TableCommandInput)
  ├── Add "Delete Selected" via constraintTable.addToolbarCommandInput()
  ├── Wire event handlers
  └── Append handler references to module-level list to prevent GC

preSelect (entity hover validation)
  ├── Verify hovered entity is in active sketch
  ├── Verify entity is a supported type (curve or point)
  └── Set isSelectable = False if invalid

inputChanged (entitySelect changed)
  ├── Set reentrancy guard
  ├── Get selected entity
  ├── Enumerate geometricConstraints (+ sketchDimensions if enabled)
  ├── Clear and repopulate constraintTable
  └── Release reentrancy guard

inputChanged (delete toolbar button clicked)
  ├── Set reentrancy guard
  ├── Collect checked constraints
  ├── Delete in reverse order (check isDeletable + isValid, call deleteMe)
  ├── Re-enumerate constraints for current entity
  ├── Refresh table
  └── Release reentrancy guard

execute / cancel
  └── Clean up, close command

destroy
  └── Clean up any remaining state, release handler references
```

### Reentrancy Guard

The `inputChanged` handler can fire recursively when programmatically modifying inputs (e.g., resetting a button value, clearing table rows). A simple boolean guard prevents re-entry:

```python
if self._handling_change:
    return
self._handling_change = True
try:
    # ... handle the change
finally:
    self._handling_change = False
```

### Handler Lifetime

Python event handlers in Fusion must be prevented from garbage collection. There are two tiers:

- **Add-in lifetime handlers** (e.g., `commandCreated` on the `CommandDefinition`): Stored in a module-level list in `ConstraintManager.py` (e.g., `_addin_handlers = []`). Cleared in the add-in's `stop()` function.
- **Command-instance handlers** (e.g., `inputChanged`, `preSelect`, `execute`, `destroy`): Stored in a separate module-level list in `command.py` (e.g., `_cmd_handlers = []`). Cleared in the `destroy` handler at end of each command invocation.

Both lists are module-level. Never store handlers on the command object itself — it may be garbage collected mid-session.

## Open Questions / Risks

### Must validate before full implementation (blockers)

1. **TableCommandInput checkbox support** — The entire v1 UX depends on `BoolValueCommandInput` working inside `TableCommandInput` cells. Build a minimal test command first. Fallbacks defined in Table Checkbox Strategy section.
2. **Undo granularity in `inputChanged`** — The Close-only dialog design depends on undo working. Test whether `deleteMe()` calls inside `inputChanged` produce undo steps. If not, must restructure around `execute` handler. See Undo Contract section.
3. **Dimension constraint entity properties** — Geometric constraints confirmed via `SketchEntity.geometricConstraints`. Dimension subclass properties from `SketchEntity.sketchDimensions` need verification. If unverifiable, dimensions are deferred — not a blocker for geometric-only v1.

### Should validate during implementation (non-blockers)

4. **Entity comparison edge cases** — `==` works for entity comparison in the Fusion API, but construction geometry, projected geometry, and reference geometry should be tested.
5. **Entity index stability** — Display labels like `Line #N` rely on collection indices. Verify these are stable across constraint deletions within the same session (they may shift as entities are removed). If unstable, fall back to `entityToken` or ordinal-at-command-open snapshot.
6. **Assembly-mode compatibility** — Autodesk's January 2026 API changes affect command visibility in assembly context. v1 is explicitly scoped to part/hybrid sketch editing. Assembly behavior should be tested if support is added later.

### Resolved

7. ~~**Dual SelectionCommandInput interaction**~~ — Deferred to future version. v1 uses "Related To" column text only.
8. ~~**`BoolValueCommandInput` as pseudo-button**~~ — Using `TableCommandInput.addToolbarCommandInput()` for the delete action instead.

## Scope & Compatibility

**v1 targets:** Part and hybrid sketch editing in Fusion's DESIGN workspace. The command requires an active sketch edit session — if no sketch is being edited when the command is invoked, it shows a message and exits.

**Assembly mode:** Not explicitly supported in v1. Command registration in the DESIGN workspace should still be visible, but assembly-context behavior is untested. See Open Question #6.

## Out of Scope (v1)

- Constraint creation (only viewing and deletion)
- Filtering or searching the constraint list
- Grouped display (geometric vs dimensional)
- **Viewport highlighting of related entities** (deferred — see Highlighting section)
- Custom highlight colors
- Keyboard shortcut registration
- Persistent preferences or settings

## Future Enhancements

- **Viewport highlighting** via `ui.activeSelections.add()` when table rows are checked
- Filter by constraint type
- "Select Similar" — find all entities with the same constraint type
- Bulk operations (delete all of type X)
- Upgrade to BrowserCommandInput or Palette for richer UI
- Custom graphics highlighting with configurable colors
