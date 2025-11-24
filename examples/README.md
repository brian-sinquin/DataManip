# DataManip Example Workspaces

This directory contains 10 realistic experimental physics examples that demonstrate all features of DataManip.

## Example Structure

**Tutorial Examples (01-06)** - One feature per example:
- Learn individual features step-by-step
- Focus on understanding one concept at a time
- Build foundation for complex experiments

**Complete Experiments (07-10)** - All features combined:
- Realistic experimental physics scenarios
- Demonstrate feature integration
- Show professional data analysis workflows

## Loading Examples

### In the Application
1. Launch: `uv run datamanip`
2. Go to **Examples** menu
3. Select any example
4. Example replaces current workspace

### From File Menu
1. Launch: `uv run datamanip`
2. **File → Open Workspace**
3. Navigate to `examples` directory
4. Select `.dmw` file

## Regenerating Examples

**All examples are code-generated for consistency.**

```bash
cd examples
uv run python generate_examples.py
```

Benefits:
- ✓ Consistent JSON structure
- ✓ Correct API usage
- ✓ Validated serialization
- ✓ Single source of truth

---

## Tutorial Examples (One Feature Each)

### 01 - Simple Pendulum
**Feature:** Basic data entry and plotting

Measure pendulum period vs length to verify T ∝ √L relationship.

**Skills:**
- Creating data columns
- Setting units
- Basic line plots with markers

**Data:** 9 measurements (L: 0.2-1.0 m)

---

### 02 - Resistor Network
**Feature:** Calculated columns with formulas

Calculate series and parallel resistor combinations.

**Skills:**
- Using formulas in calculated columns
- Multiple calculated columns from same data
- Comparing different calculations in plots

**Formulas:**
- R_series = R1 + R2
- R_parallel = (R1 × R2)/(R1 + R2)

---

### 03 - Free Fall
**Feature:** Range generation (linspace)

Free fall from 10m height with calculated positions and velocities.

**Skills:**
- Creating range columns with linspace
- Using workspace constants in formulas
- Kinematic equation implementation

**Constants:** g = 9.81 m/s², h0 = 10.0 m

---

### 04 - Inclined Plane
**Feature:** Numerical derivatives (1st and 2nd order)

Cart rolling down 2° incline - calculate velocity and acceleration from position data.

**Skills:**
- First derivatives (velocity from position)
- Second derivatives (acceleration from velocity)
- Multi-plot layouts for related quantities

**Data:** 9 position measurements over 4 seconds

---

### 05 - Density Measurement
**Feature:** Uncertainty propagation

Measure metal cylinder density with full error analysis (ρ = m/V).

**Skills:**
- Creating uncertainty columns
- Automatic propagation through calculations
- Error bars in plots (both axes)
- Volume calculation: V = πr²h

**Data:** 7 cylinders with mass, diameter, height uncertainties

---

### 06 - Damped Oscillation
**Feature:** Custom functions

Analyze damped harmonic motion with exponential decay envelope.

**Skills:**
- Defining custom functions
- Using NumPy in formulas
- Multiple parameters in functions
- Energy analysis (E ∝ A²)

**Functions:**
- damped_osc(t, A0, ω, γ)
- envelope(t, A0, γ)

---

## Complete Experimental Examples (All Features)

### 07 - Calorimetry
**Complete Experiment:** Heat capacity measurement

**Scenario:** Heating 200g water, measuring temperature rise, calculating power input and cumulative energy transfer.

**Features Used:**
- ✓ Range: Time axis (0-300s)
- ✓ Calculated: Temperature curve, cumulative heat
- ✓ Derivatives: Heating rate (dT/dt → power)
- ✓ Uncertainties: Thermometer precision (±0.1°C)
- ✓ Propagation: Energy uncertainty
- ✓ Constants: m_water, c_water
- ✓ Calculated constants: C_water = m × c
- ✓ Custom functions: heat_transfer(m, c, Tf, Ti)

**Physics:** Q = m × c × ΔT, P = C × dT/dt

**Plots:** Heating curve, power input, Q vs T

---

### 08 - Photoelectric Effect
**Complete Experiment:** Determining Planck's constant

**Scenario:** Measure stopping potentials for 6 wavelengths (UV to visible) to find h from Einstein's equation.

**Features Used:**
- ✓ Data: λ and V_stop measurements
- ✓ Calculated: Frequency (f = c/λ), kinetic energy
- ✓ Uncertainties: Spectrometer (±2 nm), voltmeter (±0.02 V)
- ✓ Propagation: Frequency and energy uncertainties
- ✓ Constants: c, e, work function φ
- ✓ Calculated constants: c_nm
- ✓ Custom functions: photon_energy(λ, h, c)

**Physics:** K = hf - φ, V_stop = K/e

**Plots:** V_stop vs f (slope = h/e), K vs λ

**Expected Result:** h ≈ 6.63×10⁻³⁴ J·s from linear fit

---

### 09 - Spring-Mass System
**Complete Experiment:** Simple harmonic motion with damping

**Scenario:** 250g mass on spring (k=25 N/m) with air resistance. Full energy analysis and phase space diagram.

**Features Used:**
- ✓ Range: Time axis (0-3.8s, 3 periods)
- ✓ Calculated: Position, kinetic/potential/total energy
- ✓ Derivatives: Velocity (1st), acceleration (2nd)
- ✓ Uncertainties: Position measurement (±2 mm)
- ✓ Propagation: Velocity, energy uncertainties
- ✓ Constants: m, k, b, x0
- ✓ Calculated constants: ω0, γ, ω, T
- ✓ Custom functions: position, velocity_analytic, KE, PE

**Physics:**
- ω₀ = √(k/m), γ = b/(2m), ω = √(ω₀² - γ²)
- x(t) = x0 e^(-γt) cos(ωt)
- E_total = ½kx² + ½mv² (decaying)

**Plots:** Position, phase space spiral, energy components

---

### 10 - Atwood Machine
**Complete Experiment:** Acceleration and tension measurement

**Scenario:** Two masses (200g and 250g) on pulley. Measure position vs time, calculate acceleration, compare with theory.

**Features Used:**
- ✓ Data: Time and height measurements
- ✓ Calculated: Theoretical position, net force, tension
- ✓ Derivatives: Velocity (1st), acceleration (2nd)
- ✓ Uncertainties: Timer (±5 ms), position (±5 mm)
- ✓ Propagation: v, a, F, T uncertainties
- ✓ Constants: m1, m2, g, h0
- ✓ Calculated constants: a_theory, T_theory
- ✓ Custom functions: position_atwood, tension

**Physics:**
- a = g(m2 - m1)/(m1 + m2)
- T = 2m1m2g/(m1 + m2)

**Plots:** Height (measured vs theory), velocity, acceleration, tension comparison

**Expected Results:** a ≈ 1.09 m/s², T ≈ 2.18 N

---

## Feature Reference

| Feature | Tutorial | Complete Experiments |
|---------|----------|---------------------|
| Data columns | 01, 04, 05 | 07, 08, 09, 10 |
| Calculated columns | 02, 03 | 07, 08, 09, 10 |
| Range generation | 03 | 07, 09 |
| Derivatives (1st) | 04 | 07, 09, 10 |
| Derivatives (2nd) | 04 | 09, 10 |
| Uncertainties | 05 | 07, 08, 09, 10 |
| Propagation | 05 | 07, 08, 09, 10 |
| Error bars | 05 | 07, 08, 09, 10 |
| Constants | 03 | 07, 08, 09, 10 |
| Calculated constants | - | 07, 09, 10 |
| Custom functions | 06 | 07, 08, 09, 10 |
| Multiple plots | 02, 03, 04, 06 | 07, 08, 09, 10 |

## Learning Path

### Beginner (Start Here)
1. **01 - Simple Pendulum**: Understand data entry and plots
2. **02 - Resistor Network**: Learn calculated columns
3. **03 - Free Fall**: Master range generation

### Intermediate
4. **04 - Inclined Plane**: Derivatives and multi-plot
5. **05 - Density Measurement**: Uncertainty propagation
6. **06 - Damped Oscillation**: Custom functions

### Advanced (Complete Workflows)
7. **07 - Calorimetry**: Thermal analysis with derivatives
8. **08 - Photoelectric Effect**: Quantum physics experiment
9. **09 - Spring-Mass System**: Phase space and energy
10. **10 - Atwood Machine**: Theory vs experiment comparison

## Common Patterns

### Error Propagation Workflow
```
1. Add data columns (measured values)
2. Add uncertainty columns (δ values, type=DATA)
3. Add calculated column with formula
4. Add uncertainty column (type=UNCERTAINTY, reference=calculated, propagate=True)
5. Plot with error bars (xerr_column, yerr_column)
```

### Derivative Analysis
```
1. Add range/data column (independent variable)
2. Add data/calculated column (dependent variable)
3. Add derivative column (type=DERIVATIVE, derivative_of=y, with_respect_to=x)
4. Set order=1 for first derivative, order=2 for second
```

### Custom Function Usage
```
1. Define in Constants widget (type=FUNCTION)
   - Formula: expression using parameters
   - Parameters: list of variable names
2. Use in calculated columns: my_func({col1}, {col2}, param)
3. Functions can use NumPy: np.sin(), np.sqrt(), etc.
```

---

## Version Information

All examples are compatible with **DataManip v0.2.0** and later.

**Created:** November 24, 2025  
**Examples:** 10 (6 tutorials + 4 complete experiments)  
**Total Features Demonstrated:** Data entry, calculated columns, ranges, derivatives (1st & 2nd), uncertainties, propagation, error bars, constants, calculated constants, custom functions, multiple plots
