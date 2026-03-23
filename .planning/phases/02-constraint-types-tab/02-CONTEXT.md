# Phase 2: Constraint Types Tab - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the Constraint Types tab content: a summary table showing each constraint type in the active sketch with its count, a toolbar "Delete All of Type" button acting on the selected row, and auto-refresh after deletion. All engine functions (aggregate_constraint_types, collect_constraints_by_type) were built and tested in Phase 1.

</domain>

<decisions>
## Implementation Decisions

### Load Trigger
- **D-01:** Types tab auto-populates when user switches to it — no Load button needed. Counting by type via `aggregate_constraint_types()` is O(n) with no expensive operations (no entity label resolution, no info dicts).
- **D-02:** Re-populates on each tab switch to show current state (constraints may have been deleted from Selected tab).

### Delete Behavior
- **D-03:** "Delete All of Type" is a toolbar button below the summary table, acting on the currently selected row (Fusion tables don't support per-row buttons).
- **D-04:** No confirmation dialog before deletion — Fusion's Ctrl+Z undo handles mistakes. Fast workflow.
- **D-05:** Bulk deletion uses `collect_constraints_by_type()` from the engine, then reverse-iteration `deleteMe()` to avoid forward-iteration skip bug (TYPE-05).
- **D-06:** After deletion, the table auto-refreshes by re-running `aggregate_constraint_types()` — deleted type disappears, counts adjust immediately.

### Empty/Edge States
- **D-07:** When sketch has zero constraints: show simple text message "No constraints in this sketch" instead of an empty table.
- **D-08:** After deleting all of a type, the row disappears from the refreshed table. If that was the last type, show the empty state message.

### Carried from Phase 1
- Per-tab state via `_tab_state["types"]` dict (D-05 from Phase 1)
- wire_handler utility for GC protection (D-06 from Phase 1)
- Re-entrance guard handles tab switch events (D-07 from Phase 1)
- Manual Fusion testing for verification (D-12 from Phase 1)
- args.inputs may return tab children — use the fallback pattern from Phase 1 bugfix (e6b4f60)

### Claude's Discretion
- Table column layout (type name + count, or add a percentage column)
- Button placement and label for "Delete All of Type"
- Whether to disable the delete button when no row is selected

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Current Implementation (Phase 1 output)
- `ConstraintManager/commands/constraint_manager/command.py` — Tab infrastructure, _tab_state, wire_handler, tab-aware event routing. Note the args.inputs fallback pattern for tab-scoped inputs.
- `ConstraintManager/commands/constraint_manager/constraint_engine.py` — `aggregate_constraint_types()`, `collect_constraints_by_type()`, and other sketch-wide functions built in Phase 1
- `ConstraintManager/tests/test_constraint_engine.py` — 52 existing tests including sketch-wide function coverage

### Research
- `.planning/research/STACK.md` — Fusion API: TableCommandInput, ButtonRowCommandInput limitations, toolbar button + selectedRow pattern
- `.planning/research/PITFALLS.md` — Forward-iteration deletion bug (must use reverse iteration), GC handler loss, re-entrance guards

### Phase 1 Context
- `.planning/phases/01-engine-and-tab-foundation/01-CONTEXT.md` — Prior decisions on tab behavior, state management, engine API

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `constraint_engine.aggregate_constraint_types(sketch)` — Returns `{type_name: count}` dict. Ready to use, fully tested.
- `constraint_engine.collect_constraints_by_type(sketch, type_name)` — Returns list of raw constraint objects for deletion. Fully tested.
- `_tab_state["types"]["summary"]` — Already initialized as empty dict in Phase 1.
- `_wire_handler()` — GC-safe handler wiring.
- Tab-aware `InputChangedHandler` with `_active_tab` routing — already handles `tab_types` case (currently no-op).

### Established Patterns
- Table creation: `sel_inputs.addTableCommandInput(id, label, columns, ratios)` with `addCommandInput(input, row, col)`
- Row inputs created via `adsk.core.CommandInputs.cast(table.commandInputs)`
- Tab children accessed via `tab.children` (or directly from `args.inputs` if already scoped to tab)
- Reverse-iteration for table row deletion: `for i in range(table.rowCount - 1, -1, -1)`

### Integration Points
- `InputChangedHandler.notify()` — Add `tab_types` routing branch (currently placeholder)
- `ExecuteHandler.notify()` — Add `tab_types` deletion execution branch
- Types tab placeholder text (`typesPlaceholder`) — Replace with actual table + button

</code_context>

<specifics>
## Specific Ideas

- User emphasized performance consciousness — auto-populate is acceptable because counting is cheap, but any future additions to this tab should stay lightweight
- The DXF/SVG import cleanup use case is the primary audience for this tab — "Delete All Fix" is the killer feature
- No confirmation before delete — trust Ctrl+Z. Speed matters for users cleaning up hundreds of auto-constraints.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-constraint-types-tab*
*Context gathered: 2026-03-23*
