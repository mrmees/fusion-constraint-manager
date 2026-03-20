"""Validation script: Does deleteMe() inside inputChanged produce undo steps?

Run as a Fusion Script. Requires an active sketch with at least one
constraint (e.g., draw two lines, add a Parallel constraint).

Steps:
1. Opens a command dialog with a "Delete First Constraint" button
2. Click button -> deletes first geometric constraint on first sketch curve
3. Close dialog
4. Try Ctrl+Z -> if the constraint reappears, undo works

SUCCESS: Constraint reappears after Ctrl+Z.
FALLBACK NEEDED: Constraint does not reappear (no undo support).
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
            inputs.addBoolValueInput("deleteBtn", "Delete First Constraint", False, "", False)

            changed_handler = ChangedHandler()
            cmd.inputChanged.add(changed_handler)
            _handlers.append(changed_handler)
        except:
            _ui.messageBox(traceback.format_exc())


class ChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        try:
            if args.input.id != "deleteBtn":
                return
            # Reset button
            args.input.value = False

            design = adsk.fusion.Design.cast(_app.activeProduct)
            if not design:
                _ui.messageBox("No active design")
                return

            sketch = design.activeEditObject
            if not isinstance(sketch, adsk.fusion.Sketch):
                _ui.messageBox("Not editing a sketch")
                return

            curves = sketch.sketchCurves
            if curves.count == 0:
                _ui.messageBox("No curves in sketch")
                return

            first_curve = curves.item(0)
            constraints = first_curve.geometricConstraints
            if constraints.count == 0:
                _ui.messageBox("No constraints on first curve")
                return

            constraint = constraints.item(0)
            obj_type = constraint.objectType.split("::")[-1]

            if constraint.isDeletable:
                constraint.deleteMe()
                _ui.messageBox(
                    f"Deleted {obj_type}. Close dialog, then Ctrl+Z to test undo."
                )
            else:
                _ui.messageBox(f"{obj_type} is not deletable, try another sketch")
        except:
            _ui.messageBox(traceback.format_exc())


def run(context):
    try:
        cmd_def = _ui.commandDefinitions.addButtonDefinition(
            "validateUndo",
            "Validate Undo",
            "Test if deleteMe in inputChanged supports undo",
        )
        created_handler = CreatedHandler()
        cmd_def.commandCreated.add(created_handler)
        _handlers.append(created_handler)
        cmd_def.execute()
        adsk.autoTerminate(False)
    except:
        _ui.messageBox(traceback.format_exc())
