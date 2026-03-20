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


class MockCollection:
    """Minimal mock for a Fusion collection (e.g., SketchLines)."""

    def __init__(self, items):
        self._items = items

    @property
    def count(self):
        return len(self._items)

    def item(self, index):
        return self._items[index]


def _make_entity(type_suffix, index=0, construction=False):
    return MockSketchEntity(
        f"adsk::fusion::{type_suffix}", index=index, is_construction=construction
    )


# --- Entity labeling tests ---

def test_label_sketch_line():
    from ConstraintManager.commands.constraint_manager.constraint_engine import get_entity_label
    entity = _make_entity("SketchLine", index=3)
    assert get_entity_label(entity, 3) == "Line #3"

def test_label_sketch_arc():
    from ConstraintManager.commands.constraint_manager.constraint_engine import get_entity_label
    entity = _make_entity("SketchArc", index=0)
    assert get_entity_label(entity, 0) == "Arc #0"

def test_label_sketch_circle():
    from ConstraintManager.commands.constraint_manager.constraint_engine import get_entity_label
    entity = _make_entity("SketchCircle", index=1)
    assert get_entity_label(entity, 1) == "Circle #1"

def test_label_sketch_point():
    from ConstraintManager.commands.constraint_manager.constraint_engine import get_entity_label
    entity = _make_entity("SketchPoint", index=4)
    assert get_entity_label(entity, 4) == "Point #4"

def test_label_construction_line():
    from ConstraintManager.commands.constraint_manager.constraint_engine import get_entity_label
    entity = _make_entity("SketchLine", index=2, construction=True)
    assert get_entity_label(entity, 2) == "Constr. Line #2"

def test_label_sketch_ellipse():
    from ConstraintManager.commands.constraint_manager.constraint_engine import get_entity_label
    entity = _make_entity("SketchEllipse", index=0)
    assert get_entity_label(entity, 0) == "Ellipse #0"

def test_label_sketch_spline():
    from ConstraintManager.commands.constraint_manager.constraint_engine import get_entity_label
    entity = _make_entity("SketchFittedSpline", index=1)
    assert get_entity_label(entity, 1) == "Spline #1"

def test_label_unknown_entity_type():
    from ConstraintManager.commands.constraint_manager.constraint_engine import get_entity_label
    entity = _make_entity("SketchConicCurve", index=0)
    assert get_entity_label(entity, 0) == "Entity #0"

def test_constraint_type_display_name():
    from ConstraintManager.commands.constraint_manager.constraint_engine import get_constraint_type_name
    assert get_constraint_type_name("adsk::fusion::HorizontalConstraint") == "Horizontal"
    assert get_constraint_type_name("adsk::fusion::ParallelConstraint") == "Parallel"
    assert get_constraint_type_name("adsk::fusion::CoincidentConstraint") == "Coincident"

def test_constraint_type_strips_suffix():
    from ConstraintManager.commands.constraint_manager.constraint_engine import get_constraint_type_name
    assert get_constraint_type_name("adsk::fusion::PerpendicularConstraint") == "Perpendicular"
    assert get_constraint_type_name("adsk::fusion::TangentConstraint") == "Tangent"
