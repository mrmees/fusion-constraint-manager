# Phase 1: Engine and Tab Foundation - Research

**Researched:** 2026-03-22
**Domain:** Fusion 360 add-in — TabCommandInput migration, constraint engine extension, pytest mocking
**Confidence:** HIGH

## Summary

Phase 1 transforms a working single-view command dialog (v1.1) into a three-tab structure while extending the constraint engine with sketch-wide operations. The core risk is regression — the Selected Entities tab must work identically after migration into `TabCommandInput.children`. The engine extensions (sketch-wide enumeration, type grouping, type filtering) are pure logic with no Fusion UI dependency, making them fully testable outside Fusion with the existing mock infrastructure.

The Fusion API surface for this phase is well-documented and confirmed via official Autodesk references. `TabCommandInput` is the standard mechanism for tabbed dialogs; `sketch.geometricConstraints` provides the sketch-wide collection needed for new engine methods. The main implementation challenges are: (1) correctly routing `inputChanged` events in a multi-tab context, (2) preventing re-entrance when tab switches fire cascading events, and (3) keeping all existing v1.1 behavior intact within the new tab structure.

**Primary recommendation:** Build bottom-up — engine methods with tests first, then tab infrastructure with v1.1 migration, then placeholder UI for Types/All tabs. This order maximizes testable progress before touching Fusion UI code.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Tab labels are short: "Selected", "Types", "All"
- **D-02:** "Selected" tab is the default active tab on command launch (preserves v1 UX)
- **D-03:** "Types" and "All" tabs show placeholder UI in Phase 1 — empty table structure with no data/actions, validating the tab infrastructure works before features are built
- **D-04:** No tab auto-loads anything expensive. Each tab's data is lazy-loaded only when the user explicitly triggers it (entity selection for Selected, load button for Types and All)
- **D-05:** Per-tab state isolation — Claude's discretion on exact structure (dict per tab vs separate globals), but must keep the plugin lightweight with no background loading
- **D-06:** wire_handler() utility added — simple helper that creates handler, adds to event, appends to handler list. Zero runtime overhead, prevents GC handler loss with 3x more handlers in v2
- **D-07:** Re-entrance guard must handle tab switch events (InputChanged fires on tab switch)
- **D-08:** New engine methods built and fully tested in Phase 1 — not stubbed. De-risks Phase 2/3 so they can focus purely on UI
- **D-09:** Return formats are Claude's discretion — design what each tab actually needs (Types tab just needs type+count, not full constraint info dicts)
- **D-10:** All new engine methods must have pytest coverage runnable outside Fusion
- **D-11:** V1 code migrated into Tab 1 — all entity selection, constraint table, and deletion logic moves inside TabCommandInput children
- **D-12:** Verification is manual testing in Fusion — run the add-in, test entity selection and deletion by hand
- **D-13:** Rollback strategy is Claude's discretion (git revert is simplest given clean v1.1 commits)

### Claude's Discretion
- State organization pattern (D-05)
- Engine return formats per tab (D-09)
- Rollback approach (D-13)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ENGN-01 | Constraint engine supports sketch-wide enumeration via `sketch.geometricConstraints` collection | STACK.md confirms API: `sketch.geometricConstraints` returns `GeometricConstraints` with `.count` and `.item(i)`. New `enumerate_all_constraints()` function. |
| ENGN-02 | Constraint engine supports grouping/counting constraints by type | New `aggregate_constraint_types()` function — single pass reading `.objectType`, returns `{type_name: count}`. Reuses existing `get_constraint_type_name()`. |
| ENGN-03 | Constraint engine supports filtering constraints by type | New `filter_constraints_by_type()` function — filters a pre-enumerated list by type name. Pure list comprehension over cached data. |
| ENGN-04 | Bulk deletion uses reverse iteration to prevent forward-iteration collection re-index bug | Existing `delete_constraints()` already uses `reversed()`. New bulk-by-type deletion reuses this pattern. |
| TABS-01 | Command dialog displays three tabs: Selected Entities, Constraint Types, All Constraints | `inputs.addTabCommandInput(id, label)` creates tabs; children accessed via `tab.children`. Labels per D-01: "Selected", "Types", "All". |
| TABS-02 | Tab switching preserves per-tab state without re-enumeration | Per-tab module-level state variables; tab switch handler reads `_active_tab` to route, never re-enumerates. |
| TABS-03 | Per-tab state isolation — each tab maintains its own constraint list independently | Separate globals: `_selected_constraints`, `_type_summary`, `_all_constraints` (or dict-based equivalent per D-05). |
| TABS-04 | Handler GC protection utility to prevent garbage collection of event handlers across all tabs | `wire_handler(event, handler_class, handler_list)` utility per D-06. |
| ENTY-01 | Selected Entities tab preserves identical behavior to v1.1 — entity selection, constraint table, checkbox deletion | All existing `_on_selection_changed()`, `_on_select_all()`, `ExecuteHandler` logic moves inside tab1's children. Same IDs, same flow. |
| ENTY-02 | Selected Entities tab is the default active tab on command launch | First `addTabCommandInput()` call creates the default-active tab. No `activate()` needed — first tab is active by default. |
</phase_requirements>

## Standard Stack

### Core (Runtime-Provided)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python 3.x | Fusion-embedded | All add-in logic | Only option — Fusion's embedded interpreter |
| `adsk.core` | Fusion-provided | TabCommandInput, TableCommandInput, BoolValueCommandInput, event handlers | Required for tabbed dialog UI |
| `adsk.fusion` | Fusion-provided | Sketch.geometricConstraints, GeometricConstraints collection, Design.findEntityByToken | Required for sketch-wide constraint access |

### Development

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | Dev-only | Unit testing constraint engine outside Fusion | All engine method testing (D-10) |
| `logging` | stdlib | Debug logging | Already established in v1.1 |

### Installation

```bash
# Development only — no production deps beyond folder copy
pip install pytest
```

## Architecture Patterns

### Project Structure (Unchanged)

```
ConstraintManager/
  ConstraintManager.py           # Entry point (unchanged)
  commands/
    constraint_manager/
      __init__.py
      command.py                  # UI + event handlers (extended with tabs)
      constraint_engine.py        # Pure logic (extended with sketch-wide methods)
  tests/
    test_constraint_engine.py     # Unit tests (extended with new method tests)
```

No new files. All changes are extensions to existing files.

### Pattern 1: Tab-Aware Event Routing

**What:** Route `inputChanged` events based on active tab, not just input ID.
**When to use:** Any `inputChanged` handler in a multi-tab command.
**Why:** Prevents cross-tab event leakage and enables clean per-tab handler methods.

```python
# In InputChangedHandler.notify():
changed_input = args.input

# Tab switch events — TabCommandInput fires on activation
if changed_input.objectType.endswith('TabCommandInput'):
    if changed_input.isActive:
        self._on_tab_activated(changed_input.id, args.inputs)
    return

# Route to active tab's handler
if _active_tab == 'tab_selected':
    self._handle_selected_input(changed_input, args.inputs)
elif _active_tab == 'tab_types':
    self._handle_types_input(changed_input, args.inputs)
elif _active_tab == 'tab_all':
    self._handle_all_input(changed_input, args.inputs)
```

**Confidence:** HIGH — `TabCommandInput.isActive` and `objectType` confirmed in Autodesk docs.

### Pattern 2: wire_handler() GC Protection Utility (D-06)

**What:** Single-call helper that creates a handler, adds it to an event, and stores the reference.
**When to use:** Every event handler registration in v2.

```python
def _wire_handler(event, handler_class, handler_list):
    """Create handler, add to event, store reference to prevent GC."""
    handler = handler_class()
    event.add(handler)
    handler_list.append(handler)
    return handler
```

Usage replaces the current 3-line pattern:
```python
# Before (easy to forget the append):
input_changed = InputChangedHandler()
cmd.inputChanged.add(input_changed)
_cmd_handlers.append(input_changed)

# After:
_wire_handler(cmd.inputChanged, InputChangedHandler, _cmd_handlers)
```

**Confidence:** HIGH — straightforward Python helper, no API dependency.

### Pattern 3: Per-Tab State with Module-Level Dict

**What:** Single dict organizing state per tab instead of N separate globals.
**When to use:** Per D-05, Claude's discretion on structure.
**Recommendation:** Dict-based approach — cleaner to reset on destroy, easier to extend in Phase 2/3.

```python
# Module-level state
_tab_state = {
    'selected': {
        'constraints': [],      # List of constraint info dicts
    },
    'types': {
        'summary': {},          # {type_name: count}
    },
    'all': {
        'constraints': [],      # List of constraint info dicts
        'loaded': False,        # Whether Load has been clicked
    },
}
_active_tab = 'tab_selected'

# Clean reset on destroy
def _reset_tab_state():
    _tab_state['selected']['constraints'] = []
    _tab_state['types']['summary'] = {}
    _tab_state['all']['constraints'] = []
    _tab_state['all']['loaded'] = False
```

**Alternative:** Separate globals (`_selected_constraints`, `_type_summary`, `_all_constraints`). Simpler, matches v1.1 pattern, but messier to reset. Either works — dict is marginally cleaner.

**Confidence:** HIGH — pure Python pattern choice, no API dependency.

### Pattern 4: Moving Existing Inputs into Tab Children

**What:** Migrating v1.1 inputs from root `commandInputs` into `tab.children`.
**When to use:** The core migration task for ENTY-01.

```python
# Before (v1.1) — inputs on root:
inputs = cmd.commandInputs
entity_select = inputs.addSelectionInput('entitySelect', ...)
table = inputs.addTableCommandInput('constraintTable', ...)

# After (v2) — inputs on tab1's children:
tab1 = inputs.addTabCommandInput('tab_selected', 'Selected')
tab1_inputs = tab1.children
entity_select = tab1_inputs.addSelectionInput('entitySelect', ...)
table = tab1_inputs.addTableCommandInput('constraintTable', ...)
```

**Critical detail:** `args.inputs` in `InputChangedHandler.notify()` returns the **root** command inputs, NOT the tab's children. To access tab-specific inputs, use `args.inputs.itemById('tab_selected').children.itemById('constraintTable')`. However, `args.input` (singular) is the specific changed input regardless of which tab it belongs to.

**Confidence:** HIGH — `TabCommandInput.children` returns `CommandInputs` collection per official docs.

### Anti-Patterns to Avoid

- **Auto-loading on tab switch (D-04):** Types and All tabs must not auto-enumerate. Show placeholder text only.
- **Shared constraint list across tabs:** Each tab's data is independent. `_current_constraints` must become tab-specific.
- **Model mutations in inputChanged:** No `deleteMe()` calls outside the `execute` handler. This is a Fusion API rule that clears selections.
- **Forward iteration during deletion:** Always use `reversed()` or snapshot-then-delete. The existing `delete_constraints()` pattern is correct.

## Engine API Design (D-08, D-09)

### New Functions for constraint_engine.py

```python
def aggregate_constraint_types(geometric_constraints):
    """Count constraints by type across a sketch's geometric constraints.

    Args:
        geometric_constraints: A GeometricConstraints collection
            (sketch.geometricConstraints).

    Returns:
        dict mapping type display name to count.
        e.g., {"Fix": 87, "Horizontal": 12, "Coincident": 45}
    """

def enumerate_all_constraints(geometric_constraints, index_finder):
    """Enumerate every constraint in a sketch with full metadata.

    Args:
        geometric_constraints: A GeometricConstraints collection.
        index_finder: Callable(entity) -> int for entity label resolution.

    Returns:
        list of constraint info dicts (same schema as enumerate_constraints).
    """

def filter_constraints_by_type(constraints, type_name):
    """Filter a pre-enumerated constraint list by type.

    Args:
        constraints: List of constraint info dicts.
        type_name: Display name to filter by (e.g., "Fix").

    Returns:
        Filtered list of constraint info dicts.
    """

def collect_constraints_by_type(geometric_constraints, type_name):
    """Collect raw constraint objects of a specific type for bulk deletion.

    Args:
        geometric_constraints: A GeometricConstraints collection.
        type_name: Display name of the constraint type.

    Returns:
        list of constraint objects (raw Fusion objects, not info dicts).
    """
```

**Design rationale for return formats (D-09):**
- `aggregate_constraint_types` returns `{str: int}` — Types tab only needs type name and count, not full constraint metadata.
- `enumerate_all_constraints` returns same schema as existing `enumerate_constraints` — All Constraints tab needs the same display info.
- `filter_constraints_by_type` operates on already-enumerated data — pure Python filtering, no Fusion API calls.
- `collect_constraints_by_type` returns raw constraint objects — deletion needs the objects, not display info.

**Key difference from per-entity enumeration:** These methods take the sketch-level `geometric_constraints` collection directly, not an individual entity. The constraint's `.objectType` identifies its type. For `enumerate_all_constraints`, building the "related entity" label requires determining which entities a constraint references — this uses the same `_CONSTRAINT_ENTITY_PROPS` map but reads the constraint's entity properties directly rather than knowing which entity was "selected."

**Confidence:** HIGH — builds on confirmed API surface and existing engine patterns.

### Modified _build_constraint_info for Sketch-Wide Context

The existing `_build_constraint_info(constraint, selected_entity, index_finder)` takes a `selected_entity` to resolve "related" entities. For sketch-wide enumeration, there is no "selected" entity — the constraint stands alone. Options:

**Recommendation:** Create `_build_sketch_constraint_info(constraint, index_finder)` that labels ALL referenced entities instead of labeling the "other" one. For a ParallelConstraint, instead of "Line #3" (relative to selected), show "Line #0 -- Line #3" (both entities). This is more informative for the All Constraints tab where there's no selection context.

```python
def _build_sketch_constraint_info(constraint, index_finder):
    """Build display info for a constraint in sketch-wide context (no selected entity)."""
    type_name = get_constraint_type_name(constraint.objectType)
    type_key = constraint.objectType.split('::')[-1]
    props = _CONSTRAINT_ENTITY_PROPS.get(type_key)

    entities_label = '--'
    if props:
        labels = []
        for prop in props:
            entity = getattr(constraint, prop, None)
            if entity:
                labels.append(get_entity_label(entity, index_finder(entity)))
        entities_label = ', '.join(labels) if labels else '--'

    return {
        'constraint': constraint,
        'entity_token': getattr(constraint, 'entityToken', None),
        'type_name': type_name,
        'entities_label': entities_label,  # Note: different key than 'related_label'
        'is_deletable': getattr(constraint, 'isDeletable', False),
    }
```

**Confidence:** HIGH — pure logic extension of existing pattern.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tab UI framework | Custom visibility toggling on GroupCommandInputs | `TabCommandInput` | Native Fusion tab behavior, automatic tab switching events, proper visual separation |
| GC handler protection | Per-handler manual append | `wire_handler()` utility (D-06) | Single point of failure prevention, can't forget the append |
| Constraint type name mapping | New type lookup | Existing `get_constraint_type_name()` | Already strips namespace and "Constraint" suffix |
| Reverse-order deletion | Custom deletion loop | Existing `delete_constraints()` | Already handles reverse iteration, `isValid`/`isDeletable` checks, failure counting |
| Entity label formatting | New label builder | Existing `get_entity_label()` | Already handles type prefix + construction flag + index |

## Common Pitfalls

### Pitfall 1: Tab Children vs Root CommandInputs

**What goes wrong:** After migrating to tabs, code that accesses `inputs.itemById('constraintTable')` returns `None` because the table now lives inside `tab1.children`, not the root inputs.
**Why it happens:** `args.inputs` in event handlers returns root command inputs. Tab children are a separate `CommandInputs` collection.
**How to avoid:** Access tab-specific inputs via `inputs.itemById('tab_selected').children.itemById('constraintTable')`. Or store tab children references during `CommandCreated`.
**Warning signs:** `NoneType has no attribute` errors when trying to access table or selection input after migration.

### Pitfall 2: Re-Entrance on Tab Switch (D-07)

**What goes wrong:** Tab switch fires `inputChanged` with `TabCommandInput` as the changed input. If the handler then modifies other inputs (showing/hiding, updating text), those modifications fire additional `inputChanged` events.
**Why it happens:** Fusion delivers secondary events after the current handler returns and the `_handling_change` guard is cleared.
**How to avoid:** Keep tab switch handling minimal — just update `_active_tab` tracking variable. Don't modify inputs during tab switch. Phase 1 placeholder tabs should have no dynamic content, making this low-risk initially.
**Warning signs:** Dialog flickers, stack overflows, stale data appearing briefly.

### Pitfall 3: First Tab is Default Active (ENTY-02)

**What goes wrong:** Developer calls `tab1.activate()` explicitly in `CommandCreated`, which fires an `inputChanged` event before the handler is wired.
**Why it happens:** The first `addTabCommandInput()` call creates a tab that is active by default. Calling `activate()` is redundant and triggers an event at a time when handlers may not be ready.
**How to avoid:** Don't call `activate()` on the first tab. Just create tabs in order: Selected first, Types second, All third. The first tab is automatically active.
**Warning signs:** Error in `inputChanged` handler during command creation, or silent event swallowed by missing handler.

### Pitfall 4: SelectionCommandInput Not Supported in Tables

**What goes wrong:** Attempting to add a SelectionCommandInput inside a TableCommandInput fails silently or throws.
**Why it happens:** Official docs state "Selection and button row command inputs are not supported in a table."
**How to avoid:** Keep the SelectionCommandInput at the tab level (inside `tab.children`), not inside the table. This is already the v1.1 pattern.
**Warning signs:** Selection input doesn't appear or doesn't respond to clicks.

### Pitfall 5: entityToken is None for Some Constraint Types

**What goes wrong:** `getattr(constraint, 'entityToken', None)` returns `None` for certain system-generated or internal constraints.
**Why it happens:** Not all constraint objects expose stable tokens. Fixed constraints on the origin point, for example, may behave differently.
**How to avoid:** Always check for `None` token before storing. In `aggregate_constraint_types`, this doesn't matter (just counting). In `enumerate_all_constraints`, skip or flag constraints with no token.
**Warning signs:** `findEntityByToken(None)` call, or deletion silently fails on certain constraints.

## Code Examples

### Tab Creation in CommandCreatedHandler

```python
# Source: STACK.md + official Autodesk TabCommandInput docs
def notify(self, args):
    cmd = args.command
    inputs = cmd.commandInputs

    # Create three tabs (D-01 labels, D-02 ordering)
    tab_selected = inputs.addTabCommandInput('tab_selected', 'Selected')
    tab_types = inputs.addTabCommandInput('tab_types', 'Types')
    tab_all = inputs.addTabCommandInput('tab_all', 'All')

    # Selected tab children — migrate v1.1 inputs here
    sel_inputs = tab_selected.children
    entity_select = sel_inputs.addSelectionInput(
        'entitySelect', 'Select Entities', 'Click sketch entities'
    )
    # ... same setup as v1.1 ...

    # Types tab placeholder (D-03)
    types_inputs = tab_types.children
    types_inputs.addTextBoxCommandInput(
        'typesPlaceholder', '', 'Constraint type summary will appear here.', 1, True
    )

    # All tab placeholder (D-03)
    all_inputs = tab_all.children
    all_inputs.addTextBoxCommandInput(
        'allPlaceholder', '', 'Full constraint list will appear here.', 1, True
    )
```

### aggregate_constraint_types Test Pattern

```python
# Test mock for sketch-wide constraint collection
class MockGeometricConstraints:
    """Mock for sketch.geometricConstraints (sketch-level collection)."""
    def __init__(self, constraints):
        self._items = constraints

    @property
    def count(self):
        return len(self._items)

    def item(self, index):
        return self._items[index]


def test_aggregate_constraint_types_basic():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        aggregate_constraint_types,
    )
    constraints = MockGeometricConstraints([
        MockConstraint('HorizontalConstraint'),
        MockConstraint('HorizontalConstraint'),
        MockConstraint('FixConstraint'),
        MockConstraint('ParallelConstraint'),
    ])
    result = aggregate_constraint_types(constraints)
    assert result == {'Horizontal': 2, 'Fix': 1, 'Parallel': 1}


def test_aggregate_constraint_types_empty():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        aggregate_constraint_types,
    )
    constraints = MockGeometricConstraints([])
    result = aggregate_constraint_types(constraints)
    assert result == {}
```

### wire_handler Usage

```python
# In CommandCreatedHandler.notify():
_wire_handler(cmd.inputChanged, InputChangedHandler, _cmd_handlers)
_wire_handler(cmd.preSelect, PreSelectHandler, _cmd_handlers)
_wire_handler(cmd.execute, ExecuteHandler, _cmd_handlers)
_wire_handler(cmd.destroy, DestroyHandler, _cmd_handlers)
```

## State of the Art

| Old Approach (v1.1) | Current Approach (v2 Phase 1) | Impact |
|----------------------|-------------------------------|--------|
| Single flat dialog | Three-tab `TabCommandInput` | Enables constraint type and sketch-wide workflows |
| Per-entity enumeration only | + Sketch-wide `geometricConstraints` access | Enables Types tab counting and All tab listing |
| Single `_current_constraints` list | Per-tab state dict | Prevents cross-tab state corruption |
| Manual 3-line handler wiring | `wire_handler()` utility | Eliminates GC handler loss as handler count grows |
| Instance-level `_handling_change` | + Tab switch awareness (D-07) | Prevents re-entrance from tab switch cascades |

## Open Questions

1. **Tab children input access pattern in event handlers**
   - What we know: `args.inputs` returns root command inputs; tab children are separate.
   - What's unclear: Whether `inputs.itemById('entitySelect')` traverses into tab children or only searches root level. If root-only, all `itemById` calls in existing code need updating.
   - Recommendation: Test empirically during implementation. If root-only, store tab children references in module-level variables during `CommandCreated`.

2. **Tab switch event timing with _handling_change guard**
   - What we know: Tab switches fire `inputChanged`. The current guard is instance-level and resets after each `notify()` call.
   - What's unclear: Whether Fusion queues secondary events or delivers them synchronously.
   - Recommendation: Start with the existing guard pattern. If re-entrance occurs, escalate to a module-level `_switching_tabs` flag.

3. **Performance of _build_sketch_constraint_info entity property access**
   - What we know: Reading constraint entity properties (`.line`, `.lineOne`, `.lineTwo`) is fast per-access.
   - What's unclear: Whether property access on 2000+ constraints causes noticeable delay.
   - Recommendation: Build it straightforward first. Optimize only if empirical testing shows delay. This is Phase 2/3 concern anyway — Phase 1 only needs `aggregate_constraint_types` which doesn't resolve entity labels.

## Project Constraints (from CLAUDE.md)

- **No external dependencies in production** — Fusion's embedded Python interpreter is the runtime; `pytest` is dev-only
- **Python version caution** — Fusion's runtime may be pinned to 3.9.x; avoid 3.10+ syntax (match/case, `X | Y` union types)
- **Commit/push requires permission** — Ask before committing or pushing to git
- **Double quotes for strings** — Established convention in codebase
- **Bare except clauses** — Acceptable for Fusion API robustness but log with `traceback.format_exc()`
- **Module-level state** — Standard pattern for cross-handler communication in Fusion add-ins
- **No linter enforced** — Follow implicit PEP 8 (4-space indent, ~100 char lines)

## Sources

### Primary (HIGH confidence)
- [Autodesk: TabCommandInput Object](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/TabCommandInput.htm) — `isActive`, `children`, `activate()` properties
- [Autodesk: Command Inputs](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CommandInputs_UM.htm) — Tab grouping, input limitations in tables
- [Autodesk: Sketch.geometricConstraints](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Sketch_geometricConstraints.htm) — Sketch-wide constraint collection API
- [Autodesk: GeometricConstraints Object](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/GeometricConstraints.htm) — `.count`, `.item(i)` collection API
- [Autodesk: Python Specific Issues](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/PythonSpecific_UM.htm) — GC handler loss documentation
- Project research: `.planning/research/STACK.md`, `ARCHITECTURE.md`, `PITFALLS.md`
- Existing codebase: `command.py` (419 lines), `constraint_engine.py` (247 lines), `test_constraint_engine.py` (338 lines, 30 tests passing)

### Secondary (MEDIUM confidence)
- [Autodesk Forum: deleteMe iteration bug](https://forums.autodesk.com/t5/fusion-api-and-scripts-forum/deleteme-method-not-deleting-all-sketch-curves-in-for-loop/td-p/10941332) — Forward-iteration deletion skipping confirmed by community
- [Autodesk: Command Inputs API Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CommandInputsSample_Sample.htm) — Tab creation code samples

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Fusion API is the only option, well-documented
- Architecture: HIGH — extending proven v1.1 patterns, no new external dependencies
- Engine API design: HIGH — pure Python logic, fully testable with existing mock infrastructure
- Tab migration: HIGH for API surface, MEDIUM for event routing edge cases (need empirical validation)
- Pitfalls: HIGH — well-documented in project research and Autodesk forums

**Research date:** 2026-03-22
**Valid until:** Indefinite — Fusion API is stable, no version-dependent concerns
