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
CMD_NAME = "Constraint Manager"
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
            cmd.isOKButtonVisible = False
            cmd.cancelButtonText = "Close"

            # Verify active sketch edit mode
            design = adsk.fusion.Design.cast(_app.activeProduct)
            if not design or not isinstance(
                design.activeEditObject, adsk.fusion.Sketch
            ):
                _ui.messageBox(
                    "Constraint Manager requires an active sketch.\n"
                    "Enter sketch edit mode first."
                )
                args.command.doExecute(True)
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
                "constraintTable", "Constraints", 3, "1:3:3"
            )
            table.maximumVisibleRows = 10
            table.isEnabled = True

            # Delete toolbar button on table (starts disabled)
            del_btn = inputs.addBoolValueInput(
                "deleteBtn", "Delete Selected", False, "", False
            )
            del_btn.isEnabled = False
            table.addToolbarCommandInput(del_btn)

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
    """Handles entity selection changes, checkbox toggles, and delete button."""

    _handling_change = False

    def notify(self, args):
        if self._handling_change:
            return
        self._handling_change = True
        try:
            changed_input = args.input
            inputs = args.inputs

            if changed_input.id == "entitySelect":
                self._on_entity_changed(inputs)
            elif changed_input.id == "deleteBtn":
                self._on_delete(inputs)
                changed_input.value = False
            elif changed_input.id.startswith("check_"):
                self._update_delete_state(inputs)
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
            self._update_delete_state(inputs)
            return

        selected = entity_select.selection(0).entity

        # Enumerate constraints
        infos = constraint_engine.enumerate_constraints(
            selected, index_finder=_find_entity_index
        )

        if not infos:
            self._current_constraints = []
            msg = inputs.addStringValueInput(
                "noConstraints", "", "No constraints found"
            )
            msg.isReadOnly = True
            table.addCommandInput(msg, 0, 0)
            self._update_delete_state(inputs)
            return

        # Populate table rows
        for i, info in enumerate(infos):
            row_inputs = adsk.core.CommandInputs.cast(table.commandInputs)

            # Checkbox (disabled if not deletable)
            cb = row_inputs.addBoolValueInput(
                f"check_{i}", "", True, "", False
            )
            cb.isEnabled = info["is_deletable"]

            # Type name (with lock indicator for non-deletable)
            type_display = info["type_name"]
            if not info["is_deletable"]:
                type_display = f"\U0001F512 {type_display}"
            type_input = row_inputs.addStringValueInput(
                f"type_{i}", "", type_display
            )
            type_input.isReadOnly = True

            # Related entity label
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
        self._update_delete_state(inputs)

    def _update_delete_state(self, inputs):
        """Enable/disable delete button based on whether any rows are checked."""
        del_btn = inputs.itemById("deleteBtn")
        table = inputs.itemById("constraintTable")
        if not del_btn or not table:
            return
        any_checked = False
        for i in range(table.rowCount):
            cb = table.getInputAtPosition(i, 0)
            if cb and hasattr(cb, "value") and cb.value:
                any_checked = True
                break
        del_btn.isEnabled = any_checked

    def _on_delete(self, inputs):
        """Delete checked constraints and refresh the table."""
        table = inputs.itemById("constraintTable")

        if not hasattr(self, "_current_constraints") or not self._current_constraints:
            return

        # Collect checked constraints
        to_delete = []
        for i in range(table.rowCount):
            cb_input = table.getInputAtPosition(i, 0)
            if cb_input and cb_input.value:
                to_delete.append(self._current_constraints[i]["constraint"])

        if not to_delete:
            return

        # Delete
        result = constraint_engine.delete_constraints(to_delete)
        _log.info(
            "Deleted %d, failed %d, skipped %d",
            result["deleted"], result["failed"], result["skipped"],
        )

        # Check if selected entity is still valid after deletion
        entity_select = inputs.itemById("entitySelect")
        if entity_select.selectionCount > 0:
            selected = entity_select.selection(0).entity
            if hasattr(selected, "isValid") and not selected.isValid:
                entity_select.clearSelection()

        # Refresh table
        self._on_entity_changed(inputs)


class ExecuteHandler(adsk.core.CommandEventHandler):
    """Fires on OK/Close — clean up."""

    def notify(self, args):
        pass


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
