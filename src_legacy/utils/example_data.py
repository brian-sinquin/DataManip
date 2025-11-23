# Example datasets for DataManip application
# Reimplemented for new DataTable API

from widgets import DataTableWidget, ColumnType, DataType
import math


def _clear_all_columns(model):
    """Safely clear all columns from a DataTable model.
    
    Removes columns in reverse dependency order to avoid errors.
    
    Args:
        model: DataTableModel instance
    """
    max_iterations = 100  # Safety limit
    iteration = 0
    
    while model.get_column_names() and iteration < max_iterations:
        cols = model.get_column_names()
        removed = False
        
        # Try removing from the end (usually has fewer dependencies)
        for col_name in reversed(cols):
            try:
                model.remove_column(col_name)
                removed = True
                break
            except Exception:
                continue
        
        if not removed:
            # If we can't remove any column, force clear
            print(f"Warning: Could not remove some columns, forcing clear of {len(cols)} columns")
            break
        
        iteration += 1
    
    # Final check - if columns remain, clear the entire model
    if model.get_column_names():
        print("Warning: Forcing model clear")
        # Clear variables too
        model.set_variables({})


def load_projectile_motion(table: DataTableWidget):
    """Load Projectile Motion physics example - Baseball trajectory.
    
    Realistic scenario: Baseball hit at 45 m/s (162 km/h) at 35° angle.
    Demonstrates projectile motion with proper physical constants.
    
    Args:
        table: DataTableWidget to populate
        
    Returns:
        True if successful
    """
    try:
        # Get the model
        model = table.model()
        
        # Clear existing data
        _clear_all_columns(model)
        
        # Set up physical constants using global variables
        model.set_variables({
            'g': (9.80665, 'm/s²'),      # Standard gravity
            'v0': (45.0, 'm/s'),          # Initial velocity (162 km/h)
            'theta': (35.0, 'deg'),       # Launch angle
            'mass': (0.145, 'kg')         # Baseball mass
        })
        
        # Calculate derived constants
        theta_rad = 35.0 * math.pi / 180.0
        v0x = 45.0 * math.cos(theta_rad)  # ~36.86 m/s
        v0y = 45.0 * math.sin(theta_rad)  # ~25.81 m/s
        
        # Flight time calculation: t_max = 2 * v0y / g
        t_max = 2 * v0y / 9.80665  # ~5.27 seconds
        
        # Add time column (independent variable)
        model.add_range_column(
            name="t",
            start=0.0,
            end=t_max,
            points=54,  # ~0.1 second intervals
            unit="s",
            description="Time since launch"
        )
        
        # Add horizontal position: x = v0*cos(θ)*t
        model.add_calculated_column(
            name="x",
            formula=f"{v0x:.6f} * {{t}}",
            unit="m",
            description="Horizontal position",
            precision=2
        )
        
        # Add vertical position: y = v0*sin(θ)*t - 0.5*g*t²
        model.add_calculated_column(
            name="y",
            formula=f"{v0y:.6f} * {{t}} - 0.5 * {{g}} * {{t}}**2",
            unit="m",
            description="Vertical position",
            precision=2
        )
        
        # Add distance from origin: r = sqrt(x² + y²)
        model.add_calculated_column(
            name="r",
            formula="({x}**2 + {y}**2)**0.5",
            unit="m",
            description="Distance from origin",
            precision=2
        )
        
        # Add derivatives for velocity components
        model.add_derivative_column(
            name="vx",
            numerator="x",
            denominator="t",
            method="central",
            description="Horizontal velocity (should be constant)",
            precision=2
        )
        
        model.add_derivative_column(
            name="vy",
            numerator="y",
            denominator="t",
            method="central",
            description="Vertical velocity (decreases with time)",
            precision=2
        )
        
        # Add total speed: v = sqrt(vx² + vy²)
        model.add_calculated_column(
            name="v",
            formula="({vx}**2 + {vy}**2)**0.5",
            unit="m/s",
            description="Total speed",
            precision=2
        )
        
        # Add vertical acceleration (derivative of vy)
        model.add_derivative_column(
            name="ay",
            numerator="vy",
            denominator="t",
            method="central",
            description="Vertical acceleration (should be -g)",
            precision=2
        )
        
        # Add kinetic energy: KE = 0.5 * m * v²
        model.add_calculated_column(
            name="KE",
            formula="0.5 * {mass} * {v}**2",
            unit="J",
            description="Kinetic energy",
            precision=2
        )
        
        # Add potential energy: PE = m * g * y
        model.add_calculated_column(
            name="PE",
            formula="{mass} * {g} * {y}",
            unit="J",
            description="Potential energy",
            precision=2
        )
        
        # Add total mechanical energy: E = KE + PE (should be conserved)
        model.add_calculated_column(
            name="E",
            formula="{KE} + {PE}",
            unit="J",
            description="Total mechanical energy (conserved)",
            precision=2
        )
        
        print("\n" + "="*70)
        print("PHYSICS EXAMPLE: BASEBALL TRAJECTORY")
        print("="*70)
        print("Realistic scenario:")
        print("  • Baseball hit at 45 m/s (162 km/h)")
        print("  • Launch angle: θ = 35°")
        print("  • Mass: 0.145 kg (official MLB baseball)")
        print("  • Standard gravity: g = 9.80665 m/s²")
        print("\nPhysical constants defined (use Variables dialog to view):")
        print("  • g = 9.80665 m/s²")
        print("  • v0 = 45.0 m/s")
        print("  • theta = 35.0 deg")
        print("  • mass = 0.145 kg")
        print("\nColumns created:")
        print("  [RANGE]  t - Time (0 to {:.2f} s)".format(t_max))
        print("  [CALC]   x - Horizontal position")
        print("  [CALC]   y - Vertical position")
        print("  [CALC]   r - Distance from origin")
        print("  [DERIV]  vx - Horizontal velocity")
        print("  [DERIV]  vy - Vertical velocity")
        print("  [CALC]   v - Total speed")
        print("  [DERIV]  ay - Vertical acceleration")
        print("  [CALC]   KE - Kinetic energy")
        print("  [CALC]   PE - Potential energy")
        print("  [CALC]   E - Total energy (conserved)")
        print("\nTry:")
        print("  • Plot x vs y to see the parabolic trajectory!")
        print("  • Right-click → 'Manage Variables...' to see constants")
        print("  • Energy should be conserved (~146.7 J)")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"Error loading projectile motion example: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_ideal_gas(table: DataTableWidget):
    """Load Ideal Gas Law example - Temperature vs Pressure relationship.
    
    Demonstrates: PV = nRT
    Fixed: Volume = 1.0 L, n = 0.1 mol
    Variable: Temperature (200-400 K)
    Calculate: Pressure
    
    Args:
        table: DataTableWidget to populate
        
    Returns:
        True if successful
    """
    try:
        model = table.model()
        
        # Clear existing data
        _clear_all_columns(model)
        
        # Set up constants
        model.set_variables({
            'R': (8.314, 'J/(mol*K)'),  # Universal gas constant
            'n': (0.1, 'mol'),           # Amount of gas (0.1 moles)
            'V': (1.0, 'L')              # Volume (1 liter)
        })
        
        # Temperature range (200-400 K in 5K steps)
        model.add_range_column(
            name="T",
            start=200.0,
            end=400.0,
            points=41,
            unit="K",
            description="Temperature"
        )
        
        # Pressure using ideal gas law: P = nRT/V
        # Convert L to m³: 1 L = 0.001 m³
        model.add_calculated_column(
            name="P",
            formula="{n} * {R} * {T} / ({V} * 0.001)",
            unit="Pa",
            description="Pressure from ideal gas law",
            precision=1
        )
        
        # Convert pressure to atmospheres (1 atm = 101325 Pa)
        model.add_calculated_column(
            name="P_atm",
            formula="{P} / 101325",
            unit="atm",
            description="Pressure in atmospheres",
            precision=3
        )
        
        # Add derivative to show dP/dT (constant for ideal gas)
        model.add_derivative_column(
            name="dPdT",
            numerator="P",
            denominator="T",
            method="central",
            description="Rate of pressure change with temperature",
            precision=2
        )
        
        print("\n" + "="*70)
        print("PHYSICS EXAMPLE: IDEAL GAS LAW")
        print("="*70)
        print("Demonstrates: PV = nRT")
        print("\nConstants:")
        print("  • R = 8.314 J/(mol·K) - Universal gas constant")
        print("  • n = 0.1 mol - Amount of gas")
        print("  • V = 1.0 L - Volume")
        print("\nColumns:")
        print("  [RANGE]  T - Temperature (200-400 K)")
        print("  [CALC]   P - Pressure (Pa)")
        print("  [CALC]   P_atm - Pressure (atm)")
        print("  [DERIV]  dP/dT - Pressure change rate")
        print("\nTry:")
        print("  • Plot P vs T to see linear relationship")
        print("  • dP/dT should be constant (~83.14 Pa/K)")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"Error loading ideal gas example: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_harmonic_oscillator(table: DataTableWidget):
    """Load Simple Harmonic Motion example - Mass on a spring.
    
    Demonstrates: x(t) = A·cos(ωt + φ)
    Shows position, velocity, acceleration for oscillating mass.
    
    Args:
        table: DataTableWidget to populate
        
    Returns:
        True if successful
    """
    try:
        model = table.model()
        
        # Clear existing data
        _clear_all_columns(model)
        
        # Physical parameters
        model.set_variables({
            'A': (0.1, 'm'),           # Amplitude (10 cm)
            'omega': (3.14159, 'rad/s'), # Angular frequency (π rad/s, T ≈ 2s)
            'phi': (0.0, 'rad'),       # Phase angle
            'mass': (0.5, 'kg'),       # Mass of oscillator
            'k': (4.935, 'N/m')        # Spring constant (k = m·ω²)
        })
        
        # Time range (2 complete periods)
        model.add_range_column(
            name="t",
            start=0.0,
            end=4.0,
            points=81,
            unit="s",
            description="Time"
        )
        
        # Position: x = A·cos(ωt + φ)
        model.add_calculated_column(
            name="x",
            formula="{A} * cos({omega} * {t} + {phi})",
            unit="m",
            description="Position (displacement from equilibrium)",
            precision=4
        )
        
        # Velocity: v = dx/dt
        model.add_derivative_column(
            name="v",
            numerator="x",
            denominator="t",
            method="central",
            description="Velocity",
            precision=4
        )
        
        # Acceleration: a = dv/dt
        model.add_derivative_column(
            name="a",
            numerator="v",
            denominator="t",
            method="central",
            description="Acceleration",
            precision=4
        )
        
        # Kinetic energy: KE = ½mv²
        model.add_calculated_column(
            name="KE",
            formula="0.5 * {mass} * {v}**2",
            unit="J",
            description="Kinetic energy",
            precision=5
        )
        
        # Potential energy: PE = ½kx²
        model.add_calculated_column(
            name="PE",
            formula="0.5 * {k} * {x}**2",
            unit="J",
            description="Potential energy (spring)",
            precision=5
        )
        
        # Total mechanical energy (should be conserved)
        model.add_calculated_column(
            name="E",
            formula="{KE} + {PE}",
            unit="J",
            description="Total mechanical energy (conserved)",
            precision=5
        )
        
        print("\n" + "="*70)
        print("PHYSICS EXAMPLE: SIMPLE HARMONIC MOTION")
        print("="*70)
        print("Mass on a spring: x(t) = A·cos(ωt + φ)")
        print("\nConstants:")
        print("  • A = 0.1 m - Amplitude")
        print("  • ω = π rad/s - Angular frequency")
        print("  • mass = 0.5 kg")
        print("  • k = 4.935 N/m - Spring constant")
        print("\nColumns:")
        print("  [RANGE]  t - Time (0-4 s, 2 periods)")
        print("  [CALC]   x - Position")
        print("  [DERIV]  v - Velocity (dx/dt)")
        print("  [DERIV]  a - Acceleration (dv/dt)")
        print("  [CALC]   KE - Kinetic energy")
        print("  [CALC]   PE - Potential energy")
        print("  [CALC]   E - Total energy (conserved)")
        print("\nTry:")
        print("  • Plot x vs t to see sinusoidal motion")
        print("  • Plot KE and PE vs t - they oscillate!")
        print("  • Total energy E ≈ 0.024675 J (constant)")
        print("  • Acceleration should satisfy: a = -ω²x")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"Error loading harmonic oscillator example: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_rc_circuit(table: DataTableWidget):
    """Load RC Circuit example - Capacitor charging.
    
    Demonstrates: V(t) = V₀(1 - e^(-t/τ)) where τ = RC
    Shows voltage and current during capacitor charging.
    
    Args:
        table: DataTableWidget to populate
        
    Returns:
        True if successful
    """
    try:
        model = table.model()
        
        # Clear existing data
        _clear_all_columns(model)
        
        # Circuit parameters
        model.set_variables({
            'V0': (9.0, 'V'),          # Supply voltage (9V battery)
            'R': (10000.0, 'ohm'),     # Resistance (10 kΩ)
            'C': (0.0001, 'F'),        # Capacitance (100 μF)
            'tau': (1.0, 's')          # Time constant τ = RC = 1 s
        })
        
        # Time range (5 time constants for ~99% charge)
        model.add_range_column(
            name="t",
            start=0.0,
            end=5.0,
            points=101,
            unit="s",
            description="Time since switch closed"
        )
        
        # Capacitor voltage: V = V₀(1 - e^(-t/τ))
        model.add_calculated_column(
            name="Vc",
            formula="{V0} * (1 - exp(-{t}/{tau}))",
            unit="V",
            description="Voltage across capacitor",
            precision=3
        )
        
        # Resistor voltage: VR = V₀ - Vc
        model.add_calculated_column(
            name="Vr",
            formula="{V0} - {Vc}",
            unit="V",
            description="Voltage across resistor",
            precision=3
        )
        
        # Current: I = VR/R = (V₀/R)e^(-t/τ)
        model.add_calculated_column(
            name="I",
            formula="{Vr} / {R}",
            unit="A",
            description="Current through circuit",
            precision=6
        )
        
        # Current in milliamps for easier reading
        model.add_calculated_column(
            name="I_mA",
            formula="{I} * 1000",
            unit="mA",
            description="Current in milliamps",
            precision=3
        )
        
        # Charge on capacitor: Q = C·Vc
        model.add_calculated_column(
            name="Q",
            formula="{C} * {Vc}",
            unit="C",
            description="Charge stored on capacitor",
            precision=6
        )
        
        # Energy stored in capacitor: E = ½CV²
        model.add_calculated_column(
            name="E",
            formula="0.5 * {C} * {Vc}**2",
            unit="J",
            description="Energy stored in capacitor",
            precision=6
        )
        
        # Derivative: dVc/dt (charging rate)
        model.add_derivative_column(
            name="dVdt",
            numerator="Vc",
            denominator="t",
            method="central",
            description="Rate of voltage change",
            precision=3
        )
        
        print("\n" + "="*70)
        print("PHYSICS EXAMPLE: RC CIRCUIT - CAPACITOR CHARGING")
        print("="*70)
        print("Circuit: 9V battery, 10kΩ resistor, 100μF capacitor")
        print("Equation: V(t) = V₀(1 - e^(-t/τ)) where τ = RC")
        print("\nConstants:")
        print("  • V₀ = 9.0 V - Supply voltage")
        print("  • R = 10 kΩ - Resistance")
        print("  • C = 100 μF - Capacitance")
        print("  • τ = RC = 1.0 s - Time constant")
        print("\nColumns:")
        print("  [RANGE]  t - Time (0-5 s)")
        print("  [CALC]   Vc - Capacitor voltage")
        print("  [CALC]   Vr - Resistor voltage")
        print("  [CALC]   I - Current (A)")
        print("  [CALC]   I_mA - Current (mA)")
        print("  [CALC]   Q - Charge on capacitor")
        print("  [CALC]   E - Energy stored")
        print("  [DERIV]  dV/dt - Charging rate")
        print("\nTry:")
        print("  • Plot Vc vs t - exponential rise to 9V")
        print("  • Plot I vs t - exponential decay from 0.9 mA")
        print("  • At t=τ (1s), voltage reaches ~63.2% of V₀")
        print("  • At t=5τ, capacitor is ~99% charged")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"Error loading RC circuit example: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_example_names():
    """Get list of available example names.
    
    Returns:
        List of example names
    """
    return [
        "Projectile Motion",
        "Ideal Gas Law",
        "Simple Harmonic Motion",
        "RC Circuit Charging"
    ]


def load_example(table: DataTableWidget, example_name: str):
    """Load a specific example by name.
    
    Args:
        table: DataTableWidget to populate
        example_name: Name of example to load
        
    Returns:
        True if successful, False otherwise
    """
    examples = {
        "Projectile Motion": load_projectile_motion,
        "Ideal Gas Law": load_ideal_gas,
        "Simple Harmonic Motion": load_harmonic_oscillator,
        "RC Circuit Charging": load_rc_circuit,
    }
    
    loader = examples.get(example_name)
    if loader:
        return loader(table)
    else:
        print(f"Unknown example: {example_name}")
        return False
