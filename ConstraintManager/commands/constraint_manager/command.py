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
CMD_VERSION = "1.1"
CMD_NAME = "Constraint Manager"
CMD_DESC = "View and delete constraints on sketch entities"
PANEL_ID = "SolidScriptsAddinsPanel"  # DESIGN workspace utilities panel

# Module-level state shared between handlers
_current_constraints = []


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

            # Entity selection input — multiple entities allowed
            entity_select = inputs.addSelectionInput(
                "entitySelect", "Select Entities", "Click sketch entities"
            )
            entity_select.addSelectionFilter("SketchCurves")
            entity_select.addSelectionFilter("SketchPoints")
            entity_select.setSelectionLimits(0, 0)  # 0 max = unlimited
            entity_select.isUseCurrentSelections = False

            # Constraint table — 4 columns: checkbox, entity, type, related
            table = inputs.addTableCommandInput(
                "constraintTable", "Constraints", 4, "1:3:3:3"
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
    """Handles entity selection changes, checkbox toggles, and Select All."""

    _handling_change = False

    def notify(self, args):
        if self._handling_change:
            return
        self._handling_change = True
        try:
            changed_input = args.input
            inputs = args.inputs

            if changed_input.id == "entitySelect":
                self._on_selection_changed(inputs)
            elif changed_input.id == "selectAllBtn":
                self._on_select_all(inputs)
                changed_input.value = False
        except:
            _log.error("InputChanged error: %s", traceback.format_exc())
        finally:
            self._handling_change = False

    def _on_selection_changed(self, inputs):
        """Rebuild the constraint table for all selected entities."""
        global _current_constraints
        entity_select = inputs.itemById("entitySelect")
        table = inputs.itemById("constraintTable")

        # Clear existing table rows
        for i in range(table.rowCount - 1, -1, -1):
            table.deleteRow(i)

        # Hide old "no constraints" message
        old_msg = inputs.itemById("noConstraints")
        if old_msg:
            old_msg.isVisible = False

        if entity_select.selectionCount == 0:
            _current_constraints = []
            return

        # Enumerate constraints across all selected entities, deduplicate by token
        all_infos = []
        seen_tokens = set()
        for sel_idx in range(entity_select.selectionCount):
            entity = entity_select.selection(sel_idx).entity
            entity_index = _find_entity_index(entity)
            entity_label = constraint_engine.get_entity_label(entity, entity_index)

            infos = constraint_engine.enumerate_constraints(
                entity, index_finder=_find_entity_index
            )
            for info in infos:
                token = info.get("entity_token")
                if token and token in seen_tokens:
                    continue  # Skip duplicate constraint
                if token:
                    seen_tokens.add(token)
                info["source_label"] = entity_label
                all_infos.append(info)

        if not all_infos:
            _current_constraints = []
            msg = inputs.itemById("noConstraints")
            if not msg:
                msg = inputs.addTextBoxCommandInput(
                    "noConstraints", "", "No constraints found", 1, True
                )
            msg.isVisible = True
            return

        # Column headers
        row_inputs = adsk.core.CommandInputs.cast(table.commandInputs)
        hdr_cb = row_inputs.addStringValueInput("hdr_cb", "", "")
        hdr_cb.isReadOnly = True
        hdr_entity = row_inputs.addStringValueInput("hdr_entity", "", "Entity")
        hdr_entity.isReadOnly = True
        hdr_type = row_inputs.addStringValueInput("hdr_type", "", "Type")
        hdr_type.isReadOnly = True
        hdr_related = row_inputs.addStringValueInput("hdr_related", "", "Related To")
        hdr_related.isReadOnly = True
        table.addCommandInput(hdr_cb, 0, 0)
        table.addCommandInput(hdr_entity, 0, 1)
        table.addCommandInput(hdr_type, 0, 2)
        table.addCommandInput(hdr_related, 0, 3)

        # Populate table rows: checkbox | entity | type | related
        for i, info in enumerate(all_infos):
            row = i + 1  # offset by header row
            row_inputs = adsk.core.CommandInputs.cast(table.commandInputs)

            cb = row_inputs.addBoolValueInput(
                f"check_{i}", "", True, "", False
            )
            cb.isEnabled = info["is_deletable"]

            # Source entity column
            entity_input = row_inputs.addStringValueInput(
                f"entity_{i}", "", info["source_label"]
            )
            entity_input.isReadOnly = True

            # Type column
            type_display = info["type_name"]
            if not info["is_deletable"]:
                type_display = f"\U0001F512 {type_display}"
            type_input = row_inputs.addStringValueInput(
                f"type_{i}", "", type_display
            )
            type_input.isReadOnly = True

            # Related entity column
            related_display = info["related_label"]
            if not info["is_deletable"] and related_display != "--":
                related_display = f"{related_display} (locked)"
            related_input = row_inputs.addStringValueInput(
                f"related_{i}", "", related_display
            )
            related_input.isReadOnly = True

            table.addCommandInput(cb, row, 0)
            table.addCommandInput(entity_input, row, 1)
            table.addCommandInput(type_input, row, 2)
            table.addCommandInput(related_input, row, 3)

        _current_constraints = all_infos

    def _on_select_all(self, inputs):
        """Check all deletable constraint checkboxes (skip header row)."""
        table = inputs.itemById("constraintTable")
        if not table or table.rowCount < 2:
            return
        for i in range(1, table.rowCount):  # Skip row 0 (header)
            cb = table.getInputAtPosition(i, 0)
            if cb and hasattr(cb, "value") and cb.isEnabled:
                cb.value = True


class ExecuteHandler(adsk.core.CommandEventHandler):
    """Performs deletion of checked constraints when Delete Selected is clicked.

    Re-resolves constraints from entityToken via Design.findEntityByToken().
    """

    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs
            table = inputs.itemById("constraintTable")

            constraints = _current_constraints
            if not constraints or not table:
                return

            # Collect tokens of checked constraints (skip row 0 = header)
            tokens_to_delete = []
            for i in range(1, table.rowCount):
                cb = table.getInputAtPosition(i, 0)
                if cb and hasattr(cb, "value") and cb.value:
                    constraint_idx = i - 1  # offset for header row
                    if constraint_idx < len(constraints):
                        token = constraints[constraint_idx].get("entity_token")
                        if token:
                            tokens_to_delete.append(token)

            if not tokens_to_delete:
                return

            # Re-resolve constraints from tokens and delete
            design = adsk.fusion.Design.cast(_app.activeProduct)
            if not design:
                return

            deleted = 0
            failed = 0
            for token in tokens_to_delete:
                try:
                    matches = design.findEntityByToken(token)
                    if not matches or len(matches) == 0:
                        failed += 1
                        continue
                    entity = matches[0]
                    if hasattr(entity, "isDeletable") and entity.isDeletable:
                        entity.deleteMe()
                        deleted += 1
                except Exception as e:
                    _log.error("Failed to delete constraint: %s", e)
                    failed += 1

            _log.info("Deleted %d, failed %d", deleted, failed)

        except:
            _log.error("Execute error: %s", traceback.format_exc())


class DestroyHandler(adsk.core.CommandEventHandler):
    """Fires when command is destroyed — clean up handler references."""

    def notify(self, args):
        global _cmd_handlers, _current_constraints
        _cmd_handlers = []
        _current_constraints = []


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
