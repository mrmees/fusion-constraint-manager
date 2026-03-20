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


# --- Related entity resolution tests ---

class MockConstraint:
    """Mock for a geometric constraint."""

    def __init__(self, object_type, isDeletable=True, **entity_refs):
        self.objectType = f"adsk::fusion::{object_type}"
        self.isDeletable = isDeletable
        self.isValid = True
        for k, v in entity_refs.items():
            setattr(self, k, v)


def test_resolve_single_entity_horizontal():
    """Horizontal constraint has one entity — related should be '--'."""
    from ConstraintManager.commands.constraint_manager.constraint_engine import resolve_related_entity
    selected = _make_entity("SketchLine", index=0)
    constraint = MockConstraint("HorizontalConstraint", line=selected)
    result = resolve_related_entity(constraint, selected)
    assert result == "--"

def test_resolve_two_entity_parallel():
    """Parallel: return the entity that isn't the selected one."""
    from ConstraintManager.commands.constraint_manager.constraint_engine import resolve_related_entity
    line_a = _make_entity("SketchLine", index=0)
    line_b = _make_entity("SketchLine", index=3)
    constraint = MockConstraint("ParallelConstraint", lineOne=line_a, lineTwo=line_b)
    result = resolve_related_entity(constraint, line_a)
    assert result is line_b

def test_resolve_two_entity_selected_is_second():
    from ConstraintManager.commands.constraint_manager.constraint_engine import resolve_related_entity
    line_a = _make_entity("SketchLine", index=0)
    line_b = _make_entity("SketchLine", index=3)
    constraint = MockConstraint("ParallelConstraint", lineOne=line_a, lineTwo=line_b)
    result = resolve_related_entity(constraint, line_b)
    assert result is line_a

def test_resolve_coincident():
    from ConstraintManager.commands.constraint_manager.constraint_engine import resolve_related_entity
    point = _make_entity("SketchPoint", index=0)
    line = _make_entity("SketchLine", index=1)
    constraint = MockConstraint("CoincidentConstraint", point=point, entity=line)
    result = resolve_related_entity(constraint, point)
    assert result is line

def test_resolve_fix_constraint():
    from ConstraintManager.commands.constraint_manager.constraint_engine import resolve_related_entity
    entity = _make_entity("SketchPoint", index=0)
    constraint = MockConstraint("FixConstraint", entity=entity)
    result = resolve_related_entity(constraint, entity)
    assert result == "--"

def test_resolve_symmetry_selected_is_entity_one():
    from ConstraintManager.commands.constraint_manager.constraint_engine import resolve_related_entity
    e1 = _make_entity("SketchLine", index=0)
    e2 = _make_entity("SketchLine", index=1)
    sym_line = _make_entity("SketchLine", index=2)
    constraint = MockConstraint("SymmetryConstraint", entityOne=e1, entityTwo=e2, symmetryLine=sym_line)
    result = resolve_related_entity(constraint, e1)
    assert isinstance(result, list)
    assert e2 in result
    assert sym_line in result

def test_resolve_unknown_type():
    from ConstraintManager.commands.constraint_manager.constraint_engine import resolve_related_entity
    entity = _make_entity("SketchLine", index=0)
    constraint = MockConstraint("SomeNewConstraint")
    result = resolve_related_entity(constraint, entity)
    assert result == "--"

def test_resolve_offset_selected_in_parent():
    from ConstraintManager.commands.constraint_manager.constraint_engine import resolve_related_entity
    parent = _make_entity("SketchLine", index=0)
    child1 = _make_entity("SketchLine", index=1)
    child2 = _make_entity("SketchArc", index=0)
    constraint = MockConstraint("OffsetConstraint")
    constraint.parentCurves = MockCollection([parent])
    constraint.childCurves = MockCollection([child1, child2])
    result = resolve_related_entity(constraint, parent)
    assert isinstance(result, list)
    assert len(result) == 2
    assert child1 in result
    assert child2 in result
