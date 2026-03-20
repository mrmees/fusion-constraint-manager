# Fusion API: Sketch Constraints Research

Research compiled 2026-03-20 for building a constraint management add-in.

---

## 1. Getting the Active Sketch and Its Constraints

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)

# Get active edit sketch (returns None if not editing a sketch)
sketch = design.activeEditObject
if not isinstance(sketch, adsk.fusion.Sketch):
    sketch = None

# Alternative: get a specific sketch by name
root = design.rootComponent
sketch = root.sketches.itemByName('Sketch1')

# Access constraints
geo_constraints = sketch.geometricConstraints   # GeometricConstraints collection
dim_constraints = sketch.sketchDimensions        # SketchDimensions collection

# Iterate geometric constraints
for i in range(geo_constraints.count):
    constraint = geo_constraints.item(i)
    print(f"{constraint.objectType} - deletable: {constraint.isDeletable}")

# Iterate dimension constraints
for i in range(dim_constraints.count):
    dim = dim_constraints.item(i)
    print(f"{dim.objectType} - value: {dim.value} - driving: {dim.isDriving}")
```

### Key Sketch Properties
- `sketch.isFullyConstrained` - bool, whether sketch is fully constrained
- `sketch.isParametric` - bool, parametric vs direct mode
- `sketch.areConstraintsShown` - bool, get/set visibility of constraint icons
- `sketch.areDimensionsShown` - bool, get/set visibility of dimensions
- `sketch.isComputeDeferred` - bool, defer recomputation (performance optimization)

---

## 2. Geometric Constraint Types

All derive from `GeometricConstraint` base class. Accessed via `sketch.geometricConstraints`.

### GeometricConstraint (Base Class) Properties
| Property | Type | Description |
|----------|------|-------------|
| `parentSketch` | Sketch | Parent sketch |
| `isDeletable` | bool | Whether constraint can be deleted |
| `isValid` | bool | Whether reference is still valid |
| `objectType` | str | Full type string e.g. `adsk::fusion::HorizontalConstraint` |
| `entityToken` | str | Persistent token for `Design.findEntityByToken()` |
| `attributes` | AttributeCollection | Custom metadata |

### GeometricConstraint (Base Class) Methods
| Method | Returns | Description |
|--------|---------|-------------|
| `deleteMe()` | bool | Delete constraint, returns success |
| `classType()` | str | Static - returns class type string |

### Constraint Types and Their Entity Reference Properties

| Constraint Class | Creation Method | Entity Properties |
|-----------------|-----------------|-------------------|
| `HorizontalConstraint` | `addHorizontal(line)` | `line` |
| `VerticalConstraint` | `addVertical(line)` | `line` |
| `ParallelConstraint` | `addParallel(lineOne, lineTwo)` | `lineOne`, `lineTwo` |
| `PerpendicularConstraint` | `addPerpendicular(lineOne, lineTwo)` | `lineOne`, `lineTwo` |
| `CollinearConstraint` | `addCollinear(lineOne, lineTwo)` | `lineOne`, `lineTwo` |
| `CoincidentConstraint` | `addCoincident(point, entity)` | `point`, `entity` |
| `ConcentricConstraint` | `addConcentric(entityOne, entityTwo)` | `entityOne`, `entityTwo` |
| `EqualConstraint` | `addEqual(curveOne, curveTwo)` | `curveOne`, `curveTwo` |
| `TangentConstraint` | `addTangent(curveOne, curveTwo)` | `curveOne`, `curveTwo` |
| `SmoothConstraint` | `addSmooth(curveOne, curveTwo)` | `curveOne`, `curveTwo` |
| `SymmetryConstraint` | `addSymmetry(entityOne, entityTwo, symmetryLine)` | `entityOne`, `entityTwo`, `symmetryLine` |
| `MidPointConstraint` | `addMidPoint(point, midPointCurve)` | `point`, `midPointCurve` |
| `HorizontalPointsConstraint` | `addHorizontalPoints(pointOne, pointTwo)` | `pointOne`, `pointTwo` |
| `VerticalPointsConstraint` | `addVerticalPoints(pointOne, pointTwo)` | `pointOne`, `pointTwo` |
| `CoincidentToSurfaceConstraint` | `addCoincidentToSurface(point, surface)` | `point`, `surface` |
| `LineOnPlanarSurfaceConstraint` | `addLineOnPlanarSurface(line, surface)` | `line`, `surface` |
| `LineParallelToPlanarSurfaceConstraint` | `addLineParallelToPlanarSurface(line, surface)` | `line`, `surface` |
| `PerpendicularToSurfaceConstraint` | `addPerpendicularToSurface(line, surface)` | `line`, `surface` |
| `OffsetConstraint` | `addOffset2(curves, directionPoint, offset)` | (complex - curves collection) |
| `CircularPatternConstraint` | `addCircularPattern(...)` | (complex - pattern entities) |
| `RectangularPatternConstraint` | `addRectangularPattern(...)` | (complex - pattern entities) |
| `PolygonConstraint` | `addPolygon(...)` | (complex - polygon entities) |

### 25 Total Creation Methods on GeometricConstraints
`addHorizontal`, `addVertical`, `addCollinear`, `addParallel`, `addPerpendicular`,
`addCoincident`, `addCoincidentToSurface`, `addMidPoint`, `addConcentric`, `addEqual`,
`addTangent`, `addSmooth`, `addSymmetry`, `addLineOnPlanarSurface`,
`addLineParallelToPlanarSurface`, `addPerpendicularToSurface`, `addHorizontalPoints`,
`addVerticalPoints`, `addOffset` (retired), `addOffset2`, `addTwoSidesOffset`,
`addPolygon`, `addCircularPattern`, `addRectangularPattern`

Plus input builders: `createCircularPatternInput`, `createRectangularPatternInput`, `createOffsetInput`

---

## 3. Dimension Constraint Types

All derive from `SketchDimension` base class. Accessed via `sketch.sketchDimensions`.

### SketchDimension (Base Class) Properties
| Property | Type | Description |
|----------|------|-------------|
| `value` | float | Current value (cm for distance, radians for angles) |
| `parameter` | Parameter | Associated model parameter (or None) |
| `isDriving` | bool | Get/set driving vs driven mode |
| `isDeletable` | bool | Whether dimension can be deleted |
| `textPosition` | Point3D | Get/set dimension text position |
| `parentSketch` | Sketch | Parent sketch |
| `entityToken` | str | Persistent token |

### SketchDimension (Base Class) Methods
| Method | Returns | Description |
|--------|---------|-------------|
| `deleteMe()` | bool | Delete dimension, returns success |

### Dimension Types (SketchDimensions collection methods)
| Method | Creates | Parameters |
|--------|---------|------------|
| `addDistanceDimension(ptOne, ptTwo, orientation, textPt)` | SketchLinearDimension | Distance between two points/entities |
| `addAngularDimension(lineOne, lineTwo, textPt)` | SketchAngularDimension | Angle between two lines |
| `addDiameterDimension(entity, textPt)` | SketchDiameterDimension | Diameter of circle/arc |
| `addRadialDimension(entity, textPt)` | SketchRadialDimension | Radius of circle/arc |
| `addConcentricCircleDimension(circleOne, circleTwo, textPt)` | SketchConcentricCircleDimension | Between concentric arcs |
| `addOffsetDimension(line, entity, textPt)` | SketchOffsetDimension | Perpendicular distance |
| `addEllipseMajorRadiusDimension(ellipse, textPt)` | SketchEllipseMajorRadiusDimension | Ellipse major radius |
| `addEllipseMinorRadiusDimension(ellipse, textPt)` | SketchEllipseMinorRadiusDimension | Ellipse minor radius |
| `addLinearDiameterDimension(...)` | SketchLinearDiameterDimension | Linear diameter |
| `addDistanceBetweenLineAndPlanarSurfaceDimension(...)` | SketchLinearDimension | Line-to-surface distance |
| `addTangentDistanceDimension(...)` | SketchLinearDimension | Tangent distance |

All `add*` methods accept an optional `isDriving` bool parameter (default True).

---

## 4. Enumerating Constraints Attached to a Specific Entity

**UPDATE (2026-03-20):** The Fusion API *does* provide direct per-entity constraint access via `SketchEntity.geometricConstraints` and `SketchEntity.sketchDimensions`. The full-scan approach below is preserved for reference but is **superseded by the design spec** at `docs/superpowers/specs/2026-03-20-constraint-manager-design.md`. The property mapping table below remains useful for resolving "related entity" from each constraint type.

~~There is no direct API to query "which constraints reference this entity."~~ You can iterate all constraints and check their entity reference properties, but the direct API is preferred:

```python
def find_constraints_for_entity(sketch, target_entity):
    """Find all geometric constraints that reference a specific sketch entity."""
    results = []

    geo = sketch.geometricConstraints
    for i in range(geo.count):
        c = geo.item(i)
        obj_type = c.objectType

        # Check entity reference properties based on constraint type
        references_target = False

        if 'HorizontalConstraint' in obj_type or 'VerticalConstraint' in obj_type:
            references_target = (c.line == target_entity)

        elif 'CoincidentConstraint' in obj_type:
            references_target = (c.point == target_entity or c.entity == target_entity)

        elif 'ParallelConstraint' in obj_type or 'PerpendicularConstraint' in obj_type or 'CollinearConstraint' in obj_type:
            references_target = (c.lineOne == target_entity or c.lineTwo == target_entity)

        elif 'EqualConstraint' in obj_type or 'TangentConstraint' in obj_type or 'SmoothConstraint' in obj_type:
            references_target = (c.curveOne == target_entity or c.curveTwo == target_entity)

        elif 'ConcentricConstraint' in obj_type:
            references_target = (c.entityOne == target_entity or c.entityTwo == target_entity)

        elif 'SymmetryConstraint' in obj_type:
            references_target = (c.entityOne == target_entity or c.entityTwo == target_entity or c.symmetryLine == target_entity)

        elif 'MidPointConstraint' in obj_type:
            references_target = (c.point == target_entity or c.midPointCurve == target_entity)

        elif 'HorizontalPointsConstraint' in obj_type or 'VerticalPointsConstraint' in obj_type:
            references_target = (c.pointOne == target_entity or c.pointTwo == target_entity)

        if references_target:
            results.append(c)

    # Also check dimension constraints
    dims = sketch.sketchDimensions
    for i in range(dims.count):
        d = dims.item(i)
        # Dimension entity references vary by type - check specific subclass properties
        # SketchLinearDimension has entityOne, entityTwo
        # SketchDiameterDimension has entity
        # SketchAngularDimension has lineOne, lineTwo
        # etc.
        # Cast to specific type and check
        results.append(d)  # placeholder - needs type-specific checks

    return results
```

### Entity Comparison Note
Entity comparison in Fusion API uses object identity. Two references to the same entity will be `==` equal. You can also compare `entityToken` strings for persistence across sessions.

---

## 5. Deleting a Constraint Programmatically

```python
# Delete a geometric constraint
constraint = sketch.geometricConstraints.item(0)
if constraint.isDeletable:
    success = constraint.deleteMe()

# Delete a dimension constraint
dim = sketch.sketchDimensions.item(0)
if dim.isDeletable:
    success = dim.deleteMe()
```

### Important Notes
- Always check `isDeletable` first - some constraints are system-generated and cannot be deleted
- `deleteMe()` returns `bool` indicating success
- After `deleteMe()`, the object reference becomes invalid (`isValid` returns False)
- Deleting within a command's execute handler groups deletions into a single undo transaction
- When iterating and deleting, iterate **in reverse** to avoid index shifting:

```python
# Safe deletion pattern - iterate in reverse
geo = sketch.geometricConstraints
for i in range(geo.count - 1, -1, -1):
    c = geo.item(i)
    if some_condition(c) and c.isDeletable:
        c.deleteMe()
```

---

## 6. Highlighting/Selecting Sketch Entities Programmatically

### Option A: Custom Graphics Overlay (Visual Highlighting)
Draw colored overlays on top of existing geometry to visually highlight entities.

```python
# Create a custom graphics group on the root component
root = design.rootComponent
cgGroup = root.customGraphicsGroups.add()

# Highlight a sketch line by drawing a colored line on top
line = sketch.sketchCurves.sketchLines.item(0)
startPt = line.startSketchPoint.geometry
endPt = line.endSketchPoint.geometry

# Create line coordinates (in model space, use sketch.transform if needed)
coords = adsk.fusion.CustomGraphicsCoordinates.create(
    [startPt.x, startPt.y, startPt.z, endPt.x, endPt.y, endPt.z]
)
cgLine = cgGroup.addLines(coords, [0, 1], False)
cgLine.weight = 4  # thicker than original

# Set highlight color (bright yellow)
highlightColor = adsk.fusion.CustomGraphicsSolidColorEffect.create(
    adsk.core.Color.create(255, 255, 0, 255)
)
cgLine.color = highlightColor

# To remove highlighting later:
cgGroup.deleteMe()
```

### Option B: Programmatic Selection
Add entities to the active selection set.

```python
# Using UserInterface.activeSelections
ui = app.userInterface
selections = ui.activeSelections

# Clear and add entities
selections.clear()
selections.add(some_sketch_entity)  # highlights with selection color
```

### Option C: SelectionCommandInput (within a command)
Pre-populate selection inputs with entities.

```python
# In the activate event handler (NOT commandCreated):
class MyActivateHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        cmd = args.command
        sel_input = cmd.commandInputs.itemById('mySelection')
        sel_input.addSelection(some_entity)  # pre-selects and highlights
```

### Custom Graphics Color Effects Summary
| Effect | Use Case |
|--------|----------|
| `CustomGraphicsSolidColorEffect` | Flat color, best for wireframe/lines |
| `CustomGraphicsBasicMaterialColorEffect` | Phong shading with lighting |
| `CustomGraphicsShowThroughColorEffect` | Visible through other geometry (like X-ray) |
| `CustomGraphicsVertexColorEffect` | Per-vertex coloring for gradients |
| `CustomGraphicsAppearanceColorEffect` | Full material appearance |

---

## 7. UI Options for Add-in Panels

### A. Command Dialog (CommandInputs)
Standard modal-ish dialog that appears when running a command. Defined by adding inputs programmatically.

```python
class MyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        cmd = args.command
        inputs = cmd.commandInputs

        # Selection input
        sel = inputs.addSelectionInput('selInput', 'Select Entity', 'Pick something')
        sel.addSelectionFilter('SketchCurves')
        sel.addSelectionFilter('SketchPoints')
        sel.addSelectionFilter('SketchConstraints')
        sel.setSelectionLimits(1, 0)  # min 1, max unlimited

        # Checkbox
        inputs.addBoolValueInput('showAll', 'Show All Constraints', True, '', False)

        # Dropdown
        dd = inputs.addDropDownCommandInput('filterType', 'Filter',
            adsk.core.DropDownStyles.TextListDropDownStyle)
        dd.listItems.add('Geometric', True)
        dd.listItems.add('Dimensional', False)
        dd.listItems.add('All', False)

        # Text/info display
        inputs.addTextBoxCommandInput('info', 'Info', 'Select an entity to see its constraints', 3, True)

        # Value input
        inputs.addValueInput('tolerance', 'Tolerance', 'mm',
            adsk.core.ValueInput.createByReal(0.1))

        # Button row
        btnRow = inputs.addButtonRowCommandInput('actions', 'Actions', False)
        btnRow.listItems.add('Delete Selected', False, '')
        btnRow.listItems.add('Highlight All', False, '')

        # Table
        table = inputs.addTableCommandInput('constraintTable', 'Constraints', 3, '1:2:1')
```

**Available Command Input Types:**
- `SelectionCommandInput` - entity selection with filters
- `BoolValueCommandInput` - checkbox or button
- `ValueCommandInput` - numeric value with units
- `StringValueCommandInput` - text entry
- `TextBoxCommandInput` - read-only or editable text area
- `DropDownCommandInput` - dropdown list (text, checkbox, or icon styles)
- `ButtonRowCommandInput` - row of toggle buttons
- `FloatSliderCommandInput` / `IntegerSliderCommandInput` - sliders
- `FloatSpinnerCommandInput` / `IntegerSpinnerCommandInput` - spinners
- `RadioButtonGroupCommandInput` - radio buttons
- `GroupCommandInput` - collapsible group container
- `TabCommandInput` - tabbed sections
- `TableCommandInput` - table layout
- `ImageCommandInput` - display an image
- `DirectionCommandInput` - 3D direction picker
- `DistanceValueCommandInput` - distance with manipulator
- `AngleValueCommandInput` - angle with manipulator
- `BrowserCommandInput` - embedded HTML browser (like mini palette in a command)
- `SeparatorCommandInput` - visual separator

### B. Palette (Floating HTML Panel)
Full HTML/CSS/JS panel that persists independently of commands. Best for complex UIs.

```python
# Create palette
palette = ui.palettes.add(
    'constraintMgr',           # unique ID
    'Constraint Manager',       # title
    'palette.html',            # HTML file (relative to add-in dir)
    True,                      # isVisible
    True,                      # showCloseButton
    True,                      # isResizable
    400,                       # width
    600,                       # height
    True                       # useNewWebBrowser (True = Qt WebEngine)
)

# Position it
palette.setPosition(100, 100)
palette.dockingState = adsk.core.PaletteDockStateEnum.PaletteDockStateFloating
# Also: PaletteDockStateLeft, PaletteDockStateRight, PaletteDockStateTop, PaletteDockStateBottom

# Communication: Add-in -> HTML
palette.sendInfoToHTML('updateConstraints', json.dumps(constraint_data))

# Communication: HTML -> Add-in
class MyHTMLEventHandler(adsk.core.HTMLEventHandler):
    def notify(self, args):
        htmlArgs = adsk.core.HTMLEventArgs.cast(args)
        action = htmlArgs.action
        data = json.loads(htmlArgs.data)

        if action == 'deleteConstraint':
            # handle deletion
            pass

        htmlArgs.returnData = json.dumps({'status': 'ok'})

palette.incomingFromHTML.add(MyHTMLEventHandler())
```

**JavaScript side (palette.html):**
```javascript
// Receive data from add-in
window.fusionJavaScriptHandler = {
    handle: function(action, data) {
        if (action === 'updateConstraints') {
            renderConstraintList(JSON.parse(data));
        }
        return 'OK';
    }
};

// Send data to add-in (Qt browser - async with Promise)
function deleteConstraint(id) {
    adsk.fusionSendData('deleteConstraint', JSON.stringify({id: id}))
        .then(result => {
            console.log('Result:', result);
        });
}
```

### C. BrowserCommandInput (Inline HTML in Command Dialog)
Embed HTML content directly within a command dialog.

```python
browser = inputs.addBrowserCommandInput('browser', 'Details', 'details.html', 200, 300)
browser.isFullWidth = True
```

Uses the same `fusionJavaScriptHandler` / `adsk.fusionSendData` communication pattern as palettes.

### Palette Lifecycle Notes
- Palettes are deleted when users switch workspaces
- Check `palette.isValid` before using
- Handle `UserInterface.workspacePreActivate` for cleanup
- Enable dev tools via Fusion preferences for debugging HTML

---

## 8. Selection Events

### SelectionCommandInput Setup
```python
sel = inputs.addSelectionInput('entitySelect', 'Entity', 'Select sketch entity')
sel.addSelectionFilter('SketchCurves')
sel.addSelectionFilter('SketchLines')
sel.addSelectionFilter('SketchCircles')
sel.addSelectionFilter('SketchPoints')
sel.setSelectionLimits(0, 0)  # 0 min, 0 max = optional & unlimited
```

### Selection Filter Strings (Sketch-Relevant)
- `SketchCurves` - all sketch curves
- `SketchLines` - sketch lines only
- `SketchCircles` - circles only
- `SketchPoints` - sketch points
- `SketchConstraints` - geometric constraints
- `Sketches` - entire sketches
- `Profiles` - enclosed sketch profiles
- `Texts` - sketch text entities

### Full Selection Filter List
Bodies, SolidBodies, SurfaceBodies, MeshBodies, Faces, SolidFaces, SurfaceFaces, PlanarFaces,
CylindricalFaces, ConicalFaces, SphericalFaces, ToroidalFaces, SplineFaces, Edges, LinearEdges,
CircularEdges, EllipticalEdges, TangentEdges, NonTangentEdges, Vertices, RootComponents,
Occurrences, Sketches, SketchConstraints, Profiles, Texts, SketchCurves, SketchLines,
SketchCircles, SketchPoints, ConstructionPoints, ConstructionLines, ConstructionPlanes,
Features, Canvases, Decals, JointOrigins, Joints

### Command Events for Selection Handling

```python
class MyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        cmd = args.command
        inputs = cmd.commandInputs

        # Selection input
        sel = inputs.addSelectionInput('sel', 'Select', 'Pick entity')
        sel.addSelectionFilter('SketchCurves')
        sel.setSelectionLimits(1, 1)

        # Connect all relevant event handlers
        cmd.inputChanged.add(MyInputChangedHandler())       # fires when any input changes
        cmd.selectionEvent.add(MySelectionHandler())         # DEPRECATED in newer API
        cmd.preSelect.add(MyPreSelectHandler())              # fires on hover before selection
        cmd.preSelectMouseMove.add(MyPreSelectMoveHandler()) # fires on mouse move during preselect
        cmd.select.add(MySelectHandler())                    # fires when entity is selected
        cmd.unselect.add(MyUnselectHandler())                # fires when entity is unselected
        cmd.executePreview.add(MyPreviewHandler())           # fires for preview updates
        cmd.execute.add(MyExecuteHandler())                  # fires on OK/confirm
        cmd.destroy.add(MyDestroyHandler())                  # fires on command end

# PreSelect handler - filter what CAN be selected
class MyPreSelectHandler(adsk.core.SelectionEventHandler):
    def notify(self, args):
        eventArgs = adsk.core.SelectionEventArgs.cast(args)
        selected_entity = eventArgs.selection.entity

        # Reject entities that don't meet criteria
        if not isinstance(selected_entity, adsk.fusion.SketchLine):
            eventArgs.isSelectable = False

# Select handler - react AFTER selection
class MySelectHandler(adsk.core.SelectionEventHandler):
    def notify(self, args):
        eventArgs = adsk.core.SelectionEventArgs.cast(args)
        entity = eventArgs.selection.entity
        # Update UI, show constraint info, etc.

# InputChanged handler - fires when selection count changes
class MyInputChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        eventArgs = adsk.core.InputChangedEventArgs.cast(args)
        changed_input = eventArgs.input

        if changed_input.id == 'sel':
            sel_input = adsk.core.SelectionCommandInput.cast(changed_input)
            if sel_input.selectionCount > 0:
                entity = sel_input.selection(0).entity
                # Do something with selected entity

# Execute handler
class MyExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)
        cmd = eventArgs.command
        sel_input = cmd.commandInputs.itemById('sel')

        for i in range(sel_input.selectionCount):
            entity = sel_input.selection(i).entity
            # Process selections
```

### SelectionCommandInput Key Methods
| Method | Description |
|--------|-------------|
| `addSelectionFilter(filterStr)` | Add allowed entity type filter |
| `setSelectionLimits(min, max)` | Set required selection count (0 max = unlimited) |
| `addSelection(entity)` | Programmatically add entity (NOT in commandCreated - use activate) |
| `clearSelection()` | Remove all selections |
| `selection(index)` | Get Selection object at index |
| `selectionCount` | Current number of selected entities |
| `hasFocus` | Get/set whether this input receives selections |
| `tooltip` | Get/set tooltip text |

### Selection Object Properties
The `selection(index)` method returns a `Selection` object with:
- `entity` - the selected entity
- `point` - the 3D point where the user clicked

---

## Architecture Recommendations for a Constraint Manager Add-in

### Approach 1: Command-Based (Simpler)
- Single command with SelectionCommandInput for entity picking
- TextBoxCommandInput or TableCommandInput to display constraint list
- InputChanged handler to update the constraint list when selection changes
- Execute handler to perform delete/modify operations
- Custom graphics for visual highlighting of related constraints

### Approach 2: Palette-Based (Richer UI)
- HTML palette with full constraint browser/editor UI
- SelectionEventHandler on the document to detect what the user selects
- Two-way communication: Fusion tells palette what's selected, palette tells Fusion what to delete
- Custom graphics for visual overlays
- Persists while user works - doesn't block other operations

### Approach 3: Hybrid
- Palette for the constraint list/management UI
- Commands for specific operations (delete, select similar, etc.)
- Custom graphics for persistent visual feedback
- BrowserCommandInput for inline details in command dialogs

### Key Technical Constraints
1. **No direct "constraints for entity" query** - must iterate all constraints and check references
2. **Entity comparison** works with `==` operator
3. **Custom graphics** are on the Component, not the Sketch - need coordinate transform (`sketch.transform`)
4. **Palette HTML** can be a URL or local file relative to add-in directory
5. **Qt WebEngine** (useNewWebBrowser=True) uses async Promises; older CEF is synchronous
6. **Workspace switching** invalidates palettes - need recreation logic
