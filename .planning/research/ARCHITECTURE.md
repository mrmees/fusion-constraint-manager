# Architecture Patterns

**Domain:** Fusion 360 desktop add-in with tabbed constraint management UI
**Researched:** 2026-03-22

## Recommended Architecture

### High-Level Structure

```
Entry Point (ConstraintManager.py)
  |
  v
Command & UI Layer (command.py)
  |-- Tab Controller logic (tab creation, tab-switch handling)
  |-- Per-tab UI builders (Selected Entities, Constraint Types, All Constraints)
  |-- Event handlers (InputChanged, PreSelect, Execute, Destroy)
  |
  v
Constraint Engine (constraint_engine.py)
  |-- Per-entity enumeration (existing)
  |-- Sketch-wide enumeration (NEW)
  |-- Type aggregation / counting (NEW)
  |-- Bulk deletion by type (NEW)
  |
  v
Fusion 360 API (adsk.core, adsk.fusion)
```

The existing two-layer separation (command.py for UI, constraint_engine.py for logic) is the right pattern and should be preserved. The key evolution is that command.py grows tab-management responsibilities, and constraint_engine.py gains sketch-wide enumeration functions.

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `command.py` - Tab Controller | Create 3 tabs, detect tab switches via `inputChanged`, route events to per-tab handlers | All tab UI builders, Fusion event system |
| `command.py` - Selected Entities Tab | Existing v1 behavior: selection input, per-entity constraint table, checkboxes | Constraint engine (per-entity enumeration) |
| `command.py` - Constraint Types Tab | Type summary table with counts and Delete All buttons per type | Constraint engine (sketch-wide type aggregation) |
| `command.py` - All Constraints Tab | Load button, full constraint table with type filter dropdown, checkboxes | Constraint engine (sketch-wide enumeration) |
| `constraint_engine.py` | All constraint logic: enumeration, labeling, counting, deletion | Fusion API model objects only (no UI imports) |
| `ConstraintManager.py` | Bootstrap, toolbar registration, lifecycle | command.py start/stop |

### Why Not Split command.py Into Multiple Files

Tempting to split each tab into its own module, but don't. Fusion's event system passes a single `CommandInputs` collection that spans all tabs. The `inputChanged` handler needs to see inputs from every tab to route correctly, and the `execute` handler needs to know which tab is active to decide what to delete. Splitting into separate files would create circular dependencies or require a shared state module that adds complexity without benefit. Keep it in one file with clear internal structure (methods per tab, not classes per tab).

## Data Flow

### Tab Switch Detection

**Finding (MEDIUM confidence):** When a user clicks a tab, Fusion fires `inputChanged` with the `TabCommandInput` as the changed input. You detect which tab activated by checking `changed_input.id` against tab IDs, and can verify with `tab.isActive`. The `TabCommandInput` object has:
- `isActive` (read-only): Returns whether this tab is currently selected
- `children`: Returns the `CommandInputs` collection for this tab
- `activate()`: Programmatically selects this tab

```python
# In InputChangedHandler.notify():
if changed_input.id in ("tab_selected", "tab_types", "tab_all"):
    self._on_tab_switched(inputs, changed_input.id)
```

### Selected Entities Tab (Unchanged)

```
User selects entity in viewport
  -> InputChanged fires (entitySelect changed)
  -> enumerate_constraints(entity) per entity
  -> Deduplicate by entityToken
  -> Populate table
  -> User checks rows, clicks Delete Selected
  -> ExecuteHandler re-resolves tokens, deletes
```

No changes to this flow. The selection input and table live inside the tab's `children` collection instead of the top-level `inputs`, but the logic is identical.

### Constraint Types Tab

```
User switches to Constraint Types tab
  -> InputChanged fires (tab_types changed)
  -> aggregate_constraint_types(sketch) called
     -> sketch.geometricConstraints iteration (count + item())
     -> Returns: {"Horizontal": 12, "Fix": 87, "Coincident": 45, ...}
  -> Populate summary table: Type | Count | [Delete All] button
  -> User clicks "Delete All Fix"
  -> InputChanged fires (deleteAll_Fix button changed)
  -> Collect all Fix constraints from sketch.geometricConstraints
  -> Delete batch, refresh table
```

**Key design decision:** The type aggregation is lightweight -- just iterating `sketch.geometricConstraints` once, reading `objectType` on each, and counting. No entity resolution needed. This should populate instantly even for large sketches (thousands of constraints iterate in milliseconds since it's just reading a property).

### All Constraints Tab

```
User switches to All Constraints tab
  -> InputChanged fires (tab_all changed)
  -> Show empty table + Load button + type filter dropdown
  -> User clicks Load button
  -> InputChanged fires (loadAllBtn changed)
  -> enumerate_all_constraints(sketch) called
     -> sketch.geometricConstraints full iteration
     -> For each: resolve type, entity labels, deletability
     -> Returns list of constraint info dicts
  -> Populate table with all constraints
  -> User selects type in dropdown filter
  -> InputChanged fires (typeFilter changed)
  -> Filter _all_constraints list by type, rebuild table rows
  -> User checks rows, clicks Delete Selected
  -> ExecuteHandler re-resolves tokens, deletes
```

**Why the Load button matters:** Entity label resolution (`_find_entity_index`) iterates parent collections per constraint. For a sketch with 500 entities and 2000 constraints, that's 2000 collection scans. The Load button makes this an explicit user action, not something triggered by tab switch.

## State Management

### Module-Level State (Extended)

```python
# Existing
_current_constraints = []    # Selected Entities tab constraint list
_cmd_handlers = []           # Event handler GC prevention
_addin_handlers = []         # Lifecycle handler GC prevention

# New for v2
_type_summary = {}           # Constraint Types tab: {"Fix": 87, "Horizontal": 12, ...}
_all_constraints = []        # All Constraints tab: full constraint info list
_all_constraints_loaded = False  # Whether Load has been clicked
_active_tab = "tab_selected"    # Track which tab is active for Execute routing
```

### Why Separate State Per Tab

Each tab operates on a different constraint set:
- **Selected Entities** operates on constraints from selected entities only (subset)
- **Constraint Types** operates on aggregated counts (summary data)
- **All Constraints** operates on every constraint in the sketch (full set)

Sharing a single `_current_constraints` list would require constant rebuilding when switching tabs and introduce bugs where the Execute handler deletes from the wrong set. Keep them separate.

### Execute Handler Routing

The Execute handler (OK button / "Delete Selected") needs to know which tab is active to decide what to delete:

```python
def notify(self, args):
    if _active_tab == "tab_selected":
        self._delete_selected_constraints(_current_constraints, inputs)
    elif _active_tab == "tab_types":
        # Type tab uses per-type delete buttons, not the OK button
        # OK button on this tab = no-op or close dialog
        pass
    elif _active_tab == "tab_all":
        self._delete_selected_constraints(_all_constraints, inputs)
```

**Important nuance:** The Constraint Types tab uses inline "Delete All" buttons per type row, not the dialog's OK button. Those delete actions fire through `inputChanged`, not `execute`. This means type deletion happens inside `InputChangedHandler`, not `ExecuteHandler`. Use a confirmation pattern (button click sets a flag, second click or OK confirms) to prevent accidental bulk deletion.

## Sketch-Wide Constraint Enumeration Strategy

### The API Surface

**Confirmed (HIGH confidence):** `Sketch.geometricConstraints` returns a `GeometricConstraints` collection containing ALL geometric constraints in the sketch. This is the sketch-wide collection -- not per-entity.

- `sketch.geometricConstraints.count` -- total number of geometric constraints
- `sketch.geometricConstraints.item(i)` -- access by index
- Each constraint has `.objectType` for type identification and `.entityToken` for stable references

This is the exact API needed for tabs 2 and 3. The current v1 code only uses `entity.geometricConstraints` (per-entity), but the sketch-level collection exists and provides direct access.

### New Engine Functions Needed

```python
# constraint_engine.py additions:

def aggregate_constraint_types(sketch):
    """Count constraints by type across entire sketch.

    Returns: dict mapping type display name -> count
    e.g., {"Fix": 87, "Horizontal": 12, "Coincident": 45}
    """

def enumerate_all_constraints(sketch, index_finder):
    """Enumerate every constraint in the sketch with full metadata.

    Returns: list of constraint info dicts (same format as enumerate_constraints)
    """

def collect_constraints_by_type(sketch, type_name):
    """Collect all constraint objects of a specific type for bulk deletion.

    Returns: list of constraint objects (not info dicts -- raw objects for deletion)
    """
```

### Performance Characteristics

| Operation | Sketch Size | Expected Cost | Notes |
|-----------|-------------|---------------|-------|
| `aggregate_constraint_types()` | 2000 constraints | ~5ms | Just reads `.objectType`, no entity resolution |
| `enumerate_all_constraints()` | 2000 constraints | ~500-2000ms | Entity label resolution is the bottleneck |
| `collect_constraints_by_type()` | 2000 constraints, 500 Fix | ~5ms | Just reads `.objectType`, collects matching |
| Bulk delete 500 constraints | 500 Fix constraints | ~200-500ms | `.deleteMe()` per constraint, Fusion handles undo |

The expensive operation is `enumerate_all_constraints()` because `_find_entity_index()` iterates parent collections. For 2000 constraints, each needing 1-2 entity label lookups, and each lookup scanning a collection of ~100 items, that's ~200K-400K iterations. Not catastrophic but noticeable. The Load button pattern is correct.

### Optimization: Index Cache

Build an entity index cache once per load operation instead of scanning collections repeatedly:

```python
def _build_entity_index_cache(sketch):
    """Pre-build a lookup from entity to its collection index.

    Returns: dict mapping entity -> index
    """
    cache = {}
    for collection_name, getter in _COLLECTION_GETTERS.items():
        collection = getter(sketch)
        for i in range(collection.count):
            cache[collection.item(i)] = i
    return cache
```

This turns O(N*M) entity lookups into O(N+M) -- one pass to build the cache, then O(1) lookups. For the All Constraints tab this could reduce load time from seconds to tens of milliseconds.

## Patterns to Follow

### Pattern 1: Tab-Aware Event Routing

**What:** Route `inputChanged` events based on which tab is active, not just which input changed.
**When:** Any multi-tab command dialog.
**Why:** Inputs across tabs can have ID collisions if you're not careful, and the same OK button means different things on different tabs.

```python
def notify(self, args):
    changed_input = args.input

    # Tab switch events
    if isinstance(changed_input, adsk.core.TabCommandInput):
        self._on_tab_switched(changed_input)
        return

    # Route to active tab's handler
    if _active_tab == "tab_selected":
        self._handle_selected_entities_input(changed_input, args.inputs)
    elif _active_tab == "tab_types":
        self._handle_types_input(changed_input, args.inputs)
    elif _active_tab == "tab_all":
        self._handle_all_constraints_input(changed_input, args.inputs)
```

### Pattern 2: Lazy Loading with Explicit Trigger

**What:** Don't populate expensive UI content until user explicitly requests it.
**When:** Data requires iteration over large collections.

```python
def _handle_all_constraints_input(self, changed_input, inputs):
    if changed_input.id == "loadAllBtn":
        self._load_all_constraints(inputs)
    elif changed_input.id == "typeFilter":
        self._apply_type_filter(inputs)
```

### Pattern 3: Inline Action Buttons via BoolValueInput

**What:** Fusion has no real "button" input for table rows. Use `BoolValueInput` (checkbox-style) as a clickable action trigger -- it fires `inputChanged` when clicked, then immediately reset its value.
**When:** Need per-row actions like "Delete All of Type."

```python
# Create "Delete All" button for each type row
btn = row_inputs.addBoolValueInput(
    f"deleteAll_{type_name}", "Delete All", False, "", False
)

# In inputChanged handler:
if changed_input.id.startswith("deleteAll_"):
    type_name = changed_input.id.replace("deleteAll_", "")
    self._delete_all_of_type(type_name, inputs)
    changed_input.value = False  # Reset button state
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Auto-Loading All Constraints on Tab Switch

**What:** Populating the All Constraints table every time the user switches to that tab.
**Why bad:** Tab switches should feel instant. If auto-loading takes 1-2 seconds on a large sketch, the UI feels broken. Users may switch tabs just to glance, not to interact.
**Instead:** Show an empty state with a Load button. Cache results after first load. Only re-load if user explicitly clicks Load again.

### Anti-Pattern 2: Shared Constraint List Across Tabs

**What:** Using a single `_current_constraints` list for all three tabs.
**Why bad:** The Execute handler won't know which constraints the user selected. Tab switches would require rebuilding the list. Race conditions between tab state and deletion targets.
**Instead:** Separate state per tab with explicit naming: `_selected_constraints`, `_type_summary`, `_all_constraints`.

### Anti-Pattern 3: Re-Enumerating on Every InputChanged

**What:** Calling `sketch.geometricConstraints` iteration inside every `inputChanged` call.
**Why bad:** `inputChanged` fires for checkbox toggles, dropdown changes, button clicks. Re-enumerating thousands of constraints on each checkbox click would make the UI unresponsive.
**Instead:** Enumerate once (on Load or on tab switch for Types), store results, filter/display from cached state.

### Anti-Pattern 4: Deleting Constraints While Iterating

**What:** Iterating `sketch.geometricConstraints` and calling `.deleteMe()` during iteration.
**Why bad:** Deleting modifies the collection, invalidating indices. Constraint at index 5 becomes the constraint that was at index 6.
**Instead:** Collect all targets first (by entityToken), then delete from a separate list. The existing `delete_constraints()` function already handles this correctly by iterating in reverse.

## Suggested Build Order

Dependencies flow downward -- build bottom-up:

### Step 1: Constraint Engine Extensions (No UI)

Add to `constraint_engine.py`:
1. `aggregate_constraint_types(sketch)` -- count by type
2. `enumerate_all_constraints(sketch, index_finder)` -- full sketch enumeration
3. `collect_constraints_by_type(sketch, type_name)` -- bulk collection for deletion
4. `_build_entity_index_cache(sketch)` -- performance optimization

**Why first:** These are testable without Fusion UI. Write unit tests with mocks. The constraint engine has zero UI dependencies by design.

### Step 2: Tab Infrastructure in command.py

1. Replace flat `inputs` creation with three `TabCommandInput` instances
2. Move existing selection input + table into Selected Entities tab's `children`
3. Add `_active_tab` tracking in `InputChangedHandler`
4. Verify Selected Entities tab still works identically to v1.1

**Why second:** Validates the tab framework without new features. If tabs break existing behavior, catch it before adding new tabs.

### Step 3: Constraint Types Tab

1. Create summary table inside Types tab `children`
2. Wire `aggregate_constraint_types()` to tab activation
3. Add per-type Delete All buttons
4. Implement bulk deletion through `collect_constraints_by_type()` + `delete_constraints()`
5. Refresh summary after deletion

**Why third:** This is the killer feature for the DXF/SVG import audience. Simpler than All Constraints (no filtering, no entity labels in the table, no Load button). Validates sketch-wide enumeration at a low UI complexity level.

### Step 4: All Constraints Tab

1. Create Load button, type filter dropdown, and constraint table
2. Wire `enumerate_all_constraints()` to Load button click
3. Implement dropdown filter (rebuild table from cached `_all_constraints`)
4. Wire checkbox selection + Execute handler routing
5. Add entity index cache optimization if performance warrants it

**Why last:** Most complex tab. Depends on all engine functions from Step 1. Can be validated against the Constraint Types tab's data (same sketch, counts should match).

## Scalability Considerations

| Concern | 50 entities / 100 constraints | 200 entities / 1000 constraints | 500+ entities / 2000+ constraints |
|---------|-------------------------------|----------------------------------|-----------------------------------|
| Type aggregation | Instant | Instant | Instant (~5ms) |
| All Constraints load | Instant | ~200ms | ~1-2s (needs Load button) |
| Table rendering (Fusion) | Fine | Fine | May hit Fusion table limits -- cap at ~500 rows with "showing first 500" message |
| Bulk type deletion | Instant | ~100ms | ~500ms (acceptable) |
| Selected Entities tab | Unchanged from v1 | Unchanged | Unchanged |

**Fusion table row limit:** Fusion's `TableCommandInput` doesn't have a documented hard limit on rows, but rendering hundreds of rows with embedded command inputs (checkboxes, text fields) will slow down dialog rendering. Consider capping All Constraints table at 500 rows with a note "Showing first 500 of 2000 constraints. Use type filter to narrow results." This is a pragmatic limit, not an API limit.

## Sources

- [Fusion Help: Sketch.geometricConstraints Property](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Sketch_geometricConstraints.htm) -- confirms sketch-level collection
- [Fusion Help: GeometricConstraints Object](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/GeometricConstraints.htm) -- collection API (count, item)
- [Fusion Help: TabCommandInput Object](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/TabCommandInput.htm) -- isActive, children, activate properties
- [Fusion Help: Command Inputs API Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CommandInputsSample_Sample.htm) -- tab creation pattern
- [Fusion Help: Command Inputs User Manual](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CommandInputs_UM.htm) -- tab grouping documentation
- [Fusion Help: Command.inputChanged Event](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Command_inputChanged.htm) -- event routing

---

*Architecture analysis: 2026-03-22*
