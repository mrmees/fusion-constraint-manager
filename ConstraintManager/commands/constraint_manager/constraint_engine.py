"""Pure logic for constraint enumeration, name resolution, and deletion.

No Fusion UI imports (adsk.core UI classes). Takes Fusion API model objects
as arguments, returns plain data structures.
"""

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
