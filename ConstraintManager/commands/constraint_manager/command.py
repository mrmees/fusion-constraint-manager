"""Command definition and event handlers for the Constraint Manager."""

import adsk.core
import adsk.fusion
import traceback
import logging

from . import constraint_engine

_log = logging.getLogger(__name__)

_app = None
_ui = None

# Module-level list — prevents GC of command-instance handlers
_cmd_handlers = []

# Add-in lifetime handlers (commandCreated)
_addin_handlers = []

# Command identifiers
CMD_ID = "constraintManagerCmd"
CMD_VERSION = "0.7"
CMD_NAME = f"Constraint Manager v{CMD_VERSION}"
CMD_DESC = "View and delete constraints on sketch entities"
PANEL_ID = "SolidScriptsAddinsPanel"  # DESIGN workspace utilities panel


def start(app, ui):
    """Register the command definition and add a toolbar button."""
    global _app, _ui
    _app = app
    _ui = ui

    # Clean up any existing definition (dev reload)
    existing = ui.commandDefinitions.itemById(CMD_ID)
    if existing:
        existing.deleteMe()

    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID, CMD_NAME, CMD_DESC,
        "./resources/constraint_manager"
    )

    created_handler = CommandCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    _addin_handlers.append(created_handler)

    # Add to the DESIGN workspace panel
    design_ws = ui.workspaces.itemById("FusionSolidEnvironment")
    if design_ws:
        panel = design_ws.toolbarPanels.itemById(PANEL_ID)
        if panel:
            existing_ctrl = panel.controls.itemById(CMD_ID)
            if not existing_ctrl:
                panel.controls.addCommand(cmd_def)


def stop():
    """Remove toolbar button and command definition."""
    global _addin_handlers, _cmd_handlers
    try:
        design_ws = _ui.workspaces.itemById("FusionSolidEnvironment")
        if design_ws:
            panel = design_ws.toolbarPanels.itemById(PANEL_ID)
            if panel:
                ctrl = panel.controls.itemById(CMD_ID)
                if ctrl:
                    ctrl.deleteMe()

        cmd_def = _ui.commandDefinitions.itemById(CMD_ID)
        if cmd_def:
            cmd_def.deleteMe()
    except:
        _log.error("Error during stop: %s", traceback.format_exc())

    _addin_handlers = []
    _cmd_handlers = []


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    """Fires when the user clicks the Constraint Manager button."""

    def notify(self, args):
        try:
            cmd = args.command
            # OK = perform deletion, Cancel = close without deleting
            cmd.okButtonText = "Delete Selected"

            # Verify active sketch edit mode
            design = adsk.fusion.Design.cast(_app.activeProduct)
            if not design or not isinstance(
                design.activeEditObject, adsk.fusion.Sketch
            ):
                _ui.messageBox(
                    "Constraint Manager requires an active sketch.\n"
                    "Enter sketch edit mode first."
                )
                return

            inputs = cmd.commandInputs

            # Entity selection input
            entity_select = inputs.addSelectionInput(
                "entitySelect", "Select Entity", "Click a sketch entity"
            )
            entity_select.addSelectionFilter("SketchCurves")
            entity_select.addSelectionFilter("SketchPoints")
            entity_select.setSelectionLimits(0, 1)
            entity_select.isUseCurrentSelections = False

            # Constraint table
            table = inputs.addTableCommandInput(
                "constraintTable", "Constraints", 3, "1:4:4"
            )
            table.maximumVisibleRows = 15
            table.minimumVisibleRows = 6
            table.isEnabled = True

            # Select All button
            sel_all = inputs.addBoolValueInput(
                "selectAllBtn", "Select All", False, "", False
            )
            sel_all.isFullWidth = True

            # Wire command-instance event handlers
            input_changed = InputChangedHandler()
            cmd.inputChanged.add(input_changed)
            _cmd_handlers.append(input_changed)

            pre_select = PreSelectHandler()
            cmd.preSelect.add(pre_select)
            _cmd_handlers.append(pre_select)

            execute = ExecuteHandler()
            cmd.execute.add(execute)
            _cmd_handlers.append(execute)

            destroy = DestroyHandler()
            cmd.destroy.add(destroy)
            _cmd_handlers.append(destroy)

        except:
            _ui.messageBox(f"CommandCreated error:\n{traceback.format_exc()}")


class PreSelectHandler(adsk.core.SelectionEventHandler):
    """Validates entity hover — only allow supported sketch curves/points in active sketch."""

    _SUPPORTED_TYPES = {
        "SketchLine", "SketchArc", "SketchCircle", "SketchEllipse",
        "SketchFittedSpline", "SketchPoint",
    }

    def notify(self, args):
        try:
            selection = args.selection
            entity = selection.entity

            design = adsk.fusion.Design.cast(_app.activeProduct)
            if not design:
                args.isSelectable = False
                return

            active_sketch = design.activeEditObject
            if not isinstance(active_sketch, adsk.fusion.Sketch):
                args.isSelectable = False
                return

            if hasattr(entity, "parentSketch"):
                if entity.parentSketch != active_sketch:
                    args.isSelectable = False
                    return

            entity_type = entity.objectType.split("::")[-1]
            if entity_type not in self._SUPPORTED_TYPES:
                args.isSelectable = False
        except:
            pass


class InputChangedHandler(adsk.core.InputChangedEventHandler):
    """Handles entity selection changes, checkbox toggles, and Select All.

    No model changes here — just UI updates. Deletion happens in execute.
    """

    _handling_change = False
    _current_constraints = []

    def notify(self, args):
        if self._handling_change:
            return
        self._handling_change = True
        try:
            changed_input = args.input
            inputs = args.inputs

            if changed_input.id == "entitySelect":
                self._on_entity_changed(inputs)
            elif changed_input.id == "selectAllBtn":
                self._on_select_all(inputs)
                changed_input.value = False
            elif changed_input.id.startswith("check_"):
                pass  # Checkboxes just toggle, no action needed
        except:
            _log.error("InputChanged error: %s", traceback.format_exc())
        finally:
            self._handling_change = False

    def _on_entity_changed(self, inputs):
        """Rebuild the constraint table for the newly selected entity."""
        entity_select = inputs.itemById("entitySelect")
        table = inputs.itemById("constraintTable")

        # Clear existing table rows
        for i in range(table.rowCount - 1, -1, -1):
            table.deleteRow(i)

        if entity_select.selectionCount == 0:
            self._current_constraints = []
            return

        selected = entity_select.selection(0).entity
        self._populate_table(inputs, selected)

    def _populate_table(self, inputs, selected):
        """Enumerate constraints for an entity and fill the table."""
        table = inputs.itemById("constraintTable")

        infos = constraint_engine.enumerate_constraints(
            selected, index_finder=_find_entity_index
        )

        # Handle "no constraints" message
        old_msg = inputs.itemById("noConstraints")
        if old_msg:
            old_msg.isVisible = False

        if not infos:
            self._current_constraints = []
            msg = inputs.itemById("noConstraints")
            if not msg:
                msg = inputs.addTextBoxCommandInput(
                    "noConstraints", "", "No constraints found", 1, True
                )
            msg.isVisible = True
            return

        # Populate table rows
        for i, info in enumerate(infos):
            row_inputs = adsk.core.CommandInputs.cast(table.commandInputs)

            cb = row_inputs.addBoolValueInput(
                f"check_{i}", "", True, "", False
            )
            cb.isEnabled = info["is_deletable"]

            type_display = info["type_name"]
            if not info["is_deletable"]:
                type_display = f"\U0001F512 {type_display}"
            type_input = row_inputs.addStringValueInput(
                f"type_{i}", "", type_display
            )
            type_input.isReadOnly = True

            related_display = info["related_label"]
            if not info["is_deletable"] and related_display != "--":
                related_display = f"{related_display} (locked)"
            related_input = row_inputs.addStringValueInput(
                f"related_{i}", "", related_display
            )
            related_input.isReadOnly = True

            table.addCommandInput(cb, i, 0)
            table.addCommandInput(type_input, i, 1)
            table.addCommandInput(related_input, i, 2)

        self._current_constraints = infos

    def _on_select_all(self, inputs):
        """Check all deletable constraint checkboxes."""
        table = inputs.itemById("constraintTable")
        if not table:
            return
        for i in range(table.rowCount):
            cb = table.getInputAtPosition(i, 0)
            if cb and cb.isEnabled:
                cb.value = True


class ExecuteHandler(adsk.core.CommandEventHandler):
    """Performs deletion of checked constraints when OK/Delete Selected is clicked.

    This is the proper place for model changes in Fusion's command lifecycle.
    """

    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs
            table = inputs.itemById("constraintTable")

            constraints = InputChangedHandler._current_constraints
            if not constraints or not table:
                return

            # Collect checked constraints
            to_delete = []
            for i in range(table.rowCount):
                cb = table.getInputAtPosition(i, 0)
                if cb and cb.value:
                    to_delete.append(constraints[i]["constraint"])

            if not to_delete:
                return

            result = constraint_engine.delete_constraints(to_delete)
            _log.info(
                "Deleted %d, failed %d, skipped %d",
                result["deleted"], result["failed"], result["skipped"],
            )

        except:
            _log.error("Execute error: %s", traceback.format_exc())


class DestroyHandler(adsk.core.CommandEventHandler):
    """Fires when command is destroyed — clean up handler references."""

    def notify(self, args):
        global _cmd_handlers
        _cmd_handlers = []


def _find_entity_index(entity):
    """Find the index of an entity within its parent sketch collection.

    Returns 0 if the entity type isn't recognized or lookup fails.
    """
    try:
        sketch = entity.parentSketch
        obj_type = entity.objectType.split("::")[-1]

        collection = None
        if obj_type == "SketchLine":
            collection = sketch.sketchCurves.sketchLines
        elif obj_type == "SketchArc":
            collection = sketch.sketchCurves.sketchArcs
        elif obj_type == "SketchCircle":
            collection = sketch.sketchCurves.sketchCircles
        elif obj_type == "SketchEllipse":
            collection = sketch.sketchCurves.sketchEllipses
        elif obj_type == "SketchFittedSpline":
            collection = sketch.sketchCurves.sketchFittedSplines
        elif obj_type == "SketchPoint":
            collection = sketch.sketchPoints

        if collection:
            for i in range(collection.count):
                if collection.item(i) == entity:
                    return i
    except Exception as e:
        _log.warning("Could not determine entity index: %s", e)

    return 0
