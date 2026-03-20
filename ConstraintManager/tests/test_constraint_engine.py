"""Unit tests for constraint_engine.py.

These tests use mock objects to simulate Fusion API types.
Run with: python -m pytest ConstraintManager/tests/ -v
(from the project root, outside Fusion)
"""


class MockSketchEntity:
    """Minimal mock for SketchEntity-like objects."""

    def __init__(self, object_type, index=0, is_construction=False):
        self.objectType = object_type
        self._index = index
        self.isConstruction = is_construction


# TODO: Task 2 — add tests as engine functions are built
