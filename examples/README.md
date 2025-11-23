# DataManip Example Workspaces

This directory contains a series of example workspaces that demonstrate all features of DataManip, from basic to advanced usage.

## Loading Examples

**Important:** Examples are generated programmatically from `generate_examples.py`. Do not manually edit `.dmw` files.

### In the Application
To load an example in DataManip:
1. Launch the application: `uv run datamanip`
2. Go to **Examples** menu in the menu bar
3. Select any example from the list
4. The example will replace your current workspace

### From File Menu (Alternative)
1. Launch the application: `uv run datamanip`
2. Go to **File → Open Workspace**
3. Navigate to the `examples` directory
4. Select any `.dmw` file

## Regenerating Examples

**All examples are code-generated to ensure consistency and correctness.**

To regenerate all 7 example files:

```bash
cd examples
uv run python generate_examples.py
```

The script will:
- Create each workspace using the DataManip API
- Save to `.dmw` JSON format
- Reload and verify integrity
- Report success/failure for each example

**When to regenerate:**
- After API changes
- When adding new features to showcase
- If examples fail to load
- To fix formatting inconsistencies

**Benefits of code generation:**
- ✓ Ensures consistent JSON structure
- ✓ Uses correct API calls (no manual errors)
- ✓ Validates serialization/deserialization
- ✓ Single source of truth
- ✓ Easy to update multiple examples
- ✓ Serves as API usage documentation

## Example Progression

### 01 - Basic Introduction
**Features:** Data entry, basic plotting
- Simple temperature measurements over time
- Single data table with two columns
- Basic line plot with custom styling

**Skills:** Creating data columns, setting units, basic plot configuration

---

### 02 - Constants and Formulas
**Features:** Workspace constants, calculated columns
- Circle geometry (circumference and area)
- Uses constant `π` in formulas
- Multiple calculated columns from single input

**Skills:** Defining numeric constants, using constants in formulas, multiple series plotting

---

### 03 - Ranges and Derivatives
**Features:** Range generation (linspace), numerical derivatives (1st and 2nd order)
- Projectile motion physics
- Time range auto-generated with `linspace`
- Velocity (1st derivative) and acceleration (2nd derivative)

**Skills:** Creating range columns, computing derivatives, multi-plot layouts

---

### 04 - Uncertainty Propagation
**Features:** Uncertainty columns, automatic propagation, error bars
- Ohm's law: V = I × R, P = I × V
- Manual uncertainty input (δI, δR)
- Automatic propagation to calculated columns (δV, δP)
- Error bars in both X and Y axes

**Skills:** Creating uncertainty columns, enabling propagation, plotting with error bars

---

### 05 - Custom Functions
**Features:** User-defined functions, complex formulas
- Signal processing (sine waves)
- Custom functions: `sine_wave(t, f, A, phase)` and `rms(v1, v2)`
- Signal combination and RMS analysis

**Skills:** Defining custom functions, using NumPy in formulas, multi-parameter functions

---

### 06 - Calculated Constants
**Features:** Calculated constants, constant dependencies
- Ideal gas law (PV = nRT)
- Constants computed from other constants (V₀, n)
- Gay-Lussac's and Charles's laws demonstrated

**Skills:** Creating calculated constants, constant dependency chains, scientific constants

---

### 07 - Advanced Kinematics (Master Example)
**Features:** ALL features combined
- 2D projectile motion at 30° angle
- Range generation (time axis)
- Calculated columns (X, Y positions)
- Manual uncertainties (δX, δY)
- Derivatives (Vx, Vy from positions)
- Uncertainty propagation (speed from Vx, Vy)
- Multiple coordinated plots
- Statistical analysis

**Skills:** Complete workflow, feature integration, advanced physics simulation

## Feature Reference

| Feature | Examples |
|---------|----------|
| Data columns | 01, 04, 07 |
| Calculated columns | 02, 03, 04, 05, 06, 07 |
| Range generation (linspace) | 03, 05, 06, 07 |
| Derivatives (1st order) | 03, 07 |
| Derivatives (2nd order) | 03 |
| Uncertainty columns | 04, 07 |
| Uncertainty propagation | 04, 07 |
| Error bars (X/Y) | 04, 07 |
| Numeric constants | 02, 03, 04, 05, 06, 07 |
| Calculated constants | 06, 07 |
| Custom functions | 05 |
| Multiple plots | 03, 04, 05, 06, 07 |
| Multiple series | 02, 03, 04, 05 |
| Statistics study | 07 |

## Tips for Learning

1. **Start simple**: Work through examples 01-03 to understand basics
2. **Focus on uncertainty**: Examples 04 and 07 show proper error handling
3. **Master constants**: Example 06 demonstrates constant relationships
4. **Study example 07**: The ultimate showcase of all features working together
5. **Modify examples**: Try changing constants, formulas, or adding new columns
6. **Check formulas**: View column metadata to see formula syntax
7. **Explore plots**: Notice how plot styling and labels enhance clarity

## Common Patterns

### Creating a calculated column with uncertainty:
```
1. Add data column (e.g., "Current (A)")
2. Add uncertainty column (e.g., "δCurrent (A)", type=UNCERTAINTY, reference="Current (A)")
3. Add calculated column with formula (e.g., "Voltage (V) = {Current (A)} * {Resistance (Ω)}")
4. Enable propagate_uncertainty=True
5. Uncertainty column "δVoltage (V)" is auto-created
```

### Setting up derivatives:
```
1. Add range column for independent variable (e.g., "Time (s)")
2. Add calculated column for dependent variable (e.g., "Position (m)")
3. Add derivative column (type=DERIVATIVE, derivative_of="Position (m)", with_respect_to="Time (s)")
4. Set order=1 for velocity, order=2 for acceleration
```

### Custom functions:
```
1. Define function constant (type=FUNCTION, formula="expression")
2. Use in calculated columns: "my_func({col1}, {col2}, param1, param2)"
3. Functions can use NumPy: np.sin(), np.sqrt(), etc.
```

## Version Information

All examples are compatible with **DataManip v0.2.0** and later.

Created: November 23, 2025
