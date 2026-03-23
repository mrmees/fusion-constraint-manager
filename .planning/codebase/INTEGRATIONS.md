# External Integrations

**Analysis Date:** 2026-03-22

## APIs & External Services

**Autodesk Fusion 360:**
- Core modeling and CAD API
  - SDK/Client: `adsk.core`, `adsk.fusion` (built into Fusion runtime)
  - Auth: Handled by Fusion itself; add-in inherits user's Fusion 360 session
  - Used for: Sketch entity enumeration, constraint traversal, constraint deletion, UI command registration

**Not applicable:**
- No third-party REST APIs
- No cloud integrations
- No external SaaS dependencies

## Data Storage

**Databases:**
- None - Add-in is stateless and ephemeral

**File Storage:**
- Local filesystem only (add-in installation directory)
  - PNG icon assets: `ConstraintManager/resources/constraint_manager/16x16.png`, `32x32.png`
  - No user data persistence — all work is in-memory during Fusion session

**Caching:**
- None - Module-level state variables store constraint info for current command session only
  - See `_current_constraints` global in `command.py`

## Authentication & Identity

**Auth Provider:**
- None — Add-in runs within Fusion's authenticated session
- User identity handled entirely by Fusion 360 (cloud account or local)

## Monitoring & Observability

**Error Tracking:**
- None - Errors logged locally to Python logger

**Logs:**
- Python `logging` module (local console/stderr)
  - Module-level logger: `_log = logging.getLogger(__name__)`
  - Errors caught and displayed via Fusion UI: `_ui.messageBox()`
  - No external log aggregation

## CI/CD & Deployment

**Hosting:**
- GitHub Releases (`https://github.com/mrmees/fusion-constraint-manager/releases`)
  - Distributes `.zip` file containing `ConstraintManager/` folder
  - User manually extracts and copies to Fusion add-ins directory

**CI Pipeline:**
- None detected - No GitHub Actions workflows

**Distribution:**
- Manual zip packaging (see `ConstraintManager-v1.1.zip` in repo root)
- No automation for builds or releases

## Environment Configuration

**Required env vars:**
- None - No environment variables used

**Secrets location:**
- Not applicable - Add-in has no secrets or API keys

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None - Fully offline, no HTTP/webhook integration

## Fusion API Integration Points

**Command Lifecycle:**
- `run(context)` (top-level entry in `ConstraintManager.py`)
  - Registers command definition and toolbar button
  - Initializes `CommandCreatedHandler` for UI setup

- `stop(context)` (top-level in `ConstraintManager.py`)
  - Cleans up toolbar controls and event handlers

**Event Handlers (all in `command.py`):**
- `CommandCreatedHandler` — Fires when user clicks toolbar button
  - Sets up constraint table UI and entity selection input
  - Validates active sketch edit mode

- `PreSelectHandler` — Validates hoverable entities during selection
  - Only allows supported sketch curves/points (lines, arcs, circles, ellipses, splines, points)
  - Restricts to active sketch entities only

- `InputChangedHandler` — Populates constraint table as entities are selected
  - Calls `constraint_engine.enumerate_constraints()` for each selected entity
  - Deduplicates constraints across multi-entity selection

- `ExecuteHandler` — Deletes checked constraints when "Delete Selected" clicked
  - Re-resolves constraints via `Design.findEntityByToken()`
  - Calls `constraint.deleteMe()` on each resolved constraint

- `DestroyHandler` — Cleanup when command dialog closed
  - Clears module-level handler references and constraint cache

## Data Flow Through Fusion API

1. User clicks Constraint Manager toolbar button
2. Fusion creates command, fires `CommandCreatedHandler.notify()`
3. Handler constructs UI: entity selection input + constraint table
4. User selects sketch entities (lines, arcs, etc.)
5. `InputChangedHandler` enumerates constraints via Fusion API:
   - `entity.geometricConstraints` — list of constraints on the entity
   - `constraint.isDeletable` — whether Fusion allows deletion
   - `constraint.entityToken` — stable identifier across Fusion events
6. Handler populates table with constraint type, related entity, deletability
7. User checks constraints to delete and clicks "Delete Selected"
8. `ExecuteHandler` re-resolves constraints from `entityToken` via `Design.findEntityByToken()`
9. Calls `constraint.deleteMe()` on each, which modifies the active sketch
10. Sketch updates in Fusion viewport; undo stack captures deletion transaction

---

*Integration audit: 2026-03-22*
