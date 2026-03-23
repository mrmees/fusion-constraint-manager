# Codebase Concerns

**Analysis Date:** 2026-03-22

## Tech Debt

**Entity Token Re-Resolution Fragility:**
- Issue: Constraint objects obtained during `inputChanged` event become stale by the time `execute` fires. The code stores `entityToken` strings and re-resolves them via `Design.findEntityByToken()` in the execute handler.
- Files: `ConstraintManager/commands/constraint_manager/command.py` (lines 346-369)
- Impact: If a constraint is deleted, moved, or otherwise invalidated between table population and user clicking Delete, the re-resolution will fail. Current code logs the failure but doesn't provide user feedback about what went wrong. Silent failures reduce confidence in the tool.
- Fix approach: Catch all token re-resolution failures and aggregate them into a user-facing summary dialog at the end showing "Deleted X, failed Y, skipped Z". Currently only logged internally.

**Module-Level Global State:**
- Issue: Handlers rely on module-level mutable state (`_current_constraints`, `_cmd_handlers`, `_addin_handlers`) to communicate across events because Fusion's event system doesn't preserve instance state between events.
- Files: `ConstraintManager/commands/constraint_manager/command.py` (lines 15-29, 64-81, 384-386)
- Impact: Global state creates tight coupling between handlers and makes the code harder to test. If a command instance somehow fires twice before being destroyed, stale references could accumulate. This is mitigated by the DestroyHandler cleanup (lines 380-386) but is fundamentally fragile.
- Fix approach: Wrap globals in a simple class for better organization and add guards to prevent double-initialization. Consider: `class CommandState: pass` instantiated per command invocation and stored in the command object itself where possible.

**Bare Exception Handling:**
- Issue: Multiple catch-all `except:` blocks that swallow all exceptions, some with silent failures
- Files: `ConstraintManager/ConstraintManager.py` (lines 25, 33); `ConstraintManager/commands/constraint_manager/command.py` (lines 145-146, 180-181, 202-203, 376-377)
- Impact: Makes debugging hard — exceptions from Fusion API calls get wrapped in generic error boxes or silent logs. A typo in constraint property access (e.g., `.line` vs `.lineOne`) will fail invisibly within the PreSelectHandler.
- Fix approach: Replace bare `except:` with specific exception types. At minimum use `except Exception as e:` and log the full traceback. For PreSelectHandler, let exceptions bubble up so selection validation fails visibly.

## Known Issues

**Constraint Display Name Limitation for Unknown Types:**
- Issue: When Fusion adds a new constraint type that the code doesn't recognize, it's displayed as "Unknown (ConstraintTypeName)" and forced non-deletable.
- Files: `ConstraintManager/commands/constraint_manager/constraint_engine.py` (lines 163-177)
- Trigger: Autodesk adds a new constraint type to Fusion, user selects an entity with that constraint
- Current mitigation: Unknown types show as read-only with warning logged. Prevents accidental deletions but blocks users from managing new constraints until plugin is updated.
- Approach: Maintain a separate config file listing new constraint types discovered in the wild, auto-update from community reports, or allow advanced users to whitelist constraint types manually.

**entityToken Validity Across Undo/Redo:**
- Issue: After an undo operation, entity tokens may reference deleted constraints or point to invalid entities. The code stores tokens in `_current_constraints` dict but doesn't validate them before attempting re-resolution.
- Files: `ConstraintManager/commands/constraint_manager/command.py` (lines 338-348, 360-372)
- Trigger: User deletes constraints, undoes, then re-runs the command and tries to delete again
- Workaround: Command dialog closes after execute, forcing user to re-open and re-select if they want to continue. Tokens aren't persisted across command invocations.
- Safe modification: This is actually not a bug in practice because the command modal closes after execute. However, if Approach 2 (Palette-based v2) is pursued, tokens will need validation.

**No Pre-Deletion Validation:**
- Issue: Code checks `isDeletable` and `isValid` before calling `deleteMe()` in the execute handler, but doesn't validate that the sketch is still in edit mode or that the active document hasn't changed.
- Files: `ConstraintManager/commands/constraint_manager/command.py` (lines 354-369)
- Impact: If user somehow switches documents or exits sketch edit mode between dialog creation and execute, deletions will silently fail. Unlikely in normal usage but possible in edge cases.
- Fix approach: Re-validate sketch edit mode in execute handler before processing deletions.

## Security Considerations

**No Input Validation on Entity Properties:**
- Issue: The code accesses entity properties like `entity.parentSketch`, `entity.objectType`, etc. without checking for None or catching AttributeError comprehensively.
- Files: `ConstraintManager/commands/constraint_manager/constraint_engine.py` (lines 98-111); `ConstraintManager/commands/constraint_manager/command.py` (lines 394-419)
- Current mitigation: PreSelectHandler catches exceptions on hover (line 180-181), preventing selection of invalid entities. For table building, constraint enumeration assumes valid Fusion API objects.
- Risk: Low — Fusion API doesn't allow invalid objects to be passed around. However, future API changes could introduce null references.
- Recommendations: Add type hints to function signatures to document expected Fusion object types. Consider a validation helper function.

**No Rate Limiting on Selection Events:**
- Issue: The `InputChangedHandler` processes every selection change immediately, rebuilding the entire constraint table for every entity added/removed. Users can trigger expensive enumeration by multi-selecting large numbers of entities.
- Files: `ConstraintManager/commands/constraint_manager/command.py` (lines 207-244)
- Current mitigation: `_handling_change` flag (line 187-205) prevents re-entrant calls within a single change, but doesn't throttle rapid successive changes.
- Risk: Low in practice — most sketches have tens of constraints per entity, not hundreds. However, on very complex sketches (1000+ constraints), table rebuilds could lag noticeably.
- Recommendations: Add a debounce timer for selection changes if v2 adopts a palette-based approach.

## Performance Bottlenecks

**Constraint Enumeration Scales with Constraints Count:**
- Slow operation: `enumerate_constraints()` calls `_build_constraint_info()` for every constraint on an entity.
- Files: `ConstraintManager/commands/constraint_manager/constraint_engine.py` (lines 132-160)
- Cause: Loops through entity.geometricConstraints collection and builds display info for each (name resolution, related entity lookup, formatting). For entities with 50+ constraints, this is noticeable but acceptable.
- Current: ~246 lines, tight loop, no caching of computed names.
- Improvement path: Cache constraint type name mappings in a module-level dict after first lookup. Memoize `get_constraint_type_name()` results. If v2 involves thousands of constraints, consider lazy-loading constraint details on demand (display count initially, load full info on expand).

**Table Rendering with Many Constraints:**
- Slow operation: Building a Fusion table row for each constraint (lines 256-308 in command.py).
- Files: `ConstraintManager/commands/constraint_manager/command.py` (lines 271-308)
- Cause: For each constraint, creates 4 StringValueInput objects and adds them to the table. This is a Fusion API limitation — no bulk row addition.
- Impact: On an entity with 100+ constraints, the loop creates 400+ UI input objects. Dialog responsiveness degrades.
- Scaling path: Implement pagination (show 20 constraints at a time with prev/next buttons), or migrate to a HTML palette (v2) where you control rendering directly.

**Entity Index Lookup in _find_entity_index():**
- Slow operation: Linear search through sketch collection to find entity index.
- Files: `ConstraintManager/commands/constraint_manager/command.py` (lines 389-419)
- Cause: No built-in Fusion API to get an entity's index without iterating. The function loops through the collection until it finds a matching object reference.
- Impact: Called once per selected entity to build display labels. On a sketch with 1000 lines and 10 entities selected, this is ~10,000 comparisons. Noticeable but not blocking.
- Improvement path: Cache the index once per entity during constraint enumeration to avoid repeated lookups. Or accept the slow path — user selections are typically single-digit counts.

## Fragile Areas

**PreSelectHandler Hover Validation:**
- Files: `ConstraintManager/commands/constraint_manager/command.py` (lines 149-181)
- Why fragile: Fires on every hover in the viewport. Any exception inside is silently swallowed (line 181). If Fusion API adds a new property to entities or changes object structure, the type checks (lines 168-175) silently fail and the entity becomes un-selectable.
- Safe modification: Add detailed logging before the bare except. Validate assumptions about entity properties (e.g., `hasattr(entity, 'parentSketch')` before accessing). Write a test that hovers over different entity types and confirms they're properly validated.
- Test coverage: No unit tests for PreSelectHandler — only integration in Fusion. If you change type checking logic, test manually with different entity types.

**Constraint Type Mapping Maintenance:**
- Files: `ConstraintManager/commands/constraint_manager/constraint_engine.py` (lines 57-74, 12-19)
- Why fragile: The `_CONSTRAINT_ENTITY_PROPS` dict is a hardcoded mapping of constraint types to property names. If Autodesk adds a constraint type (e.g., `SplineConstraint`, `ProjectionConstraint`), it won't appear in this dict and will be marked non-deletable.
- Safe modification: Add a comment documenting the constraint types and their source (Fusion API docs or version number). When a new version of Fusion ships, manually audit constraint types and update the dict.
- Current coverage: Research document (RESEARCH.md) lists 25 constraint types and their properties. Covers all documented types as of 2026.

**Related Entity Resolution Logic:**
- Files: `ConstraintManager/commands/constraint_manager/constraint_engine.py` (lines 77-129)
- Why fragile: The `resolve_related_entity()` function assumes specific property names for each constraint type. If a constraint has multiple entities but one is optional (e.g., None), the filtering (line 105) will skip it silently. The OffsetConstraint handling (lines 114-129) is a special case that could break if Offset API changes.
- Safe modification: Add assertions or defensive checks for null properties. Example: if `constraint.lineOne` is None on a ParallelConstraint, log a warning instead of filtering silently.
- Test coverage: Unit tests cover the happy path well. Missing: tests for constraints with null optional properties, edge cases with malformed constraint objects.

**Deduplication Token Assumption:**
- Files: `ConstraintManager/commands/constraint_manager/command.py` (lines 226-244)
- Why fragile: Deduplication relies on comparing `info.get("entity_token")` strings to avoid showing the same constraint twice when multiple entities are selected. If two different constraint objects somehow have the same token, or if a constraint's token changes, deduplication breaks.
- Safe modification: Log all tokens found during deduplication to catch duplicates. Add a post-dedup assertion that no constraint appears twice in the final list.
- Test coverage: Unit tests check basic deduplication. Missing: tests with multi-selected entities sharing constraints.

## Scaling Limits

**Maximum Constraint Count Per Entity:**
- Current capacity: Table set to display max 15 visible rows (line 118 in command.py). Not a hard limit — table scrolls — but UI becomes unwieldy at 50+ constraints.
- Limit: User experience degrades visibly with 100+ constraints per entity. Dialog takes 2-3 seconds to open and populate.
- Scaling path: Implement lazy-loading, pagination, or filtering by type. For v2, migrate to HTML palette with virtual scrolling (render only visible rows).

**Number of Selected Entities:**
- Current capacity: No enforced limit on multi-selection. Code handles this at line 112: `setSelectionLimits(0, 0)` = unlimited.
- Limit: With 10+ entities selected, table rebuilds every time you add another entity. Each rebuild re-enumerates all constraints on all selected entities. Becomes slow at 20+ selections.
- Scaling path: Add a selection count limit (e.g., max 10 entities) or implement batched updates (don't rebuild until user stops selecting for 500ms).

**Constraint Deduplication with Shared Constraints:**
- Current capacity: Seen-tokens set (line 228) deduplicates constraints appearing in multiple selected entities.
- Limit: If the same constraint somehow appears 1000+ times (shouldn't happen in practice), the set grows unbounded, though set lookup is still O(1).
- Scaling path: No issue in practice. Constraints are typically shared by 2-3 entities max.

## Dependencies at Risk

**Fusion API Stability:**
- Risk: The add-in directly calls Fusion API methods like `Design.findEntityByToken()`, `geometricConstraints.item()`, `constraint.isDeletable`, etc. These are stable documented APIs, but future Fusion versions could deprecate or change them.
- Impact: If Fusion 360 version X+1 changes the constraint API structure, the add-in will break. This is a risk for any add-in.
- Migration plan: Monitor Autodesk's API release notes. Test against each new Fusion version during beta period. Maintain a branch for each Fusion major version if needed.

**Python Version in Fusion Runtime:**
- Risk: The add-in is Python 3.x but Fusion's Python runtime version is pinned to a specific minor version (e.g., 3.9). If new code uses f-strings, type hints, or 3.10+ features, it will fail on older Fusion versions.
- Current: Code uses f-strings (supported in Python 3.6+) and basic type hints in comments. Safe for Python 3.9+.
- Migration plan: Document minimum Python version required. Add a CI check (in v2) that runs code through a Python syntax checker for the target version.

**`adsk.core` and `adsk.fusion` Import Safety:**
- Risk: The imports at the top of ConstraintManager.py (lines 1-3) are Fusion-specific and will fail if the code is imported outside of Fusion's runtime environment.
- Current mitigation: Tests mock all Fusion objects. Main entry point (ConstraintManager.py) wraps imports and calls in try/except. Constraint engine imports nothing Fusion-specific (by design).
- Impact: Low — this is intentional architecture. The constraint engine can be tested standalone.

## Missing Critical Features (v2 Roadmap)

**Constraint Type Filtering:**
- Problem: Users want to delete only horizontal constraints, or only fix constraints, etc. Currently must select entities and delete individually or all-at-once.
- Blocks: Bulk cleanup workflows (e.g., "remove all auto-constraints"). Directly addresses community pain point #2 and #6 from v2 research.
- Integration point: Add a filter dropdown to command UI or palette.

**Bulk Deletion By Type Across Sketch:**
- Problem: No way to say "delete all Fix constraints in this sketch" without selecting every entity.
- Blocks: DXF import cleanup (pain point #9). Currently users must manually select ~100 entities with Fix constraints.
- Integration point: New command or palette mode "Delete by type across sketch" that iterates all sketch entities and deletes matching constraint types.

**Over-Constraint Diagnosis:**
- Problem: When a new constraint would over-constrain the sketch, Fusion shows a warning but doesn't identify which existing constraint conflicts.
- Blocks: Common workflow — user needs to find the conflicting constraint to delete it.
- Integration point: New command "Find constraint conflicts" that could enumerate constraints and suggest which to remove. Requires more complex Fusion API usage.

**Undo Support Clarity:**
- Problem: Deletions are grouped in a single undo transaction (good), but user doesn't know this. If they press Ctrl+Z, all deletions undo at once, which can be surprising.
- Blocks: Power user workflows. Users expect fine-grained undo per constraint deleted.
- Approach: Document this behavior in README. Consider wrapping each deletion in its own undo group if Fusion API allows (unlikely).

## Test Coverage Gaps

**InputChangedHandler with Multi-Select Deduplication:**
- What's not tested: How deduplication behaves when the same constraint appears in multiple selected entities. What if a constraint is shared by all 3 selected entities? Does it show 1 or 3 times?
- Files: `ConstraintManager/commands/constraint_manager/command.py` (lines 207-244)
- Risk: Medium. Code logic looks correct but lacks concrete test data. If a user selects 5 entities with overlapping constraints, deduplication should work but has never been verified.
- Priority: High — add integration test in Fusion manually selecting 2+ entities with shared constraints.

**ExecuteHandler Failure Scenarios:**
- What's not tested: Partial failure cases (some deletions succeed, some fail). What if a constraint's `isDeletable` property changes between table render and execute?
- Files: `ConstraintManager/commands/constraint_manager/command.py` (lines 323-377)
- Risk: Medium. Code has a try/catch for individual constraint deletions and logs failures, but user sees no feedback.
- Priority: High — add user-facing result summary dialog.

**PreSelectHandler with New Constraint Types:**
- What's not tested: What happens when a new constraint type (not in the supported list) is present but not on a selected entity? Does hover validation correctly reject it?
- Files: `ConstraintManager/commands/constraint_manager/command.py` (lines 149-181)
- Risk: Low. Validation logic is simple but lacks concrete test with unknown types.
- Priority: Medium — add mock object test for unknown constraint type.

**Entity Token Re-Resolution Edge Cases:**
- What's not tested: What if `Design.findEntityByToken()` returns an empty list? What if it returns multiple matches? Current code assumes 0 or 1 match (lines 362-366).
- Files: `ConstraintManager/commands/constraint_manager/command.py` (lines 360-372)
- Risk: Low. The API docs suggest tokens are unique, but Fusion internals could have edge cases.
- Priority: Low — document the assumption and add defensive code to handle multiple matches (use first match, log warning).

**Constraint Offset Type Handling:**
- What's not tested: OffsetConstraint resolution with empty parent/child collections. What if `parentCurves.count == 0` or `childCurves.count == 0`?
- Files: `ConstraintManager/commands/constraint_manager/constraint_engine.py` (lines 114-129)
- Risk: Low. Code returns `"--"` on AttributeError (line 120), but doesn't test what happens if the collections exist but are empty.
- Priority: Low — add test for offset constraint with empty collections.

---

*Concerns audit: 2026-03-22*
