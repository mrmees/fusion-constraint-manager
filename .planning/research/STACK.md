# Technology Stack

**Project:** Constraint Manager v2.0
**Researched:** 2026-03-22

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python 3.x (Fusion embedded) | Runtime-provided | All add-in logic | No choice here -- Fusion's embedded interpreter is the only option. No external deps allowed in production. |
| `adsk.core` | Runtime-provided | Command UI framework, event handlers, all dialog inputs | Required for TabCommandInput, TableCommandInput, DropDownCommandInput, BoolValueCommandInput |
| `adsk.fusion` | Runtime-provided | Sketch/constraint model access | Required for Sketch.geometricConstraints, GeometricConstraints collection, Design.findEntityByToken |

### UI Components for v2 (All from `adsk.core`)

| Class | Purpose | Confidence | Why This One |
|-------|---------|------------|--------------|
| **TabCommandInput** | Three-tab dialog (Selected Entities / Constraint Types / All Constraints) | HIGH | The only Fusion API mechanism for tabbed command dialogs. Creates separate input spaces via `.children` property. Supports `.isActive` to detect current tab, `.activate()` to programmatically switch tabs. Tab switches fire `inputChanged` with the tab as `args.input`. |
| **TableCommandInput** | Constraint tables within each tab (checkbox rows, sortable-ish columns) | HIGH | Already used in v1. Only option for structured row/column display of command inputs. Key methods: `addCommandInput()`, `deleteRow()`, `getInputAtPosition()`, `addToolbarCommandInput()`, `.selectedRow`, `.rowCount`. |
| **DropDownCommandInput** (TextListDropDownStyle) | Type filter on "All Constraints" tab | HIGH | `TextListDropDownStyle` is correct for dynamic content lists. Populate with constraint type names discovered at load time. Selection change fires `inputChanged`. Use `.selectedItem` to read current filter. |
| **BoolValueCommandInput** (checkbox mode) | Per-row delete checkboxes in constraint tables | HIGH | Already used in v1. `isCheckBox=True` for table row checkboxes. `isCheckBox=False` with no resource folder for text-only click buttons (Select All, Load, Delete All). |
| **BoolValueCommandInput** (button mode) | "Load Constraints" button, "Select All" button, "Delete All [Type]" actions | HIGH | Text-only button: `addBoolValueInput(id, label, False, "", False)`. Click fires `inputChanged`, value auto-resets. Already proven in v1 for Select All. |
| **StringValueCommandInput** (read-only) | Table cell text display (entity names, type names, related entities, counts) | HIGH | Already used in v1. Set `.isReadOnly = True` for display-only text cells in tables. |
| **TextBoxCommandInput** | Status messages ("No constraints found", "Loading...", count summaries) | HIGH | Already used in v1 for "no constraints" message. Good for non-interactive display text. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `logging` (stdlib) | Python stdlib | Debug logging for constraint enumeration, deletion, event handling | Always -- already established in v1 |
| `traceback` (stdlib) | Python stdlib | Error capture for user-facing error messages | Already established in v1 |
| `pytest` | Dev only | Unit testing constraint engine logic outside Fusion | Development only -- not shipped |

## API Method Reference (v2-Specific)

### TabCommandInput Creation and Usage

```python
# Creation -- add tabs to command inputs
tab1 = inputs.addTabCommandInput('tab_selected', 'Selected Entities')
tab2 = inputs.addTabCommandInput('tab_types', 'Constraint Types')
tab3 = inputs.addTabCommandInput('tab_all', 'All Constraints')

# Add inputs to a specific tab via .children
tab1_inputs = tab1.children
table1 = tab1_inputs.addTableCommandInput('selectedTable', 'Constraints', 4, '1:3:3:3')

# Detect tab switch in inputChanged handler
if changed_input.objectType.endswith('TabCommandInput'):
    if changed_input.id == 'tab_types' and changed_input.isActive:
        # User switched to Constraint Types tab
        populate_types_tab(inputs)

# Programmatic tab switch
tab2.activate()
```

**Confidence:** HIGH -- `isActive`, `activate()`, and `children` confirmed via official Autodesk API reference for TabCommandInput.

### DropDownCommandInput for Type Filtering

```python
# Creation inside tab's children
tab3_inputs = tab3.children
type_filter = tab3_inputs.addDropDownCommandInput(
    'typeFilter', 'Filter by Type',
    adsk.core.DropDownStyles.TextListDropDownStyle
)

# Populate dynamically after loading constraints
type_filter.listItems.add('All Types', True)  # selected=True for default
type_filter.listItems.add('Fix', False)
type_filter.listItems.add('Horizontal', False)

# Read selection in inputChanged
if changed_input.id == 'typeFilter':
    selected = changed_input.selectedItem
    if selected:
        filter_type = selected.name  # 'All Types', 'Fix', etc.
        rebuild_filtered_table(filter_type)
```

**Confidence:** HIGH -- `TextListDropDownStyle`, `listItems.add()`, and `selectedItem` confirmed via official docs.

### TableCommandInput Toolbar Buttons

```python
# "Delete All" button for Constraint Types tab -- use table toolbar
delete_all_btn = tab2_inputs.addBoolValueInput('deleteAllType', 'Delete All of Type', False, '', False)
types_table.addToolbarCommandInput(delete_all_btn)

# "Load Constraints" button for All Constraints tab
load_btn = tab3_inputs.addBoolValueInput('loadAll', 'Load All Constraints', False, '', False)
```

**Confidence:** HIGH -- `addToolbarCommandInput()` confirmed on TableCommandInput. Creates a button in the table's bottom toolbar area.

### Sketch-Wide Constraint Enumeration

```python
# Access all geometric constraints in active sketch
sketch = design.activeEditObject  # must be adsk.fusion.Sketch
constraints = sketch.geometricConstraints

# Iterate all constraints
for i in range(constraints.count):
    constraint = constraints.item(i)
    type_name = constraint.objectType.split('::')[-1]
    token = constraint.entityToken
    is_deletable = getattr(constraint, 'isDeletable', False)
```

**Confidence:** HIGH -- `Sketch.geometricConstraints` returns `GeometricConstraints` collection with `.count` and `.item(i)`. Confirmed via official docs.

## Critical Constraints and Limitations

### What CANNOT Go Inside a TableCommandInput

| Input Type | Supported in Table? | Workaround |
|------------|---------------------|------------|
| BoolValueCommandInput (checkbox) | YES | Already used in v1 |
| StringValueCommandInput | YES | Already used in v1 |
| DropDownCommandInput | YES | Can use for in-row type display if needed |
| SelectionCommandInput | **NO** | Keep selection input outside tables, at tab level |
| ButtonRowCommandInput | **NO** | Use BoolValueCommandInput (button mode) or table toolbar buttons instead |

**Confidence:** HIGH -- "Selection and button row command inputs are not supported in a table" per official docs.

### "Delete All" Pattern for Constraint Types Tab

ButtonRowCommandInput cannot go in a table, so for the "Delete All [Type]" action per row:

**Option A (Recommended): Table toolbar button + selectedRow.** User clicks a row in the types table, then clicks a toolbar "Delete All" button. Handler reads `typesTable.selectedRow` to determine which type. This matches Fusion's native UX patterns (e.g., Loft profile management).

**Option B: BoolValueCommandInput per row.** Add a clickable button-mode BoolValueInput in a 5th column. More discoverable but creates N extra inputs for N rows. Risk of ID management complexity and potential `inputChanged` event storms.

**Recommendation:** Option A. It is simpler, matches Fusion conventions, and avoids per-row button management. The toolbar approach is exactly how Fusion's own Loft/Profiles commands work.

### Row Spanning

`TableCommandInput.addCommandInput()` accepts `rowSpan` and `columnSpan` parameters, but **row spanning is not currently supported** -- `rowSpan` must always be 0. Column spanning works.

**Confidence:** HIGH -- confirmed in official method documentation.

### Tab Switch Detection

Tab switches fire `inputChanged` with the TabCommandInput as `args.input`. Check `changed_input.isActive` to confirm the tab was activated (not deactivated). This is the mechanism for lazy-loading tab content.

**Confidence:** HIGH -- `isActive` property confirmed on TabCommandInput object.

## Performance Considerations

### Sketch-Wide Enumeration Cost

| Sketch Size | Entities | Est. Constraints | Strategy |
|-------------|----------|-----------------|----------|
| Small | <50 | <200 | Direct enumeration, no gating |
| Medium | 50-200 | 200-1000 | Direct enumeration, still fast |
| Large (DXF import) | 200-500+ | 500-2000+ | **Explicit Load button required** |

**Why the Load button matters:** `sketch.geometricConstraints.count` iterates the internal collection. For 500+ entities each with 2-5 constraints, you are looking at 1000-2500+ constraint objects to enumerate, build info dicts for, and render as table rows. Each row creates 4-5 CommandInput objects. Fusion's UI framework is not designed for hundreds of command inputs in a single dialog.

**Recommended approach:**
1. **Constraint Types tab**: Always auto-load on tab switch. Only counts constraints by type (single pass through `sketch.geometricConstraints`, no table row creation beyond ~15 type summary rows). This is O(n) with n=constraint count, no UI overhead.
2. **All Constraints tab**: Show "Click Load to enumerate all constraints" by default. Load button triggers full enumeration + table build. Set `maximumVisibleRows` to 20 for scrollable display.
3. **Selected Entities tab**: Keep existing behavior (enumerate per-selection, typically <50 constraints).

**Confidence:** MEDIUM -- performance characteristics are based on Fusion API behavioral patterns and v1 experience. No official benchmarks exist for large constraint tables. The Load button is a safety valve -- test with real DXF imports to validate thresholds.

### Table Rendering Performance

Each table row requires creating 4-5 `CommandInput` objects via `table.commandInputs`. For 500+ rows, this means 2000+ CommandInput objects in a single dialog. Fusion's command framework was designed for ~50-100 inputs max.

**Mitigation strategies:**
1. Cap visible rows at 20 (`maximumVisibleRows = 20`) -- Fusion handles scrolling
2. Consider a "page" pattern if >200 constraints (show 50 at a time with Next/Previous buttons)
3. The dropdown filter reduces visible row count by only showing one type at a time

**Confidence:** LOW for specific numbers -- no official documentation on CommandInput limits. The 200+ threshold is a conservative estimate based on community reports of dialog sluggishness. Test empirically.

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Tab UI | TabCommandInput | GroupCommandInput (collapsible sections) | Groups create a single scrollable dialog instead of separate tab spaces. Three distinct workflows deserve tabs, not sections. |
| Type filter | DropDownCommandInput (TextListDropDownStyle) | CheckBoxDropDownStyle | Multi-select filtering adds complexity without clear value. Users want to see one type at a time, not combinations. |
| Delete All action | Table toolbar button + selectedRow | BoolValueCommandInput per row | Per-row buttons create N extra inputs, complicate ID management, risk event storms. Toolbar matches Fusion conventions. |
| Constraint list | TableCommandInput | BrowserCommandInput (HTML) | HTML tables offer more flexibility but add a second tech stack (HTML/JS/CSS) and a message-passing bridge. Massive overengineering for this use case. |
| Large table handling | Load button + filter | Virtual scrolling / pagination | Fusion API does not support virtual scrolling. Pagination via Next/Prev buttons is possible but filter-by-type is a better UX for the constraint domain. |

## Installation

```bash
# Production -- no installation needed beyond folder copy
# Copy ConstraintManager/ to Fusion's AddIns directory

# Development only
pip install pytest
```

## Sources

- [Command Inputs - Fusion Help](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CommandInputs_UM.htm) -- TabCommandInput, TableCommandInput, DropDownCommandInput overview and limitations
- [Command Inputs API Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CommandInputsSample_Sample.htm) -- Python code samples for all input types
- [TabCommandInput Object](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/TabCommandInput.htm) -- isActive, activate(), children properties
- [TableCommandInput Object](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/TableCommandInput.htm) -- addToolbarCommandInput, deleteRow, selectedRow, rowCount
- [DropDownCommandInput Object](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/DropDownCommandInput.htm) -- TextListDropDownStyle, listItems, selectedItem
- [CommandInputs.addTableCommandInput](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CommandInputs_addTableCommandInput.htm) -- columnRatio, deprecated numberOfColumns parameter
- [TableCommandInput.addCommandInput](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/TableCommandInput_addCommandInput.htm) -- rowSpan limitation, columnSpan support
- [GeometricConstraints Object](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/GeometricConstraints.htm) -- count, item(), constraint type creation methods
- [Sketch.geometricConstraints Property](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Sketch_geometricConstraints.htm) -- sketch-wide constraint access

---

*Stack research: 2026-03-22*
