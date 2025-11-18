"""
Custom formulas example.

Demonstrates:
- Using mathematical functions in formulas
- Working with physical constants
- Unit conversions
- Advanced formula features
"""

from widgets import DataTableModel
import numpy as np

def custom_formulas_example():
    """Example of custom formulas with various mathematical functions."""
    model = DataTableModel()
    
    # Set up some mathematical and physical constants
    model.set_variables({
        'pi': np.pi,
        'e': np.e,
        'c': 299792458,  # Speed of light (m/s)
        'h': 6.62607015e-34,  # Planck's constant (J·s)
        'k': 1.380649e-23,  # Boltzmann constant (J/K)
    })
    
    # Create a range of x values
    model.add_range_column(
        name="x",
        start=0.0,
        end=10.0,
        points=21,
        unit="",
        description="Independent variable"
    )
    
    # Trigonometric functions
    model.add_calculated_column(
        name="sin_x",
        formula="sin({x})",
        description="Sine of x"
    )
    
    model.add_calculated_column(
        name="cos_x",
        formula="cos({x})",
        description="Cosine of x"
    )
    
    # Exponential and logarithmic
    model.add_calculated_column(
        name="exp_x",
        formula="exp({x})",
        description="e^x"
    )
    
    model.add_calculated_column(
        name="log_x",
        formula="log({x} + 1)",  # +1 to avoid log(0)
        description="Natural log of (x+1)"
    )
    
    # Compound expressions
    model.add_calculated_column(
        name="complex",
        formula="sin({x}) * exp(-{x}/5) + cos(2*{x})/2",
        description="Complex expression"
    )
    
    # Power functions
    model.add_calculated_column(
        name="power",
        formula="{x}**2 + 2*{x} + 1",
        description="Quadratic function"
    )
    
    # Using constants
    model.add_calculated_column(
        name="circle_area",
        formula="pi * {x}**2",
        unit="m²",
        description="Area of circle with radius x"
    )
    
    # Conditional-like expressions using abs
    model.add_calculated_column(
        name="wave",
        formula="abs(sin(2*pi*{x}/5))",
        description="Absolute value of sine wave"
    )
    
    return model

def physics_formulas_example():
    """Example of physics formulas with proper units."""
    model = DataTableModel()
    
    # Physical constants
    model.set_variables({
        'c': 299792458,  # m/s
        'epsilon_0': 8.854187817e-12,  # F/m
        'mu_0': 1.25663706212e-6,  # H/m
    })
    
    # Frequency range
    model.add_range_column(
        name="f",
        start=1e9,
        end=1e12,
        points=11,
        unit="Hz",
        description="Frequency"
    )
    
    # Wavelength
    model.add_calculated_column(
        name="lambda",
        formula="c / {f}",
        unit="m",
        description="Wavelength"
    )
    
    # Angular frequency
    model.add_calculated_column(
        name="omega",
        formula="2 * pi * {f}",
        unit="rad/s",
        description="Angular frequency"
    )
    
    # Photon energy
    model.add_calculated_column(
        name="E",
        formula="h * {f}",
        unit="J",
        description="Photon energy"
    )
    
    return model

if __name__ == "__main__":
    print("Custom Formulas Example 1: Mathematical Functions")
    print("="*80)
    model1 = custom_formulas_example()
    
    print(f"{'x':<8}{'sin(x)':<12}{'exp(x)':<12}{'complex':<12}")
    print("-"*80)
    for i in range(min(10, model1.rowCount())):
        x = model1.get_cell_value(i, "x")
        sin_x = model1.get_cell_value(i, "sin_x")
        exp_x = model1.get_cell_value(i, "exp_x")
        complex_val = model1.get_cell_value(i, "complex")
        print(f"{x:<8.2f}{sin_x:<12.4f}{exp_x:<12.4f}{complex_val:<12.4f}")
    
    model1.save_to_file("custom_formulas_math.json")
    
    print("\n\nCustom Formulas Example 2: Physics")
    print("="*80)
    model2 = physics_formulas_example()
    
    print(f"{'f(Hz)':<15}{'λ(m)':<15}{'E(J)':<15}")
    print("-"*80)
    for i in range(model2.rowCount()):
        f = model2.get_cell_value(i, "f")
        lambda_val = model2.get_cell_value(i, "lambda")
        e = model2.get_cell_value(i, "E")
        print(f"{f:<15.2e}{lambda_val:<15.2e}{e:<15.2e}")
    
    model2.save_to_file("custom_formulas_physics.json")
    print("\nData saved to custom_formulas_*.json")
