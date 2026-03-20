import adsk.core
import adsk.fusion
import os
import sys
import traceback

# Fusion loads this file as a top-level script, not a package member.
# Add the add-in directory to sys.path so submodule imports work.
_addin_dir = os.path.dirname(os.path.abspath(__file__))
if _addin_dir not in sys.path:
    sys.path.insert(0, _addin_dir)

from commands.constraint_manager import command as constraint_cmd

_app = None
_ui = None


def run(context):
    global _app, _ui
    try:
        _app = adsk.core.Application.get()
        _ui = _app.userInterface
        constraint_cmd.start(_app, _ui)
    except:
        if _ui:
            _ui.messageBox(f"Failed to start ConstraintManager:\n{traceback.format_exc()}")


def stop(context):
    try:
        constraint_cmd.stop()
    except:
        if _ui:
            _ui.messageBox(f"Failed to stop ConstraintManager:\n{traceback.format_exc()}")
