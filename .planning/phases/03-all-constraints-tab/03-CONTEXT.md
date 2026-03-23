# Phase 3: All Constraints Tab - Context

**Gathered:** 2026-03-23
**Status:** SCRAPPED — user decision during discuss-phase

<domain>
## Phase Boundary

Phase 3 was originally scoped as a full listing of every constraint in the active sketch with Load button, type filter, and checkbox deletion.

**Decision: Phase scrapped.** During discussion, the user questioned whether the All tab adds meaningful value over the Selected + Types tabs. Analysis confirmed:

- **Selected tab** covers surgical per-entity debugging (the #1 community request)
- **Types tab** covers bulk operations and DXF import cleanup (the #2 community request)
- **All tab** fills a gap between the two, but community research didn't surface strong demand for "flat list of all constraints"
- The All tab also carries the most performance risk (500+ row tables in Fusion's dialog framework)

v2.0 ships as a two-tab tool. All Constraints tab deferred to v2.1+ if users request it.

</domain>

<decisions>
## Implementation Decisions

### D-01: Phase scrapped
All Constraints tab removed from v2.0 scope. ALLC-01 through ALLC-07 requirements moved to v2 (deferred).

### D-02: Remove placeholder
The "All" tab placeholder from Phase 1 should be removed from the command dialog. Ship with two tabs: Selected and Types.

</decisions>

<deferred>
## Deferred Ideas

- All Constraints tab (ALLC-01 through ALLC-07) — deferred to v2.1+ if community requests it
- Type filter dropdown for All tab — deferred with the tab
- The executePreview highlighting pattern established in Phase 2 can be reused if All tab is built later

</deferred>

---

*Phase: 03-all-constraints-tab*
*Context gathered: 2026-03-23*
