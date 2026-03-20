# Constraint Manager Add-in Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Fusion add-in that lets users select a sketch entity and view/delete its geometric constraints from a table dialog.

**Architecture:** Native Fusion command dialog with `SelectionCommandInput` for entity picking and `TableCommandInput` for constraint display. Pure-logic engine module handles constraint enumeration and name resolution, keeping Fusion UI concerns in the command module. Add-in registers in the DESIGN workspace toolbar.

**Tech Stack:** Python 3 (Fusion's embedded interpreter), Fusion API (`adsk.core`, `adsk.fusion`). No external dependencies.

**Spec:** `docs/superpowers/specs/2026-03-20-constraint-manager-design.md`
**API Research:** `RESEARCH.md`

---

## Important Context for Implementors

This is a **Fusion add-in** — it runs inside Autodesk Fusion's embedded Python environment. The Fusion API (`adsk.core`, `adsk.fusion`) is only available at runtime inside Fusion.

**Testing strategy:** Two layers:
- **Unit tests** (constraint_engine.py): Run **outside Fusion** on your local machine using `pytest`. Requires Python 3 and pytest installed locally (`pip install pytest`). These tests use mock objects — no Fusion installation needed.
- **Integration tests**: Manual testing inside Fusion — load the add-in, open a sketch, use the tool.

**Two blockers must be validated first** (Task 1): checkbox support in tables, and undo behavior for in-dialog deletion. Dimension support is explicitly deferred to post-v1 — geometric constraints only. Do not build the full add-in until both blockers pass.

**How to test in Fusion:** Tools > Scripts & Add-Ins > Scripts tab > Run. For add-ins: copy folder to `%APPDATA%/Autodesk/Autodesk Fusion/API/AddIns/`, enable via Add-Ins tab.

---

## File Structure

```
ConstraintManager/
├── ConstraintManager.py            # Add-in entry point (run/stop lifecycle)
├── ConstraintManager.manifest      # Add-in metadata (JSON)
├── commands/
│   └── constraint_manager/
│       ├── __init__.py              # Package init (empty)
│       ├── command.py               # Command definition, all event handlers, UI wiring
│       └── constraint_engine.py     # Pure logic: enumerate, resolve names, delete
├── resources/
│   └── constraint_manager/
│       └── 16x16.png               # Toolbar icon (placeholder)
└── tests/
    └── test_constraint_engine.py   # Unit tests for engine (runs outside Fusion with mocks)
```

**Import strategy:** Fusion loads `ConstraintManager.py` as a top-level script (not a package). It adds its own directory to `sys.path`, then uses absolute imports like `from commands.constraint_manager import command`. Within the `commands/constraint_manager/` package, relative imports work normally (e.g., `from . import constraint_engine`).

**Boundary:** `constraint_engine.py` has zero UI imports — it takes Fusion API objects as arguments and returns plain data (dicts, lists, strings). `command.py` owns all `adsk.core` UI interactions and translates between engine output and `CommandInput` widgets.

---

## Task 0: Project Scaffolding

**Files:**
- Create: `ConstraintManager/ConstraintManager.manifest`
- Create: `ConstraintManager/ConstraintManager.py`
- Create: `ConstraintManager/commands/__init__.py` (empty)
- Create: `ConstraintManager/commands/constraint_manager/__init__.py` (empty)
- Create: `ConstraintManager/commands/constraint_manager/command.py` (stub)
- Create: `ConstraintManager/commands/constraint_manager/constraint_engine.py` (stub)
- Create: `ConstraintManager/resources/constraint_manager/16x16.png` (placeholder)
- Create: `ConstraintManager/tests/test_constraint_engine.py` (stub)

- [ ] **Step 1: Create manifest**

```json
{
    "autodeskProduct": "Fusion",
    "type": "addin",
    "id": "ConstraintManager",
    "author": "Matthew Mees",
    "description": {
        "": "View and delete sketch constraints attached to a selected entity"
    },
    "version": "0.1.0",
    "runOnStartup": false,
    "supportedOS": "windows|mac"
}
```

- [ ] **Step 2: Create add-in entry point**

`ConstraintManager/ConstraintManager.py`:

```python
import adsk.core
import adsk.fusion
import os
import sys
import traceback

# Fusion loads this file as a top-level script, not a package member.
# Add the add-in directory to sys.path so submodule imports work.
_addin_dir = os.path.dirname(os.path.abspath(__file__))
if _addin_dir not in sys.path:
    sys.path.insert(0, _addin_dir)

from commands.constraint_manager import command as constraint_cmd

_app = None
_ui = None


def run(context):
    global _app, _ui
    try:
        _app = adsk.core.Application.get()
        _ui = _app.userInterface
        constraint_cmd.start(_app, _ui)
    except:
        if _ui:
            _ui.messageBox(f"Failed to start ConstraintManager:\n{traceback.format_exc()}")


def stop(context):
    try:
        constraint_cmd.stop()
    except:
        if _ui:
            _ui.messageBox(f"Failed to stop ConstraintManager:\n{traceback.format_exc()}")
```

- [ ] **Step 3: Create empty package inits**

`ConstraintManager/commands/__init__.py` — empty file
`ConstraintManager/commands/constraint_manager/__init__.py` — empty file

- [ ] **Step 4: Create command.py stub**

```python
"""Command definition and event handlers for the Constraint Manager."""

_app = None
_ui = None
_cmd_handlers = []


def start(app, ui):
    """Register the command in the DESIGN workspace toolbar."""
    global _app, _ui
    _app = app
    _ui = ui
    # TODO: Task 3 — register command definition and toolbar button


def stop():
    """Clean up command registration."""
    global _cmd_handlers
    _cmd_handlers = []
    # TODO: Task 3 — remove toolbar button and command definition
```

- [ ] **Step 5: Create constraint_engine.py stub**

```python
"""Pure logic for constraint enumeration, name resolution, and deletion.

No Fusion UI imports (adsk.core UI classes). Takes Fusion API model objects
as arguments, returns plain data structures.
"""

# TODO: Task 2 — entity labeling, constraint enumeration, related entity resolution
```

- [ ] **Step 6: Create placeholder icon**

Create a minimal 16x16 PNG at `ConstraintManager/resources/constraint_manager/16x16.png`. A solid-color square is fine for development.

- [ ] **Step 7: Create test stub**

`ConstraintManager/tests/test_constraint_engine.py`:

```python
"""Unit tests for constraint_engine.py.

These tests use mock objects to simulate Fusion API types.
Run with: python -m pytest ConstraintManager/tests/ -v
(from the project root, outside Fusion)
"""


class MockSketchEntity:
    """Minimal mock for SketchEntity-like objects."""

    def __init__(self, object_type, index=0, is_construction=False):
        self.objectType = object_type
        self._index = index
        self.isConstruction = is_construction


# TODO: Task 2 — add tests as engine functions are built
```

- [ ] **Step 8: Commit**

```bash
git add ConstraintManager/
git commit -m "scaffold: add-in skeleton with manifest, entry point, and module stubs"
```

---

## Task 1: Validate Blockers (Manual in Fusion)

**Files:**
- Create: `ConstraintManager/tests/validate_checkbox.py` (temporary validation script)
- Create: `ConstraintManager/tests/validate_undo.py` (temporary validation script)

This task produces two small standalone scripts to run as Fusion Scripts (not add-ins). They validate the three spec blockers before we invest in the full implementation.

- [ ] **Step 1: Write checkbox validation script**

`ConstraintManager/tests/validate_checkbox.py`:

```python
"""Validation script: Can BoolValueCommandInput work as checkboxes in TableCommandInput?

Run as a Fusion Script (Tools > Scripts & Add-Ins > Scripts > Run).
Creates a command dialog with a table containing checkbox rows.
SUCCESS: Checkboxes render, toggle, and fire inputChanged events.
FALLBACK NEEDED: If checkboxes don't render or events don't fire.
"""
import adsk.core
import adsk.fusion
import traceback

_app = adsk.core.Application.get()
_ui = _app.userInterface
_handlers = []


class CreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            table = inputs.addTableCommandInput(
                "testTable", "Test Table", 3, "1:2:2"
            )
            table.maximumVisibleRows = 5

            for i in range(3):
                row_inputs = adsk.core.CommandInputs.cast(table.commandInputs)
                cb = row_inputs.addBoolValueInput(
                    f"check_{i}", "", True, "", False
                )
                type_input = row_inputs.addStringValueInput(
                    f"type_{i}", "", f"Constraint {i}"
                )
                related_input = row_inputs.addStringValueInput(
                    f"related_{i}", "", f"Entity {i}"
                )
                table.addCommandInput(cb, i, 0)
                table.addCommandInput(type_input, i, 1)
                table.addCommandInput(related_input, i, 2)

            # Add toolbar delete button
            del_btn = inputs.addBoolValueInput(
                "deleteBtn", "Delete Selected", False, "", False
            )
            table.addToolbarCommandInput(del_btn)

            changed_handler = ChangedHandler()
            cmd.inputChanged.add(changed_handler)
            _handlers.append(changed_handler)
        except:
            _ui.messageBox(traceback.format_exc())


class ChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        try:
            changed = args.input
            _ui.messageBox(f"inputChanged fired for: {changed.id}")
        except:
            _ui.messageBox(traceback.format_exc())


def run(context):
    try:
        cmd_def = _ui.commandDefinitions.addButtonDefinition(
            "validateCheckbox",
            "Validate Checkbox",
            "Test BoolValueCommandInput in TableCommandInput",
        )
        created_handler = CreatedHandler()
        cmd_def.commandCreated.add(created_handler)
        _handlers.append(created_handler)
        cmd_def.execute()
        adsk.autoTerminate(False)
    except:
        _ui.messageBox(traceback.format_exc())
```

- [ ] **Step 2: Write undo validation script**

`ConstraintManager/tests/validate_undo.py`:

```python
"""Validation script: Does deleteMe() inside inputChanged produce undo steps?

Run as a Fusion Script. Requires an active sketch with at least one
constraint (e.g., draw two lines, add a Parallel constraint).

Steps:
1. Opens a command dialog with a "Delete First Constraint" button
2. Click button -> deletes first geometric constraint on first sketch curve
3. Close dialog
4. Try Ctrl+Z -> if the constraint reappears, undo works

SUCCESS: Constraint reappears after Ctrl+Z.
FALLBACK NEEDED: Constraint does not reappear (no undo support).
"""
import adsk.core
import adsk.fusion
import traceback

_app = adsk.core.Application.get()
_ui = _app.userInterface
_handlers = []


class CreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs
            inputs.addBoolValueInput("deleteBtn", "Delete First Constraint", False, "", False)

            changed_handler = ChangedHandler()
            cmd.inputChanged.add(changed_handler)
            _handlers.append(changed_handler)
        except:
            _ui.messageBox(traceback.format_exc())


class ChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        try:
            if args.input.id != "deleteBtn":
                return
            # Reset button
            args.input.value = False

            design = adsk.fusion.Design.cast(_app.activeProduct)
            if not design:
                _ui.messageBox("No active design")
                return

            sketch = design.activeEditObject
            if not isinstance(sketch, adsk.fusion.Sketch):
                _ui.messageBox("Not editing a sketch")
                return

            curves = sketch.sketchCurves
            if curves.count == 0:
                _ui.messageBox("No curves in sketch")
                return

            first_curve = curves.item(0)
            constraints = first_curve.geometricConstraints
            if constraints.count == 0:
                _ui.messageBox("No constraints on first curve")
                return

            constraint = constraints.item(0)
            obj_type = constraint.objectType.split("::")[-1]

            if constraint.isDeletable:
                constraint.deleteMe()
                _ui.messageBox(
                    f"Deleted {obj_type}. Close dialog, then Ctrl+Z to test undo."
                )
            else:
                _ui.messageBox(f"{obj_type} is not deletable, try another sketch")
        except:
            _ui.messageBox(traceback.format_exc())


def run(context):
    try:
        cmd_def = _ui.commandDefinitions.addButtonDefinition(
            "validateUndo",
            "Validate Undo",
            "Test if deleteMe in inputChanged supports undo",
        )
        created_handler = CreatedHandler()
        cmd_def.commandCreated.add(created_handler)
        _handlers.append(created_handler)
        cmd_def.execute()
        adsk.autoTerminate(False)
    except:
        _ui.messageBox(traceback.format_exc())
```

- [ ] **Step 3: Run checkbox validation in Fusion**

1. Open Fusion, create or open any document
2. Tools > Scripts & Add-Ins > Scripts tab > + (add) > navigate to `validate_checkbox.py`
3. Run it
4. Verify: checkboxes render in table, toggling fires `inputChanged`, toolbar button appears
5. Record results in this plan (edit the checkbox below)

- [ ] Checkbox validation result: `PASS / FAIL / FALLBACK_A / FALLBACK_B` (fill in after testing)

- [ ] **Step 4: Run undo validation in Fusion**

1. Open Fusion, create a new component, create a sketch
2. Draw two lines, add a Parallel constraint between them
3. Tools > Scripts & Add-Ins > Scripts tab > + (add) > navigate to `validate_undo.py`
4. Run it, click "Delete First Constraint"
5. Close dialog, press Ctrl+Z
6. Check if the Parallel constraint reappears

- [ ] Undo validation result: `PASS / FAIL` (fill in after testing)

- [ ] **Step 5: Commit validation scripts**

```bash
git add ConstraintManager/tests/validate_*.py
git commit -m "test: add Fusion validation scripts for checkbox and undo blockers"
```

- [ ] **Step 6: Decision gate**

Based on validation results:
- **Both pass:** Continue to Task 2 as designed.
- **Checkbox fails:** Apply Fallback A changes (see below), then continue to Task 2.
- **Undo fails:** Apply Undo Fallback changes (see below), then continue to Task 2.
- **Both fail:** Apply both fallback sets.

### Fallback A: Row Selection (if checkboxes fail)

If `BoolValueCommandInput` doesn't work in table cells, make these changes to Task 6's `command.py`:

1. **Remove checkbox column.** Change table column ratio from `"1:3:3"` to `"1:1"` (type + related only).
2. **Remove all `check_N` BoolValueCommandInput creation** from `_on_entity_changed`.
3. **Replace `_on_delete` logic:** Instead of iterating checkboxes, use `table.selectedRow` to get the single selected row index. Delete that one constraint. No batch, no reverse order.
4. **Remove `_update_delete_state` checkbox scanning.** Instead, enable delete button whenever `table.selectedRow >= 0`, disable when `-1`.
5. **Update `inputChanged` routing:** Listen for `constraintTable` changes (row selection) instead of `check_*` changes.

### Undo Fallback: Queued-Delete-on-Execute (if undo fails)

If `deleteMe()` inside `inputChanged` doesn't produce undo steps:

1. **Add a pending-delete queue** to `InputChangedHandler`: `self._pending_deletes = []`.
2. **`_on_delete` queues instead of deleting:** Append checked constraints to `_pending_deletes`, visually mark rows as "pending delete" (e.g., strikethrough text or grayed out).
3. **Move actual deletion to `ExecuteHandler.notify`:** Iterate `_pending_deletes`, call `deleteMe()` on each. This runs inside the command's execute transaction, giving undo support.
4. **Change dialog from Close-only back to OK/Cancel:** OK commits queued deletions, Cancel discards them.
5. **Update spec status** to reflect the execute-based deletion model.

---

## Task 2: Constraint Engine — Entity Labeling

**Files:**
- Create: `ConstraintManager/commands/constraint_manager/constraint_engine.py`
- Modify: `ConstraintManager/tests/test_constraint_engine.py`

- [ ] **Step 1: Write tests for entity labeling**

`ConstraintManager/tests/test_constraint_engine.py`:

```python
"""Unit tests for constraint_engine.py.

Uses mock objects to simulate Fusion API types. Run outside Fusion with:
    python -m pytest ConstraintManager/tests/ -v
"""


class MockSketchEntity:
    """Minimal mock for SketchEntity-like objects."""

    def __init__(self, object_type, index=0, is_construction=False):
        self.objectType = object_type
        self._index = index
        self.isConstruction = is_construction


class MockCollection:
    """Minimal mock for a Fusion collection (e.g., SketchLines)."""

    def __init__(self, items):
        self._items = items

    @property
    def count(self):
        return len(self._items)

    def item(self, index):
        return self._items[index]


def _make_entity(type_suffix, index=0, construction=False):
    return MockSketchEntity(
        f"adsk::fusion::{type_suffix}", index=index, is_construction=construction
    )


# --- Entity labeling tests ---

def test_label_sketch_line():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        get_entity_label,
    )
    entity = _make_entity("SketchLine", index=3)
    assert get_entity_label(entity, 3) == "Line #3"


def test_label_sketch_arc():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        get_entity_label,
    )
    entity = _make_entity("SketchArc", index=0)
    assert get_entity_label(entity, 0) == "Arc #0"


def test_label_sketch_circle():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        get_entity_label,
    )
    entity = _make_entity("SketchCircle", index=1)
    assert get_entity_label(entity, 1) == "Circle #1"


def test_label_sketch_point():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        get_entity_label,
    )
    entity = _make_entity("SketchPoint", index=4)
    assert get_entity_label(entity, 4) == "Point #4"


def test_label_construction_line():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        get_entity_label,
    )
    entity = _make_entity("SketchLine", index=2, construction=True)
    assert get_entity_label(entity, 2) == "Constr. Line #2"


def test_label_sketch_ellipse():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        get_entity_label,
    )
    entity = _make_entity("SketchEllipse", index=0)
    assert get_entity_label(entity, 0) == "Ellipse #0"


def test_label_sketch_spline():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        get_entity_label,
    )
    entity = _make_entity("SketchFittedSpline", index=1)
    assert get_entity_label(entity, 1) == "Spline #1"


def test_label_unknown_entity_type():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        get_entity_label,
    )
    entity = _make_entity("SketchConicCurve", index=0)
    assert get_entity_label(entity, 0) == "Entity #0"


def test_constraint_type_display_name():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        get_constraint_type_name,
    )
    assert get_constraint_type_name("adsk::fusion::HorizontalConstraint") == "Horizontal"
    assert get_constraint_type_name("adsk::fusion::ParallelConstraint") == "Parallel"
    assert get_constraint_type_name("adsk::fusion::CoincidentConstraint") == "Coincident"


def test_constraint_type_strips_suffix():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        get_constraint_type_name,
    )
    # Should strip "Constraint" suffix for cleaner display
    assert get_constraint_type_name("adsk::fusion::PerpendicularConstraint") == "Perpendicular"
    assert get_constraint_type_name("adsk::fusion::TangentConstraint") == "Tangent"
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `python -m pytest ConstraintManager/tests/test_constraint_engine.py -v`
Expected: ImportError or AttributeError — functions don't exist yet.

- [ ] **Step 3: Implement entity labeling and type name functions**

`ConstraintManager/commands/constraint_manager/constraint_engine.py`:

```python
"""Pure logic for constraint enumeration, name resolution, and deletion.

No Fusion UI imports (adsk.core UI classes). Takes Fusion API model objects
as arguments, returns plain data structures.
"""

# objectType suffix -> display prefix
_ENTITY_TYPE_MAP = {
    "SketchLine": "Line",
    "SketchArc": "Arc",
    "SketchCircle": "Circle",
    "SketchEllipse": "Ellipse",
    "SketchFittedSpline": "Spline",
    "SketchPoint": "Point",
}


def get_entity_label(entity, index):
    """Build a display label like 'Line #3' or 'Constr. Arc #1'.

    Args:
        entity: A Fusion SketchEntity (or anything with .objectType and .isConstruction).
        index: The entity's index within its parent collection.

    Returns:
        A human-readable label string.
    """
    obj_type = entity.objectType.split("::")[-1]
    prefix = _ENTITY_TYPE_MAP.get(obj_type, "Entity")
    construction = getattr(entity, "isConstruction", False)
    if construction:
        return f"Constr. {prefix} #{index}"
    return f"{prefix} #{index}"


def get_constraint_type_name(object_type):
    """Strip namespace and 'Constraint' suffix from a Fusion objectType string.

    'adsk::fusion::HorizontalConstraint' -> 'Horizontal'
    'adsk::fusion::ParallelConstraint' -> 'Parallel'

    Args:
        object_type: Full objectType string from a constraint.

    Returns:
        A clean display name string.
    """
    name = object_type.split("::")[-1]
    if name.endswith("Constraint"):
        name = name[: -len("Constraint")]
    return name
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `python -m pytest ConstraintManager/tests/test_constraint_engine.py -v`
Expected: All 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add ConstraintManager/commands/constraint_manager/constraint_engine.py ConstraintManager/tests/test_constraint_engine.py
git commit -m "feat: add entity labeling and constraint type name resolution"
```

---

## Task 3: Constraint Engine — Related Entity Resolution

**Files:**
- Modify: `ConstraintManager/commands/constraint_manager/constraint_engine.py`
- Modify: `ConstraintManager/tests/test_constraint_engine.py`

- [ ] **Step 1: Write tests for related entity resolution**

Add to `test_constraint_engine.py`:

```python
class MockConstraint:
    """Mock for a geometric constraint."""

    def __init__(self, object_type, isDeletable=True, **entity_refs):
        self.objectType = f"adsk::fusion::{object_type}"
        self.isDeletable = isDeletable
        self.isValid = True
        for k, v in entity_refs.items():
            setattr(self, k, v)


def test_resolve_single_entity_horizontal():
    """Horizontal constraint has one entity — related should be '--'."""
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        resolve_related_entity,
    )
    selected = _make_entity("SketchLine", index=0)
    constraint = MockConstraint("HorizontalConstraint", line=selected)
    result = resolve_related_entity(constraint, selected)
    assert result == "--"


def test_resolve_two_entity_parallel():
    """Parallel: return the entity that isn't the selected one."""
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        resolve_related_entity,
    )
    line_a = _make_entity("SketchLine", index=0)
    line_b = _make_entity("SketchLine", index=3)
    constraint = MockConstraint("ParallelConstraint", lineOne=line_a, lineTwo=line_b)
    result = resolve_related_entity(constraint, line_a)
    assert result is line_b


def test_resolve_two_entity_selected_is_second():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        resolve_related_entity,
    )
    line_a = _make_entity("SketchLine", index=0)
    line_b = _make_entity("SketchLine", index=3)
    constraint = MockConstraint("ParallelConstraint", lineOne=line_a, lineTwo=line_b)
    result = resolve_related_entity(constraint, line_b)
    assert result is line_a


def test_resolve_coincident():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        resolve_related_entity,
    )
    point = _make_entity("SketchPoint", index=0)
    line = _make_entity("SketchLine", index=1)
    constraint = MockConstraint("CoincidentConstraint", point=point, entity=line)
    result = resolve_related_entity(constraint, point)
    assert result is line


def test_resolve_fix_constraint():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        resolve_related_entity,
    )
    entity = _make_entity("SketchPoint", index=0)
    constraint = MockConstraint("FixConstraint", entity=entity)
    result = resolve_related_entity(constraint, entity)
    assert result == "--"


def test_resolve_symmetry_selected_is_entity_one():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        resolve_related_entity,
    )
    e1 = _make_entity("SketchLine", index=0)
    e2 = _make_entity("SketchLine", index=1)
    sym_line = _make_entity("SketchLine", index=2)
    constraint = MockConstraint(
        "SymmetryConstraint", entityOne=e1, entityTwo=e2, symmetryLine=sym_line
    )
    result = resolve_related_entity(constraint, e1)
    # Returns list of other entities for multi-entity constraints
    assert isinstance(result, list)
    assert e2 in result
    assert sym_line in result


def test_resolve_unknown_type():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        resolve_related_entity,
    )
    entity = _make_entity("SketchLine", index=0)
    constraint = MockConstraint("SomeNewConstraint")
    result = resolve_related_entity(constraint, entity)
    assert result == "--"


def test_resolve_offset_selected_in_parent():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        resolve_related_entity,
    )
    parent = _make_entity("SketchLine", index=0)
    child1 = _make_entity("SketchLine", index=1)
    child2 = _make_entity("SketchArc", index=0)

    constraint = MockConstraint("OffsetConstraint")
    constraint.parentCurves = MockCollection([parent])
    constraint.childCurves = MockCollection([child1, child2])

    result = resolve_related_entity(constraint, parent)
    assert isinstance(result, list)
    assert len(result) == 2
    assert child1 in result
    assert child2 in result


def test_format_related_single_entity():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        _format_related,
    )
    entity = _make_entity("SketchLine", index=5)
    result = _format_related(entity, lambda e: e._index)
    assert result == "Line #5"


def test_format_related_list():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        _format_related,
    )
    e1 = _make_entity("SketchLine", index=1)
    e2 = _make_entity("SketchArc", index=2)
    result = _format_related([e1, e2], lambda e: e._index)
    assert result == "Line #1, Arc #2"


def test_format_related_list_truncation():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        _format_related,
    )
    entities = [_make_entity("SketchLine", index=i) for i in range(5)]
    result = _format_related(entities, lambda e: e._index)
    assert "+2 more" in result
    assert result.count(",") == 3  # 3 labels + "+2 more"


def test_format_related_dash():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        _format_related,
    )
    assert _format_related("--", lambda e: 0) == "--"
    assert _format_related([], lambda e: 0) == "--"
```

- [ ] **Step 2: Run tests — verify new tests fail**

Run: `python -m pytest ConstraintManager/tests/test_constraint_engine.py -v`
Expected: New tests FAIL (resolve_related_entity doesn't exist).

- [ ] **Step 3: Implement resolve_related_entity**

Add to `constraint_engine.py`:

```python
import logging

_log = logging.getLogger(__name__)

# Constraint type -> (property names referencing entities)
# Single-prop means single-entity constraint. Two-prop means two-entity.
_CONSTRAINT_ENTITY_PROPS = {
    "HorizontalConstraint": ("line",),
    "VerticalConstraint": ("line",),
    "FixConstraint": ("entity",),
    "ParallelConstraint": ("lineOne", "lineTwo"),
    "PerpendicularConstraint": ("lineOne", "lineTwo"),
    "CollinearConstraint": ("lineOne", "lineTwo"),
    "CoincidentConstraint": ("point", "entity"),
    "EqualConstraint": ("curveOne", "curveTwo"),
    "TangentConstraint": ("curveOne", "curveTwo"),
    "SmoothConstraint": ("curveOne", "curveTwo"),
    "ConcentricConstraint": ("entityOne", "entityTwo"),
    "MidPointConstraint": ("point", "midPointCurve"),
    "HorizontalPointsConstraint": ("pointOne", "pointTwo"),
    "VerticalPointsConstraint": ("pointOne", "pointTwo"),
    "SymmetryConstraint": ("entityOne", "entityTwo", "symmetryLine"),
    # Offset uses collections — handled separately
}


def resolve_related_entity(constraint, selected_entity):
    """Identify the 'other' entity/entities in a constraint relative to selected_entity.

    Returns:
        '--' for single-entity constraints or unknown types.
        The other entity object for two-entity constraints.
        A list of other entity objects for three+ entity constraints (Symmetry).
    """
    type_name = constraint.objectType.split("::")[-1]

    # Handle Offset separately (collection-based)
    if type_name == "OffsetConstraint":
        return _resolve_offset(constraint, selected_entity)

    props = _CONSTRAINT_ENTITY_PROPS.get(type_name)
    if props is None:
        _log.warning("Unknown constraint type: %s", constraint.objectType)
        return "--"

    if len(props) == 1:
        # Single-entity constraint
        return "--"

    # Gather all referenced entities
    referenced = []
    for prop in props:
        val = getattr(constraint, prop, None)
        if val is not None:
            referenced.append(val)

    # Filter out the selected entity
    # Use == not 'is' — Fusion may return different wrapper objects for the same entity
    others = [e for e in referenced if e != selected_entity]

    if len(others) == 0:
        return "--"
    if len(others) == 1:
        return others[0]
    return others


def _resolve_offset(constraint, selected_entity):
    """Resolve related entities for Offset constraints (collection-based).

    Returns '--' if we can't determine the other side, or a list of entities.
    """
    try:
        parent_curves = constraint.parentCurves
        child_curves = constraint.childCurves
    except AttributeError:
        return "--"

    # Determine which collection the selected entity is in
    parent_list = [parent_curves.item(i) for i in range(parent_curves.count)]
    child_list = [child_curves.item(i) for i in range(child_curves.count)]

    if selected_entity in parent_list:
        return child_list if child_list else "--"
    if selected_entity in child_list:
        return parent_list if parent_list else "--"
    return "--"
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `python -m pytest ConstraintManager/tests/test_constraint_engine.py -v`
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add ConstraintManager/commands/constraint_manager/constraint_engine.py ConstraintManager/tests/test_constraint_engine.py
git commit -m "feat: add related entity resolution for all geometric constraint types"
```

---

## Task 4: Constraint Engine — Enumeration and Info Gathering

**Files:**
- Modify: `ConstraintManager/commands/constraint_manager/constraint_engine.py`
- Modify: `ConstraintManager/tests/test_constraint_engine.py`

- [ ] **Step 1: Write tests for constraint enumeration**

Add to `test_constraint_engine.py`:

```python
class MockConstraintList:
    """Mock for GeometricConstraintList."""

    def __init__(self, items):
        self._items = items

    @property
    def count(self):
        return len(self._items)

    def item(self, index):
        return self._items[index]

    def __iter__(self):
        return iter(self._items)


class MockSketchEntityWithConstraints(MockSketchEntity):
    """Mock entity that also has geometricConstraints."""

    def __init__(self, object_type, index=0, constraints=None, is_construction=False):
        super().__init__(object_type, index, is_construction)
        self.geometricConstraints = MockConstraintList(constraints or [])


def _mock_index_finder(entity):
    """Test index finder — returns the mock's _index attribute."""
    return getattr(entity, "_index", 0)


def test_enumerate_constraints_basic():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        enumerate_constraints,
    )
    line_a = MockSketchEntityWithConstraints("adsk::fusion::SketchLine", index=0)
    line_b = _make_entity("SketchLine", index=1)
    h_constraint = MockConstraint("HorizontalConstraint", isDeletable=True, line=line_a)
    p_constraint = MockConstraint(
        "ParallelConstraint", isDeletable=True, lineOne=line_a, lineTwo=line_b
    )
    line_a.geometricConstraints = MockConstraintList([h_constraint, p_constraint])

    results = enumerate_constraints(line_a, index_finder=_mock_index_finder)
    assert len(results) == 2
    assert results[0]["type_name"] == "Horizontal"
    assert results[0]["related_label"] == "--"
    assert results[0]["is_deletable"] is True
    assert results[1]["type_name"] == "Parallel"
    assert results[1]["related_label"] == "Line #1"
    assert results[1]["is_deletable"] is True


def test_enumerate_constraints_non_deletable():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        enumerate_constraints,
    )
    entity = MockSketchEntityWithConstraints("adsk::fusion::SketchLine", index=0)
    constraint = MockConstraint("HorizontalConstraint", isDeletable=False, line=entity)
    entity.geometricConstraints = MockConstraintList([constraint])

    results = enumerate_constraints(entity, index_finder=_mock_index_finder)
    assert len(results) == 1
    assert results[0]["is_deletable"] is False


def test_enumerate_constraints_empty():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        enumerate_constraints,
    )
    entity = MockSketchEntityWithConstraints("adsk::fusion::SketchLine", index=0)
    entity.geometricConstraints = MockConstraintList([])

    results = enumerate_constraints(entity, index_finder=_mock_index_finder)
    assert results == []


def test_enumerate_unknown_constraint_shown():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        enumerate_constraints,
    )
    entity = MockSketchEntityWithConstraints("adsk::fusion::SketchLine", index=0)
    unknown = MockConstraint("BrandNewConstraint", isDeletable=True)
    entity.geometricConstraints = MockConstraintList([unknown])

    results = enumerate_constraints(entity, index_finder=_mock_index_finder)
    assert len(results) == 1
    assert results[0]["type_name"] == "Unknown (BrandNewConstraint)"
    assert results[0]["is_deletable"] is False  # Unknown types forced non-deletable
    assert results[0]["related_label"] == "--"
```

- [ ] **Step 2: Run tests — verify new tests fail**

Run: `python -m pytest ConstraintManager/tests/test_constraint_engine.py -v`
Expected: New tests FAIL.

- [ ] **Step 3: Implement enumerate_constraints**

Add to `constraint_engine.py`:

```python
def enumerate_constraints(entity, index_finder, include_dimensions=False):
    """Enumerate all geometric constraints on an entity, returning display-ready info.

    Args:
        entity: A Fusion SketchEntity with .geometricConstraints property.
        index_finder: Callable(entity) -> int. Resolves an entity's collection index
            for display labeling. Provided by command.py (_find_entity_index).
        include_dimensions: If True, also enumerate .sketchDimensions (v1: disabled).

    Returns:
        List of dicts, each with keys:
            - constraint: The original Fusion constraint object
            - type_name: Display name (e.g., 'Horizontal', 'Parallel')
            - related_label: Display label for related entity (e.g., 'Line #3', '--')
            - is_deletable: Whether the constraint can be deleted
    """
    results = []

    for i in range(entity.geometricConstraints.count):
        constraint = entity.geometricConstraints.item(i)
        info = _build_constraint_info(constraint, entity, index_finder)
        results.append(info)

    if include_dimensions and hasattr(entity, "sketchDimensions"):
        for i in range(entity.sketchDimensions.count):
            dim = entity.sketchDimensions.item(i)
            info = _build_constraint_info(dim, entity, index_finder)
            results.append(info)

    return results


def _build_constraint_info(constraint, selected_entity, index_finder):
    """Build a display-ready dict for a single constraint."""
    type_name_raw = constraint.objectType.split("::")[-1]
    is_known = type_name_raw in _CONSTRAINT_ENTITY_PROPS or type_name_raw == "OffsetConstraint"

    if is_known:
        type_name = get_constraint_type_name(constraint.objectType)
        is_deletable = getattr(constraint, "isDeletable", False)
    else:
        type_name = f"Unknown ({type_name_raw})"
        is_deletable = False
        _log.warning("Unknown constraint type: %s", constraint.objectType)

    related = resolve_related_entity(constraint, selected_entity)
    related_label = _format_related(related, index_finder)

    return {
        "constraint": constraint,
        "type_name": type_name,
        "related_label": related_label,
        "is_deletable": is_deletable,
    }


def _format_related(related, index_finder):
    """Format the related entity result into a display string.

    Args:
        related: '--', a single entity, or a list of entities.
        index_finder: Callable(entity) -> int for resolving collection indices.
    """
    if related == "--":
        return "--"
    if isinstance(related, list):
        if len(related) == 0:
            return "--"
        labels = []
        for e in related[:3]:
            label = get_entity_label(e, index_finder(e))
            labels.append(label)
        if len(related) > 3:
            labels.append(f"+{len(related) - 3} more")
        return ", ".join(labels)
    # Single entity
    return get_entity_label(related, index_finder(related))
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `python -m pytest ConstraintManager/tests/test_constraint_engine.py -v`
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add ConstraintManager/commands/constraint_manager/constraint_engine.py ConstraintManager/tests/test_constraint_engine.py
git commit -m "feat: add constraint enumeration with display-ready info dicts"
```

---

## Task 5: Constraint Engine — Deletion

**Files:**
- Modify: `ConstraintManager/commands/constraint_manager/constraint_engine.py`
- Modify: `ConstraintManager/tests/test_constraint_engine.py`

- [ ] **Step 1: Write tests for deletion**

Add to `test_constraint_engine.py`:

```python
class MockDeletableConstraint(MockConstraint):
    """Mock constraint that tracks deleteMe() calls."""

    def __init__(self, object_type, isDeletable=True, **kwargs):
        super().__init__(object_type, isDeletable, **kwargs)
        self.deleted = False

    def deleteMe(self):
        if not self.isDeletable:
            return False
        self.deleted = True
        self.isValid = False
        return True


def test_delete_single_constraint():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        delete_constraints,
    )
    c = MockDeletableConstraint("HorizontalConstraint")
    results = delete_constraints([c])
    assert c.deleted is True
    assert results["deleted"] == 1
    assert results["failed"] == 0


def test_delete_skips_non_deletable():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        delete_constraints,
    )
    c = MockDeletableConstraint("HorizontalConstraint", isDeletable=False)
    results = delete_constraints([c])
    assert c.deleted is False
    assert results["deleted"] == 0
    assert results["skipped"] == 1


def test_delete_skips_invalid():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        delete_constraints,
    )
    c = MockDeletableConstraint("HorizontalConstraint")
    c.isValid = False
    results = delete_constraints([c])
    assert c.deleted is False
    assert results["skipped"] == 1


def test_delete_batch_reverse_order():
    from ConstraintManager.commands.constraint_manager.constraint_engine import (
        delete_constraints,
    )
    deletion_order = []

    class OrderedConstraint(MockDeletableConstraint):
        def __init__(self, name, **kwargs):
            super().__init__("HorizontalConstraint", **kwargs)
            self.name = name

        def deleteMe(self):
            deletion_order.append(self.name)
            return super().deleteMe()

    c1 = OrderedConstraint("first")
    c2 = OrderedConstraint("second")
    c3 = OrderedConstraint("third")
    delete_constraints([c1, c2, c3])
    assert deletion_order == ["third", "second", "first"]
```

- [ ] **Step 2: Run tests — verify new tests fail**

Run: `python -m pytest ConstraintManager/tests/test_constraint_engine.py -v`
Expected: New tests FAIL.

- [ ] **Step 3: Implement delete_constraints**

Add to `constraint_engine.py`:

```python
def delete_constraints(constraints):
    """Delete a list of constraints in reverse order.

    Checks isDeletable and isValid before each deletion. Logs and continues
    on failure — never aborts the batch.

    Args:
        constraints: List of Fusion constraint objects (in table display order).

    Returns:
        Dict with keys: 'deleted' (int), 'failed' (int), 'skipped' (int).
    """
    deleted = 0
    failed = 0
    skipped = 0

    for constraint in reversed(constraints):
        if not getattr(constraint, "isValid", False):
            _log.info("Skipping invalid constraint")
            skipped += 1
            continue
        if not getattr(constraint, "isDeletable", False):
            _log.info("Skipping non-deletable constraint: %s", constraint.objectType)
            skipped += 1
            continue
        try:
            constraint.deleteMe()
            deleted += 1
        except Exception as e:
            _log.error("Failed to delete constraint: %s", e)
            failed += 1

    return {"deleted": deleted, "failed": failed, "skipped": skipped}
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `python -m pytest ConstraintManager/tests/test_constraint_engine.py -v`
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add ConstraintManager/commands/constraint_manager/constraint_engine.py ConstraintManager/tests/test_constraint_engine.py
git commit -m "feat: add batch constraint deletion with safety checks"
```

---

## Task 6: Add-in Registration and Full Command Wiring

**Files:**
- Modify: `ConstraintManager/ConstraintManager.py`
- Modify: `ConstraintManager/commands/constraint_manager/command.py`

This task wires up everything: add-in lifecycle, toolbar registration, command dialog creation, entity selection handling, table population via the engine, deletion flow, and all state management. This is the largest task — it connects the engine (Tasks 2-5) to the Fusion UI.

- [ ] **Step 1: Implement command registration in ConstraintManager.py**

Replace the stub with:

```python
import adsk.core
import adsk.fusion
import os
import sys
import traceback

# Fusion loads this file as a top-level script, not a package member.
# Add the add-in directory to sys.path so submodule imports work.
_addin_dir = os.path.dirname(os.path.abspath(__file__))
if _addin_dir not in sys.path:
    sys.path.insert(0, _addin_dir)

from commands.constraint_manager import command as constraint_cmd

_app = None
_ui = None


def run(context):
    global _app, _ui
    try:
        _app = adsk.core.Application.get()
        _ui = _app.userInterface
        constraint_cmd.start(_app, _ui)
    except:
        if _ui:
            _ui.messageBox(f"Failed to start ConstraintManager:\n{traceback.format_exc()}")


def stop(context):
    try:
        constraint_cmd.stop()
    except:
        if _ui:
            _ui.messageBox(f"Failed to stop ConstraintManager:\n{traceback.format_exc()}")
```

- [ ] **Step 2: Implement command.py with full event handler wiring**

```python
"""Command definition and event handlers for the Constraint Manager."""

import adsk.core
import adsk.fusion
import traceback
import logging

from . import constraint_engine

_log = logging.getLogger(__name__)

_app = None
_ui = None

# Module-level list — prevents GC of command-instance handlers
_cmd_handlers = []

# Add-in lifetime handlers (commandCreated)
_addin_handlers = []

# Command identifiers
CMD_ID = "constraintManagerCmd"
CMD_NAME = "Constraint Manager"
CMD_DESC = "View and delete constraints on sketch entities"
PANEL_ID = "SolidScriptsAddinsPanel"  # DESIGN workspace utilities panel


def start(app, ui):
    """Register the command definition and add a toolbar button."""
    global _app, _ui
    _app = app
    _ui = ui

    # Clean up any existing definition (dev reload)
    existing = ui.commandDefinitions.itemById(CMD_ID)
    if existing:
        existing.deleteMe()

    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID, CMD_NAME, CMD_DESC,
        # Icon resource folder (relative to add-in root)
        "./resources/constraint_manager"
    )

    created_handler = CommandCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    _addin_handlers.append(created_handler)

    # Add to the DESIGN workspace panel
    design_ws = ui.workspaces.itemById("FusionSolidEnvironment")
    if design_ws:
        panel = design_ws.toolbarPanels.itemById(PANEL_ID)
        if panel:
            # Check if control already exists
            existing_ctrl = panel.controls.itemById(CMD_ID)
            if not existing_ctrl:
                panel.controls.addCommand(cmd_def)


def stop():
    """Remove toolbar button and command definition."""
    global _addin_handlers, _cmd_handlers
    try:
        design_ws = _ui.workspaces.itemById("FusionSolidEnvironment")
        if design_ws:
            panel = design_ws.toolbarPanels.itemById(PANEL_ID)
            if panel:
                ctrl = panel.controls.itemById(CMD_ID)
                if ctrl:
                    ctrl.deleteMe()

        cmd_def = _ui.commandDefinitions.itemById(CMD_ID)
        if cmd_def:
            cmd_def.deleteMe()
    except:
        _log.error("Error during stop: %s", traceback.format_exc())

    _addin_handlers = []
    _cmd_handlers = []


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    """Fires when the user clicks the Constraint Manager button."""

    def notify(self, args):
        try:
            cmd = args.command
            cmd.isOKButtonVisible = False
            cmd.cancelButtonText = "Close"

            # Verify active sketch edit mode
            design = adsk.fusion.Design.cast(_app.activeProduct)
            if not design or not isinstance(
                design.activeEditObject, adsk.fusion.Sketch
            ):
                _ui.messageBox(
                    "Constraint Manager requires an active sketch.\n"
                    "Enter sketch edit mode first."
                )
                args.command.doExecute(True)  # Close immediately
                return

            inputs = cmd.commandInputs

            # Entity selection input
            entity_select = inputs.addSelectionInput(
                "entitySelect", "Select Entity", "Click a sketch entity"
            )
            entity_select.addSelectionFilter("SketchCurves")
            entity_select.addSelectionFilter("SketchPoints")
            entity_select.setSelectionLimits(0, 1)
            entity_select.isUseCurrentSelections = False

            # Constraint table
            table = inputs.addTableCommandInput(
                "constraintTable", "Constraints", 3, "1:3:3"
            )
            table.maximumVisibleRows = 10
            table.isEnabled = True

            # Delete toolbar button on table (starts disabled)
            del_btn = inputs.addBoolValueInput(
                "deleteBtn", "Delete Selected", False, "", False
            )
            del_btn.isEnabled = False
            table.addToolbarCommandInput(del_btn)

            # Wire command-instance event handlers
            input_changed = InputChangedHandler()
            cmd.inputChanged.add(input_changed)
            _cmd_handlers.append(input_changed)

            pre_select = PreSelectHandler()
            cmd.preSelect.add(pre_select)
            _cmd_handlers.append(pre_select)

            execute = ExecuteHandler()
            cmd.execute.add(execute)
            _cmd_handlers.append(execute)

            destroy = DestroyHandler()
            cmd.destroy.add(destroy)
            _cmd_handlers.append(destroy)

        except:
            _ui.messageBox(f"CommandCreated error:\n{traceback.format_exc()}")


class PreSelectHandler(adsk.core.SelectionEventHandler):
    """Validates entity hover — only allow supported sketch curves/points in active sketch."""

    # Supported entity types (per spec: curves and points)
    _SUPPORTED_TYPES = {
        "SketchLine", "SketchArc", "SketchCircle", "SketchEllipse",
        "SketchFittedSpline", "SketchPoint",
    }

    def notify(self, args):
        try:
            selection = args.selection
            entity = selection.entity

            design = adsk.fusion.Design.cast(_app.activeProduct)
            if not design:
                args.isSelectable = False
                return

            active_sketch = design.activeEditObject
            if not isinstance(active_sketch, adsk.fusion.Sketch):
                args.isSelectable = False
                return

            # Verify entity belongs to the active sketch
            if hasattr(entity, "parentSketch"):
                if entity.parentSketch != active_sketch:
                    args.isSelectable = False
                    return

            # Verify entity is a supported type
            entity_type = entity.objectType.split("::")[-1]
            if entity_type not in self._SUPPORTED_TYPES:
                args.isSelectable = False
        except:
            pass  # Don't block selection on error


class InputChangedHandler(adsk.core.InputChangedEventHandler):
    """Handles entity selection changes, checkbox toggles, and delete button."""

    _handling_change = False

    def notify(self, args):
        if self._handling_change:
            return
        self._handling_change = True
        try:
            changed_input = args.input
            inputs = args.inputs

            if changed_input.id == "entitySelect":
                self._on_entity_changed(inputs)
            elif changed_input.id == "deleteBtn":
                self._on_delete(inputs)
                # Reset button
                changed_input.value = False
            elif changed_input.id.startswith("check_"):
                # Checkbox toggled — update delete button enabled state
                self._update_delete_state(inputs)
        except:
            _log.error("InputChanged error: %s", traceback.format_exc())
        finally:
            self._handling_change = False

    def _on_entity_changed(self, inputs):
        """Rebuild the constraint table for the newly selected entity."""
        entity_select = inputs.itemById("entitySelect")
        table = inputs.itemById("constraintTable")

        # Clear existing table rows
        for i in range(table.rowCount - 1, -1, -1):
            table.deleteRow(i)

        if entity_select.selectionCount == 0:
            self._current_constraints = []
            self._update_delete_state(inputs)
            return

        selected = entity_select.selection(0).entity

        # Enumerate constraints (pass _find_entity_index so engine can label related entities)
        infos = constraint_engine.enumerate_constraints(
            selected, index_finder=_find_entity_index
        )

        if not infos:
            # Show "no constraints" message
            self._current_constraints = []
            msg = inputs.addStringValueInput(
                "noConstraints", "", "No constraints found"
            )
            msg.isReadOnly = True
            table.addCommandInput(msg, 0, 0)
            self._update_delete_state(inputs)
            return

        # Populate table rows
        for i, info in enumerate(infos):
            row_inputs = adsk.core.CommandInputs.cast(table.commandInputs)

            # Checkbox (disabled if not deletable)
            cb = row_inputs.addBoolValueInput(
                f"check_{i}", "", True, "", False
            )
            cb.isEnabled = info["is_deletable"]

            # Type name (with lock indicator for non-deletable)
            type_display = info["type_name"]
            if not info["is_deletable"]:
                type_display = f"\U0001F512 {type_display}"  # Lock emoji prefix
            type_input = row_inputs.addStringValueInput(
                f"type_{i}", "", type_display
            )
            type_input.isReadOnly = True

            # Related entity label
            related_display = info["related_label"]
            if not info["is_deletable"] and related_display != "--":
                related_display = f"{related_display} (locked)"
            related_input = row_inputs.addStringValueInput(
                f"related_{i}", "", related_display
            )
            related_input.isReadOnly = True

            table.addCommandInput(cb, i, 0)
            table.addCommandInput(type_input, i, 1)
            table.addCommandInput(related_input, i, 2)

        # Store constraint objects for deletion lookup
        self._current_constraints = infos

        # Disable delete button (nothing checked yet)
        self._update_delete_state(inputs)

    def _update_delete_state(self, inputs):
        """Enable/disable delete button based on whether any rows are checked."""
        del_btn = inputs.itemById("deleteBtn")
        table = inputs.itemById("constraintTable")
        if not del_btn or not table:
            return
        any_checked = False
        for i in range(table.rowCount):
            cb = table.getInputAtPosition(i, 0)
            if cb and hasattr(cb, "value") and cb.value:
                any_checked = True
                break
        del_btn.isEnabled = any_checked

    def _on_delete(self, inputs):
        """Delete checked constraints and refresh the table."""
        table = inputs.itemById("constraintTable")

        if not hasattr(self, "_current_constraints") or not self._current_constraints:
            return

        # Collect checked constraints
        to_delete = []
        for i in range(table.rowCount):
            cb_input = table.getInputAtPosition(i, 0)
            if cb_input and cb_input.value:
                to_delete.append(self._current_constraints[i]["constraint"])

        if not to_delete:
            return

        # Delete
        result = constraint_engine.delete_constraints(to_delete)
        _log.info(
            "Deleted %d, failed %d, skipped %d",
            result["deleted"], result["failed"], result["skipped"],
        )

        # Check if selected entity is still valid after deletion
        entity_select = inputs.itemById("entitySelect")
        if entity_select.selectionCount > 0:
            selected = entity_select.selection(0).entity
            if hasattr(selected, "isValid") and not selected.isValid:
                # Entity was invalidated by cascading deletes — clear selection
                entity_select.clearSelection()

        # Refresh table
        self._on_entity_changed(inputs)


class ExecuteHandler(adsk.core.CommandEventHandler):
    """Fires on OK/Close — clean up."""

    def notify(self, args):
        pass  # Close button just closes, nothing to finalize


class DestroyHandler(adsk.core.CommandEventHandler):
    """Fires when command is destroyed — clean up handler references."""

    def notify(self, args):
        global _cmd_handlers
        _cmd_handlers = []


def _find_entity_index(entity):
    """Find the index of an entity within its parent sketch collection.

    Returns 0 if the entity type isn't recognized or lookup fails.
    """
    try:
        sketch = entity.parentSketch
        obj_type = entity.objectType.split("::")[-1]

        collection = None
        if obj_type == "SketchLine":
            collection = sketch.sketchCurves.sketchLines
        elif obj_type == "SketchArc":
            collection = sketch.sketchCurves.sketchArcs
        elif obj_type == "SketchCircle":
            collection = sketch.sketchCurves.sketchCircles
        elif obj_type == "SketchEllipse":
            collection = sketch.sketchCurves.sketchEllipses
        elif obj_type == "SketchFittedSpline":
            collection = sketch.sketchCurves.sketchFittedSplines
        elif obj_type == "SketchPoint":
            collection = sketch.sketchPoints

        if collection:
            for i in range(collection.count):
                if collection.item(i) == entity:
                    return i
    except Exception as e:
        _log.warning("Could not determine entity index: %s", e)

    return 0
```

- [ ] **Step 3: Commit**

```bash
git add ConstraintManager/ConstraintManager.py ConstraintManager/commands/constraint_manager/command.py
git commit -m "feat: add command registration, event handlers, and full UI wiring"
```

---

## Task 7: Manual Integration Test in Fusion

This task is done manually in Fusion. No code changes — just verification.

- [ ] **Step 1: Install add-in**

Copy the `ConstraintManager/` folder to `%APPDATA%/Autodesk/Autodesk Fusion/API/AddIns/`.

- [ ] **Step 2: Enable add-in**

Fusion > Tools > Scripts & Add-Ins > Add-Ins tab > ConstraintManager > Run

- [ ] **Step 3: Test basic workflow**

1. Create new component > Create sketch on XY plane
2. Draw several lines, arcs, circles
3. Add constraints: Horizontal, Parallel, Coincident, Equal, etc.
4. Click Constraint Manager button in toolbar
5. Select a line — verify table populates with correct constraints
6. Check a deletable constraint > click Delete Selected
7. Verify constraint is deleted and table refreshes
8. Select a different entity — verify table updates
9. Click Close

- [ ] **Step 4: Test edge cases**

1. Open Constraint Manager with no sketch active — verify error message
2. Select entity with no constraints — verify "No constraints found"
3. Delete all constraints on an entity — verify table clears
4. Try to select entity outside active sketch — verify it's blocked

- [ ] **Step 5: Test undo (if blocker 2 passed)**

1. Delete a constraint
2. Close dialog
3. Ctrl+Z — verify constraint reappears

- [ ] **Step 6: Record results**

Note any bugs or issues found. If anything needs fixing, create additional targeted commits.

---

## Task 8: Cleanup and Documentation

**Files:**
- Modify: `docs/superpowers/specs/2026-03-20-constraint-manager-design.md` (update status)

- [ ] **Step 1: Update spec status**

Change `**Status:** Draft (revised per Codex review)` to `**Status:** v1 Implemented`

- [ ] **Step 2: Record blocker validation results in spec**

Update Open Questions section with actual test results from Task 1.

- [ ] **Step 3: Delete validation scripts if no longer needed**

```bash
rm ConstraintManager/tests/validate_checkbox.py ConstraintManager/tests/validate_undo.py
```

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "docs: update spec status, record validation results, cleanup"
```
