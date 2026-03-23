# Testing Patterns

**Analysis Date:** 2026-03-22

## Test Framework

**Runner:**
- `pytest` (community standard for Python testing)
- Config: Not explicitly configured (default behavior used)
- No `pytest.ini`, `setup.cfg`, or `pyproject.toml` test configuration found

**Assertion Library:**
- `assert` statements (built-in Python, no external library)

**Run Commands:**
```bash
python -m pytest ConstraintManager/tests/ -v              # Run all tests with verbose output
python -m pytest ConstraintManager/tests/test_constraint_engine.py -v  # Run single test file
python -m pytest ConstraintManager/tests/test_constraint_engine.py::test_label_sketch_line  # Run single test
```

**Setup:**
```bash
pip install pytest
```

## Test File Organization

**Location:**
- Tests co-located in `ConstraintManager/tests/` directory (separate from source, not alongside it)
- Main test file: `ConstraintManager/tests/test_constraint_engine.py` (covers pure constraint engine logic)
- Validation scripts: `ConstraintManager/tests/validate_checkbox.py`, `validate_undo.py` (exploratory tests for Fusion API capabilities, run inside Fusion via Tools > Scripts & Add-Ins)

**Naming:**
- Test files: `test_*.py` prefix following pytest convention
- Test functions: `test_*` prefix describing what is being tested
- Example: `test_label_sketch_line`, `test_resolve_single_entity_horizontal`, `test_delete_batch_reverse_order`

**Structure:**
```
ConstraintManager/
├── tests/
│   ├── test_constraint_engine.py    # Unit tests for constraint_engine.py (pytest)
│   ├── validate_checkbox.py          # Exploratory test (Fusion Script)
│   └── validate_undo.py              # Exploratory test (Fusion Script)
├── ConstraintManager.py              # Entry point (cannot be unit tested outside Fusion)
├── commands/
│   └── constraint_manager/
│       ├── command.py                # UI handlers (cannot be unit tested outside Fusion)
│       └── constraint_engine.py      # Pure logic (unit tested)
```

## Test Structure

**Suite Organization:**
- Tests grouped by functionality with comment sections: "Entity labeling tests", "Related entity resolution tests", "Enumeration tests", "Deletion tests"
- Within each section, tests follow logical order (basic case first, then edge cases)

```python
# --- Entity labeling tests ---

def test_label_sketch_line():
    from ConstraintManager.commands.constraint_manager.constraint_engine import get_entity_label
    entity = _make_entity("SketchLine", index=3)
    assert get_entity_label(entity, 3) == "Line #3"

def test_label_construction_line():
    from ConstraintManager.commands.constraint_manager.constraint_engine import get_entity_label
    entity = _make_entity("SketchLine", index=2, construction=True)
    assert get_entity_label(entity, 2) == "Constr. Line #2"
```

**Patterns:**
- **Setup pattern:** Minimal in each test. Test data created inline with helper functions: `_make_entity("SketchLine", index=3)`
- **Assertion pattern:** Direct `assert` statements checking return values against expected strings or objects
- **No teardown:** No explicit cleanup needed; tests don't modify shared state

## Mocking

**Framework:** Custom mock classes (no external mocking library like `unittest.mock`)

**Mock Objects Provided:**

1. **MockSketchEntity** (lines 9-15 in `test_constraint_engine.py`):
   - Simulates minimal Fusion `SketchEntity`
   - Has `objectType` (full namespace string), `_index` (internal), `isConstruction` (bool)
   - Used for entity labeling and type resolution tests

2. **MockCollection** (lines 18-29):
   - Simulates Fusion collection API (e.g., `sketchLines`, `sketchPoints`)
   - Provides `count` property and `item(index)` method
   - Used for entity lookup tests

3. **MockConstraint** (lines 94-102):
   - Simulates a geometric constraint with `objectType`, `isDeletable`, `isValid`, and arbitrary entity reference properties
   - Constructor accepts keyword args as entity references: `MockConstraint("HorizontalConstraint", line=entity1)`
   - Used for constraint resolution and enumeration tests

4. **MockConstraintList** (lines 180-194):
   - Simulates `GeometricConstraintList` from Fusion API
   - Provides `count` property, `item(index)` method, and `__iter__()` support
   - Used in enumeration tests

5. **MockSketchEntityWithConstraints** (lines 197-202):
   - Extends `MockSketchEntity` with `geometricConstraints` property
   - Subclass for testing constraint enumeration

6. **MockDeletableConstraint** (lines 281-293):
   - Extends `MockConstraint` with `deleteMe()` method
   - Tracks deletion via `.deleted` flag and updates `.isValid` state
   - Used for deletion tests to verify both successful deletions and rejections

**Patterns:**
```python
# Creating mock entities
entity = _make_entity("SketchLine", index=3)

# Creating mock constraints
constraint = MockConstraint("HorizontalConstraint", isDeletable=True, line=entity)

# Testing deletion with tracking
class OrderedConstraint(MockDeletableConstraint):
    def __init__(self, name, **kwargs):
        super().__init__("HorizontalConstraint", **kwargs)
        self.name = name

    def deleteMe(self):
        deletion_order.append(self.name)
        return super().deleteMe()
```

**What to Mock:**
- Fusion API objects (`SketchEntity`, `Constraint`, `Collection`)
- Entity relationships and references
- API method behavior (`deleteMe()`, property access)

**What NOT to Mock:**
- Python builtins (`list`, `dict`, `str`)
- Test helper functions (`get_entity_label()`, `resolve_related_entity()`)
- Assertion logic

## Fixtures and Factories

**Test Data:**
- Helper function `_make_entity(type_suffix, index=0, construction=False)` creates standardized mock entities
  - Returns `MockSketchEntity` with properly formatted `objectType` and index
  - Example: `_make_entity("SketchLine", index=3)` returns entity with `objectType = "adsk::fusion::SketchLine"`

- Helper function `_mock_index_finder(entity)` simulates the index lookup callback
  - Returns `entity._index` attribute for mock objects
  - Used as `index_finder` parameter in enumeration tests

**Location:**
- Helpers defined at module level in `test_constraint_engine.py` before test functions
- Reusable across test sections

**Example Factory:**
```python
def _make_entity(type_suffix, index=0, construction=False):
    return MockSketchEntity(
        f"adsk::fusion::{type_suffix}", index=index, is_construction=construction
    )

def _mock_index_finder(entity):
    """Test index finder — returns the mock's _index attribute."""
    return getattr(entity, "_index", 0)
```

## Coverage

**Requirements:** No coverage enforcement detected (no `pytest-cov` in dependencies, no `.coveragerc`)

**View Coverage:**
```bash
pip install pytest-cov
python -m pytest ConstraintManager/tests/ --cov=ConstraintManager.commands.constraint_manager.constraint_engine --cov-report=html
```

**What IS Tested:**
- Core constraint engine logic: `get_entity_label()`, `get_constraint_type_name()`, `resolve_related_entity()`, `enumerate_constraints()`, `delete_constraints()`
- Edge cases: unknown constraint types, non-deletable constraints, invalid constraints, empty collections, symmetry constraints with multiple entities
- Data formatting: related entity label generation, constraint info dict construction

**What is NOT Tested:**
- Fusion API integration (requires running inside Fusion)
- UI event handling (`command.py`: `CommandCreatedHandler`, `InputChangedHandler`, `ExecuteHandler`, `PreSelectHandler`)
- Entry point (`ConstraintManager.py`): Fusion lifecycle management
- Network/file I/O: None in codebase

## Test Types

**Unit Tests:**
- Scope: Pure functions in `constraint_engine.py`
- Approach: Isolated function testing with mock Fusion objects
- Framework: pytest with custom mocks
- Location: `ConstraintManager/tests/test_constraint_engine.py`
- Coverage: 38 test functions covering all public functions and major edge cases

**Integration Tests:**
- Scope: Fusion API command/event flow, dialog interaction, constraint deletion
- Approach: Manual testing inside Fusion using validation scripts
- Framework: Fusion script API
- Location: `ConstraintManager/tests/validate_checkbox.py`, `validate_undo.py`
- Coverage: Checkbox rendering in table, undo/redo support for constraint deletion

**E2E Tests:**
- Not automated
- Manual testing: Follow install steps, enter sketch edit mode, select entities, verify constraint table population, test deletion and undo

## Common Patterns

**Async Testing:**
- Not applicable (no async code in codebase)

**Error Testing:**
- Tested via mock state manipulation: setting `isDeletable=False` or `isValid=False` on constraints
- Example from lines 304-310:
  ```python
  def test_delete_skips_non_deletable():
      from ConstraintManager.commands.constraint_manager.constraint_engine import delete_constraints
      c = MockDeletableConstraint("HorizontalConstraint", isDeletable=False)
      results = delete_constraints([c])
      assert c.deleted is False
      assert results["deleted"] == 0
      assert results["skipped"] == 1
  ```

**Batch Operation Testing:**
- Reverse-order deletion verified via custom mock subclass tracking deletion order (lines 320-337):
  ```python
  def test_delete_batch_reverse_order():
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
  ```

**Constraint Resolution Testing:**
- Single-entity vs. multi-entity constraints tested separately
- Symmetry constraints with 3+ entities tested as list return: lines 145-154
  ```python
  def test_resolve_symmetry_selected_is_entity_one():
      e1 = _make_entity("SketchLine", index=0)
      e2 = _make_entity("SketchLine", index=1)
      sym_line = _make_entity("SketchLine", index=2)
      constraint = MockConstraint("SymmetryConstraint", entityOne=e1, entityTwo=e2, symmetryLine=sym_line)
      result = resolve_related_entity(constraint, e1)
      assert isinstance(result, list)
      assert e2 in result
      assert sym_line in result
  ```

**Data Structure Testing:**
- Dict keys validated: `results[0]["type_name"]`, `results[0]["related_label"]`, `results[0]["is_deletable"]`
- List truncation tested: line 266-271 verifies "+2 more" suffix for >3 related entities

---

*Testing analysis: 2026-03-22*
