# Project Research Summary

**Project:** Constraint Manager v2.0 — Fusion 360 Add-in
**Domain:** CAD sketch constraint management, Autodesk Fusion desktop add-in
**Researched:** 2026-03-22
**Confidence:** HIGH

## Executive Summary

Constraint Manager v2 is a Fusion 360 Python add-in extending a working v1.1 foundation with sketch-wide constraint management. The problem space is well-understood: SolidWorks and Onshape solved this years ago with tabbed/filtered constraint panels, and Fusion's built-in tooling offers essentially nothing. v1.1 fills the per-entity gap; v2 fills the sketch-wide gap — specifically the "Delete All Fix constraints from this DXF import" use case that drives real pain in the user community. The recommended approach builds directly on the existing two-layer architecture (command.py for UI, constraint_engine.py for logic) with a three-tab dialog using `TabCommandInput`, which is the only Fusion API mechanism for this layout.

The implementation path is unusually clear: all required UI components are confirmed in official Autodesk docs with HIGH confidence, the sketch-wide API surface (`Sketch.geometricConstraints`) is confirmed, and the v1.1 codebase already demonstrates the correct deletion and event-handling patterns. The primary risk is not architectural uncertainty — it's implementation-level pitfalls that are well-documented and avoidable. The forward-iteration deletion bug, GC eating event handlers, and model mutations inside `inputChanged` are the three gotchas that have burned Fusion API developers repeatedly. All three have clear prevention strategies and the v1.1 codebase already avoids two of them.

The scope defined in PROJECT.md is well-calibrated. The Constraint Types tab (type counts + Delete All per type) is the killer feature and should be built first. The All Constraints tab (full sketch listing with filter) completes the picture but is significantly more complex. Nothing in the research suggests the planned scope needs expansion or contraction — it is the right thing to build.

## Key Findings

### Recommended Stack

The stack has zero degrees of freedom: Fusion's embedded Python interpreter, `adsk.core`, and `adsk.fusion` are the only options. No external dependencies are possible in production. The research value here is in the specific API classes confirmed for each UI component: `TabCommandInput` for the three-tab dialog, `TableCommandInput` for constraint rows (already used in v1), `DropDownCommandInput` (TextListDropDownStyle) for the type filter, and `BoolValueCommandInput` in button mode for action triggers. One important API constraint: `SelectionCommandInput` and `ButtonRowCommandInput` cannot be placed inside a `TableCommandInput`. See STACK.md for full API reference.

**Core technologies:**
- `adsk.core` (TabCommandInput, TableCommandInput, DropDownCommandInput, BoolValueCommandInput): all UI components — confirmed HIGH confidence from official docs
- `adsk.fusion` (Sketch.geometricConstraints, GeometricConstraints): sketch-wide constraint enumeration — confirmed HIGH confidence
- `logging` / `traceback` (stdlib): debug logging and error capture — already established in v1.1
- `pytest` (dev only): unit testing constraint engine logic outside Fusion

### Expected Features

Fusion has almost no built-in constraint management (show/hide toggle and a hidden Ctrl+A delete-all trick). SolidWorks and Onshape both offer full constraint panels. Our add-in fills a years-old gap. The v2 feature set maps directly to what competitor tools provide, plus one unique differentiator: the Constraint Types summary view (counts by type at a glance) which no competitor offers.

**Must have (table stakes):**
- Sketch-wide constraint listing — SolidWorks and Onshape both offer this; Fusion does not
- Filter by constraint type — universal expectation from any user who has used a real constraint manager
- Delete by constraint type (bulk) — THE killer feature for DXF/SVG import cleanup workflows; Onshape has it but Fusion doesn't
- Constraint type summary with counts — quick audit before doing anything else
- Explicit Load button for large sketches — required for safety on DXF imports with 500+ entities

**Should have (competitive differentiator):**
- Constraint type count dashboard (Constraint Types tab) — unique; no competitor offers "Fix: 47, Coincident: 23" at a glance; this is the standout feature
- "Show in All Constraints" cross-tab action from Constraint Types tab — improves workflow without significant complexity

**Defer (v2.1+):**
- Viewport highlighting on constraint hover — High complexity, Fusion API feasibility unconfirmed
- Dimension constraint support — Different API surface (SketchDimensions), validate geometric constraints first
- Sort modes (by entity vs by constraint) — trivial to add later, not essential
- Constraint status indicators (under/over-constrained coloring) — API feasibility unconfirmed

**Explicit non-features (do not attempt):**
- Auto-constraint interception — no API event hook for constraint creation, polling would be fragile
- Constraint replacement (swap types) — high complexity, edge cases, risk of breaking sketch solve
- Suppress/unsuppress — SolidWorks-specific capability; Fusion API does not support it
- Real-time monitoring panel — requires HTML palette, completely different architecture

### Architecture Approach

Preserve the existing two-layer separation and extend it. `command.py` gains tab management responsibilities; `constraint_engine.py` gains three new functions for sketch-wide enumeration. Module-level state gets per-tab variables (`_type_summary`, `_all_constraints`, `_all_constraints_loaded`, `_active_tab`) rather than a shared list. The key architectural rule: keep all three tabs in one `command.py` file — splitting into per-tab modules would create circular dependencies because Fusion's event system delivers a single `CommandInputs` collection spanning all tabs, and the Execute handler needs cross-tab awareness.

**Major components:**
1. `ConstraintManager.py` — entry point, toolbar registration, lifecycle (unchanged)
2. `command.py` — tab controller, per-tab UI builders, all event handlers (extended)
3. `constraint_engine.py` — all constraint logic, zero UI imports (extended with 3 new functions)

**New engine functions needed:**
- `aggregate_constraint_types(sketch)` — count-only pass, fast (~5ms even on 2000 constraints)
- `enumerate_all_constraints(sketch, index_finder)` — full metadata pass, expensive, Load-button-gated
- `collect_constraints_by_type(sketch, type_name)` — collect targets for bulk deletion
- `_build_entity_index_cache(sketch)` — O(N+M) optimization replacing O(N*M) entity lookups

**Recommended build order:** Engine extensions first (testable without Fusion UI) → Tab scaffolding (validates framework, preserves v1 behavior) → Constraint Types tab (killer feature, simpler than All Constraints) → All Constraints tab (most complex, depends on all prior work).

### Critical Pitfalls

1. **Forward-iteration deletion skips ~50% of targets** — Fusion collections re-index live on deletion. Always iterate in reverse or snapshot tokens to a list before deleting. The v1.1 execute handler already does this correctly; extend the same pattern to bulk-delete operations. This is the #1 forum bug report for Fusion bulk operations.

2. **Garbage collection silently destroys event handlers** — Python GC eats handlers with no error. Every `.add(handler)` call must have a matching `_cmd_handlers.append(handler)`. Create a `wire_handler()` helper that does both in one call to eliminate the risk of forgetting. The v1.1 codebase has this pattern; apply it consistently to all new handlers.

3. **Model mutations inside `inputChanged` clear all selections** — Fusion treats `inputChanged` as UI-only. Calling `deleteMe()` or any model-mutating method here will silently wipe entity selections. All deletions must happen in the Execute handler. "Delete All [Type]" buttons must set a flag in `inputChanged` and execute the deletion in `execute`, not inline.

4. **InputChanged re-entrance during tab switches** — Tab switches fire `inputChanged`. If the handler modifies other inputs in response (updating tables, changing text), it queues secondary events. The existing `_handling_change` guard may not catch them all. Use a module-level `_switching_tabs` guard and keep tab-switch handlers minimal.

5. **UI freeze on large sketch enumeration** — `enumerate_all_constraints()` on a 500-entity sketch can take 1-2 seconds on Fusion's main thread (no background threading). The Load button pattern gates this correctly. Add progress indication via `adsk.doEvents()` every 50-100 constraints, guarded against re-entrance.

## Implications for Roadmap

Research strongly supports a 4-phase build ordered by dependency and risk. Architecture research provides an explicit build order that matches this phasing.

### Phase 1: Foundation and Constraint Types Tab

**Rationale:** The Constraint Types tab is the killer feature with the lowest UI complexity of the two new tabs. It requires only type counting (fast, no entity label resolution) and bulk deletion. Building this first validates sketch-wide enumeration, the tab framework, and the bulk deletion pattern before taking on the heavier All Constraints tab. All 6 critical pitfalls have their "address in Phase 1" designation from PITFALLS.md.

**Delivers:** Working three-tab dialog with Constraint Types tab functional. Users can see "Fix: 87, Coincident: 45" and delete an entire type in one action. This alone solves the DXF import cleanup use case.

**Addresses:**
- Sketch-wide constraint listing (Constraint Types view)
- Delete by constraint type (bulk)
- Constraint type summary with counts
- Explicit Load gating for type aggregation (lightweight but principle established)

**Avoids:**
- Forward-iteration deletion bug (establish reverse-iteration pattern here first)
- GC handler bug (establish `wire_handler()` helper here)
- Model mutations in inputChanged (enforce deletion-in-execute rule)
- InputChanged re-entrance (tab switch guard established here)
- Missing confirmation for "Delete All [Type]" (add count-showing confirmation dialog)

### Phase 2: All Constraints Tab

**Rationale:** Most complex tab. Depends on all engine functions from Phase 1. The Load button pattern, type filter, checkbox deletion, and entity index cache all live here. Validate against Phase 1 data (type counts should match between tabs).

**Delivers:** Full sketch-wide constraint listing with Load button, type filter dropdown, checkbox selection, and individual/batch deletion from the complete list.

**Addresses:**
- Full sketch-wide constraint listing (All Constraints tab)
- Filter by constraint type (dropdown filter)
- Individual deletion from sketch-wide view
- Performance safety on large sketches (Load button, progress indication, entity index cache)

**Avoids:**
- UI freeze (Load button gates enumeration; `adsk.doEvents()` with re-entrance guard for progress)
- Token invalidation during bulk delete (re-resolve-before-delete + isValid check)
- Shared constraint list across tabs (per-tab state architecture)

### Phase 3: Polish and Edge Cases

**Rationale:** After both new tabs are functional, address the UX rough edges that research flagged but that don't block core functionality. These are the "looks done but isn't" checklist items from PITFALLS.md.

**Delivers:** Production-quality release. Confirmed correct behavior across edge cases: empty sketches, zero constraints of a type, macOS layout, Python 3.9.x compatibility, undo behavior verification, deletion result summaries.

**Addresses:**
- Empty state handling per tab (no constraints, no selection, no data loaded)
- Deletion feedback messages ("Deleted 47 of 52 constraints; 5 could not be resolved")
- Filter state persistence across tab switches
- Cross-platform dialog layout verification (macOS font/DPI)
- Undo behavior confirmation (single Ctrl+Z per Delete All operation)

### Phase 4: v1 Integration Verification

**Rationale:** The Selected Entities tab is v1.1 functionality that must continue working after the three-tab refactor. This deserves its own verification pass since the inputs now live inside a tab's `children` instead of root `commandInputs`.

**Delivers:** Confirmed regression-free v1.1 behavior in the new three-tab context. Release candidate.

**Addresses:**
- Selected Entities tab input wiring inside TabCommandInput.children (not root commandInputs)
- Pre-selection behavior preserved
- Execute handler routing for the selected-entities path

### Phase Ordering Rationale

- Engine extensions are tested in isolation (no Fusion required) before UI work begins — this de-risks the expensive enumeration path
- Tab scaffolding + v1 migration happens before any new features — if tabs break existing behavior, it's caught before new complexity is added
- Constraint Types tab ships before All Constraints because it delivers the primary user value (bulk delete by type) at lower complexity
- Polish phase is last by definition — all behavioral correctness comes first

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (All Constraints tab):** The entity index cache optimization changes the enumeration approach meaningfully. Validate performance characteristics empirically with real DXF imports during Phase 1 before committing to caching strategy details in Phase 2.
- **Phase 3 (macOS compatibility):** TableCommandInput column ratio behavior and font scaling on macOS is documented as potentially different. Needs manual testing if macOS users are in the target audience.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation + Constraint Types):** All API patterns confirmed HIGH confidence. The tab creation, type enumeration, and bulk deletion patterns are fully specified in STACK.md and ARCHITECTURE.md. Build from specs.
- **Phase 4 (v1 Integration):** This is regression testing, not new development. No research needed.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All required API classes confirmed via official Autodesk docs. TabCommandInput, TableCommandInput, DropDownCommandInput behavior fully documented. No external dependencies to vet. |
| Features | HIGH | SolidWorks and Onshape serve as high-confidence reference implementations. Community research (v2-research.md) provides direct user pain point evidence. Feature scope is well-bounded. |
| Architecture | HIGH | Two-layer pattern proven in v1.1. New pattern (tab-aware routing, per-tab state) follows directly from API constraints. Build order is logical and risk-ordered. One MEDIUM item: tab switch event behavior (confirmed via docs but not yet empirically verified in this codebase). |
| Pitfalls | HIGH | Forward-iteration deletion and GC handler issues are Autodesk-forum-documented with community confirmation. Model mutation restriction is in official docs. Performance estimates for large sketches are MEDIUM (no official benchmarks; based on API behavioral patterns and community reports). |

**Overall confidence:** HIGH

### Gaps to Address

- **Performance thresholds for large tables:** Fusion's `TableCommandInput` has no documented row limit. The 200-500 row range where performance degrades is based on community reports. Test empirically with real DXF imports during Phase 2 development; add pagination in v2.1 if needed.
- **`adsk.doEvents()` re-entrance behavior:** The progress indication pattern (call `doEvents()` every N constraints) is theoretically sound but needs empirical validation. If it triggers unwanted events, fall back to no-progress-indication with a "Loading..." static message.
- **Viewport highlighting feasibility:** FEATURES.md flags this as a differentiator but notes Fusion API support needs validation. Specifically: whether `isHighlighted` on sketch entities can be set during a command dialog interaction without clearing selections. Investigate as a separate spike before committing to it in any phase.
- **macOS TableCommandInput column widths:** Column ratio string (`'1:3:3:3'`) behavior may differ on macOS due to font metrics. Flag for testing if macOS users are in scope.

## Sources

### Primary (HIGH confidence)
- [Fusion Help: Command Inputs User Manual](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CommandInputs_UM.htm) — TabCommandInput, TableCommandInput, DropDownCommandInput overview and limitations
- [Fusion Help: TabCommandInput Object](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/TabCommandInput.htm) — isActive, activate(), children properties
- [Fusion Help: TableCommandInput Object](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/TableCommandInput.htm) — addToolbarCommandInput, deleteRow, selectedRow, rowCount
- [Fusion Help: GeometricConstraints Object](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/GeometricConstraints.htm) — sketch-wide collection API
- [Fusion Help: Sketch.geometricConstraints Property](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Sketch_geometricConstraints.htm) — sketch-level constraint access
- [Fusion Help: Python Specific Issues](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/PythonSpecific_UM.htm) — GC, object comparison, threading constraints
- [SolidWorks Display/Delete Relations (2019)](https://help.solidworks.com/2019/english/SolidWorks/sldworks/hidd_dve_sk_edit_relations.htm) — competitor reference implementation
- [Onshape Constraint Manager tech tip](https://www.onshape.com/en/resource-center/tech-tips/sketch-constraint-manager) — competitor reference implementation
- [Onshape Working with Constraints](https://cad.onshape.com/help/Content/constraints.htm) — competitor feature set

### Secondary (MEDIUM confidence)
- [Autodesk Forum: deleteMe not deleting all items in loop](https://forums.autodesk.com/t5/fusion-api-and-scripts-forum/deleteme-method-not-deleting-all-sketch-curves-in-for-loop/td-p/10941332) — forward-iteration deletion bug confirmation
- [Autodesk Forum: Event handlers not being released](https://forums.autodesk.com/t5/fusion-api-and-scripts-forum/event-handlers-not-being-released/td-p/9796828) — GC handler issue confirmation
- [Autodesk Forum: InputChanged handler usage](https://forums.autodesk.com/t5/fusion-api-and-scripts/how-to-use-the-input-changed-event-handler-correctly/td-p/9706955) — re-entrance patterns
- Community research: `.planning/docs/v2-research.md` — user pain points and feature requests

### Tertiary (LOW confidence)
- Performance estimates for large sketch enumeration (~5ms type aggregation, ~500-2000ms full enumeration) — based on API behavioral patterns and v1 experience; no official benchmarks exist
- TableCommandInput row performance degradation at 200-500 rows — community reports, not empirically verified in this codebase

---
*Research completed: 2026-03-22*
*Ready for roadmap: yes*
