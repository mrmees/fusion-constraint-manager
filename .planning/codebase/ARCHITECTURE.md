# Architecture

**Analysis Date:** 2026-03-22

## Pattern Overview

**Overall:** Layered add-in architecture with UI-logic separation via event handler abstraction.

**Key Characteristics:**
- Fusion 360 add-in entry point that registers a command button in the DESIGN workspace toolbar
- Strict separation of UI concerns (Fusion API interaction) from pure business logic (constraint enumeration/deletion)
- Event-driven command lifecycle: CommandCreated → InputChanged → PreSelect → Execute → Destroy
- Module-level state preservation for event handler references to prevent garbage collection
- Token-based re-resolution pattern for handling object staleness across Fusion event boundaries

## Layers

**Entry Point Layer:**
- Purpose: Bootstrap the add-in, register command definition, manage lifecycle hooks
- Location: `ConstraintManager/ConstraintManager.py`
- Contains: Top-level `run()` and `stop()` functions, global app/UI references
- Depends on: Fusion SDK (`adsk.core`, `adsk.fusion`), command module
- Used by: Fusion runtime (called automatically on add-in load/unload)

**Command & UI Layer:**
- Purpose: Manage the command dialog, handle user interactions, rebuild UI in response to selections
- Location: `ConstraintManager/commands/constraint_manager/command.py`
- Contains: Command definition/registration, all event handler classes (CommandCreatedHandler, InputChangedHandler, PreSelectHandler, ExecuteHandler, DestroyHandler)
- Depends on: Fusion SDK (UI/command APIs), constraint engine
- Used by: Fusion event system, entry point

**Constraint Engine (Pure Logic):**
- Purpose: Entity/constraint enumeration, display name resolution, deletion logic — zero Fusion UI dependencies
- Location: `ConstraintManager/commands/constraint_manager/constraint_engine.py`
- Contains: Constraint metadata maps, enumeration algorithms, related entity resolution, deletion helper
- Depends on: Python standard library (logging) only
- Used by: Command layer, tests

**Test Layer:**
- Purpose: Validate constraint engine logic outside Fusion environment
- Location: `ConstraintManager/tests/test_constraint_engine.py`
- Contains: Mock Fusion API objects, unit test suites for labeling, enumeration, and deletion
- Depends on: pytest, constraint engine module
- Used by: Developer validation during development

## Data Flow

**User Selection → Constraint Display:**

1. User clicks Constraint Manager toolbar button
2. `CommandCreatedHandler.notify()` fires: creates command dialog with entity selection input and empty constraint table
3. User selects one or more sketch entities (filtered by `PreSelectHandler`)
4. `InputChangedHandler._on_selection_changed()` fires:
   - Collects all geometric constraints from each selected entity via `constraint_engine.enumerate_constraints()`
   - Deduplicates by `entityToken` (prevents same constraint appearing twice if multiple selected entities share it)
   - Stores constraint metadata in module-level `_current_constraints` list
   - Rebuilds table UI with checkbox, entity label, constraint type, related entity columns
5. Table populates in the dialog (non-deletable constraints shown with lock emoji, checkboxes disabled)

**Deletion Workflow:**

1. User checks constraints they want to delete, clicks "Delete Selected" (okButton)
2. `ExecuteHandler.notify()` fires:
   - Iterates checked rows, extracts `entityToken` from each checked constraint
   - Calls `Design.findEntityByToken()` to re-resolve constraint objects (handles staleness)
   - Calls `.deleteMe()` on resolved constraints, logs success/failure
3. Constraint deletion commits to Fusion's undo transaction (handles undo support)
4. `DestroyHandler.notify()` fires: clears handler references to allow garbage collection

**State Management:**
- `_current_constraints` (module-level list in command.py): Holds constraint metadata dicts across events
- `_cmd_handlers` (module-level list in command.py): Holds event handler instances to prevent premature GC
- `_addin_handlers` (module-level list in command.py): Holds command definition handler for lifecycle
- Handler class attributes (e.g., `InputChangedHandler._handling_change`): Prevent re-entrance during event handling

## Key Abstractions

**Constraint Info Dict:**
- Purpose: Display-ready representation of a single constraint
- Examples: `{"constraint": <obj>, "entity_token": <str>, "type_name": "Horizontal", "related_label": "Line #3", "is_deletable": True, "source_label": "Line #0"}`
- Pattern: Built by `constraint_engine._build_constraint_info()`, stored in `_current_constraints`, consumed by table UI and executor

**Entity Label:**
- Purpose: Human-readable identifier for sketch entities in display (e.g., "Line #3", "Constr. Arc #1")
- Examples: `constraint_engine.get_entity_label(entity, index)` → "Line #3"
- Pattern: Type prefix + optional "Constr." + index, mapped via `_ENTITY_TYPE_MAP`

**Related Entity Resolution:**
- Purpose: Identify the "other" entity in a constraint relative to the selected entity
- Examples: Parallel constraint with line A and line B → return line B if A was selected
- Pattern: Type-specific property lookup via `_CONSTRAINT_ENTITY_PROPS` map, special handling for multi-entity constraints (Symmetry, Offset)

**Entity Token:**
- Purpose: Stable identifier for constraints across Fusion event boundaries (addresses object staleness)
- Pattern: Store `constraint.entityToken` during `inputChanged`, re-resolve via `Design.findEntityByToken()` in `execute` handler

## Entry Points

**Add-in Startup:**
- Location: `ConstraintManager.py::run(context)`
- Triggers: Fusion calls this when add-in is loaded (auto or manual)
- Responsibilities: Acquire Fusion app/UI references, call `constraint_cmd.start()` to register command

**Add-in Shutdown:**
- Location: `ConstraintManager.py::stop(context)`
- Triggers: Fusion calls this when add-in is unloaded
- Responsibilities: Call `constraint_cmd.stop()` to remove toolbar button and clean up handlers

**Command Invocation:**
- Location: `command.py::CommandCreatedHandler.notify()`
- Triggers: User clicks Constraint Manager button in toolbar
- Responsibilities: Validate active sketch edit mode, create command dialog with selection input and table

**Entity Selection:**
- Location: `command.py::InputChangedHandler._on_selection_changed()`
- Triggers: User selects entities in viewport or clears selection
- Responsibilities: Call constraint engine to enumerate constraints, populate table, store constraint metadata

**Deletion:**
- Location: `command.py::ExecuteHandler.notify()`
- Triggers: User clicks "Delete Selected" button
- Responsibilities: Re-resolve constraint tokens, delete via Fusion API, log results

## Error Handling

**Strategy:** Silent failure with logging + user-facing error boxes for initialization problems.

**Patterns:**
- Try/except blocks around all Fusion API calls (objects may become invalid across event boundaries)
- Logging with `_log.error()`, `_log.warning()`, `_log.info()` for debugging
- `traceback.format_exc()` captured and shown to user in `messageBox()` for startup/shutdown errors
- Constraint deletion wrapped in per-constraint try/except: failures logged but batch continues
- Pre-deletion validation: check `isValid` and `isDeletable` properties before attempting deletion

## Cross-Cutting Concerns

**Logging:**
- Module logger created at module-level: `_log = logging.getLogger(__name__)`
- Used for constraint enumeration warnings, deletion results, handler errors
- Not displayed to user (logged to Fusion script output console)

**Validation:**
- Entity type whitelist in `PreSelectHandler._SUPPORTED_TYPES`: only sketch curves and points selectable
- Active sketch requirement: command handler validates `design.activeEditObject` is a Sketch
- Entity re-resolution validation: `findEntityByToken()` returns list, check length before accessing
- Deletability check: respect constraint `.isDeletable` property, disable checkbox if False

**Constraint Type Support:**
- Hardcoded support map: `_CONSTRAINT_ENTITY_PROPS` covers 14+ constraint types
- Unknown types: logged as warning, marked non-deletable (safety), shown with "Unknown (TypeName)" label
- Extensible via adding entries to constraint type maps

---

*Architecture analysis: 2026-03-22*
