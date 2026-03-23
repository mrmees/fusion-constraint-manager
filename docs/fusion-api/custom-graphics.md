# Fusion 360 CustomGraphics API Reference

Fetched 2026-03-23 from official Autodesk docs + confirmed working GitHub examples.

## Access Point

```python
root = design.rootComponent
cg_group = root.customGraphicsGroups.add()  # returns CustomGraphicsGroup
```

For CAM workspace, use `cam.customGraphicsGroups` instead.

## CustomGraphicsGroup

Created via `component.customGraphicsGroups.add()`.

### Methods

| Method | Description |
|--------|-------------|
| `addBRepBody(body)` | Add a BRepBody as custom graphics |
| `addCurve(curve3D)` | Add any Curve3D subclass (NOT InfiniteLine3D) |
| `addGroup()` | Create child group |
| `addLines(coords, indexList, isLineStrip, stripLengths?)` | Add line geometry |
| `addMesh(coords, vertexIndices, normals, normalIndices)` | Add triangle mesh |
| `addPointSet(coords, indexList, pointType, imagePath)` | Add point set |
| `addText(text, fontName, size, matrix)` | Add text |
| `deleteMe()` | Remove this group |
| `setOpacity(value, isOverride)` | 0.0-1.0; isOverride=True overrides material opacity |

### Key Properties

- `color` — `CustomGraphicsColorEffect`, applied to all children unless overridden
- `isVisible`, `isSelectable` — bools, default True
- `depthPriority` — int, draw order when overlapping, default 0
- `transform` — `Matrix3D`, default identity

## CustomGraphicsCurve

Created via `group.addCurve(curve3D)`.

Supports: `Arc3D`, `Circle3D`, `Ellipse3D`, `EllipticalArc3D`, `Line3D`, `NurbsCurve3D`.
Does NOT support: `InfiniteLine3D`.

### Key Properties

- `curve` — the underlying Curve3D
- `weight` — line thickness in pixels
- `lineStylePattern` — continuous (default), dashed, center, dot, phantom, tracks, zigzag
- `color` — `CustomGraphicsColorEffect`

## CustomGraphicsLines

Created via `group.addLines(coords, indexList, isLineStrip, stripLengths?)`.

- `coords` — `CustomGraphicsCoordinates` from flat `[x,y,z, ...]` array
- `indexList` — pairs of vertex indices (non-strip) or sequential (strip)
- `isLineStrip` — True = connected strip, False = individual segments
- `stripLengths` — optional `int[]` for multiple disconnected strips

### Key Properties

- `weight` — pixels
- `lineStylePattern` — enum from `adsk.fusion.LineStylePatterns.*`
- `isScreenSpaceLineStyle` — pattern in screen space (default) vs model space

## CustomGraphicsPointSet

Created via `group.addPointSet(coords, indexList, pointType, imagePath)`.

- `UserDefinedCustomGraphicsPointType` — custom PNG
- `PointCloudPointType` — built-in dot, better performance

## Color Effects

Set via `entity.color = someEffect`.

### SolidColorEffect (flat, no lighting)

```python
color = adsk.core.Color.create(255, 0, 0, 255)
solid = adsk.fusion.CustomGraphicsSolidColorEffect.create(color)
entity.color = solid
```

**CRITICAL: Alpha in Color.create() is IGNORED. Use setOpacity() separately.**

### Other Effects

- `CustomGraphicsBasicMaterialColorEffect` — Phong shading
- `CustomGraphicsAppearanceColorEffect` — uses Fusion appearance library
- `CustomGraphicsVertexColorEffect` — per-vertex RGBA (meshes only)
- `CustomGraphicsShowThroughColorEffect` — shows through other objects

## CustomGraphicsCoordinates

```python
coords = adsk.fusion.CustomGraphicsCoordinates.create([x,y,z, x,y,z, ...])
```

Units are centimeters.

## executePreview Event

Fires when inputs change and Fusion needs a live preview.

### Wiring (class-based pattern)

```python
class MyPreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args: adsk.core.CommandEventArgs):
        # draw CustomGraphics here
        pass

handler = MyPreviewHandler()
cmd.executePreview.add(handler)
handlers.append(handler)
```

### Critical Behaviors

1. **Graphics are NOT auto-cleaned between calls** — delete old group or create fresh each time
2. **executePreview fires AFTER execute completes** — use a `_completed` flag to guard
3. **Same handler class can be used for both execute and executePreview**
4. `args.isValidResult = True` shows preview; `False` hides it

## Working Patterns from Real Add-ins

### Pattern 1: Official Sample

```python
cgGroup = adsk.fusion.CustomGraphicsGroup.cast(cgGroups.add())
cgEnt = drawLines(cgGroup)
solidColor = adsk.fusion.CustomGraphicsSolidColorEffect.create(
    adsk.core.Color.create(r, g, b, 255))
cgEnt.color = solidColor
```

### Pattern 2: GOKOTAI Voxel (executePreview with BRepBody)

```python
def command_executePreview(args):
    if _completed:
        return
    root = futil.app.activeProduct.rootComponent
    cgGroup = root.customGraphicsGroups.add()
    cgBox = cgGroup.addBRepBody(base_Box)
    cgBox.setOpacity(0.2, True)
```

### Pattern 3: Drawing curves from sketch geometry

```python
# entity.worldGeometry returns 3D curve in model space
# entity.geometry returns 2D curve in sketch space
# Use worldGeometry for CustomGraphics (they render in model space)
geom = entity.worldGeometry  # or entity.geometry for sketch-plane coords
curve_graphic = cg_group.addCurve(geom)
curve_graphic.weight = 2
```

## Sketch Entity Geometry Types

| Entity | .geometry type | .worldGeometry type |
|--------|---------------|-------------------|
| SketchLine | Line3D | Line3D |
| SketchArc | Arc3D | Arc3D |
| SketchCircle | Circle3D | Circle3D |
| SketchEllipse | Ellipse3D | Ellipse3D |
| SketchFittedSpline | NurbsCurve3D | NurbsCurve3D |
| SketchPoint | Point3D | Point3D |

Note: Point3D is NOT a Curve3D subclass — cannot use addCurve for points. Use addPointSet.
