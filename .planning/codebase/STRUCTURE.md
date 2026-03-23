# Codebase Structure

**Analysis Date:** 2026-03-22

## Directory Layout

```
ConstraintManager/
├── ConstraintManager.py              # Add-in entry point (run/stop lifecycle)
├── ConstraintManager.manifest        # Add-in metadata and version
├── commands/
│   ├── __init__.py                   # Empty package marker
│   └── constraint_manager/
│       ├── __init__.py               # Empty package marker
│       ├── command.py                # Command UI, event handlers, table logic
│       └── constraint_engine.py      # Pure constraint logic (testable outside Fusion)
├── resources/
│   └── constraint_manager/
│       ├── 16x16.png                 # Toolbar icon (16px)
│       └── 32x32.png                 # Toolbar icon (32px, high-DPI)
└── tests/
    ├── test_constraint_engine.py     # Unit tests (pytest, run outside Fusion)
    ├── validate_checkbox.py          # Manual test script (for Fusion)
    └── validate_undo.py              # Manual test script (for Fusion)
```

## Directory Purposes

**ConstraintManager/ (root):**
- Purpose: Add-in package root, contains entry point and manifest
- Contains: Python entry point, manifest metadata
- Key files: `ConstraintManager.py`, `ConstraintManager.manifest`

**ConstraintManager/commands/ :**
- Purpose: Organize command definitions by feature/module (Fusion convention)
- Contains: One subdir per command (currently just constraint_manager)
- Key files: `__init__.py` (package marker only)

**ConstraintManager/commands/constraint_manager/ :**
- Purpose: Implementation of the Constraint Manager command
- Contains: Command UI/handler logic, pure constraint engine logic
- Key files: `command.py` (UI), `constraint_engine.py` (logic)

**ConstraintManager/resources/ :**
- Purpose: Non-code resources (icons, images)
- Contains: Icon assets organized by command
- Key files: `constraint_manager/16x16.png`, `constraint_manager/32x32.png`

**ConstraintManager/tests/ :**
- Purpose: Test and validation scripts
- Contains: Unit tests (pytest), manual validation scripts
- Key files: `test_constraint_engine.py` (automated), `validate_checkbox.py`, `validate_undo.py` (manual)

## Key File Locations

**Entry Points:**
- `ConstraintManager/ConstraintManager.py`: Fusion calls `run(context)` on load, `stop(context)` on unload. Acquires Fusion app/UI, delegates to command module.

**Configuration:**
- `ConstraintManager/ConstraintManager.manifest`: JSON metadata (id, version, author, OS support). Parsed by Fusion to register add-in.

**Core Logic:**
- `ConstraintManager/commands/constraint_manager/command.py`: All Fusion API UI interaction. Command registration, dialog creation, event handlers (CommandCreatedHandler, InputChangedHandler, PreSelectHandler, ExecuteHandler, DestroyHandler).
- `ConstraintManager/commands/constraint_manager/constraint_engine.py`: Pure Python constraint enumeration, labeling, deletion. No Fusion dependencies, fully testable.

**Testing:**
- `ConstraintManager/tests/test_constraint_engine.py`: Pytest unit tests covering entity labeling, constraint enumeration, related entity resolution, deletion logic. Uses mock objects.
- `ConstraintManager/tests/validate_checkbox.py`: Manual test script (run inside Fusion) for checkbox behavior.
- `ConstraintManager/tests/validate_undo.py`: Manual test script (run inside Fusion) for undo transaction behavior.

## Naming Conventions

**Files:**
- Module files: `snake_case.py` (e.g., `constraint_engine.py`, `command.py`)
- Test files: `test_<module>.py` or `validate_<feature>.py` (e.g., `test_constraint_engine.py`)
- Manifest: `<AddInName>.manifest` (e.g., `ConstraintManager.manifest`)
- Entry point: `<AddInName>.py` (e.g., `ConstraintManager.py`)

**Directories:**
- Feature/command dirs: `snake_case` (e.g., `constraint_manager/`)
- Package dirs: typically the feature name
- Resource dirs: match command name (e.g., `resources/constraint_manager/`)

**Python Identifiers:**
- Functions: `snake_case` (e.g., `get_entity_label()`, `enumerate_constraints()`)
- Classes: `PascalCase` (e.g., `CommandCreatedHandler`, `MockSketchEntity`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `CMD_ID`, `_ENTITY_TYPE_MAP`)
- Private/internal: `_leading_underscore` (e.g., `_current_constraints`, `_build_constraint_info()`)
- Event handlers: `PascalCase` + `Handler` suffix (e.g., `InputChangedHandler`)

## Where to Add New Code

**New Feature/Command:**
- Create new subdir under `commands/` (e.g., `commands/my_feature/`)
- Add `command.py` for UI/handlers, `my_module.py` for pure logic
- Create `tests/test_my_feature.py` for unit tests
- Add new `start()` and `stop()` functions to handle registration, called from main entry point

**New Constraint Type Support:**
- Add entry to `_CONSTRAINT_ENTITY_PROPS` map in `constraint_engine.py` with property names (keys: "MyConstraint", values: tuple of entity property names)
- Add optional display mapping to `_ENTITY_TYPE_MAP` if entity type is new
- Add test cases to `tests/test_constraint_engine.py` for related entity resolution and enumeration
- Example:
  ```python
  _CONSTRAINT_ENTITY_PROPS = {
      # ... existing types ...
      "MyNewConstraint": ("entityOne", "entityTwo"),
  }
  ```

**New UI Control:**
- Place in `command.py` command handler (CommandCreatedHandler.notify())
- Wire event handler reference into `_cmd_handlers` list (prevents garbage collection)
- Example: adding new table column or button input

**Shared Utilities:**
- Pure logic (no Fusion API): add to `constraint_engine.py`
- Fusion API utilities: create new module in `commands/constraint_manager/` and import from `command.py`
- Test any pure logic in `tests/test_constraint_engine.py`

**Test Files:**
- Automated tests (pytest, run outside Fusion): `tests/test_<module>.py`
- Manual validation (run inside Fusion): `tests/validate_<feature>.py`
- Mock objects: define in test file itself (Fusion API not available for import outside Fusion)

## Special Directories

**ConstraintManager/__pycache__/ :**
- Purpose: Python bytecode cache (auto-generated by Python)
- Generated: Yes (automatically by Python interpreter)
- Committed: No (in .gitignore)

**tests/__pycache__/ :**
- Purpose: Test bytecode cache
- Generated: Yes
- Committed: No

## Import Patterns

**Entry point imports:**
```python
import adsk.core
import adsk.fusion
# Relative imports for submodules:
from commands.constraint_manager import command as constraint_cmd
```

**Command module imports:**
```python
import adsk.core
import adsk.fusion
import logging
import traceback
# Relative imports for sibling modules:
from . import constraint_engine
```

**Constraint engine imports:**
```python
import logging
# No Fusion API imports (by design — maintains testability)
```

**Test imports:**
```python
import pytest
# Import from ConstraintManager package:
from ConstraintManager.commands.constraint_manager.constraint_engine import get_entity_label
# Mock objects defined in test file itself
```

---

*Structure analysis: 2026-03-22*
