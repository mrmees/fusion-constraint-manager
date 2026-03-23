# Fusion 360 Geometric Constraint Types — Complete Reference

Fetched 2026-03-23 from official Autodesk API docs.

## All 22 Types

### Single-Entity Constraints

| Type | Entity Props | Notes |
|------|-------------|-------|
| `HorizontalConstraint` | `line` | Line horizontal |
| `VerticalConstraint` | `line` | Line vertical |
| `FixConstraint` | `entity` | Locks geometry in place |

### Two-Entity Constraints

| Type | Entity Props | Notes |
|------|-------------|-------|
| `ParallelConstraint` | `lineOne`, `lineTwo` | Two lines parallel |
| `PerpendicularConstraint` | `lineOne`, `lineTwo` | Two lines at 90 degrees |
| `CollinearConstraint` | `lineOne`, `lineTwo` | Two lines on same infinite line |
| `CoincidentConstraint` | `point`, `entity` | Point on point or curve |
| `EqualConstraint` | `curveOne`, `curveTwo` | Equal size/radius/length |
| `TangentConstraint` | `curveOne`, `curveTwo` | Tangent between curves |
| `SmoothConstraint` | `curveOne`, `curveTwo` | G2 smooth blend |
| `ConcentricConstraint` | `entityOne`, `entityTwo` | Shared center |
| `MidPointConstraint` | `point`, `midPointCurve` | Point at midpoint |
| `HorizontalPointsConstraint` | `pointOne`, `pointTwo` | Two points share Y |
| `VerticalPointsConstraint` | `pointOne`, `pointTwo` | Two points share X |

### Three-Entity Constraints

| Type | Entity Props | Notes |
|------|-------------|-------|
| `SymmetryConstraint` | `entityOne`, `entityTwo`, `symmetryLine` | Mirror symmetry |

### Surface Constraints (3D sketch)

| Type | Sketch Entity | Surface Prop | Notes |
|------|--------------|-------------|-------|
| `CoincidentToSurfaceConstraint` | `point` (SketchPoint) | `surface` (BRepFace/ConstructionPlane) | Point onto 3D surface |
| `LineOnPlanarSurfaceConstraint` | `line` (SketchLine) | `planarSurface` | Line on a surface |
| `LineParallelToPlanarSurfaceConstraint` | `line` (SketchLine) | `planarSurface` | Line parallel to surface |
| `PerpendicularToSurfaceConstraint` | `curve` (SketchCurve) | `surface` | Curve perpendicular to surface |

### Pattern/Polygon Constraints (collection-based)

| Type | Entity Props | Notes |
|------|-------------|-------|
| `CircularPatternConstraint` | `centerPoint`, `entities[]`, `createdEntities[]` | Circular pattern |
| `RectangularPatternConstraint` | `entities[]`, `createdEntities[]`, `directionOneEntity`, `directionTwoEntity` | Rectangular pattern |
| `PolygonConstraint` | `centerPoint`, `points[]` | Polygon on lines |

### Collection-Based (special handling)

| Type | Entity Props | Notes |
|------|-------------|-------|
| `OffsetConstraint` | `parentCurves[]`, `childCurves[]` | Handled separately in engine |

## IMPORTANT: Shared Endpoints Are NOT Constraints

When lines are drawn end-to-end in Fusion, the connection is a **shared SketchPoint instance** — NOT a `CoincidentConstraint`. Two lines meeting at a point literally reference the same `SketchPoint` object.

- `CoincidentConstraint` only appears when you **explicitly apply** one (e.g., snapping a floating point to a curve)
- To find shared-endpoint connections: use `SketchPoint.connectedEntities`
- `connectedEntities` does NOT include constraint-related entities — only structural connections

## Sources

- GeometricConstraint base class (authoritative derived-type list)
- Individual constraint type pages on help.autodesk.com
- Forum: "Get CoincidentConstraint of line endpoints"
- Forum: "Where are Coincident Constraints saved?"
