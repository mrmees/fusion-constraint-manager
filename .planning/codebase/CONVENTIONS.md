# Coding Conventions

**Analysis Date:** 2026-03-22

## Naming Patterns

**Files:**
- Module files use `snake_case`: `constraint_engine.py`, `command.py`
- Entry point file matches add-in name: `ConstraintManager.py`
- Test files follow pytest convention: `test_*.py` (e.g., `test_constraint_engine.py`)
- Validation/debug scripts use `validate_*.py` for exploratory tests (e.g., `validate_checkbox.py`, `validate_undo.py`)

**Functions:**
- Use `snake_case` for all functions: `get_entity_label()`, `enumerate_constraints()`, `resolve_related_entity()`
- Private/internal functions prefixed with single underscore: `_find_entity_index()`, `_build_constraint_info()`, `_format_related()`
- Event handler methods always named `notify()` per Fusion API: `CommandCreatedHandler.notify()`, `InputChangedHandler.notify()`

**Variables:**
- Use `snake_case` for local variables and module-level state: `_current_constraints`, `_cmd_handlers`, `_addin_handlers`
- Module-level globals prefixed with underscore and descriptive name: `_app`, `_ui`, `_log`
- Collection iteration uses `i` for simple indices, semantic names otherwise: `for i in range(entity.geometricConstraints.count)`, `for sel_idx in range(entity_select.selectionCount)`
- Boolean variables and inputs descriptive: `isDeletable`, `isConstruction`, `is_selectable`, `_handling_change`

**Types:**
- Mock classes for testing use `Mock` prefix: `MockSketchEntity`, `MockConstraint`, `MockDeletableConstraint`, `MockCollection`, `MockConstraintList`
- Constants (IDs, strings) use `SCREAMING_SNAKE_CASE`: `CMD_ID`, `CMD_VERSION`, `CMD_NAME`, `CMD_DESC`, `PANEL_ID`
- Internal constraint type mappings stored in SCREAMING_SNAKE_CASE dicts: `_ENTITY_TYPE_MAP`, `_CONSTRAINT_ENTITY_PROPS`, `_SUPPORTED_TYPES`

## Code Style

**Formatting:**
- No linter/formatter detected (no `.pylintrc`, `.flake8`, `.black`, `pyproject.toml`)
- Code follows implicit PEP 8 conventions: 4-space indentation, no trailing whitespace
- Line lengths vary but generally stay under 100 characters
- String literals use double quotes: `"constraintManagerCmd"`, `"Select Entities"`

**Linting:**
- Not enforced in codebase
- No requirements file specifying formatting tools

**Imports:**
- Ordered by standard library first, then third-party (Fusion API), then local imports
- Example from `ConstraintManager.py`:
  ```python
  import adsk.core
  import adsk.fusion
  import os
  import sys
  import traceback

  from commands.constraint_manager import command as constraint_cmd
  ```
- Example from `command.py`:
  ```python
  import adsk.core
  import adsk.fusion
  import traceback
  import logging

  from . import constraint_engine
  ```

## Import Organization

**Order:**
1. Standard library (`os`, `sys`, `traceback`, `logging`)
2. Third-party/Fusion API (`adsk.core`, `adsk.fusion`)
3. Local imports (`.`, `..`, package-relative)

**Path Aliases:**
- No explicit path aliases in use
- Relative imports used in package: `from . import constraint_engine` in `command.py`
- Top-level entry point manually inserts add-in directory to `sys.path` to enable submodule imports: see `ConstraintManager.py` lines 9-11

**Module Comments:**
- Module docstrings describe purpose and constraints: `constraint_engine.py` states "Pure logic for constraint enumeration... No Fusion UI imports"

## Error Handling

**Patterns:**
- Bare `except:` clauses used for broad Fusion API robustness (required due to Fusion SDK's unpredictable failures)
- Always capture and log/display with `traceback.format_exc()`: see `ConstraintManager.py` line 27
- In UI-critical paths, catch errors and display to user: `_ui.messageBox(f"Failed to start ConstraintManager:\n{traceback.format_exc()}")`
- In logging context, use `_log.error()` with format strings: `_log.error("Error during stop: %s", traceback.format_exc())`
- Defensive property access with `getattr()` for optional Fusion API attributes: `getattr(constraint, "isDeletable", False)`, `getattr(entity, "isConstruction", False)`
- Type validation before casting: check `isinstance(design.activeEditObject, adsk.fusion.Sketch)` before proceeding

**Exception Recovery:**
- Never re-raise — log and continue or return safe default
- Batch operations (constraint deletion) continue on per-item failure: lines 360-372 in `command.py` track deleted/failed counts

## Logging

**Framework:** Standard Python `logging` module

**Usage:**
- Logger initialized per module: `_log = logging.getLogger(__name__)` in `command.py` and `constraint_engine.py`
- Log level used appropriately: `_log.info()` for informational messages, `_log.warning()` for recoverable issues, `_log.error()` for failures
- Log messages use format strings with `%s` placeholder style: `_log.info("Deleted %d, failed %d", deleted, failed)`
- Example info log: `_log.info("Skipping invalid constraint")` (line 209 in `constraint_engine.py`)
- Example warning log: `_log.warning("Unknown constraint type: %s", constraint.objectType)` (line 92 in `constraint_engine.py`)
- Example error log: `_log.error("Failed to delete constraint: %s", e)` (line 220 in `constraint_engine.py`)

## Comments

**When to Comment:**
- Docstrings on all public functions explain purpose, args, returns
- Inline comments clarify non-obvious Fusion API quirks or workarounds
- Comments explain WHY decisions were made, not WHAT the code does

**Docstring Pattern:**
- Functions include docstring with description, Args section, Returns section (if applicable)
- Example from `constraint_engine.py`:
  ```python
  def get_entity_label(entity, index):
      """Build a display label like 'Line #3' or 'Constr. Arc #1'.

      Args:
          entity: A Fusion SketchEntity (or anything with .objectType and .isConstruction).
          index: The entity's index within its parent collection.

      Returns:
          A human-readable label string.
      """
  ```

**Class Docstrings:**
- Handler classes include docstring explaining trigger condition: `CommandCreatedHandler` line 84 states "Fires when the user clicks the Constraint Manager button"

**Inline Comments:**
- Comments explain Fusion API constraints: "Module-level list — prevents GC of command-instance handlers" (line 15 in `command.py`)
- Comments document workarounds: "Use == not 'is' — Fusion may return different wrapper objects for the same entity" (line 104 in `constraint_engine.py`)

## Function Design

**Size:** Functions generally 10-50 lines; event handlers are ~40-80 lines due to UI setup complexity

**Parameters:**
- Functions accept Fusion API objects directly or plain data structures (dicts, lists)
- Constraint engine functions use optional `index_finder` callback for flexible entity resolution
- Event handlers access data via `args` parameter from Fusion events

**Return Values:**
- Constraint enumeration returns list of dicts with standardized keys: `{"constraint": obj, "entity_token": str, "type_name": str, "related_label": str, "is_deletable": bool}`
- Deletion operations return summary dict: `{"deleted": int, "failed": int, "skipped": int}`
- Label builders return formatted strings

## Module Design

**Exports:**
- `command.py` exposes `start(app, ui)` and `stop()` as public API called by entry point
- `constraint_engine.py` exposes functions as utilities: `get_entity_label()`, `enumerate_constraints()`, `resolve_related_entity()`, `delete_constraints()`
- Private functions prefixed with `_` are not exported

**Barrel Files:**
- `__init__.py` files are minimal or empty (e.g., `/commands/__init__.py` is empty)
- No re-exports or barrel patterns in use

**Handler Classes:**
- Event handler classes are defined in `command.py` but stored in module-level list `_cmd_handlers` to prevent garbage collection
- Handlers maintain state through instance attributes: `InputChangedHandler._handling_change` flag prevents re-entrant calls

**State Management:**
- Global state shared across handlers stored at module level: `_current_constraints = []`, `_cmd_handlers = []`, `_addin_handlers = []`
- No class-level state used (would not survive between Fusion events)
- State reset on handler destruction: `DestroyHandler` clears global lists

---

*Convention analysis: 2026-03-22*
