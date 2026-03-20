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


# --- Enumeration tests ---

class MockConstraintList:
    """Mock for GeometricConstraintList."""

    def __init__(self, items):
        self._items = items

    @property
    def count(self):
        return len(self._items)

    def item(self, index):
        return self._items[index]

    def __iter__(self):
        return iter(self._items)


class MockSketchEntityWithConstraints(MockSketchEntity):
    """Mock entity that also has geometricConstraints."""

    def __init__(self, object_type, index=0, constraints=None, is_construction=False):
        super().__init__(object_type, index, is_construction)
        self.geometricConstraints = MockConstraintList(constraints or [])


def _mock_index_finder(entity):
    """Test index finder — returns the mock's _index attribute."""
    return getattr(entity, "_index", 0)


def test_enumerate_constraints_basic():
    from ConstraintManager.commands.constraint_manager.constraint_engine import enumerate_constraints
    line_a = MockSketchEntityWithConstraints("adsk::fusion::SketchLine", index=0)
    line_b = _make_entity("SketchLine", index=1)
    h_constraint = MockConstraint("HorizontalConstraint", isDeletable=True, line=line_a)
    p_constraint = MockConstraint("ParallelConstraint", isDeletable=True, lineOne=line_a, lineTwo=line_b)
    line_a.geometricConstraints = MockConstraintList([h_constraint, p_constraint])
    results = enumerate_constraints(line_a, index_finder=_mock_index_finder)
    assert len(results) == 2
    assert results[0]["type_name"] == "Horizontal"
    assert results[0]["related_label"] == "--"
    assert results[0]["is_deletable"] is True
    assert results[1]["type_name"] == "Parallel"
    assert results[1]["related_label"] == "Line #1"
    assert results[1]["is_deletable"] is True

def test_enumerate_constraints_non_deletable():
    from ConstraintManager.commands.constraint_manager.constraint_engine import enumerate_constraints
    entity = MockSketchEntityWithConstraints("adsk::fusion::SketchLine", index=0)
    constraint = MockConstraint("HorizontalConstraint", isDeletable=False, line=entity)
    entity.geometricConstraints = MockConstraintList([constraint])
    results = enumerate_constraints(entity, index_finder=_mock_index_finder)
    assert len(results) == 1
    assert results[0]["is_deletable"] is False

def test_enumerate_constraints_empty():
    from ConstraintManager.commands.constraint_manager.constraint_engine import enumerate_constraints
    entity = MockSketchEntityWithConstraints("adsk::fusion::SketchLine", index=0)
    entity.geometricConstraints = MockConstraintList([])
    results = enumerate_constraints(entity, index_finder=_mock_index_finder)
    assert results == []

def test_enumerate_unknown_constraint_shown():
    from ConstraintManager.commands.constraint_manager.constraint_engine import enumerate_constraints
    entity = MockSketchEntityWithConstraints("adsk::fusion::SketchLine", index=0)
    unknown = MockConstraint("BrandNewConstraint", isDeletable=True)
    entity.geometricConstraints = MockConstraintList([unknown])
    results = enumerate_constraints(entity, index_finder=_mock_index_finder)
    assert len(results) == 1
    assert results[0]["type_name"] == "Unknown (BrandNewConstraint)"
    assert results[0]["is_deletable"] is False  # Unknown types forced non-deletable
    assert results[0]["related_label"] == "--"

def test_format_related_single_entity():
    from ConstraintManager.commands.constraint_manager.constraint_engine import _format_related
    entity = _make_entity("SketchLine", index=5)
    result = _format_related(entity, lambda e: e._index)
    assert result == "Line #5"

def test_format_related_list():
    from ConstraintManager.commands.constraint_manager.constraint_engine import _format_related
    e1 = _make_entity("SketchLine", index=1)
    e2 = _make_entity("SketchArc", index=2)
    result = _format_related([e1, e2], lambda e: e._index)
    assert result == "Line #1, Arc #2"

def test_format_related_list_truncation():
    from ConstraintManager.commands.constraint_manager.constraint_engine import _format_related
    entities = [_make_entity("SketchLine", index=i) for i in range(5)]
    result = _format_related(entities, lambda e: e._index)
    assert "+2 more" in result
    assert result.count(",") == 3  # 3 labels + "+2 more"

def test_format_related_dash():
    from ConstraintManager.commands.constraint_manager.constraint_engine import _format_related
    assert _format_related("--", lambda e: 0) == "--"
    assert _format_related([], lambda e: 0) == "--"


# --- Deletion tests ---

class MockDeletableConstraint(MockConstraint):
    """Mock constraint that tracks deleteMe() calls."""

    def __init__(self, object_type, isDeletable=True, **kwargs):
        super().__init__(object_type, isDeletable, **kwargs)
        self.deleted = False

    def deleteMe(self):
        if not self.isDeletable:
            return False
        self.deleted = True
        self.isValid = False
        return True


def test_delete_single_constraint():
    from ConstraintManager.commands.constraint_manager.constraint_engine import delete_constraints
    c = MockDeletableConstraint("HorizontalConstraint")
    results = delete_constraints([c])
    assert c.deleted is True
    assert results["deleted"] == 1
    assert results["failed"] == 0

def test_delete_skips_non_deletable():
    from ConstraintManager.commands.constraint_manager.constraint_engine import delete_constraints
    c = MockDeletableConstraint("HorizontalConstraint", isDeletable=False)
    results = delete_constraints([c])
    assert c.deleted is False
    assert results["deleted"] == 0
    assert results["skipped"] == 1

def test_delete_skips_invalid():
    from ConstraintManager.commands.constraint_manager.constraint_engine import delete_constraints
    c = MockDeletableConstraint("HorizontalConstraint")
    c.isValid = False
    results = delete_constraints([c])
    assert c.deleted is False
    assert results["skipped"] == 1

def test_delete_batch_reverse_order():
    from ConstraintManager.commands.constraint_manager.constraint_engine import delete_constraints
    deletion_order = []

    class OrderedConstraint(MockDeletableConstraint):
        def __init__(self, name, **kwargs):
            super().__init__("HorizontalConstraint", **kwargs)
            self.name = name

        def deleteMe(self):
            deletion_order.append(self.name)
            return super().deleteMe()

    c1 = OrderedConstraint("first")
    c2 = OrderedConstraint("second")
    c3 = OrderedConstraint("third")
    delete_constraints([c1, c2, c3])
    assert deletion_order == ["third", "second", "first"]
