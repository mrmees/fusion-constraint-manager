"""Command definition and event handlers for the Constraint Manager."""

_app = None
_ui = None
_cmd_handlers = []


def start(app, ui):
    """Register the command in the DESIGN workspace toolbar."""
    global _app, _ui
    _app = app
    _ui = ui
    # TODO: Task 6 — register command definition and toolbar button


def stop():
    """Clean up command registration."""
    global _cmd_handlers
    _cmd_handlers = []
    # TODO: Task 6 — remove toolbar button and command definition
