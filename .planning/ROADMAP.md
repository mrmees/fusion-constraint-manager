# Roadmap: Constraint Manager v2.0

## Overview

v1.1 ships a working per-entity constraint tool. v2.0 adds sketch-wide constraint management via a two-tab dialog: the original Selected Entities tab plus a new Constraint Types tab with type summaries, bulk deletion, and viewport highlighting. Phase 3 (All Constraints Tab) was scrapped during discussion — the two tabs cover the highest-impact community needs without the performance risks of a full constraint listing.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (1.1, 2.1): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Engine and Tab Foundation** - Extend the constraint engine, migrate to tab dialog, preserve v1.1 Selected Entities behavior (completed 2026-03-23)
- [x] **Phase 2: Constraint Types Tab** - Sketch-wide type summary with counts, bulk delete by type, and viewport highlighting (completed 2026-03-23)
- [x] **Phase 3: All Constraints Tab** - SCRAPPED — Selected + Types tabs cover highest-impact use cases (scrapped 2026-03-23)

## Phase Details

### Phase 1: Engine and Tab Foundation
**Goal**: The add-in opens with a tabbed dialog, v1.1 Selected Entities behavior works identically to before, and the constraint engine supports sketch-wide enumeration
**Depends on**: Nothing (brownfield — builds on v1.1)
**Requirements**: ENGN-01, ENGN-02, ENGN-03, ENGN-04, TABS-01, TABS-02, TABS-03, TABS-04, ENTY-01, ENTY-02
**Success Criteria** (what must be TRUE):
  1. User opens the command and sees two tabs: Selected, Types
  2. User interacts with the Selected tab exactly as in v1.1 — entity selection, constraint table, checkbox deletion all work without regression
  3. Selected tab is active by default on command launch
  4. Switching between tabs does not re-enumerate constraints or reset per-tab state
  5. Engine functions for sketch-wide enumeration, type grouping, and type filtering pass unit tests outside Fusion
**Plans:** 2/2 plans complete

Plans:
- [x] 01-01-PLAN.md — Extend constraint engine with sketch-wide functions (TDD)
- [x] 01-02-PLAN.md — Migrate to tab dialog, preserve v1.1 Selected Entities behavior

### Phase 2: Constraint Types Tab
**Goal**: Users can see every constraint type present in the active sketch with its count, and delete all constraints of a given type in one action
**Depends on**: Phase 1
**Requirements**: TYPE-01, TYPE-02, TYPE-03, TYPE-04, TYPE-05
**Success Criteria** (what must be TRUE):
  1. User opens Types tab and sees a summary table listing each constraint type with its count — no manual load step required
  2. User can check constraint type rows via checkboxes
  3. User clicks "Delete Selected" and all constraints of checked types are removed — none skipped due to forward-iteration issues
  4. After bulk deletion, reopening shows updated counts
  5. Checked types highlight associated geometry in the viewport via CustomGraphics
**Plans:** 1/1 plans complete

Plans:
- [x] 02-01-PLAN.md — Build Types tab UI, auto-populate, bulk delete, and viewport highlighting

### Phase 3: All Constraints Tab — SCRAPPED
**Status**: Scrapped during discuss-phase (2026-03-23)
**Reason**: Selected + Types tabs cover the two highest-impact community use cases (surgical per-entity debugging and bulk type deletion). The All Constraints tab added marginal value with significant performance risk (500+ row tables in Fusion's dialog). ALLC-01 through ALLC-07 deferred to v2.1+ if users request it.

## Progress

**Execution Order:**
Phases 1 and 2 complete. Phase 3 scrapped.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Engine and Tab Foundation | 2/2 | Complete | 2026-03-23 |
| 2. Constraint Types Tab | 1/1 | Complete | 2026-03-23 |
| 3. All Constraints Tab | — | Scrapped | 2026-03-23 |
