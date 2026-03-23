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
CMD_VERSION = "2.0"
CMD_NAME = "Constraint Manager"
CMD_DESC = "View and delete constraints on sketch entities"
PANEL_ID = "SolidScriptsAddinsPanel"  # DESIGN workspace utilities panel

# Per-tab state (D-05: per-tab isolation)
_tab_state = {
    "selected": {
        "constraints": [],      # List of constraint info dicts
    },
    "types": {
        "summary": {},          # {type_name: count}
        "pending_delete": None, # Type name awaiting deletion
    },
    "all": {
        "constraints": [],      # List of constraint info dicts — Phase 3
        "loaded": False,        # Whether Load has been clicked — Phase 3
    },
}
_active_tab = "tab_selected"


def _wire_handler(event, handler_class, handler_list):
    """Create handler, add to event, store reference to prevent GC."""
    handler = handler_class()
    event.add(handler)
    handler_list.append(handler)
    return handler


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


def _populate_types_tab(inputs):
    """Populate the Constraint Types table with type counts from active sketch."""
    try:
        # Navigate to types tab inputs (Phase 1 bugfix pattern: fallback if already scoped)
        tab_types = inputs.itemById("tab_types")
        if tab_types:
            types_inputs = tab_types.children
        else:
            types_inputs = inputs

        table = types_inputs.itemById("typesTable")
        empty_msg = types_inputs.itemById("typesEmpty")
        status_msg = types_inputs.itemById("typesStatus")
        delete_btn = types_inputs.itemById("deleteTypeBtn")

        # Clear existing rows (reverse iteration)
        for i in range(table.rowCount - 1, -1, -1):
            table.deleteRow(i)

        # Clear any pending delete from previous populate
        _tab_state["types"]["pending_delete"] = None
        if status_msg:
            status_msg.formattedText = ""
            status_msg.isVisible = False

        # Get active sketch and aggregate
        design = adsk.fusion.Design.cast(_app.activeProduct)
        if not design:
            return
        sketch = design.activeEditObject
        if not isinstance(sketch, adsk.fusion.Sketch):
            return

        summary = constraint_engine.aggregate_constraint_types(
            sketch.geometricConstraints
        )
        _tab_state["types"]["summary"] = summary

        # Empty state (D-07)
        if not summary:
            if empty_msg:
                empty_msg.isVisible = True
            table.isVisible = False
            if delete_btn:
                delete_btn.isVisible = False
            return

        if empty_msg:
            empty_msg.isVisible = False
        table.isVisible = True
        if delete_btn:
            delete_btn.isVisible = True

        # Unique ID counter to avoid duplicate input IDs on re-populate
        counter = _tab_state["types"].get("row_counter", 0)
        _tab_state["types"]["row_counter"] = counter + 1

        row_inputs = adsk.core.CommandInputs.cast(table.commandInputs)

        # Header row
        hdr_type = row_inputs.addStringValueInput(
            f"thdr_type_{counter}", "", "Type"
        )
        hdr_type.isReadOnly = True
        hdr_count = row_inputs.addStringValueInput(
            f"thdr_count_{counter}", "", "Count"
        )
        hdr_count.isReadOnly = True
        table.addCommandInput(hdr_type, 0, 0)
        table.addCommandInput(hdr_count, 0, 1)

        # Data rows (sorted alphabetically by type name)
        for i, (type_name, count) in enumerate(sorted(summary.items())):
            row = i + 1
            row_inputs = adsk.core.CommandInputs.cast(table.commandInputs)
            name_input = row_inputs.addStringValueInput(
                f"tname_{counter}_{i}", "", type_name
            )
            name_input.isReadOnly = True
            count_input = row_inputs.addStringValueInput(
                f"tcount_{counter}_{i}", "", str(count)
            )
            count_input.isReadOnly = True
            table.addCommandInput(name_input, row, 0)
            table.addCommandInput(count_input, row, 1)

    except:
        _log.error("Error populating types tab: %s", traceback.format_exc())


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

            # Create three tabs — first tab is active by default (D-02, ENTY-02)
            tab_selected = inputs.addTabCommandInput("tab_selected", "Selected")
            tab_types = inputs.addTabCommandInput("tab_types", "Types")
            tab_all = inputs.addTabCommandInput("tab_all", "All")

            # --- Selected Entities tab (D-11: migrate v1.1 inputs into tab children) ---
            sel_inputs = tab_selected.children

            entity_select = sel_inputs.addSelectionInput(
                "entitySelect", "Select Entities", "Click sketch entities"
            )
            entity_select.addSelectionFilter("SketchCurves")
            entity_select.addSelectionFilter("SketchPoints")
            entity_select.setSelectionLimits(0, 0)  # 0 max = unlimited
            entity_select.isUseCurrentSelections = False

            table = sel_inputs.addTableCommandInput(
                "constraintTable", "Constraints", 4, "1:3:3:3"
            )
            table.maximumVisibleRows = 15
            table.minimumVisibleRows = 6
            table.isEnabled = True

            sel_all = sel_inputs.addBoolValueInput(
                "selectAllBtn", "Select All", False, "", False
            )
            sel_all.isFullWidth = True

            # --- Types tab (Phase 2) ---
            types_inputs = tab_types.children

            types_table = types_inputs.addTableCommandInput(
                "typesTable", "Constraint Types", 2, "3:1"
            )
            types_table.maximumVisibleRows = 15
            types_table.minimumVisibleRows = 4

            # Toolbar delete button (D-03: acts on selectedRow)
            delete_type_btn = types_inputs.addBoolValueInput(
                "deleteTypeBtn", "Delete All of Type", False, "", False
            )
            types_table.addToolbarCommandInput(delete_type_btn)

            # Status message for pending delete action
            types_inputs.addTextBoxCommandInput("typesStatus", "", "", 1, True)

            # Empty state (D-07: shown when sketch has zero constraints)
            types_empty = types_inputs.addTextBoxCommandInput(
                "typesEmpty", "", "No constraints in this sketch", 1, True
            )
            types_empty.isVisible = False

            # --- All tab placeholder (D-03) ---
            all_inputs = tab_all.children
            all_inputs.addTextBoxCommandInput(
                "allPlaceholder", "", "Full constraint list will appear here.", 1, True
            )

            # Wire command-instance event handlers (D-06)
            _wire_handler(cmd.inputChanged, InputChangedHandler, _cmd_handlers)
            _wire_handler(cmd.preSelect, PreSelectHandler, _cmd_handlers)
            _wire_handler(cmd.execute, ExecuteHandler, _cmd_handlers)
            _wire_handler(cmd.destroy, DestroyHandler, _cmd_handlers)

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
            global _active_tab
            changed_input = args.input
            inputs = args.inputs

            # Tab switch events — update active tab tracker (D-07)
            if changed_input.objectType.endswith("TabCommandInput"):
                if changed_input.isActive:
                    _active_tab = changed_input.id
                    # Auto-populate Types tab on switch (D-02)
                    if changed_input.id == "tab_types":
                        _populate_types_tab(inputs)
                return

            # Route to active tab's handler (TABS-02: no re-enumeration on switch)
            if _active_tab == "tab_selected":
                self._handle_selected_input(changed_input, inputs)
            elif _active_tab == "tab_types":
                self._handle_types_input(changed_input, inputs)
        except:
            _log.error("InputChanged error: %s", traceback.format_exc())
        finally:
            self._handling_change = False

    def _handle_selected_input(self, changed_input, inputs):
        """Route inputs for the Selected Entities tab."""
        if changed_input.id == "entitySelect":
            self._on_selection_changed(inputs)
        elif changed_input.id == "selectAllBtn":
            self._on_select_all(inputs)
            changed_input.value = False

    def _handle_types_input(self, changed_input, inputs):
        """Route inputs for the Constraint Types tab."""
        if changed_input.id != "deleteTypeBtn":
            return

        # Reset button value immediately
        changed_input.value = False

        # Navigate to types tab (Phase 1 fallback pattern)
        tab_types = inputs.itemById("tab_types")
        if tab_types:
            types_inputs = tab_types.children
        else:
            types_inputs = inputs

        table = types_inputs.itemById("typesTable")
        status_msg = types_inputs.itemById("typesStatus")

        if not table:
            return

        selected_row = table.selectedRow
        # Row 0 is header, -1 means no selection
        if selected_row <= 0:
            if status_msg:
                status_msg.formattedText = "Select a constraint type row first."
                status_msg.isVisible = True
            return

        # Extract type name from selected row, column 0
        type_name_input = table.getInputAtPosition(selected_row, 0)
        if not type_name_input:
            return
        type_name = type_name_input.value

        # Look up count from cached summary
        summary = _tab_state["types"].get("summary", {})
        count = summary.get(type_name, "?")

        # Store pending delete for ExecuteHandler
        _tab_state["types"]["pending_delete"] = type_name

        # Show status message
        if status_msg:
            status_msg.formattedText = (
                f"Ready to delete all <b>{count}</b> <b>{type_name}</b> "
                f"constraints. Click 'Delete Selected' to confirm."
            )
            status_msg.isVisible = True

    def _on_selection_changed(self, inputs):
        """Rebuild the constraint table for all selected entities."""
        # args.inputs may be root CommandInputs or tab children depending on
        # Fusion version — handle both by checking for the tab first
        tab_selected = inputs.itemById("tab_selected")
        if tab_selected:
            sel_inputs = tab_selected.children
        else:
            sel_inputs = inputs  # already inside the tab
        entity_select = sel_inputs.itemById("entitySelect")
        table = sel_inputs.itemById("constraintTable")

        # Clear existing table rows
        for i in range(table.rowCount - 1, -1, -1):
            table.deleteRow(i)

        # Hide old "no constraints" message
        old_msg = sel_inputs.itemById("noConstraints")
        if old_msg:
            old_msg.isVisible = False

        if entity_select.selectionCount == 0:
            _tab_state["selected"]["constraints"] = []
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
            _tab_state["selected"]["constraints"] = []
            msg = sel_inputs.itemById("noConstraints")
            if not msg:
                msg = sel_inputs.addTextBoxCommandInput(
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

        _tab_state["selected"]["constraints"] = all_infos

    def _on_select_all(self, inputs):
        """Check all deletable constraint checkboxes (skip header row)."""
        tab_selected = inputs.itemById("tab_selected")
        if tab_selected:
            sel_inputs = tab_selected.children
        else:
            sel_inputs = inputs
        table = sel_inputs.itemById("constraintTable")
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

            # Route by active tab
            if _active_tab == "tab_selected":
                tab_selected = inputs.itemById("tab_selected")
                if tab_selected:
                    sel_inputs = tab_selected.children
                else:
                    sel_inputs = inputs
                table = sel_inputs.itemById("constraintTable")
                constraints = _tab_state["selected"]["constraints"]
            elif _active_tab == "tab_types":
                pending = _tab_state["types"].get("pending_delete")
                if not pending:
                    return

                design = adsk.fusion.Design.cast(_app.activeProduct)
                if not design:
                    return
                sketch = design.activeEditObject
                if not isinstance(sketch, adsk.fusion.Sketch):
                    return

                # Snapshot constraints of this type, then delete in reverse (TYPE-05)
                targets = constraint_engine.collect_constraints_by_type(
                    sketch.geometricConstraints, pending
                )
                result = constraint_engine.delete_constraints(targets)
                _log.info(
                    "Bulk delete '%s': deleted=%d, failed=%d, skipped=%d",
                    pending, result["deleted"], result["failed"], result["skipped"]
                )

                # Clear pending state
                _tab_state["types"]["pending_delete"] = None
                return
            else:
                # tab_all execution handled in Phase 3
                return

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
        global _cmd_handlers, _active_tab
        _cmd_handlers = []
        _tab_state["selected"]["constraints"] = []
        _tab_state["types"]["summary"] = {}
        _tab_state["types"]["pending_delete"] = None
        _tab_state["all"]["constraints"] = []
        _tab_state["all"]["loaded"] = False
        _active_tab = "tab_selected"


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
