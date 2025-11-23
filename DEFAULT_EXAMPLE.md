# Default Example: Free Fall Motion

When you launch DataManip, you'll see a comprehensive physics example demonstrating all column types and features.

## What You'll See

### "Physics Demo" Table

The default table simulates free fall motion from a height, showcasing all 5 column types:

1. **⋯ time** (RANGE column, blue)
   - Generated using `linspace(0, 3, 13)` 
   - Creates 13 time points from 0 to 3 seconds
   - Demonstrates automatic range generation

2. **✎ h0, h0_u** (DATA columns, black)
   - Initial height: 50.0 ± 0.5 m
   - Editable values with uncertainties
   - Shows manual data entry with error bars

3. **ƒ height, δ height_u** (CALCULATED + UNCERTAINTY, orange/purple)
   - Formula: `h0 - 0.5 * 9.81 * time²`
   - **Automatic uncertainty propagation** using symbolic differentiation
   - height_u created automatically when propagate_uncertainty=True

4. **d/dx velocity** (DERIVATIVE column, blue)
   - Numerical derivative: dh/dt
   - Uses numpy.gradient for accurate derivatives
   - Shows how velocity changes over time

5. **✎ mass** (DATA column)
   - Constant 2.0 kg for all time points

6. **ƒ KE** (CALCULATED column, orange)
   - Kinetic energy: `0.5 * mass * velocity²`
   - Shows formula chaining (uses derivative column)

7. **ƒ PE** (CALCULATED column, orange)
   - Potential energy: `mass * 9.81 * height`
   - Uses calculated height column

8. **ƒ total_energy** (CALCULATED column, orange)
   - Conservation of energy: `KE + PE`
   - Should remain approximately constant (~981 J)

## Features Demonstrated

✅ **5 Column Types**: DATA, CALCULATED, DERIVATIVE, RANGE, UNCERTAINTY  
✅ **Automatic Recalculation**: Change h0 → height updates → velocity recalculates → energies update  
✅ **Uncertainty Propagation**: Uses SymPy for symbolic differentiation (δf = √(Σ(∂f/∂xᵢ · δxᵢ)²))  
✅ **Formula Dependencies**: Columns depend on other calculated columns  
✅ **Workspace Constants**: g = 9.81 m/s² defined in Constants tab  
✅ **Units**: All columns have physical units  

## Try It Out

1. **Edit h0**: Change initial height → watch everything recalculate
2. **Edit h0_u**: Change uncertainty → height_u updates automatically
3. **Add Row**: Toolbar button to add more time points
4. **Add Column**: Try creating your own calculated column
5. **Check Constants Tab**: See workspace-level constants (g, pi)
6. **Keyboard Shortcuts**: 
   - Ctrl+R: Refresh/recalculate
   - Ctrl+D: Delete row
   - Ctrl+F: Find

## Theory

Free fall motion follows:
- Position: h(t) = h₀ - ½gt²
- Velocity: v(t) = -gt (derivative of position)
- Kinetic Energy: KE = ½mv²
- Potential Energy: PE = mgh
- Total Energy: E = KE + PE (conserved ≈ 981 J)

The example shows conservation of energy - as the object falls, potential energy converts to kinetic energy, but total energy remains constant!
