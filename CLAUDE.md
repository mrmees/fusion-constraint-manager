<!-- GSD:project-start source:PROJECT.md -->
## Project

**Constraint Manager v2.0**

A Fusion (Autodesk Fusion 360) desktop add-in that gives users a comprehensive constraint management interface for sketches. v1.1 shipped a command-based tool for viewing and selectively deleting constraints on selected entities. v2.0 evolves the UI into a three-tab interface that adds sketch-wide constraint type summaries with bulk deletion, and a full constraint list with type filtering — filling the largest unmet needs in the Fusion constraint management space.

**Core Value:** Users can see and manage every constraint in a sketch without guessing, clicking blindly, or relying on Fusion's all-or-nothing deletion.

### Constraints

- **Platform**: Autodesk Fusion 360 Python API (`adsk.core`, `adsk.fusion`) — all UI must use Fusion's command input system (`TabCommandInput`, `TableCommandInput`, `DropDownCommandInput`)
- **Runtime**: Python 3.x as provided by Fusion's embedded interpreter — no external dependencies allowed in production
- **Installation**: Folder copy to `%APPDATA%/Autodesk/Autodesk Fusion 360/API/AddIns/ConstraintManager/` — no build step
- **Compatibility**: Must work on Windows and macOS
- **Performance**: Sketch-wide operations must handle sketches with 500+ entities without hanging the UI
- **Backward compatibility**: Selected Entities tab must behave identically to v1.1
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.x - Add-in implementation, command handlers, constraint logic
- JSON - Add-in manifest configuration
- PNG - Toolbar icon assets
## Runtime
- Autodesk Fusion 360 (2025+) - Required host application
- Windows / macOS - Supported platforms per manifest
- pip (Python standard) - For development and testing dependencies only
- No lockfile (`requirements.txt` or similar) - Pure Python standard library used, no production dependencies
## Frameworks
- Autodesk Fusion 360 API (adsk.core, adsk.fusion) - Desktop add-in framework and geometric modeling API
- pytest - For unit testing constraint logic outside Fusion
- No build tool - Add-in is pure Python; direct folder copy to installation directory required
## Key Dependencies
- `adsk.core` - Fusion application framework, UI command definitions, event handlers
- `adsk.fusion` - Fusion modeling API, sketch/constraint objects, design traversal
- `pytest` - Test execution; not included in production add-in
## Configuration
- Windows: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\ConstraintManager\`
- macOS: `/Users/[user]/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/ConstraintManager/`
- Installation is folder copy, no build step
- No build system - manifest file `ConstraintManager.manifest` declares metadata (name, version, author, supported OS)
## Platform Requirements
- Python 3.x installed locally (for running tests outside Fusion)
- pytest package (development only)
- Windows or macOS (no Linux/WSL support — Fusion is desktop-only)
- Autodesk Fusion 360 application installed and running
- Windows or macOS as per Fusion support
- No internet connection required — fully offline add-in
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- Module files use `snake_case`: `constraint_engine.py`, `command.py`
- Entry point file matches add-in name: `ConstraintManager.py`
- Test files follow pytest convention: `test_*.py` (e.g., `test_constraint_engine.py`)
- Validation/debug scripts use `validate_*.py` for exploratory tests (e.g., `validate_checkbox.py`, `validate_undo.py`)
- Use `snake_case` for all functions: `get_entity_label()`, `enumerate_constraints()`, `resolve_related_entity()`
- Private/internal functions prefixed with single underscore: `_find_entity_index()`, `_build_constraint_info()`, `_format_related()`
- Event handler methods always named `notify()` per Fusion API: `CommandCreatedHandler.notify()`, `InputChangedHandler.notify()`
- Use `snake_case` for local variables and module-level state: `_current_constraints`, `_cmd_handlers`, `_addin_handlers`
- Module-level globals prefixed with underscore and descriptive name: `_app`, `_ui`, `_log`
- Collection iteration uses `i` for simple indices, semantic names otherwise: `for i in range(entity.geometricConstraints.count)`, `for sel_idx in range(entity_select.selectionCount)`
- Boolean variables and inputs descriptive: `isDeletable`, `isConstruction`, `is_selectable`, `_handling_change`
- Mock classes for testing use `Mock` prefix: `MockSketchEntity`, `MockConstraint`, `MockDeletableConstraint`, `MockCollection`, `MockConstraintList`
- Constants (IDs, strings) use `SCREAMING_SNAKE_CASE`: `CMD_ID`, `CMD_VERSION`, `CMD_NAME`, `CMD_DESC`, `PANEL_ID`
- Internal constraint type mappings stored in SCREAMING_SNAKE_CASE dicts: `_ENTITY_TYPE_MAP`, `_CONSTRAINT_ENTITY_PROPS`, `_SUPPORTED_TYPES`
## Code Style
- No linter/formatter detected (no `.pylintrc`, `.flake8`, `.black`, `pyproject.toml`)
- Code follows implicit PEP 8 conventions: 4-space indentation, no trailing whitespace
- Line lengths vary but generally stay under 100 characters
- String literals use double quotes: `"constraintManagerCmd"`, `"Select Entities"`
- Not enforced in codebase
- No requirements file specifying formatting tools
- Ordered by standard library first, then third-party (Fusion API), then local imports
- Example from `ConstraintManager.py`:
- Example from `command.py`:
## Import Organization
- No explicit path aliases in use
- Relative imports used in package: `from . import constraint_engine` in `command.py`
- Top-level entry point manually inserts add-in directory to `sys.path` to enable submodule imports: see `ConstraintManager.py` lines 9-11
- Module docstrings describe purpose and constraints: `constraint_engine.py` states "Pure logic for constraint enumeration... No Fusion UI imports"
## Error Handling
- Bare `except:` clauses used for broad Fusion API robustness (required due to Fusion SDK's unpredictable failures)
- Always capture and log/display with `traceback.format_exc()`: see `ConstraintManager.py` line 27
- In UI-critical paths, catch errors and display to user: `_ui.messageBox(f"Failed to start ConstraintManager:\n{traceback.format_exc()}")`
- In logging context, use `_log.error()` with format strings: `_log.error("Error during stop: %s", traceback.format_exc())`
- Defensive property access with `getattr()` for optional Fusion API attributes: `getattr(constraint, "isDeletable", False)`, `getattr(entity, "isConstruction", False)`
- Type validation before casting: check `isinstance(design.activeEditObject, adsk.fusion.Sketch)` before proceeding
- Never re-raise — log and continue or return safe default
- Batch operations (constraint deletion) continue on per-item failure: lines 360-372 in `command.py` track deleted/failed counts
## Logging
- Logger initialized per module: `_log = logging.getLogger(__name__)` in `command.py` and `constraint_engine.py`
- Log level used appropriately: `_log.info()` for informational messages, `_log.warning()` for recoverable issues, `_log.error()` for failures
- Log messages use format strings with `%s` placeholder style: `_log.info("Deleted %d, failed %d", deleted, failed)`
- Example info log: `_log.info("Skipping invalid constraint")` (line 209 in `constraint_engine.py`)
- Example warning log: `_log.warning("Unknown constraint type: %s", constraint.objectType)` (line 92 in `constraint_engine.py`)
- Example error log: `_log.error("Failed to delete constraint: %s", e)` (line 220 in `constraint_engine.py`)
## Comments
- Docstrings on all public functions explain purpose, args, returns
- Inline comments clarify non-obvious Fusion API quirks or workarounds
- Comments explain WHY decisions were made, not WHAT the code does
- Functions include docstring with description, Args section, Returns section (if applicable)
- Example from `constraint_engine.py`:
- Handler classes include docstring explaining trigger condition: `CommandCreatedHandler` line 84 states "Fires when the user clicks the Constraint Manager button"
- Comments explain Fusion API constraints: "Module-level list — prevents GC of command-instance handlers" (line 15 in `command.py`)
- Comments document workarounds: "Use == not 'is' — Fusion may return different wrapper objects for the same entity" (line 104 in `constraint_engine.py`)
## Function Design
- Functions accept Fusion API objects directly or plain data structures (dicts, lists)
- Constraint engine functions use optional `index_finder` callback for flexible entity resolution
- Event handlers access data via `args` parameter from Fusion events
- Constraint enumeration returns list of dicts with standardized keys: `{"constraint": obj, "entity_token": str, "type_name": str, "related_label": str, "is_deletable": bool}`
- Deletion operations return summary dict: `{"deleted": int, "failed": int, "skipped": int}`
- Label builders return formatted strings
## Module Design
- `command.py` exposes `start(app, ui)` and `stop()` as public API called by entry point
- `constraint_engine.py` exposes functions as utilities: `get_entity_label()`, `enumerate_constraints()`, `resolve_related_entity()`, `delete_constraints()`
- Private functions prefixed with `_` are not exported
- `__init__.py` files are minimal or empty (e.g., `/commands/__init__.py` is empty)
- No re-exports or barrel patterns in use
- Event handler classes are defined in `command.py` but stored in module-level list `_cmd_handlers` to prevent garbage collection
- Handlers maintain state through instance attributes: `InputChangedHandler._handling_change` flag prevents re-entrant calls
- Global state shared across handlers stored at module level: `_current_constraints = []`, `_cmd_handlers = []`, `_addin_handlers = []`
- No class-level state used (would not survive between Fusion events)
- State reset on handler destruction: `DestroyHandler` clears global lists
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Fusion 360 add-in entry point that registers a command button in the DESIGN workspace toolbar
- Strict separation of UI concerns (Fusion API interaction) from pure business logic (constraint enumeration/deletion)
- Event-driven command lifecycle: CommandCreated → InputChanged → PreSelect → Execute → Destroy
- Module-level state preservation for event handler references to prevent garbage collection
- Token-based re-resolution pattern for handling object staleness across Fusion event boundaries
## Layers
- Purpose: Bootstrap the add-in, register command definition, manage lifecycle hooks
- Location: `ConstraintManager/ConstraintManager.py`
- Contains: Top-level `run()` and `stop()` functions, global app/UI references
- Depends on: Fusion SDK (`adsk.core`, `adsk.fusion`), command module
- Used by: Fusion runtime (called automatically on add-in load/unload)
- Purpose: Manage the command dialog, handle user interactions, rebuild UI in response to selections
- Location: `ConstraintManager/commands/constraint_manager/command.py`
- Contains: Command definition/registration, all event handler classes (CommandCreatedHandler, InputChangedHandler, PreSelectHandler, ExecuteHandler, DestroyHandler)
- Depends on: Fusion SDK (UI/command APIs), constraint engine
- Used by: Fusion event system, entry point
- Purpose: Entity/constraint enumeration, display name resolution, deletion logic — zero Fusion UI dependencies
- Location: `ConstraintManager/commands/constraint_manager/constraint_engine.py`
- Contains: Constraint metadata maps, enumeration algorithms, related entity resolution, deletion helper
- Depends on: Python standard library (logging) only
- Used by: Command layer, tests
- Purpose: Validate constraint engine logic outside Fusion environment
- Location: `ConstraintManager/tests/test_constraint_engine.py`
- Contains: Mock Fusion API objects, unit test suites for labeling, enumeration, and deletion
- Depends on: pytest, constraint engine module
- Used by: Developer validation during development
## Data Flow
- `_current_constraints` (module-level list in command.py): Holds constraint metadata dicts across events
- `_cmd_handlers` (module-level list in command.py): Holds event handler instances to prevent premature GC
- `_addin_handlers` (module-level list in command.py): Holds command definition handler for lifecycle
- Handler class attributes (e.g., `InputChangedHandler._handling_change`): Prevent re-entrance during event handling
## Key Abstractions
- Purpose: Display-ready representation of a single constraint
- Examples: `{"constraint": <obj>, "entity_token": <str>, "type_name": "Horizontal", "related_label": "Line #3", "is_deletable": True, "source_label": "Line #0"}`
- Pattern: Built by `constraint_engine._build_constraint_info()`, stored in `_current_constraints`, consumed by table UI and executor
- Purpose: Human-readable identifier for sketch entities in display (e.g., "Line #3", "Constr. Arc #1")
- Examples: `constraint_engine.get_entity_label(entity, index)` → "Line #3"
- Pattern: Type prefix + optional "Constr." + index, mapped via `_ENTITY_TYPE_MAP`
- Purpose: Identify the "other" entity in a constraint relative to the selected entity
- Examples: Parallel constraint with line A and line B → return line B if A was selected
- Pattern: Type-specific property lookup via `_CONSTRAINT_ENTITY_PROPS` map, special handling for multi-entity constraints (Symmetry, Offset)
- Purpose: Stable identifier for constraints across Fusion event boundaries (addresses object staleness)
- Pattern: Store `constraint.entityToken` during `inputChanged`, re-resolve via `Design.findEntityByToken()` in `execute` handler
## Entry Points
- Location: `ConstraintManager.py::run(context)`
- Triggers: Fusion calls this when add-in is loaded (auto or manual)
- Responsibilities: Acquire Fusion app/UI references, call `constraint_cmd.start()` to register command
- Location: `ConstraintManager.py::stop(context)`
- Triggers: Fusion calls this when add-in is unloaded
- Responsibilities: Call `constraint_cmd.stop()` to remove toolbar button and clean up handlers
- Location: `command.py::CommandCreatedHandler.notify()`
- Triggers: User clicks Constraint Manager button in toolbar
- Responsibilities: Validate active sketch edit mode, create command dialog with selection input and table
- Location: `command.py::InputChangedHandler._on_selection_changed()`
- Triggers: User selects entities in viewport or clears selection
- Responsibilities: Call constraint engine to enumerate constraints, populate table, store constraint metadata
- Location: `command.py::ExecuteHandler.notify()`
- Triggers: User clicks "Delete Selected" button
- Responsibilities: Re-resolve constraint tokens, delete via Fusion API, log results
## Error Handling
- Try/except blocks around all Fusion API calls (objects may become invalid across event boundaries)
- Logging with `_log.error()`, `_log.warning()`, `_log.info()` for debugging
- `traceback.format_exc()` captured and shown to user in `messageBox()` for startup/shutdown errors
- Constraint deletion wrapped in per-constraint try/except: failures logged but batch continues
- Pre-deletion validation: check `isValid` and `isDeletable` properties before attempting deletion
## Cross-Cutting Concerns
- Module logger created at module-level: `_log = logging.getLogger(__name__)`
- Used for constraint enumeration warnings, deletion results, handler errors
- Not displayed to user (logged to Fusion script output console)
- Entity type whitelist in `PreSelectHandler._SUPPORTED_TYPES`: only sketch curves and points selectable
- Active sketch requirement: command handler validates `design.activeEditObject` is a Sketch
- Entity re-resolution validation: `findEntityByToken()` returns list, check length before accessing
- Deletability check: respect constraint `.isDeletable` property, disable checkbox if False
- Hardcoded support map: `_CONSTRAINT_ENTITY_PROPS` covers 14+ constraint types
- Unknown types: logged as warning, marked non-deletable (safety), shown with "Unknown (TypeName)" label
- Extensible via adding entries to constraint type maps
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
