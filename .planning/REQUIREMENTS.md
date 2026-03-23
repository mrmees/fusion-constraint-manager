# Requirements: Constraint Manager v2.0

**Defined:** 2026-03-22
**Core Value:** Users can see and manage every constraint in a sketch without guessing, clicking blindly, or relying on Fusion's all-or-nothing deletion.

## v1 Requirements

Requirements for v2.0 release. Each maps to roadmap phases.

### Tab Infrastructure

- [ ] **TABS-01**: Command dialog displays three tabs: Selected Entities, Constraint Types, All Constraints
- [ ] **TABS-02**: Tab switching preserves per-tab state without re-enumeration
- [ ] **TABS-03**: Per-tab state isolation — each tab maintains its own constraint list independently
- [ ] **TABS-04**: Handler GC protection utility to prevent garbage collection of event handlers across all tabs

### Constraint Types Tab

- [ ] **TYPE-01**: Constraint Types tab displays a summary table showing each constraint type and its count for the active sketch
- [ ] **TYPE-02**: Constraint Types tab auto-populates on tab activation (counting by type is lightweight)
- [ ] **TYPE-03**: User can select a constraint type row in the summary table
- [ ] **TYPE-04**: User can delete all constraints of the selected type via a toolbar "Delete All of Type" button
- [ ] **TYPE-05**: Bulk deletion uses reverse iteration or snapshot-then-delete to avoid forward-iteration skip bug

### All Constraints Tab

- [ ] **ALLC-01**: All Constraints tab displays a full list of every constraint in the active sketch
- [ ] **ALLC-02**: Explicit "Load" button required before enumeration begins (no auto-load for performance safety)
- [ ] **ALLC-03**: Each constraint row includes a Type column showing the constraint type
- [ ] **ALLC-04**: Dropdown filter above the table filters displayed constraints by type
- [ ] **ALLC-05**: User can select individual constraints via per-row checkboxes
- [ ] **ALLC-06**: User can delete checked constraints via OK/Delete Selected button
- [ ] **ALLC-07**: Deletion re-resolves constraints via entityToken before deleting (handles staleness)

### Selected Entities Tab

- [ ] **ENTY-01**: Selected Entities tab preserves identical behavior to v1.1 — entity selection, constraint table, checkbox deletion
- [ ] **ENTY-02**: Selected Entities tab is the default active tab on command launch

### Engine

- [ ] **ENGN-01**: Constraint engine supports sketch-wide enumeration via `sketch.geometricConstraints` collection
- [ ] **ENGN-02**: Constraint engine supports grouping/counting constraints by type
- [ ] **ENGN-03**: Constraint engine supports filtering constraints by type
- [ ] **ENGN-04**: Bulk deletion uses reverse iteration to prevent forward-iteration collection re-index bug

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Visual Feedback

- **VSFB-01**: Viewport highlighting of constraint geometry when selecting a constraint in any tab
- **VSFB-02**: Constraint status indicators (under/over-constrained coloring)

### Extended Constraint Support

- **EXTC-01**: Dimension constraint listing alongside geometric constraints
- **EXTC-02**: Sort mode toggle (sort by entity vs sort by constraint type)

### Diagnostics

- **DIAG-01**: Under-constrained entity identification and display

## Out of Scope

| Feature | Reason |
|---------|--------|
| Auto-constraint interception | Fusion API has no event hook for constraint creation — detection would be fragile polling |
| Constraint replacement (swap types) | Requires delete + recreate with correct entity refs — high complexity, edge cases |
| Under-constrained DOF analysis | Would require reimplementing sketch solver — no API access |
| Persistent preferences/settings | Fusion add-in API has no clean settings storage — file-based config adds install complexity |
| Real-time constraint monitoring panel | Would require dockable HTML palette — completely different architecture |
| Suppress/Unsuppress constraints | SolidWorks-specific capability — Fusion API does not support constraint suppression |
| Cross-sketch constraint management | Massive scope increase — single active sketch is the right mental model |
| Undo/redo within command | Fusion undo operates at command boundary — sub-operation undo not supported |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| TABS-01 | Phase 1 | Pending |
| TABS-02 | Phase 1 | Pending |
| TABS-03 | Phase 1 | Pending |
| TABS-04 | Phase 1 | Pending |
| TYPE-01 | Phase 2 | Pending |
| TYPE-02 | Phase 2 | Pending |
| TYPE-03 | Phase 2 | Pending |
| TYPE-04 | Phase 2 | Pending |
| TYPE-05 | Phase 2 | Pending |
| ALLC-01 | Phase 3 | Pending |
| ALLC-02 | Phase 3 | Pending |
| ALLC-03 | Phase 3 | Pending |
| ALLC-04 | Phase 3 | Pending |
| ALLC-05 | Phase 3 | Pending |
| ALLC-06 | Phase 3 | Pending |
| ALLC-07 | Phase 3 | Pending |
| ENTY-01 | Phase 1 | Pending |
| ENTY-02 | Phase 1 | Pending |
| ENGN-01 | Phase 1 | Pending |
| ENGN-02 | Phase 1 | Pending |
| ENGN-03 | Phase 1 | Pending |
| ENGN-04 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0

---
*Requirements defined: 2026-03-22*
*Last updated: 2026-03-22 after roadmap creation*
