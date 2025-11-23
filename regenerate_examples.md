# Regenerate Example Files

The example files need to be converted to the standard workspace format.

## Quick Method (Recommended)

1. Close the app if running
2. Load each example file through the UI
3. Immediately save it (File → Save Workspace)
4. Overwrite the original file in `examples/`

This will convert them from the old list format to the standard dict format.

## Files to Convert

- [ ] examples/01_basic_introduction.dmw
- [ ] examples/02_constants_and_formulas.dmw
- [ ] examples/03_ranges_and_derivatives.dmw
- [ ] examples/04_uncertainty_propagation.dmw
- [ ] examples/05_custom_functions.dmw
- [ ] examples/06_calculated_constants.dmw
- [ ] examples/07_advanced_kinematics.dmw

## What Changed

**Old Format** (list of studies with flat structure):
```json
{
  "name": "Workspace Name",
  "workspace_type": "numerical",
  "studies": [
    {
      "type": "data_table",
      "name": "Study Name",
      "table": {...},
      "column_metadata": {...}
    }
  ]
}
```

**New Format** (dict of studies with nested structure):
```json
{
  "name": "Workspace Name",
  "workspace_type": "numerical",
  "studies": {
    "Study Name": {
      "type": "data_table",
      "data": {
        "name": "Study Name",
        "data_objects": {
          "main_table": {
            "name": "main_table",
            "data": {...}
          }
        },
        "column_metadata": {...}
      }
    }
  }
}
```

The new format matches what `workspace.to_dict()` produces, making the codebase simpler with a single format for both examples and saved workspaces.
