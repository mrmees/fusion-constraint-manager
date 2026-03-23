# Roadmap: Constraint Manager v2.0

## Overview

v1.1 ships a working per-entity constraint tool. v2.0 adds sketch-wide constraint management via a three-tab dialog. The build order is dictated by dependency: the constraint engine must be extended before any new UI works, the tab scaffold must exist before features can live inside tabs, and the simpler Constraint Types tab ships before the more complex All Constraints tab. Three phases deliver the complete feature set.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (1.1, 2.1): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Engine and Tab Foundation** - Extend the constraint engine, migrate to three-tab dialog, preserve v1.1 Selected Entities behavior
- [ ] **Phase 2: Constraint Types Tab** - Sketch-wide type summary with counts and bulk delete by type
- [ ] **Phase 3: All Constraints Tab** - Full sketch constraint listing with Load button, type filter, and checkbox deletion

## Phase Details

### Phase 1: Engine and Tab Foundation
**Goal**: The add-in opens with a three-tab dialog, v1.1 Selected Entities behavior works identically to before, and the constraint engine supports sketch-wide enumeration
**Depends on**: Nothing (brownfield — builds on v1.1)
**Requirements**: ENGN-01, ENGN-02, ENGN-03, ENGN-04, TABS-01, TABS-02, TABS-03, TABS-04, ENTY-01, ENTY-02
**Success Criteria** (what must be TRUE):
  1. User opens the command and sees three tabs: Selected Entities, Constraint Types, All Constraints
  2. User interacts with the Selected Entities tab exactly as in v1.1 — entity selection, constraint table, checkbox deletion all work without regression
  3. Selected Entities tab is active by default on command launch
  4. Switching between tabs does not re-enumerate constraints or reset per-tab state
  5. Engine functions for sketch-wide enumeration, type grouping, and type filtering pass unit tests outside Fusion
**Plans**: TBD
**UI hint**: yes

### Phase 2: Constraint Types Tab
**Goal**: Users can see every constraint type present in the active sketch with its count, and delete all constraints of a given type in one action
**Depends on**: Phase 1
**Requirements**: TYPE-01, TYPE-02, TYPE-03, TYPE-04, TYPE-05
**Success Criteria** (what must be TRUE):
  1. User opens Constraint Types tab and sees a summary table listing each constraint type (e.g., Fix, Coincident, Horizontal) with its count — no manual load step required
  2. User can select a constraint type row in the summary table
  3. User clicks "Delete All of Type" and all constraints of the selected type are removed from the sketch — none are skipped due to forward-iteration issues
  4. After bulk deletion, the Constraint Types table refreshes to reflect the updated counts
**Plans**: TBD
**UI hint**: yes

### Phase 3: All Constraints Tab
**Goal**: Users can load, browse, filter, and selectively delete any constraint in the active sketch from a single full-listing view
**Depends on**: Phase 2
**Requirements**: ALLC-01, ALLC-02, ALLC-03, ALLC-04, ALLC-05, ALLC-06, ALLC-07
**Success Criteria** (what must be TRUE):
  1. User clicks Load and the All Constraints tab populates with every constraint in the active sketch, each row showing its type
  2. User selects a type from the dropdown filter and the table updates to show only constraints of that type
  3. User checks individual constraint rows and clicks Delete Selected — only the checked constraints are removed
  4. Deletion correctly handles staleness — constraints invalidated between Load and Delete are skipped gracefully, not errored
  5. Loading a sketch with 500+ entities does not freeze the Fusion UI (Load button gates enumeration; progress indication provided)
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Engine and Tab Foundation | 0/? | Not started | - |
| 2. Constraint Types Tab | 0/? | Not started | - |
| 3. All Constraints Tab | 0/? | Not started | - |
