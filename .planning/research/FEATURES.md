# Feature Landscape

**Domain:** CAD sketch constraint management add-in (Autodesk Fusion)
**Researched:** 2026-03-22

## Reference: How Competitors Handle This

Before categorizing features, here is what the established CAD constraint managers provide, since they define user expectations for anyone who has used other tools:

**SolidWorks Display/Delete Relations:**
- Relation list with type, status, and involved entities per row
- Two scope modes: "All in this sketch" and "Selected entities"
- Filter by relation type and status (Satisfied, Not Satisfied, Broken, Over-defined, Dangling)
- Suppress/Unsuppress relations (disable without deleting, re-enable later)
- Selecting a relation highlights associated geometry in viewport
- Delete individual relations from the list
- No bulk "delete by type" -- one at a time only

**Onshape Constraint Manager:**
- Full constraint + dimension list with filter by Type, Mode (Internal/External/In-Context), and Status (Solved/Driven/Error)
- Sort by constraint or sort by entity
- Color-coded status: blue = under-constrained, black = fully constrained, red = conflicting
- Hover highlights associated geometry (yellow bounding box)
- "Delete All" button to remove all listed/filtered constraints
- Zoom to selection
- Auto-select constraints toggle

**NX (Siemens):**
- Type filter in toolbar to restrict selection to constraints only
- Individual constraint deletion via selection + Delete key
- Moving toward "relations" model where many constraints are inferred on-the-fly rather than persistent

**Fusion 360 (built-in):**
- Show/Hide Constraints toggle (all or nothing)
- No constraint list, no panel, no browser, no filtering
- Delete All Constraints via Ctrl+A, right-click (undiscoverable "secret trick")
- Individual constraint deletion by clicking constraint icon in viewport
- Web version has a constraint list panel; desktop does not

**Key takeaway:** SolidWorks and Onshape have mature constraint management UIs. Fusion has essentially nothing. Our add-in fills a gap that other CAD tools solved years ago.

---

## Table Stakes

Features users expect from a constraint management tool. Missing any of these and the tool feels half-baked, especially for users coming from SolidWorks or Onshape.

| Feature | Why Expected | Complexity | Status | Notes |
|---------|--------------|------------|--------|-------|
| Constraint list per selected entity | Every CAD constraint manager shows what is attached to your selection | Low | DONE (v1) | Core of Selected Entities tab |
| Constraint type shown per row | SolidWorks and Onshape both show type prominently | Low | DONE (v1) | Already in table |
| Related entities shown per row | Both competitors show which geometry participates | Low | DONE (v1) | Already in table |
| Individual constraint deletion | Every competitor supports this | Low | DONE (v1) | Checkbox + delete on execute |
| Non-deletable constraint protection | Prevents accidental deletion of structural constraints | Low | DONE (v1) | Lock emoji + disabled checkbox |
| Multi-entity selection | SolidWorks supports "selected entities" scope | Low | DONE (v1) | Unified table across selection |
| Sketch-wide constraint listing | Onshape and SolidWorks both offer "all in sketch" scope | Medium | PLANNED (v2) | All Constraints tab |
| Filter by constraint type | Onshape has Type filter; SolidWorks has type column. Universal expectation | Medium | PLANNED (v2) | Dropdown filter on All Constraints tab |
| Delete by constraint type (bulk) | Onshape has "Delete All" on filtered view. This is THE killer feature for DXF import users | Medium | PLANNED (v2) | Constraint Types tab "Delete All" per type |
| Constraint type summary with counts | Quick audit of what is in a sketch without loading every constraint | Low | PLANNED (v2) | Constraint Types tab |
| Explicit load control for expensive operations | Large sketches (500+ entities) need opt-in enumeration to avoid UI hangs | Low | PLANNED (v2) | Load button on All Constraints tab |

## Differentiators

Features that would set this tool apart from what SolidWorks and Onshape provide. Not expected, but would create real competitive advantage and user loyalty.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Constraint type count dashboard | Neither SolidWorks nor Onshape show a type-count summary view. Our Constraint Types tab is unique -- no one else provides "you have 47 Fix, 12 Coincident, 8 Horizontal at a glance" | Low | Already planned for v2. This IS the differentiator for DXF import cleanup workflows |
| Viewport highlighting on selection | Onshape highlights geometry when hovering constraints. Fusion API supports `isHighlighted` on sketch entities. Showing which geometry a constraint applies to is a powerful debugging aid | High | Deferred per PROJECT.md. Fusion API support needs validation -- may require custom graphics or temporary selection |
| Constraint status indicators | Onshape color-codes by status (under-constrained, over-constrained, conflicting). Showing which constraints are the "problem" during over-constraint debugging would be extremely valuable | High | Not currently planned. Fusion API may not expose constraint solve status -- needs feasibility check |
| Dimension constraint support | Extending beyond geometric constraints to include dimensions in the list. Completes the picture for users doing full sketch audits | Medium | Deferred to v2.x per PROJECT.md. Dimensions have different API surface (`SketchDimensions` collection) |
| Sort by entity vs sort by constraint | Onshape provides both sort modes. Useful when you want to see "all constraints on Line1" vs "all coincident constraints" | Low | Not currently planned but would be trivial to add to All Constraints tab |
| Suppress/Unsuppress (disable without deleting) | SolidWorks supports this. Extremely useful for debugging -- temporarily disable a constraint to see its effect, then re-enable | Very High | Fusion API does not appear to support constraint suppression. This is a SolidWorks-specific capability. Do NOT attempt |

## Anti-Features

Things to deliberately NOT build. Either technically impossible, out of scope, or would make the tool worse.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Auto-constraint interception | Fusion API cannot intercept constraints as they are created. There is no event hook for "constraint about to be added." Building fake detection (polling, diff-based) would be fragile and unreliable | Provide bulk delete-by-type as the cleanup tool after auto-constraints are applied |
| Constraint replacement (swap types) | Replacing one constraint type with another (e.g., perpendicular to horizontal) requires deleting the old and creating a new one with correct entity references. High complexity, edge cases around entity pairing, and risk of breaking sketch solve | Provide delete-by-type so users can quickly remove unwanted constraints and manually re-apply the correct ones |
| Under-constrained DOF analysis | Computing degrees of freedom per entity requires reimplementing the sketch solver or deep API access that does not exist. The hidden `Sketch.ShowUnderconstrained` command exists but is not exposed via API | Defer. Consider wrapping the hidden command if API access is found in future versions |
| Persistent preferences / settings | No persistent config for "always start on tab X" or "default filter." Fusion add-in API does not provide a clean settings storage mechanism, and file-based config adds installation complexity | Use sensible defaults. Selected Entities tab is the default (preserves v1 behavior). Filters reset on each command invocation |
| Real-time constraint monitoring | A persistent panel that updates as users sketch would require a dockable palette (Fusion palettes use HTML/JS, completely different architecture) and continuous polling. Massive scope increase for marginal benefit | Keep command-based UI. User invokes the tool when they need it, gets the current state, acts on it |
| Undo/redo within the command | Fusion's undo system operates at the command boundary (entire execute handler is one undo step). Sub-operation undo within a single command execution is not supported by the API | Rely on Fusion's built-in Ctrl+Z after command execution. Each command invocation is one undoable operation |
| Cross-sketch constraint management | Managing constraints across multiple sketches simultaneously adds massive complexity and scope. Onshape handles this with "External/In-Context" modes but it is a fundamentally different workflow | Keep scope to single active sketch. One sketch at a time is the right mental model |

## Feature Dependencies

```
Selected Entities tab (v1, DONE)
  --> no dependencies, standalone

Constraint Types tab (v2)
  --> requires sketch-wide constraint enumeration (new engine method)
  --> "Delete All per type" requires type-based filtering in engine

All Constraints tab (v2)
  --> requires sketch-wide constraint enumeration (shared with Constraint Types)
  --> Load button --> triggers enumeration on demand
  --> Type filter dropdown --> requires distinct type list from enumeration
  --> Checkbox deletion --> reuses v1 deletion infrastructure (entity tokens)

Constraint Types tab  --shared engine-->  All Constraints tab
  (both need sketch-wide enumeration, should share the same engine method)

Future: Viewport highlighting
  --> requires All Constraints or Selected Entities tab (needs constraint selection)
  --> requires Fusion API validation for isHighlighted or custom graphics

Future: Dimension support
  --> requires new enumeration path (SketchDimensions collection)
  --> extends all three tabs
```

## MVP Recommendation

The v2 scope as defined in PROJECT.md is well-calibrated. Prioritize in this order:

1. **Constraint Types tab** -- lowest complexity, highest immediate impact. The "Delete All Fix" use case for DXF import cleanup is the single most valuable new feature. Ship this first if incremental releases are possible.

2. **All Constraints tab with Load button** -- medium complexity, completes the "full sketch audit" workflow. The explicit Load button is the right call for performance safety.

3. **All Constraints type filter** -- low incremental complexity once the tab exists. Reuses the type enumeration from Constraint Types tab.

4. **Selected Entities tab preservation** -- already done (v1). Just verify it still works in the three-tab layout.

**Defer to v2.1+:**
- Dimension constraint support: Different API surface, increases scope. Validate tab UI with geometric constraints first.
- Viewport highlighting: High complexity, needs API feasibility check. Nice-to-have, not essential.
- Sort modes (by entity vs by constraint): Trivial to add later, not essential for launch.
- Status indicators (under/over-constrained coloring): Needs Fusion API feasibility investigation.

## Sources

- [SolidWorks Display/Delete Relations (2019 docs)](https://help.solidworks.com/2019/english/SolidWorks/sldworks/hidd_dve_sk_edit_relations.htm) -- HIGH confidence
- [Onshape Constraint Manager tech tip](https://www.onshape.com/en/resource-center/tech-tips/sketch-constraint-manager) -- HIGH confidence
- [Onshape Working with Constraints (official help)](https://cad.onshape.com/help/Content/constraints.htm) -- HIGH confidence
- [Onshape forum: Delete all sketch constraints at once](https://forum.onshape.com/discussion/7309/delete-all-sketch-constraints-at-once) -- MEDIUM confidence
- [SolidWorks Suppressing Sketch Relations (Javelin)](https://www.javelin-tech.com/blog/2015/10/suppressing-solidworks-sketch-relations/) -- MEDIUM confidence
- [NX constraint management (Siemens community)](https://community.sw.siemens.com/s/question/0D54O000061xBakSAE/nx-sketching-constraint-preferences) -- MEDIUM confidence
- [Autodesk Inventor constraint deletion (official)](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/Deleting-all-sketching-constraints-from-an-Inventor-file.html) -- HIGH confidence
- [Community research (v2-research.md)](../docs/v2-research.md) -- HIGH confidence, primary source for pain points
