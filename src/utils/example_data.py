"""
Example datasets for DataManip application.

This module provides various pre-configured examples demonstrating
different features and use cases of the AdvancedDataTableWidget.

Each example is a function that takes an AdvancedDataTableWidget and
populates it with appropriate columns and data.
"""

from widgets.AdvancedDataTableWidget.advanced_datatable import AdvancedDataTableWidget
from utils.unit_simplification import simplify_derivative_unit
from PySide6.QtWidgets import QTableWidgetItem


def load_projectile_motion(table: AdvancedDataTableWidget):
    """Load Projectile Motion physics example - Baseball trajectory.
    
    Realistic scenario: Baseball hit at 45 m/s (162 km/h) at 35° angle.
    Demonstrates projectile motion with proper physical constants.
    
    Args:
        table: AdvancedDataTableWidget to populate
    """
    # Clear existing data
    table.clear()
    table.setRowCount(0)
    table.setColumnCount(0)
    
    # Set up physical constants using variable manager
    table._variables = {
        'g': (9.80665, 'm/s²'),      # Standard Earth gravity
        'v0': (45.0, 'm/s'),          # Initial velocity (162 km/h)
        'theta': (35.0, 'deg'),       # Launch angle
        'mass': (0.145, 'kg'),        # Baseball mass (official MLB)
    }
    
    # Calculate velocity components: v0x = v0*cos(θ), v0y = v0*sin(θ)
    # theta = 35° → cos(35°) ≈ 0.8192, sin(35°) ≈ 0.5736
    v0x = 45.0 * 0.8192  # ≈ 36.86 m/s
    v0y = 45.0 * 0.5736  # ≈ 25.81 m/s
    
    # Time range: 0 to flight time (approximately 5.3 seconds)
    table.addRangeColumn(
        header_label="Time",
        start=0.0,
        end=5.3,
        points=54,
        diminutive="t",
        unit="s",
        description="Time since ball was hit"
    )
    
    # Horizontal position: x = v0x * t
    table.addCalculatedColumn(
        header_label="Position X",
        formula="{v0} * 0.8192 * {t}",
        diminutive="x",
        unit="m",
        description="Horizontal distance (v0x = 36.86 m/s)",
        propagate_uncertainty=False
    )
    
    # Vertical position: y = v0y*t - 0.5*g*t²
    table.addCalculatedColumn(
        header_label="Position Y",
        formula="{v0} * 0.5736 * {t} - 0.5 * {g} * {t}**2",
        diminutive="y",
        unit="m",
        description="Height above ground (initial height = 1m)",
        propagate_uncertainty=False
    )
    
    # Total distance from origin
    table.addCalculatedColumn(
        header_label="Distance",
        formula="sqrt({x}**2 + {y}**2)",
        diminutive="r",
        unit="m",
        description="Straight-line distance from start",
        propagate_uncertainty=False
    )
    
    # Horizontal velocity (constant, no air resistance)
    x_col_idx = 1
    t_col_idx = 0
    table.addDerivativeColumn(
        header_label="Velocity X",
        numerator_index=x_col_idx,
        denominator_index=t_col_idx,
        diminutive="vx",
        unit=simplify_derivative_unit("m", "s"),  # m/s
        description="Horizontal velocity (constant ≈ 36.86 m/s)"
    )
    
    # Vertical velocity: vy = v0y - g*t
    y_col_idx = 2
    table.addDerivativeColumn(
        header_label="Velocity Y",
        numerator_index=y_col_idx,
        denominator_index=t_col_idx,
        diminutive="vy",
        unit=simplify_derivative_unit("m", "s"),  # m/s
        description="Vertical velocity (decreases with gravity)"
    )
    
    # Total velocity magnitude
    table.addCalculatedColumn(
        header_label="Speed",
        formula="sqrt({vx}**2 + {vy}**2)",
        diminutive="v",
        unit="m/s",
        description="Total speed at each instant",
        propagate_uncertainty=False
    )
    
    # Vertical acceleration (should be -g)
    vy_col_idx = 5
    table.addDerivativeColumn(
        header_label="Acceleration Y",
        numerator_index=vy_col_idx,
        denominator_index=t_col_idx,
        diminutive="ay",
        unit=simplify_derivative_unit("m/s", "s"),  # m/s²
        description="Vertical acceleration (gravity ≈ -9.81 m/s²)"
    )
    
    # Kinetic energy: KE = 0.5 * m * v²
    table.addCalculatedColumn(
        header_label="Kinetic Energy",
        formula="0.5 * {mass} * {v}**2",
        diminutive="KE",
        unit="J",
        description="Kinetic energy (baseball mass = 0.145 kg)",
        propagate_uncertainty=False
    )
    
    # Potential energy: PE = m * g * y (relative to ground)
    table.addCalculatedColumn(
        header_label="Potential Energy",
        formula="{mass} * {g} * {y}",
        diminutive="PE",
        unit="J",
        description="Gravitational potential energy",
        propagate_uncertainty=False
    )
    
    # Total mechanical energy (conserved in ideal case)
    table.addCalculatedColumn(
        header_label="Total Energy",
        formula="{KE} + {PE}",
        diminutive="E",
        unit="J",
        description="Total mechanical energy (should be constant ≈ 147 J)",
        propagate_uncertainty=False
    )
    
    # Force recalculation and resize
    table._recalculate_all_calculated_columns()
    table.resizeColumnsToContents()


def load_ideal_gas_law(table: AdvancedDataTableWidget):
    """Load Ideal Gas Law chemistry example - Heating a gas sample.
    
    Realistic scenario: 1.00 mole of nitrogen gas (N₂) in a 22.4 L container
    heated from 0°C to 100°C at constant volume.
    
    Args:
        table: AdvancedDataTableWidget to populate
    """
    # Clear existing data
    table.clear()
    table.setRowCount(0)
    table.setColumnCount(0)
    
    # Set up physical/chemical constants
    table._variables = {
        'R': (8.314462618, 'J/(mol·K)'),  # Universal gas constant (exact)
        'n': (1.00, 'mol'),                # Amount of gas (1 mole)
        'V': (0.0224, 'm³'),               # Volume (22.4 L = standard molar volume)
        'atm_to_Pa': (101325, 'Pa/atm'),  # Conversion factor
    }
    
    # Temperature range (273.15 to 373.15 K = 0°C to 100°C)
    table.addRangeColumn(
        header_label="Temperature",
        start=273.15,
        end=373.15,
        points=21,
        diminutive="T",
        unit="K",
        description="Temperature in Kelvin"
    )
    
    # Convert to Celsius
    table.addCalculatedColumn(
        header_label="Temp Celsius",
        formula="{T} - 273.15",
        diminutive="T_C",
        unit="°C",
        description="Temperature in Celsius",
        propagate_uncertainty=False
    )
    
    # Pressure using ideal gas law: P = nRT/V
    table.addCalculatedColumn(
        header_label="Pressure",
        formula="{n} * {R} * {T} / {V}",
        diminutive="P",
        unit="Pa",
        description="Pressure from ideal gas law PV=nRT",
        propagate_uncertainty=False
    )
    
    # Convert to kPa (more convenient unit)
    table.addCalculatedColumn(
        header_label="Pressure kPa",
        formula="{P} / 1000",
        diminutive="P_kPa",
        unit="kPa",
        description="Pressure in kilopascals",
        propagate_uncertainty=False
    )
    
    # Convert to atm (standard unit in chemistry)
    table.addCalculatedColumn(
        header_label="Pressure atm",
        formula="{P} / {atm_to_Pa}",
        diminutive="P_atm",
        unit="atm",
        description="Pressure in atmospheres",
        propagate_uncertainty=False
    )
    
    # Calculate dP/dT (Gay-Lussac's Law: P ∝ T at constant V and n)
    # Theoretical: dP/dT = nR/V ≈ 371.3 Pa/K
    P_col = 2
    T_col = 0
    table.addDerivativeColumn(
        header_label="dP/dT",
        numerator_index=P_col,
        denominator_index=T_col,
        diminutive="dPdT",
        unit=simplify_derivative_unit("Pa", "K"),  # Pa/K
        description="Rate of pressure increase (should be constant ≈ 371 Pa/K)"
    )
    
    # Internal energy for ideal monatomic gas: U = (3/2)nRT
    # For diatomic N₂: U = (5/2)nRT (includes rotational degrees of freedom)
    table.addCalculatedColumn(
        header_label="Internal Energy",
        formula="2.5 * {n} * {R} * {T}",
        diminutive="U",
        unit="J",
        description="Internal energy for diatomic gas (N₂)",
        propagate_uncertainty=False
    )
    
    table._recalculate_all_calculated_columns()
    table.resizeColumnsToContents()


def load_exponential_decay(table: AdvancedDataTableWidget):
    """Load Exponential Decay example - Carbon-14 dating.
    
    Realistic scenario: Carbon-14 radioactive decay for dating archaeological samples.
    Half-life: 5,730 years. Shows decay over 20,000 years.
    
    Args:
        table: AdvancedDataTableWidget to populate
    """
    # Clear existing data
    table.clear()
    table.setRowCount(0)
    table.setColumnCount(0)
    
    # Set up physical constants for C-14 decay
    table._variables = {
        't_half': (5730, 'years'),           # Carbon-14 half-life
        'lambda': (0.000120968, '1/year'),   # Decay constant: ln(2)/t_half
        'N0': (1e12, 'atoms'),               # Initial number of atoms
    }
    
    # Time range (0 to 20,000 years - about 3.5 half-lives)
    table.addRangeColumn(
        header_label="Time",
        start=0.0,
        end=20000.0,
        points=41,
        diminutive="t",
        unit="years",
        description="Time since organism died"
    )
    
    # Number of C-14 atoms: N(t) = N₀ * exp(-λt)
    table.addCalculatedColumn(
        header_label="C-14 Atoms",
        formula="{N0} * exp(-{lambda} * {t})",
        diminutive="N",
        unit="atoms",
        description="Number of C-14 atoms remaining",
        propagate_uncertainty=False
    )
    
    # Percentage remaining (important for dating)
    table.addCalculatedColumn(
        header_label="Percent Remaining",
        formula="100 * {N} / {N0}",
        diminutive="pct",
        unit="%",
        description="Percentage of original C-14",
        propagate_uncertainty=False
    )
    
    # Activity (decay rate): A = λN (proportional to detector counts)
    table.addCalculatedColumn(
        header_label="Activity",
        formula="{lambda} * {N}",
        diminutive="A",
        unit="decays/year",
        description="Radioactive activity (decay events per year)",
        propagate_uncertainty=False
    )
    
    # Number of half-lives elapsed
    table.addCalculatedColumn(
        header_label="Half-Lives",
        formula="{t} / {t_half}",
        diminutive="n_half",
        unit="",
        description="Number of half-lives elapsed",
        propagate_uncertainty=False
    )
    
    # Decay rate: dN/dt = -λN
    N_col = 1
    t_col = 0
    table.addDerivativeColumn(
        header_label="Decay Rate",
        numerator_index=N_col,
        denominator_index=t_col,
        diminutive="dNdt",
        unit=simplify_derivative_unit("atoms", "years"),  # atoms/year
        description="Rate of decay (dN/dt, should be negative)",
    )
    
    # Age determination: If we measure pct%, we can estimate age
    table.addCalculatedColumn(
        header_label="Estimated Age",
        formula="-{t_half} * log({pct}/100) / 0.693147",
        diminutive="age",
        unit="years",
        description="Age if this percentage was measured (verification)",
        propagate_uncertainty=False
    )
    
    table._recalculate_all_calculated_columns()
    table.resizeColumnsToContents()


def load_harmonic_motion(table: AdvancedDataTableWidget):
    """Load Simple Harmonic Motion example - Mass-spring system.
    
    Realistic scenario: 500g mass on a spring (k=10 N/m) with 20cm amplitude.
    Demonstrates SHM, derivatives, and energy conservation.
    
    Args:
        table: AdvancedDataTableWidget to populate
    """
    # Clear existing data
    table.clear()
    table.setRowCount(0)
    table.setColumnCount(0)
    
    # Set up physical constants for mass-spring system
    table._variables = {
        'm': (0.500, 'kg'),          # Mass (500 grams)
        'k': (10.0, 'N/m'),          # Spring constant
        'A': (0.20, 'm'),            # Amplitude (20 cm)
        'omega': (4.472, 'rad/s'),   # Angular frequency: ω = sqrt(k/m) ≈ 4.472 rad/s
        'T': (1.405, 's'),           # Period: T = 2π/ω ≈ 1.405 s
    }
    
    # Time range (0 to 3 complete periods ≈ 4.2 seconds)
    table.addRangeColumn(
        header_label="Time",
        start=0.0,
        end=4.215,
        points=85,
        diminutive="t",
        unit="s",
        description="Time since release"
    )
    
    # Position: x(t) = A * cos(ωt)
    table.addCalculatedColumn(
        header_label="Position",
        formula="{A} * cos({omega} * {t})",
        diminutive="x",
        unit="m",
        description="Position (A = 20 cm amplitude)",
        propagate_uncertainty=False
    )
    
    # Velocity: v(t) = dx/dt = -Aω * sin(ωt)
    x_col = 1
    t_col = 0
    table.addDerivativeColumn(
        header_label="Velocity",
        numerator_index=x_col,
        denominator_index=t_col,
        diminutive="v",
        unit=simplify_derivative_unit("m", "s"),  # m/s
        description="Velocity (dx/dt, max ≈ 0.89 m/s)"
    )
    
    # Acceleration: a(t) = dv/dt = -Aω² * cos(ωt) = -ω²x
    v_col = 2
    table.addDerivativeColumn(
        header_label="Acceleration",
        numerator_index=v_col,
        denominator_index=t_col,
        diminutive="a",
        unit=simplify_derivative_unit("m/s", "s"),  # m/s²
        description="Acceleration (dv/dt, proportional to -x)"
    )
    
    # Verify a = -ω²x relationship
    table.addCalculatedColumn(
        header_label="Check a=-ω²x",
        formula="-{omega}**2 * {x}",
        diminutive="a_theory",
        unit="m/s²",
        description="Theoretical acceleration (should match measured)",
        propagate_uncertainty=False
    )
    
    # Kinetic energy: KE = 0.5 * m * v²
    table.addCalculatedColumn(
        header_label="Kinetic Energy",
        formula="0.5 * {m} * {v}**2",
        diminutive="KE",
        unit="J",
        description="Kinetic energy",
        propagate_uncertainty=False
    )
    
    # Potential energy: PE = 0.5 * k * x²
    table.addCalculatedColumn(
        header_label="Potential Energy",
        formula="0.5 * {k} * {x}**2",
        diminutive="PE",
        unit="J",
        description="Elastic potential energy in spring",
        propagate_uncertainty=False
    )
    
    # Total energy (should be constant = 0.5*k*A² ≈ 0.20 J)
    table.addCalculatedColumn(
        header_label="Total Energy",
        formula="{KE} + {PE}",
        diminutive="E",
        unit="J",
        description="Total mechanical energy (conserved ≈ 0.20 J)",
        propagate_uncertainty=False
    )
    
    # Spring force: F = -kx (Hooke's law)
    table.addCalculatedColumn(
        header_label="Spring Force",
        formula="-{k} * {x}",
        diminutive="F",
        unit="N",
        description="Restoring force from spring (F = -kx)",
        propagate_uncertainty=False
    )
    
    table._recalculate_all_calculated_columns()
    table.resizeColumnsToContents()


def load_population_growth(table: AdvancedDataTableWidget):
    """Load Population Growth example - Bacterial culture in lab.
    
    Realistic scenario: E. coli bacteria in nutrient broth showing logistic growth.
    Initial population: 1000 cells, carrying capacity: 10⁹ cells, doubling time: 20 min.
    
    Args:
        table: AdvancedDataTableWidget to populate
    """
    # Clear existing data
    table.clear()
    table.setRowCount(0)
    table.setColumnCount(0)
    
    # Set up biological parameters
    table._variables = {
        'P0': (1000, 'cells'),           # Initial population
        'K': (1e9, 'cells'),             # Carrying capacity (1 billion cells)
        'r': (2.0772, '1/hour'),         # Growth rate: r = ln(2)/t_double = 0.693/20min ≈ 2.08/h
        't_double': (20, 'min'),         # Doubling time in exponential phase
    }
    
    # Time range (0 to 10 hours)
    table.addRangeColumn(
        header_label="Time",
        start=0.0,
        end=10.0,
        points=61,
        diminutive="t",
        unit="hours",
        description="Time since inoculation"
    )
    
    # Logistic growth: P(t) = K / (1 + ((K - P₀)/P₀) * e^(-rt))
    # Simplified: P(t) = K / (1 + A*e^(-rt)) where A = (K-P₀)/P₀ ≈ 999,000
    table.addCalculatedColumn(
        header_label="Population",
        formula="{K} / (1 + 999000 * exp(-{r} * {t}))",
        diminutive="P",
        unit="cells",
        description="Number of bacterial cells",
        propagate_uncertainty=False
    )
    
    # Log₁₀ of population (commonly plotted in microbiology)
    table.addCalculatedColumn(
        header_label="Log₁₀(P)",
        formula="log10({P})",
        diminutive="logP",
        unit="",
        description="Log₁₀ of population (exponential phase is linear)",
        propagate_uncertainty=False
    )
    
    # Percentage of carrying capacity
    table.addCalculatedColumn(
        header_label="% of Capacity",
        formula="100 * {P} / {K}",
        diminutive="pct_K",
        unit="%",
        description="Percentage of carrying capacity reached",
        propagate_uncertainty=False
    )
    
    # Population growth rate: dP/dt
    P_col = 1
    t_col = 0
    table.addDerivativeColumn(
        header_label="Growth Rate",
        numerator_index=P_col,
        denominator_index=t_col,
        diminutive="dPdt",
        unit=simplify_derivative_unit("cells", "hours"),  # cells/hour
        description="Population growth rate (dP/dt, peaks at mid-exponential)"
    )
    
    # Per capita growth rate: (1/P) * dP/dt
    # In logistic model: r_percapita = r(1 - P/K)
    table.addCalculatedColumn(
        header_label="Per Capita Rate",
        formula="{dPdt} / {P}",
        diminutive="r_pc",
        unit="1/hour",
        description="Per capita growth rate (decreases as P→K)",
        propagate_uncertainty=False
    )
    
    # Doubling time (varies with population)
    # t_double = ln(2) / r_percapita
    table.addCalculatedColumn(
        header_label="Doubling Time",
        formula="0.693147 / {r_pc}",
        diminutive="t_d",
        unit="hours",
        description="Instantaneous doubling time (increases as P→K)",
        propagate_uncertainty=False
    )
    
    # Cell density (assuming 100 mL culture volume)
    table.addCalculatedColumn(
        header_label="Density",
        formula="{P} / 100",
        diminutive="density",
        unit="cells/mL",
        description="Cell concentration (100 mL culture)",
        propagate_uncertainty=False
    )
    
    # Optical density proxy (OD₆₀₀ ∝ cell density, simplified)
    table.addCalculatedColumn(
        header_label="OD₆₀₀",
        formula="log10(1 + {density} / 1e6)",
        diminutive="OD",
        unit="AU",
        description="Optical density at 600nm (simplified model)",
        propagate_uncertainty=False
    )
    
    table._recalculate_all_calculated_columns()
    table.resizeColumnsToContents()


def load_titration_curve(table: AdvancedDataTableWidget):
    """Load Acid-Base Titration example - Weak acid titration.
    
    Realistic scenario: Titration of 25.0 mL of 0.100 M acetic acid (CH₃COOH)
    with 0.100 M sodium hydroxide (NaOH). Ka = 1.8×10⁻⁵.
    
    Args:
        table: AdvancedDataTableWidget to populate
    """
    # Clear existing data
    table.clear()
    table.setRowCount(0)
    table.setColumnCount(0)
    
    # Set up chemical constants
    table._variables = {
        'Ka': (1.8e-5, 'M'),             # Acetic acid dissociation constant
        'pKa': (4.745, ''),              # -log₁₀(Ka) ≈ 4.745
        'Kw': (1.0e-14, 'M²'),           # Water ionization constant
        'C_acid': (0.100, 'M'),          # Initial acid concentration
        'V_acid': (25.0, 'mL'),          # Volume of acid solution
        'C_base': (0.100, 'M'),          # Titrant (NaOH) concentration
    }
    
    # Volume of base added (0 to 40 mL, equivalence at 25 mL)
    table.addRangeColumn(
        header_label="Volume NaOH",
        start=0.0,
        end=40.0,
        points=81,
        diminutive="V",
        unit="mL",
        description="Volume of 0.100 M NaOH added"
    )
    
    # Simplified pH calculation (Henderson-Hasselbalch region + equivalence)
    # Before equivalence: pH ≈ pKa + log([A⁻]/[HA])
    # At equivalence (V=25): pH ≈ 8.72 (weak base)
    # After equivalence: pH determined by excess base
    # This is a simplified empirical model for demonstration
    table.addCalculatedColumn(
        header_label="pH",
        formula="{pKa} + log10(({V} + 0.1) / (25.1 - {V} + 0.1))",
        diminutive="pH",
        unit="",
        description="pH of solution (simplified model)",
        propagate_uncertainty=False
    )
    
    # Hydrogen ion concentration: [H⁺] = 10^(-pH)
    table.addCalculatedColumn(
        header_label="[H⁺]",
        formula="10**(-{pH})",
        diminutive="H",
        unit="M",
        description="Hydrogen ion concentration",
        propagate_uncertainty=False
    )
    
    # Hydroxide ion concentration: [OH⁻] = Kw / [H⁺]
    table.addCalculatedColumn(
        header_label="[OH⁻]",
        formula="{Kw} / {H}",
        diminutive="OH",
        unit="M",
        description="Hydroxide ion concentration",
        propagate_uncertainty=False
    )
    
    # pOH = 14 - pH
    table.addCalculatedColumn(
        header_label="pOH",
        formula="14 - {pH}",
        diminutive="pOH",
        unit="",
        description="pOH of solution",
        propagate_uncertainty=False
    )
    
    # Fraction titrated: f = V/V_eq
    table.addCalculatedColumn(
        header_label="Fraction Titrated",
        formula="{V} / {V_acid}",
        diminutive="f",
        unit="",
        description="Fraction of equivalence point reached",
        propagate_uncertainty=False
    )
    
    # Buffer capacity indicator: dpH/dV (resistance to pH change)
    # Low dpH/dV = good buffering, high dpH/dV = poor buffering
    pH_col = 1
    V_col = 0
    table.addDerivativeColumn(
        header_label="dpH/dV",
        numerator_index=pH_col,
        denominator_index=V_col,
        diminutive="slope",
        unit=simplify_derivative_unit("", "mL"),  # 1/mL
        description="Rate of pH change (buffering indicator, peak at equivalence)"
    )
    
    # Moles of acid initially
    table.addCalculatedColumn(
        header_label="Initial Acid",
        formula="{C_acid} * {V_acid} / 1000",
        diminutive="n_acid",
        unit="mmol",
        description="Initial moles of acetic acid",
        propagate_uncertainty=False
    )
    
    # Moles of base added
    table.addCalculatedColumn(
        header_label="Base Added",
        formula="{C_base} * {V} / 1000",
        diminutive="n_base",
        unit="mmol",
        description="Moles of NaOH added",
        propagate_uncertainty=False
    )
    
    table._recalculate_all_calculated_columns()
    table.resizeColumnsToContents()


def load_experimental_measurements(table: AdvancedDataTableWidget):
    """Load experimental data with measurement uncertainties.
    
    Demonstrates:
    - DATA columns with manual entry
    - UNCERTAINTY columns linked to DATA
    - Plotting with error bars
    - Realistic experimental uncertainties
    
    Scenario: Pendulum period vs. length experiment
    - Measure pendulum length L with ruler (±0.5 cm uncertainty)
    - Measure period T with stopwatch (±0.05 s uncertainty)
    - Calculate g from T = 2π√(L/g)
    - Show g_measured ± uncertainty
    
    Args:
        table: AdvancedDataTableWidget to populate
    """
    from widgets.AdvancedDataTableWidget.models import AdvancedColumnType, AdvancedColumnDataType
    import numpy as np
    
    # Clear existing data
    table.clear()
    table.setRowCount(0)
    table.setColumnCount(0)
    table._variables.clear()
    
    # Define physical constants as variables
    table._variables['pi'] = (3.141592653589793, '')
    
    # Create length column (measured)
    L_col = table.addColumn(
        header_label="Length",
        col_type=AdvancedColumnType.DATA,
        data_type=AdvancedColumnDataType.NUMERICAL,
        diminutive="L",
        unit="m",
        description="Pendulum length (measured with meter stick)"
    )
    
    # Create uncertainty column for length
    L_unc_col = table.addUncertaintyColumn(
        reference_column_index=L_col,
        header_label="Length Uncertainty",
        diminutive="dL"
    )
    
    # Create period column (measured)
    T_col = table.addColumn(
        header_label="Period",
        col_type=AdvancedColumnType.DATA,
        data_type=AdvancedColumnDataType.NUMERICAL,
        diminutive="T",
        unit="s",
        description="Period of oscillation (10 cycles / 10)"
    )
    
    # Create uncertainty column for period
    T_unc_col = table.addUncertaintyColumn(
        reference_column_index=T_col,
        header_label="Period Uncertainty",
        diminutive="dT"
    )
    
    # Calculate g from formula: g = 4π²L/T²
    g_col = table.addCalculatedColumn(
        header_label="Gravity (measured)",
        formula="4 * {pi}**2 * {L} / {T}**2",
        diminutive="g",
        unit="m/s²",
        description="Gravitational acceleration calculated from pendulum",
        propagate_uncertainty=True
    )
    
    # Experimental data (realistic measurements with uncertainties)
    # Lengths from 0.2 m to 1.0 m
    experimental_data = [
        # L(m),  ±dL(m), T(s),   ±dT(s)
        (0.20,   0.005,  0.898,  0.010),
        (0.30,   0.005,  1.100,  0.012),
        (0.40,   0.005,  1.270,  0.015),
        (0.50,   0.005,  1.420,  0.018),
        (0.60,   0.005,  1.556,  0.020),
        (0.70,   0.005,  1.682,  0.022),
        (0.80,   0.005,  1.798,  0.024),
        (0.90,   0.005,  1.907,  0.026),
        (1.00,   0.005,  2.010,  0.028),
    ]
    
    # Populate the data
    table.setRowCount(len(experimental_data))
    
    for row, (length, length_unc, period, period_unc) in enumerate(experimental_data):
        # Set length
        item = QTableWidgetItem(f"{length:.3f}")
        item.setData(0, length)
        table.setItem(row, L_col, item)
        
        # Set length uncertainty
        item = QTableWidgetItem(f"{length_unc:.4f}")
        item.setData(0, length_unc)
        table.setItem(row, L_unc_col, item)
        
        # Set period
        item = QTableWidgetItem(f"{period:.3f}")
        item.setData(0, period)
        table.setItem(row, T_col, item)
        
        # Set period uncertainty
        item = QTableWidgetItem(f"{period_unc:.4f}")
        item.setData(0, period_unc)
        table.setItem(row, T_unc_col, item)
    
    # Recalculate all columns
    table._recalculate_all_calculated_columns()
    
    print("\n" + "="*70)
    print("EXPERIMENTAL DATA: Pendulum Measurement")
    print("="*70)
    print("Objective: Determine gravitational acceleration (g) from pendulum")
    print("\nTheoretical formula: T = 2π√(L/g)")
    print("Rearranged: g = 4π²L/T²")
    print("\nMeasurement uncertainties:")
    print("  • Length: ±0.5 cm (ruler precision)")
    print("  • Period: ±0.01-0.03 s (stopwatch + reaction time)")
    print("\nExpected value: g ≈ 9.81 m/s²")
    print("\nUncertainty propagation:")
    print("  • Automatic using partial derivatives")
    print("  • δg = √[(∂g/∂L·δL)² + (∂g/∂T·δT)²]")
    print("\nVisualization:")
    print("  • Plot Tab: Plot T vs L with 'Show Uncertainty' enabled")
    print("  • Statistics Tab: Analyze g column to see mean ± std dev")
    print("  • Column g_u shows propagated uncertainty for each point")
    print("="*70 + "\n")


def load_empty_table(table: AdvancedDataTableWidget):
    """Load an empty table ready for custom data entry.
    
    Args:
        table: AdvancedDataTableWidget to populate
    """
    # Clear all data
    table.clear()
    table.setRowCount(0)
    table.setColumnCount(0)


# Dictionary mapping example names to their loader functions
EXAMPLES = {
    "Baseball Trajectory (Physics)": load_projectile_motion,
    "Heating Nitrogen Gas (Chemistry)": load_ideal_gas_law,
    "Carbon-14 Dating (Nuclear)": load_exponential_decay,
    "Mass-Spring Oscillator (Physics)": load_harmonic_motion,
    "Bacterial Growth (Biology)": load_population_growth,
    "Acetic Acid Titration (Chemistry)": load_titration_curve,
    "Pendulum Experiment (Uncertainties)": load_experimental_measurements,
    "Empty Table": load_empty_table,
}


def get_example_names():
    """Get list of all available example names.
    
    Returns:
        List of example names
    """
    return list(EXAMPLES.keys())


def load_example(table: AdvancedDataTableWidget, example_name: str):
    """Load a specific example by name.
    
    Args:
        table: AdvancedDataTableWidget to populate
        example_name: Name of the example to load
        
    Returns:
        True if example loaded successfully, False otherwise
    """
    if example_name in EXAMPLES:
        EXAMPLES[example_name](table)
        return True
    return False
