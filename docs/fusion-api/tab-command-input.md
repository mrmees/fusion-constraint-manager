# Fusion 360 TabCommandInput API Reference

Fetched 2026-03-23 from official Autodesk docs + community-confirmed patterns.

## TabCommandInput

Created via `inputs.addTabCommandInput(id, label)`.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `isActive` | bool (read) | Whether this tab is currently selected |
| `children` | CommandInputs | Add child inputs here |
| `isEnabled` | bool | Whether user can click the tab |
| `isVisible` | bool | Whether tab is shown at all |
| `resourceFolder` | string | Path to tab icon image |

### Methods

| Method | Description |
|--------|-------------|
| `activate()` | Programmatically select this tab |
| `deleteMe()` | Remove the tab |

## Tab Switch Detection (UNDOCUMENTED but universal)

Tab switches fire `inputChanged` with `changed_input.id == "APITabBar"`.

This is NOT documented by Autodesk. Discovered through community practice. Confirmed in:
- Autodesk/synthesis exporter
- phossystems/HelicalGearPlus
- osamutake/fusion360-study-gears
- Green-AI-Hub fusion-plugin

### Pattern

```python
def notify(self, args):
    changed_input = args.input
    inputs = args.inputs

    if changed_input.id == "APITabBar":
        for tab_id in ("tab_one", "tab_two", "tab_three"):
            tab = inputs.itemById(tab_id)
            if tab and tab.isActive:
                _active_tab = tab_id
                break
        return
```

### Key Behaviors

1. `inputChanged` fires globally across all tabs — guard per-tab handlers with `isActive` check
2. Do NOT create/destroy inputs in inputChanged — use `isVisible`/`isEnabled` toggling
3. Tab switching does NOT fire `validateInputs`
4. The `APITabBar` event fires once per tab click, not for re-clicking active tab

### args.inputs Scoping

When an input inside a tab fires inputChanged, `args.inputs` may return the tab's
children (not the root CommandInputs). Use fallback pattern:

```python
tab = inputs.itemById("my_tab")
if tab:
    tab_inputs = tab.children
else:
    tab_inputs = inputs  # already scoped to tab children
```

## Sources

- https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/TabCommandInput.htm
- https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Command_inputChanged.htm
- https://github.com/phossystems/HelicalGearPlus
- https://github.com/osamutake/fusion360-study-gears
