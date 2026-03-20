"""Validation script: Can BoolValueCommandInput work as checkboxes in TableCommandInput?

Run as a Fusion Script (Tools > Scripts & Add-Ins > Scripts > Run).
Creates a command dialog with a table containing checkbox rows.
SUCCESS: Checkboxes render, toggle, and fire inputChanged events.
FALLBACK NEEDED: If checkboxes don't render or events don't fire.
"""
import adsk.core
import adsk.fusion
import traceback

_app = adsk.core.Application.get()
_ui = _app.userInterface
_handlers = []


class CreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            table = inputs.addTableCommandInput(
                "testTable", "Test Table", 3, "1:2:2"
            )
            table.maximumVisibleRows = 5

            for i in range(3):
                row_inputs = adsk.core.CommandInputs.cast(table.commandInputs)
                cb = row_inputs.addBoolValueInput(
                    f"check_{i}", "", True, "", False
                )
                type_input = row_inputs.addStringValueInput(
                    f"type_{i}", "", f"Constraint {i}"
                )
                related_input = row_inputs.addStringValueInput(
                    f"related_{i}", "", f"Entity {i}"
                )
                table.addCommandInput(cb, i, 0)
                table.addCommandInput(type_input, i, 1)
                table.addCommandInput(related_input, i, 2)

            # Add toolbar delete button
            del_btn = inputs.addBoolValueInput(
                "deleteBtn", "Delete Selected", False, "", False
            )
            table.addToolbarCommandInput(del_btn)

            changed_handler = ChangedHandler()
            cmd.inputChanged.add(changed_handler)
            _handlers.append(changed_handler)
        except:
            _ui.messageBox(traceback.format_exc())


class ChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        try:
            changed = args.input
            _ui.messageBox(f"inputChanged fired for: {changed.id}")
        except:
            _ui.messageBox(traceback.format_exc())


def run(context):
    try:
        cmd_def = _ui.commandDefinitions.addButtonDefinition(
            "validateCheckbox",
            "Validate Checkbox",
            "Test BoolValueCommandInput in TableCommandInput",
        )
        created_handler = CreatedHandler()
        cmd_def.commandCreated.add(created_handler)
        _handlers.append(created_handler)
        cmd_def.execute()
        adsk.autoTerminate(False)
    except:
        _ui.messageBox(traceback.format_exc())
