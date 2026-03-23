---
phase: 01-engine-and-tab-foundation
plan: 01
subsystem: engine
tags: [pytest, constraint-engine, tdd, pure-python]

requires: []
provides:
  - "aggregate_constraint_types function for Types tab count display"
  - "enumerate_all_constraints function for All Constraints tab listing"
  - "filter_constraints_by_type function for All Constraints tab dropdown filter"
  - "collect_constraints_by_type function for Types tab bulk deletion"
  - "_build_sketch_constraint_info helper with entities_label for sketch-wide context"
affects: [01-02, 02-types-tab, 03-all-constraints-tab]

tech-stack:
  added: []
  patterns:
    - "Sketch-wide constraint info uses entities_label (not related_label) since no selected entity context"
    - "GeometricConstraints collection iterated via .count/.item(i) pattern"

key-files:
  created: []
  modified:
    - "ConstraintManager/commands/constraint_manager/constraint_engine.py"
    - "ConstraintManager/tests/test_constraint_engine.py"

key-decisions:
  - "entities_label key (not related_label) for sketch-wide context per D-09"
  - "Unknown constraint types return is_deletable=False and entities_label='--' for safety"
  - "MockCollection reused as GeometricConstraints mock (identical API: .count, .item(i))"

patterns-established:
  - "_build_sketch_constraint_info: sketch-wide variant of _build_constraint_info without selected entity"
  - "aggregate functions take GeometricConstraints collection directly, not individual entities"

requirements-completed: [ENGN-01, ENGN-02, ENGN-03, ENGN-04]

duration: 2min
completed: 2026-03-23
---

# Phase 01 Plan 01: Sketch-Wide Engine Functions Summary

**Four pure-Python constraint engine functions (aggregate, enumerate, filter, collect) with 22 pytest tests, using entities_label for sketch-wide context**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-23T02:27:26Z
- **Completed:** 2026-03-23T02:29:00Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Built aggregate_constraint_types returning {type_name: count} for Types tab
- Built enumerate_all_constraints with entities_label showing all referenced entities
- Built filter_constraints_by_type as pure Python list comprehension
- Built collect_constraints_by_type returning raw constraint objects for bulk deletion
- 22 new tests covering empty collections, basic operation, edge cases, type safety
- All 52 tests pass (30 existing + 22 new), zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Add failing tests** - `60c35dd` (test)
2. **Task 1 (GREEN): Implement engine functions** - `f80fffe` (feat)

_Note: TDD task with RED-GREEN commits. No refactoring needed._

## Files Created/Modified
- `ConstraintManager/commands/constraint_manager/constraint_engine.py` - Added 5 new functions (4 public + 1 helper) between existing functions and delete_constraints
- `ConstraintManager/tests/test_constraint_engine.py` - Added 22 tests in new "Sketch-wide engine tests" section

## Decisions Made
- Used `entities_label` key instead of `related_label` for sketch-wide info dicts per D-09 (no "selected" entity in sketch-wide context, so all entities are labeled)
- Unknown constraint types marked non-deletable with "--" entities_label (safety first, consistent with existing _build_constraint_info pattern)
- Reused existing MockCollection as GeometricConstraints mock since the API is identical (.count property, .item(i) method)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All four engine functions ready for consumption by Phase 2 (Types tab) and Phase 3 (All Constraints tab)
- aggregate_constraint_types ready for Types tab count display
- enumerate_all_constraints + filter_constraints_by_type ready for All Constraints tab
- collect_constraints_by_type ready for Types tab "Delete All" action
- Plan 01-02 (tab infrastructure + v1 migration) can proceed independently

---
*Phase: 01-engine-and-tab-foundation*
*Completed: 2026-03-23*
