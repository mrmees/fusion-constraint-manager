# Phase 1: Engine and Tab Foundation - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Migrate the v1.1 single-view command dialog into a three-tab structure (Selected / Types / All), extend the constraint engine with sketch-wide enumeration and type operations, and preserve existing Selected Entities behavior identically. No new user-facing features beyond the tab scaffold — Phase 2 and 3 build the content.

</domain>

<decisions>
## Implementation Decisions

### Tab Behavior
- **D-01:** Tab labels are short: "Selected", "Types", "All"
- **D-02:** "Selected" tab is the default active tab on command launch (preserves v1 UX)
- **D-03:** "Types" and "All" tabs show placeholder UI in Phase 1 — empty table structure with no data/actions, validating the tab infrastructure works before features are built
- **D-04:** No tab auto-loads anything expensive. Each tab's data is lazy-loaded only when the user explicitly triggers it (entity selection for Selected, load button for Types and All)

### State Management
- **D-05:** Per-tab state isolation — Claude's discretion on exact structure (dict per tab vs separate globals), but must keep the plugin lightweight with no background loading
- **D-06:** wire_handler() utility added — simple helper that creates handler, adds to event, appends to handler list. Zero runtime overhead, prevents GC handler loss with 3x more handlers in v2
- **D-07:** Re-entrance guard must handle tab switch events (InputChanged fires on tab switch)

### Engine API Design
- **D-08:** New engine methods built and fully tested in Phase 1 — not stubbed. De-risks Phase 2/3 so they can focus purely on UI
- **D-09:** Return formats are Claude's discretion — design what each tab actually needs (Types tab just needs type+count, not full constraint info dicts)
- **D-10:** All new engine methods must have pytest coverage runnable outside Fusion

### Migration Safety
- **D-11:** V1 code migrated into Tab 1 — all entity selection, constraint table, and deletion logic moves inside TabCommandInput children
- **D-12:** Verification is manual testing in Fusion — run the add-in, test entity selection and deletion by hand
- **D-13:** Rollback strategy is Claude's discretion (git revert is simplest given clean v1.1 commits)

### Claude's Discretion
- State organization pattern (D-05)
- Engine return formats per tab (D-09)
- Rollback approach (D-13)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Implementation
- `ConstraintManager/commands/constraint_manager/command.py` — Current v1.1 command UI, event handlers, table logic (the code being migrated)
- `ConstraintManager/commands/constraint_manager/constraint_engine.py` — Current constraint enumeration/deletion logic (being extended)
- `ConstraintManager/tests/test_constraint_engine.py` — Existing pytest tests (being expanded)

### Research
- `.planning/research/STACK.md` — Fusion API classes for TabCommandInput, DropDownCommandInput, TableCommandInput
- `.planning/research/ARCHITECTURE.md` — Sketch-wide enumeration via `sketch.geometricConstraints`, tab event handling, build order
- `.planning/research/PITFALLS.md` — Forward-iteration deletion bug, GC handler loss, re-entrance guards, token invalidation

### Codebase Analysis
- `.planning/codebase/ARCHITECTURE.md` — Current layered architecture, data flow, state management patterns
- `.planning/codebase/CONVENTIONS.md` — Naming patterns, code style, import ordering

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `constraint_engine.py` — Pure logic layer with zero Fusion UI dependencies. All new sketch-wide methods go here.
- `_build_constraint_info()` — Existing constraint info dict builder. May be reusable for All Constraints tab with minimal changes.
- `_CONSTRAINT_ENTITY_PROPS` map — Covers 14+ constraint types. Reusable for type counting.
- Mock test infrastructure — `MockSketchEntity`, `MockConstraint`, `MockCollection` etc. in `test_constraint_engine.py`. Extend for sketch-wide tests.

### Established Patterns
- Module-level globals for state (`_current_constraints`, `_cmd_handlers`, `_addin_handlers`)
- Event handler classes inheriting from Fusion handler base classes with `notify()` method
- `_handling_change` boolean for re-entrance prevention
- `entityToken` + `findEntityByToken()` for cross-event object re-resolution

### Integration Points
- `command.py::CommandCreatedHandler.notify()` — Where tab creation happens (currently creates inputs directly on command)
- `command.py::InputChangedHandler._on_selection_changed()` — Needs routing logic for which tab is active
- `command.py::start()/stop()` — Toolbar button registration, unchanged

</code_context>

<specifics>
## Specific Ideas

- User emphasized keeping the plugin lightweight — no background loading, no auto-enumeration on tab switch
- Load buttons on Types and All tabs (not just All) — user wants explicit user-triggered loading everywhere
- Performance is a top concern — user specifically flagged Fusion's instability and doesn't want the add-in causing issues

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-engine-and-tab-foundation*
*Context gathered: 2026-03-22*
