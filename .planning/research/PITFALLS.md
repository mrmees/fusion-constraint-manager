# Pitfalls Research

**Domain:** Fusion 360 add-in with tabbed command UI, sketch-wide constraint enumeration, and bulk deletion
**Researched:** 2026-03-22
**Confidence:** HIGH (codebase-verified pitfalls + Fusion API documentation + community reports)

## Critical Pitfalls

### Pitfall 1: Forward-Iteration Deletion Skips Every Other Item

**What goes wrong:**
Calling `deleteMe()` on constraints while iterating forward through a Fusion collection (e.g., `geometricConstraints`) causes the collection to re-index on each deletion. Item at index 3 becomes index 2 after deleting index 2, so the loop skips it. The result: roughly half of targeted constraints survive a "Delete All" operation. This is the single most reported API bug on the Autodesk forums for bulk operations.

**Why it happens:**
Fusion collections are live — they re-index immediately when an element is removed. A standard `for i in range(collection.count)` loop increments `i` but the collection has shifted, causing every-other-item skipping. Python's `for item in collection` exhibits the same issue since the underlying iterator uses index-based access.

**How to avoid:**
Two proven approaches:
1. **Reverse iteration** — iterate from `count - 1` down to `0`. Deletions at the tail don't affect indices of remaining items.
2. **Snapshot-then-delete** — collect all target entity tokens (or object references) into a list first, then iterate the list and call `deleteMe()` on each. The v1.1 codebase already uses token-based resolution in the execute handler, so this pattern should extend naturally.

For the Constraint Types tab "Delete All [Type]" feature, always snapshot tokens before deleting. Never delete while iterating a live Fusion collection.

**Warning signs:**
- "Delete All Fix" removes ~50% of Fix constraints and user has to click again
- Constraint counts don't match expected after bulk operation
- Inconsistent deletion results between runs on the same sketch

**Phase to address:**
Phase 1 (Constraint Types tab implementation) — this is the first phase that introduces bulk deletion across a sketch.

---

### Pitfall 2: InputChanged Re-Entrance During Tab Switches

**What goes wrong:**
Switching between `TabCommandInput` tabs fires `inputChanged` events. If the handler rebuilds UI (clears and repopulates tables, triggers selection changes), it can fire additional `inputChanged` events recursively. The existing `_handling_change` flag on `InputChangedHandler` prevents re-entrance within a single handler invocation, but tab switches introduce a new trigger source that the current guard may not cover — specifically, programmatic changes to input visibility or values during tab switch handling can fire secondary events after the guard is released.

**Why it happens:**
Tab switches are `inputChanged` events where the changed input is the `TabCommandInput` itself. Responding to a tab switch by modifying other inputs (showing/hiding tables, updating text, changing dropdown values) fires additional `inputChanged` events. The current instance-level `_handling_change` flag is set/cleared within a single `notify()` call, but Fusion may queue the secondary events and deliver them after `finally` resets the flag.

**How to avoid:**
- Check `changed_input.id` early and route tab switches to a dedicated handler that does minimal work
- Use `changed_input.objectType` to distinguish `TabCommandInput` changes from other input changes
- Set a module-level `_switching_tabs` guard that persists across the tab-switch event cascade
- Avoid modifying input values or visibility during tab switch handling when possible — defer to a "tab activated" pattern where each tab's content is pre-built during `CommandCreated` and only shown/hidden

**Warning signs:**
- Dialog flickers or redraws multiple times when clicking a tab
- Stack overflow or recursion errors in InputChanged handler
- Stale data appearing briefly before correct data loads
- `_handling_change` flag silently swallowing legitimate events

**Phase to address:**
Phase 1 (Tab UI scaffolding) — must be solved before any tab-specific logic is built.

---

### Pitfall 3: Entity Token Invalidation During Bulk Deletion Within Execute

**What goes wrong:**
When deleting multiple constraints in the execute handler, deleting constraint A can invalidate the entity token for constraint B if they share geometry or if A's deletion causes Fusion to rebuild the sketch topology. The token stored during `inputChanged` resolves to nothing (or a different entity) by the time the loop reaches constraint B. This is especially dangerous for "Delete All [Type]" where dozens of constraints share the same sketch entities.

**Why it happens:**
Entity tokens are stable across Fusion events (inputChanged to execute), but within a single execute handler, deleting constraints mutates the sketch model in real time. Fusion's constraint solver runs after each `deleteMe()`, potentially reorganizing internal references. Tokens that pointed to constraint B before A's deletion may no longer resolve.

**How to avoid:**
- **Re-resolve each token immediately before deletion** — don't batch-resolve all tokens upfront and then delete from the resolved list
- **Check `isValid` on the resolved entity** before calling `deleteMe()`
- **Track and report partial failures** — aggregate results into a user-facing summary ("Deleted 47 of 52 Fix constraints; 5 could not be resolved")
- **Consider sorting deletions** — delete independent constraints first (those not sharing geometry with other targets), then handle shared ones

**Warning signs:**
- `findEntityByToken()` returns empty list for tokens that were valid moments ago
- Deleted count consistently lower than expected on complex sketches
- No errors logged but constraints visibly survive

**Phase to address:**
Phase 1 (bulk deletion in Constraint Types tab) and Phase 2 (individual deletion in All Constraints tab). Must be addressed in both phases since both perform deletions.

---

### Pitfall 4: Sketch-Wide Enumeration Hanging the UI on Large Sketches

**What goes wrong:**
Iterating every entity in a sketch to enumerate all constraints blocks Fusion's main thread. On a DXF import with 500+ entities and 2000+ constraints, this can freeze the UI for 5-15 seconds. Users think Fusion has crashed and force-quit, or they spam-click and queue up events. The PROJECT.md correctly identifies this risk and mandates an explicit Load button — but the implementation details matter.

**Why it happens:**
Fusion's Python API runs on the main thread. There is no background threading for API calls. Each `entity.geometricConstraints` access and each `_build_constraint_info()` call is synchronous. On large sketches, the cumulative time is significant. Additionally, `adsk.doEvents()` — which allows Fusion to process UI updates — is available but calling it mid-enumeration can trigger other event handlers if the user interacts with the dialog, causing re-entrance.

**How to avoid:**
- **Explicit Load button** (already planned) — don't enumerate on tab switch, only on user action
- **Progress indication** — call `adsk.doEvents()` periodically (every 50-100 constraints) with a progress message in a text input, but guard against re-entrance when doing so
- **Batch loading** — enumerate in chunks (e.g., 100 entities at a time), updating a progress counter between chunks
- **Abort mechanism** — if the user clicks Cancel during enumeration, stop early. Check `command.isValid` or a cancellation flag between chunks
- **Cache results** — once enumerated, store constraint data so tab switching back to All Constraints doesn't re-enumerate

**Warning signs:**
- Dialog appears to hang when user clicks Load
- No visual feedback during enumeration
- User reports from DXF import workflows (the primary audience for v2)

**Phase to address:**
Phase 2 (All Constraints tab) — this is where sketch-wide enumeration happens. Phase 1 (Constraint Types tab) only needs counts, which is cheaper but still needs the Load button pattern for very large sketches.

---

### Pitfall 5: Garbage Collection Eating Event Handlers

**What goes wrong:**
Python's garbage collector destroys event handler objects if no strong reference is held. The handler silently disappears — no error, no warning — and the button/event simply stops working. This is the #1 "why doesn't my add-in work" issue in Fusion API development and is explicitly documented by Autodesk as a Python-specific gotcha.

**Why it happens:**
Fusion's event system holds a weak reference to Python handler objects. When the handler's Python reference count drops to zero (e.g., local variable goes out of scope), GC destroys it. The v1.1 codebase correctly mitigates this with `_cmd_handlers` and `_addin_handlers` module-level lists, but v2 introduces more handlers (per-tab handlers, dropdown change handlers, Load button handler) that each need the same protection.

**How to avoid:**
- **Append every new handler to `_cmd_handlers`** — the existing pattern works, just don't forget to use it for every new handler added in v2
- **Audit handler creation** — every `.add(handler)` call must have a corresponding `_cmd_handlers.append(handler)` immediately after
- **Code review checklist item** — "Does every event handler have a module-level reference?"
- **Consider a helper function** — `def wire_handler(event, handler_class)` that creates the handler, adds it to the event, and appends to `_cmd_handlers` in one call. Eliminates the possibility of forgetting the append.

**Warning signs:**
- Feature works on first run but stops working after a few seconds or after GC runs
- Feature works in debugger (which holds extra references) but not in production
- Random "handler not found" or silent failure in event processing

**Phase to address:**
Phase 1 (foundation) — establish the helper pattern before adding new handlers. Apply to all subsequent phases.

---

### Pitfall 6: Model Mutations in InputChanged Clearing Selections

**What goes wrong:**
The Fusion API explicitly forbids making model changes (creating, editing, or deleting entities) within the `inputChanged` event handler. Doing so clears all current selections. If the All Constraints tab or Constraint Types tab accidentally touches model state during a tab switch or filter change, the Selected Entities tab's selections are wiped without warning.

**Why it happens:**
Fusion's command system treats `inputChanged` as a UI-only event. Model mutations are reserved for `execute` and `executePreview`. This is documented but easy to violate accidentally — for example, accessing a constraint property that triggers a lazy computation, or calling a method that has side effects on the sketch.

**How to avoid:**
- **Read-only access in inputChanged** — only read properties, never call methods that modify state
- **All deletions in execute handler only** — the v1.1 pattern is correct; maintain it for all v2 tabs
- **No `deleteMe()` calls outside execute** — even "cleanup" or "reset" operations
- **Test by checking selection persistence** — after every inputChanged path, verify entity selections survived

**Warning signs:**
- Selections vanish when switching tabs or changing dropdown filter
- Entity selection input shows "0 selected" after tab interaction
- Works fine with no selections but breaks when entities are selected

**Phase to address:**
All phases — this is a constraint on every inputChanged code path.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Module-level globals for cross-handler state | Works with Fusion's event model; proven in v1.1 | Hard to test, no isolation between command invocations, risk of stale state | Acceptable — this is the only reliable pattern in Fusion's event system. Mitigate with a `CommandState` wrapper class. |
| Bare `except:` in event handlers | Prevents Fusion crashes from unhandled exceptions | Hides bugs, makes debugging painful, silently swallows real errors | MVP only. Replace with `except Exception as e:` and full traceback logging before v2 ships. |
| Hardcoded constraint type mapping | Simple, fast lookup, no external dependencies | Breaks silently when Autodesk adds new constraint types | Acceptable if documented. Add a version comment noting which Fusion API version was used for the mapping. |
| No pagination on large tables | Simpler implementation, works for typical sketches | UI becomes unresponsive at 200+ constraint rows | Acceptable for v2.0 if the Load button gates the expensive path. Add pagination in v2.1 if users hit performance issues. |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `TabCommandInput` | Adding inputs directly to the command instead of to the tab's `children` input group | Use `tab.children.addTableCommandInput(...)` — inputs must be children of the tab, not the root `commandInputs` |
| `TableCommandInput` | Assuming row indices are stable after deletion | Always re-index or use a mapping from row index to data index; table row indices shift when rows are removed |
| `DropDownCommandInput` | Reading `selectedItem` during creation before any item is selected | Check that `selectedItem` is not None; the dropdown starts with no selection until `listItems.add()` is called with `isSelected=True` |
| `Design.findEntityByToken()` | Comparing tokens directly as strings to check entity equality | Never compare tokens — different token strings can refer to the same entity. Always resolve and compare the returned objects using `==` |
| `SelectionCommandInput` | Calling `addSelection()` programmatically expecting it to trigger `inputChanged` | Programmatic selection changes may or may not fire events depending on Fusion version. Always handle the state update explicitly. |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Creating 4 `CommandInput` objects per constraint row | Dialog takes 3+ seconds to open with 100+ constraints | Limit visible rows, implement Load button, consider pagination | 100+ constraints per table (~400 input objects) |
| `_find_entity_index()` linear scan per entity | Visible lag when selecting entities on sketches with 500+ curves | Cache index during first lookup; store in a dict keyed by entity token | 10+ entities selected on a sketch with 1000+ curves |
| Re-enumerating all constraints on every selection change | Table flickers and lags with rapid multi-selection | Debounce or batch selection changes; only rebuild when selection stabilizes | 5+ entities being rapidly selected on complex sketches |
| `adsk.doEvents()` during enumeration | Allows UI updates but enables re-entrance if user clicks during processing | Guard `doEvents()` calls with a processing flag; disable interactive inputs during enumeration | Any sketch where enumeration takes >1 second |
| Sketch-wide iteration touching every entity | Main thread blocked, Fusion appears frozen | Explicit Load button (planned), progress indication, chunked processing | Sketches with 500+ entities (common in DXF imports) |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Bulk "Delete All [Type]" with no confirmation | Accidental deletion of 200 constraints with a single click, undo is all-or-nothing | Add confirmation dialog showing count: "Delete all 47 Fix constraints? This can be undone with Ctrl+Z." |
| No feedback after deletion | User clicks Delete, dialog closes, no idea if it worked | Show summary message: "Deleted 47 constraints (2 could not be removed)" before closing |
| Tab switch loses scroll position | User scrolls to constraint #150, switches tabs, comes back — scroll is at top | Cache scroll position per tab, or accept the limitation and document it (Fusion tables may not support scroll state preservation) |
| Constraint Types tab shows counts but not which entities | User sees "Fix: 47" but can't figure out which entities have Fix constraints | Add a "Show in All Constraints" action that switches to the All Constraints tab pre-filtered to that type |
| Filter dropdown resets on tab switch | User applies "Show only Fix" filter, switches to another tab, comes back — filter is cleared | Persist filter selection in module state; restore when tab is re-activated |
| No visual distinction between tabs with/without data | User opens command, Selected Entities tab is empty because nothing is selected; doesn't realize other tabs have sketch-wide data | Add hint text on empty Selected Entities tab: "Select sketch entities to view their constraints, or use the Constraint Types / All Constraints tabs for sketch-wide operations" |

## "Looks Done But Isn't" Checklist

- [ ] **Tab switching:** Often missing — verify that switching between all three tabs in rapid succession doesn't corrupt shared state (`_current_constraints` is used by all tabs but may contain data from the wrong tab)
- [ ] **Bulk deletion results:** Often missing — verify that the deleted count matches the expected count, and that no constraints were silently skipped due to token invalidation
- [ ] **Reverse iteration for deleteMe:** Often missing — verify that deletion loops iterate backwards or use a snapshot list; a forward loop will silently skip ~50% of targets
- [ ] **Handler GC protection:** Often missing — verify every `.add(handler)` has a matching `_cmd_handlers.append(handler)` for all new v2 handlers
- [ ] **Empty state handling:** Often missing — verify each tab handles the "no data" case gracefully (empty sketch, no constraints of a type, no entities selected)
- [ ] **Undo behavior:** Often missing — verify that all deletions from a single "Delete All [Type]" operation undo as a single Ctrl+Z action (they should, since they're in one execute handler)
- [ ] **Cross-platform testing:** Often missing — verify dialog layout works on macOS (different font sizes, DPI scaling affect table column widths)
- [ ] **Python version compatibility:** Often missing — verify no Python 3.10+ syntax (match/case, union types with `|`) since Fusion's runtime may be pinned to 3.9.x

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Forward-iteration deletion skipping items | LOW | Fix loop direction to reverse; no data loss since constraints survive |
| InputChanged re-entrance corruption | MEDIUM | Add module-level guard flags; may need to restructure handler to separate tab-switch handling from input-change handling |
| Token invalidation during bulk delete | LOW | Add re-resolve-before-delete pattern and isValid check; failed deletions can be retried |
| UI freeze on large sketch enumeration | MEDIUM | Add Load button + progress indication; requires restructuring enumeration into chunks |
| GC eating handlers | LOW | Add `_cmd_handlers.append()` for missing handlers; create helper function to prevent recurrence |
| Model mutation in inputChanged | HIGH | Requires moving all mutation logic to execute handler; may need architectural rethink if mutations were woven into inputChanged paths |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Forward-iteration deletion | Phase 1 (Constraint Types bulk delete) | Unit test: delete 10 of same type, verify all 10 removed |
| InputChanged re-entrance on tab switch | Phase 1 (Tab UI scaffolding) | Manual test: rapidly switch tabs 20 times, verify no errors in log |
| Token invalidation during bulk delete | Phase 1 + Phase 2 | Integration test: delete 50 constraints, verify count matches |
| UI freeze on large sketches | Phase 2 (All Constraints tab) | Manual test with 500+ entity DXF import sketch |
| GC eating handlers | Phase 1 (foundation) | Create `wire_handler()` utility; code review checklist |
| Model mutations in inputChanged | All phases | Code review: grep for `deleteMe` outside execute handler |
| No deletion confirmation for bulk ops | Phase 1 (Constraint Types tab) | UX review: test "Delete All" with large counts |
| Shared `_current_constraints` state across tabs | Phase 1 (Tab UI scaffolding) | Refactor to per-tab state (e.g., `_tab_state = {"selected": [], "types": {}, "all": []}`) |

## Sources

- [Fusion Help: Python Specific Issues](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/PythonSpecific_UM.htm) — official Autodesk documentation on GC, object comparison, threading
- [Fusion Help: Command Inputs](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CommandInputs_UM.htm) — TabCommandInput and TableCommandInput documentation
- [Fusion Help: inputChanged Event](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Command_inputChanged.htm) — model mutation restriction
- [Fusion Help: Events](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Events_UM.htm) — handler lifecycle and GC behavior
- [Autodesk Forum: deleteMe not deleting all items in loop](https://forums.autodesk.com/t5/fusion-api-and-scripts-forum/deleteme-method-not-deleting-all-sketch-curves-in-for-loop/td-p/10941332) — community-confirmed forward-iteration bug
- [Autodesk Forum: Event handlers not being released](https://forums.autodesk.com/t5/fusion-api-and-scripts-forum/event-handlers-not-being-released/td-p/9796828) — GC handler issue
- [Autodesk Forum: InputChanged handler usage](https://forums.autodesk.com/t5/fusion-api-and-scripts/how-to-use-the-input-changed-event-handler-correctly/td-p/9706955) — re-entrance and best practices
- Codebase analysis: `.planning/codebase/CONCERNS.md`, `.planning/codebase/CONVENTIONS.md` — existing tech debt and patterns
- Codebase: `ConstraintManager/commands/constraint_manager/command.py` — current v1.1 implementation

---
*Pitfalls research for: Fusion 360 Constraint Manager v2 add-in*
*Researched: 2026-03-22*
