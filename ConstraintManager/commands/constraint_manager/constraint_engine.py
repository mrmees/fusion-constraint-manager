"""Pure logic for constraint enumeration, name resolution, and deletion.

No Fusion UI imports (adsk.core UI classes). Takes Fusion API model objects
as arguments, returns plain data structures.
"""

import logging

_log = logging.getLogger(__name__)

# objectType suffix -> display prefix
_ENTITY_TYPE_MAP = {
    "SketchLine": "Line",
    "SketchArc": "Arc",
    "SketchCircle": "Circle",
    "SketchEllipse": "Ellipse",
    "SketchFittedSpline": "Spline",
    "SketchPoint": "Point",
}


def get_entity_label(entity, index):
    """Build a display label like 'Line #3' or 'Constr. Arc #1'.

    Args:
        entity: A Fusion SketchEntity (or anything with .objectType and .isConstruction).
        index: The entity's index within its parent collection.

    Returns:
        A human-readable label string.
    """
    obj_type = entity.objectType.split("::")[-1]
    prefix = _ENTITY_TYPE_MAP.get(obj_type, "Entity")
    construction = getattr(entity, "isConstruction", False)
    if construction:
        return f"Constr. {prefix} #{index}"
    return f"{prefix} #{index}"


def get_constraint_type_name(object_type):
    """Strip namespace and 'Constraint' suffix from a Fusion objectType string.

    'adsk::fusion::HorizontalConstraint' -> 'Horizontal'

    Args:
        object_type: Full objectType string from a constraint.

    Returns:
        A clean display name string.
    """
    name = object_type.split("::")[-1]
    if name.endswith("Constraint"):
        name = name[: -len("Constraint")]
    return name


# Constraint type -> (property names referencing entities)
_CONSTRAINT_ENTITY_PROPS = {
    "HorizontalConstraint": ("line",),
    "VerticalConstraint": ("line",),
    "FixConstraint": ("entity",),
    "ParallelConstraint": ("lineOne", "lineTwo"),
    "PerpendicularConstraint": ("lineOne", "lineTwo"),
    "CollinearConstraint": ("lineOne", "lineTwo"),
    "CoincidentConstraint": ("point", "entity"),
    "EqualConstraint": ("curveOne", "curveTwo"),
    "TangentConstraint": ("curveOne", "curveTwo"),
    "SmoothConstraint": ("curveOne", "curveTwo"),
    "ConcentricConstraint": ("entityOne", "entityTwo"),
    "MidPointConstraint": ("point", "midPointCurve"),
    "HorizontalPointsConstraint": ("pointOne", "pointTwo"),
    "VerticalPointsConstraint": ("pointOne", "pointTwo"),
    "SymmetryConstraint": ("entityOne", "entityTwo", "symmetryLine"),
}


def resolve_related_entity(constraint, selected_entity):
    """Identify the 'other' entity/entities in a constraint relative to selected_entity.

    Returns:
        '--' for single-entity constraints or unknown types.
        The other entity object for two-entity constraints.
        A list of other entity objects for three+ entity constraints (Symmetry).
    """
    type_name = constraint.objectType.split("::")[-1]

    if type_name == "OffsetConstraint":
        return _resolve_offset(constraint, selected_entity)

    props = _CONSTRAINT_ENTITY_PROPS.get(type_name)
    if props is None:
        _log.warning("Unknown constraint type: %s", constraint.objectType)
        return "--"

    if len(props) == 1:
        return "--"

    referenced = []
    for prop in props:
        val = getattr(constraint, prop, None)
        if val is not None:
            referenced.append(val)

    # Use == not 'is' — Fusion may return different wrapper objects for the same entity
    others = [e for e in referenced if e != selected_entity]

    if len(others) == 0:
        return "--"
    if len(others) == 1:
        return others[0]
    return others


def _resolve_offset(constraint, selected_entity):
    """Resolve related entities for Offset constraints (collection-based)."""
    try:
        parent_curves = constraint.parentCurves
        child_curves = constraint.childCurves
    except AttributeError:
        return "--"

    parent_list = [parent_curves.item(i) for i in range(parent_curves.count)]
    child_list = [child_curves.item(i) for i in range(child_curves.count)]

    if selected_entity in parent_list:
        return child_list if child_list else "--"
    if selected_entity in child_list:
        return parent_list if parent_list else "--"
    return "--"


def enumerate_constraints(entity, index_finder, include_dimensions=False):
    """Enumerate all geometric constraints on an entity, returning display-ready info.

    Args:
        entity: A Fusion SketchEntity with .geometricConstraints property.
        index_finder: Callable(entity) -> int. Resolves an entity's collection index.
        include_dimensions: If True, also enumerate .sketchDimensions (v1: disabled).

    Returns:
        List of dicts, each with keys:
            - constraint: The original Fusion constraint object
            - type_name: Display name (e.g., 'Horizontal', 'Parallel')
            - related_label: Display label for related entity (e.g., 'Line #3', '--')
            - is_deletable: Whether the constraint can be deleted
    """
    results = []

    for i in range(entity.geometricConstraints.count):
        constraint = entity.geometricConstraints.item(i)
        info = _build_constraint_info(constraint, entity, index_finder)
        results.append(info)

    if include_dimensions and hasattr(entity, "sketchDimensions"):
        for i in range(entity.sketchDimensions.count):
            dim = entity.sketchDimensions.item(i)
            info = _build_constraint_info(dim, entity, index_finder)
            results.append(info)

    return results


def _build_constraint_info(constraint, selected_entity, index_finder):
    """Build a display-ready dict for a single constraint."""
    type_name_raw = constraint.objectType.split("::")[-1]
    is_known = type_name_raw in _CONSTRAINT_ENTITY_PROPS or type_name_raw == "OffsetConstraint"

    if is_known:
        type_name = get_constraint_type_name(constraint.objectType)
        is_deletable = getattr(constraint, "isDeletable", False)
        related = resolve_related_entity(constraint, selected_entity)
        related_label = _format_related(related, index_finder)
    else:
        type_name = f"Unknown ({type_name_raw})"
        is_deletable = False
        related_label = "--"
        _log.warning("Unknown constraint type: %s", constraint.objectType)

    # Store entityToken for stable re-resolution in execute handler
    token = getattr(constraint, "entityToken", None)

    return {
        "constraint": constraint,
        "entity_token": token,
        "type_name": type_name,
        "related_label": related_label,
        "is_deletable": is_deletable,
    }


def _build_sketch_constraint_info(constraint, index_finder):
    """Build display info for a constraint in sketch-wide context (no selected entity).

    Unlike _build_constraint_info which shows the "other" entity relative to a
    selected entity, this labels ALL referenced entities for the constraint.

    Args:
        constraint: A Fusion geometric constraint object.
        index_finder: Callable(entity) -> int for entity label resolution.

    Returns:
        Dict with keys: constraint, entity_token, type_name, entities_label,
        is_deletable.
    """
    type_key = constraint.objectType.split("::")[-1]
    props = _CONSTRAINT_ENTITY_PROPS.get(type_key)

    if props is None:
        _log.warning("Unknown constraint type: %s", constraint.objectType)
        return {
            "constraint": constraint,
            "entity_token": getattr(constraint, "entityToken", None),
            "type_name": f"Unknown ({type_key})",
            "entities_label": "--",
            "is_deletable": False,
        }

    type_name = get_constraint_type_name(constraint.objectType)
    labels = []
    for prop in props:
        entity = getattr(constraint, prop, None)
        if entity is not None:
            labels.append(get_entity_label(entity, index_finder(entity)))
    entities_label = ", ".join(labels) if labels else "--"

    return {
        "constraint": constraint,
        "entity_token": getattr(constraint, "entityToken", None),
        "type_name": type_name,
        "entities_label": entities_label,
        "is_deletable": getattr(constraint, "isDeletable", False),
    }


def aggregate_constraint_types(geometric_constraints):
    """Count constraints by type across a sketch's geometric constraints.

    Args:
        geometric_constraints: A GeometricConstraints collection
            (sketch.geometricConstraints) with .count and .item(i).

    Returns:
        Dict mapping type display name to count.
        e.g., {"Fix": 87, "Horizontal": 12, "Coincident": 45}
    """
    counts = {}
    for i in range(geometric_constraints.count):
        constraint = geometric_constraints.item(i)
        type_name = get_constraint_type_name(constraint.objectType)
        counts[type_name] = counts.get(type_name, 0) + 1
    return counts


def enumerate_all_constraints(geometric_constraints, index_finder):
    """Enumerate every constraint in a sketch with full metadata.

    Args:
        geometric_constraints: A GeometricConstraints collection
            (sketch.geometricConstraints) with .count and .item(i).
        index_finder: Callable(entity) -> int for entity label resolution.

    Returns:
        List of constraint info dicts, each with keys: constraint,
        entity_token, type_name, entities_label, is_deletable.
    """
    results = []
    for i in range(geometric_constraints.count):
        constraint = geometric_constraints.item(i)
        info = _build_sketch_constraint_info(constraint, index_finder)
        results.append(info)
    return results


def filter_constraints_by_type(constraints, type_name):
    """Filter a pre-enumerated constraint list by type.

    Args:
        constraints: List of constraint info dicts (from enumerate_all_constraints).
        type_name: Display name to filter by (e.g., "Fix"). Case-sensitive.

    Returns:
        Filtered list of constraint info dicts.
    """
    return [c for c in constraints if c["type_name"] == type_name]


def collect_constraints_by_type(geometric_constraints, type_name):
    """Collect raw constraint objects of a specific type for bulk deletion.

    Args:
        geometric_constraints: A GeometricConstraints collection
            (sketch.geometricConstraints) with .count and .item(i).
        type_name: Display name of the constraint type (e.g., "Fix").

    Returns:
        List of raw constraint objects matching the type.
    """
    results = []
    for i in range(geometric_constraints.count):
        constraint = geometric_constraints.item(i)
        if get_constraint_type_name(constraint.objectType) == type_name:
            results.append(constraint)
    return results


def collect_entities_for_types(geometric_constraints, type_names):
    """Collect unique sketch entities referenced by constraints of given types.

    Used for viewport highlighting — returns the geometry that should be
    visually highlighted when the user checks constraint types.

    Args:
        geometric_constraints: A GeometricConstraints collection.
        type_names: List of display type names (e.g., ["Fix", "Horizontal"]).

    Returns:
        List of unique sketch entity objects referenced by matching constraints.
    """
    type_set = set(type_names)
    seen_tokens = set()
    entities = []

    for i in range(geometric_constraints.count):
        constraint = geometric_constraints.item(i)
        if get_constraint_type_name(constraint.objectType) not in type_set:
            continue

        type_key = constraint.objectType.split("::")[-1]
        props = _CONSTRAINT_ENTITY_PROPS.get(type_key)
        if props is None:
            continue

        for prop in props:
            entity = getattr(constraint, prop, None)
            if entity is None:
                continue
            token = getattr(entity, "entityToken", None)
            if token and token in seen_tokens:
                continue
            if token:
                seen_tokens.add(token)
            entities.append(entity)

    return entities


def delete_constraints(constraints):
    """Delete a list of constraints in reverse order.

    Checks isDeletable and isValid before each deletion. Logs and continues
    on failure — never aborts the batch.

    Args:
        constraints: List of Fusion constraint objects (in table display order).

    Returns:
        Dict with keys: 'deleted' (int), 'failed' (int), 'skipped' (int).
    """
    deleted = 0
    failed = 0
    skipped = 0

    for constraint in reversed(constraints):
        if not getattr(constraint, "isValid", False):
            _log.info("Skipping invalid constraint")
            skipped += 1
            continue
        if not getattr(constraint, "isDeletable", False):
            _log.info("Skipping non-deletable constraint: %s", constraint.objectType)
            skipped += 1
            continue
        try:
            constraint.deleteMe()
            deleted += 1
        except Exception as e:
            _log.error("Failed to delete constraint: %s", e)
            failed += 1

    return {"deleted": deleted, "failed": failed, "skipped": skipped}


def _format_related(related, index_finder):
    """Format the related entity result into a display string.

    Args:
        related: '--', a single entity, or a list of entities.
        index_finder: Callable(entity) -> int for resolving collection indices.
    """
    if related == "--":
        return "--"
    if isinstance(related, list):
        if len(related) == 0:
            return "--"
        labels = []
        for e in related[:3]:
            label = get_entity_label(e, index_finder(e))
            labels.append(label)
        if len(related) > 3:
            labels.append(f"+{len(related) - 3} more")
        return ", ".join(labels)
    # Single entity
    return get_entity_label(related, index_finder(related))
