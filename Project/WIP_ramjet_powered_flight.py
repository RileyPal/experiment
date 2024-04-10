import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# Constants
g = 9.81  # Gravitational constant (m/s^2)
lift_coefficient = 0.8  # Lift coefficient

data_table = {
    "Altitude (m)": [-1000, 0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 15000, 20000, 25000, 30000,
                      40000, 50000, 60000, 70000, 80000, 90000],
    "Density (kg/m^3)": [1.347, 1.225, 1.112, 1.007, 0.9093, 0.8194, 0.7364, 0.6601, 0.5900, 0.5258, 0.4671, 0.4135,
                         0.1948, 0.08891, 0.04008, 0.01841, 0.003996, 0.001027, 0.0003097, 0.00008283, 0.00001846, 0.0]
}


def air_density_func(y):
    # Retrieve altitude and density data from the data table
    altitudes = data_table["Altitude (m)"]
    densities = data_table["Density (kg/m^3)"]
    # Interpolate air density based on altitude
    return np.interp(y, altitudes, densities)



# Function to calculate thrust based on air density, velocity, and intake area
def thrust_function(air_density, velocity, intake_area, energy_density, mass_flow_rate):
    # Convert energy density from MJ/kg to J/kg
    energy_density = 50 # MJ in 1 kg of methane
    energy_density_joules_per_kg = energy_density * 1e6  # 1 MJ = 1e6 J

    # Calculate theoretical maximum thrust per unit mass of fuel (N/kg)
    theoretical_max_thrust_per_kg = mass_flow_rate * energy_density_joules_per_kg * 300 * 9.81  # Isp = 300 seconds

    # Calculate thrust based on intake area, air density, and velocity
    thrust = (air_density * velocity * intake_area + (0.2 * air_density * velocity * intake_area * 15.625 / 19.625)) * (
                theoretical_max_thrust_per_kg - velocity)

    return thrust



# Function to calculate acceleration
def acceleration_function(t, state, angle_of_attack, mass, lifting_area, intake_area):
    v, y = state  # Unpack state
    theta_rad = np.radians(angle_of_attack)  # Convert angle to radians

    # Calculate air density at current altitude
    air_density = air_density_func(y)
    # Define energy density of methane and mass flow rate of methane (sample values)
    energy_density_of_methane = 55.5  # MJ/kg
    # Calculate the mass flow rate of oxygen based on air density and intake area
    mass_flow_rate_of_oxygen = air_density * intake_area  # kg/s

    # Assuming stoichiometric combustion, determine the mass flow rate of methane
    # For each unit of oxygen, methane requires a certain amount according to the stoichiometry
    # Adjust the scaling factor according to the stoichiometry of the reaction
    methane_to_oxygen_ratio = 1.5  # Example: Assuming 1 mole of methane requires 1.5 moles of oxygen
    mass_flow_rate_of_methane = methane_to_oxygen_ratio * mass_flow_rate_of_oxygen  # Adjust this based on your stoichiometry

    # Calculate thrust based on air density, velocity, intake area, and the mass flow rate of methane
    T = thrust_function(air_density, v, intake_area, energy_density_of_methane, mass_flow_rate_of_methane)

    # Constants
    drag_coefficient = 0.25
    cross_sectional_area = 249

    # Calculate drag force magnitude
    v_magnitude = np.abs(v)
    drag_magnitude = 0.5 * drag_coefficient * air_density * cross_sectional_area * v_magnitude ** 2

    # Calculate lift force magnitude
    lift_magnitude = lift_coefficient * air_density * lifting_area * v_magnitude ** 2 * np.sin(theta_rad)

    # Calculate drag force components
    drag_horizontal = -np.sign(v) * drag_magnitude * np.cos(theta_rad)
    drag_vertical = -np.sign(v) * drag_magnitude  * np.sin(theta_rad)

    # Calculate lift force components
    lift_vertical = lift_magnitude * np.cos(theta_rad)
    lift_horizontal = lift_magnitude * -np.sin(theta_rad)

    # Calculate thrust components
    T_vertical = T * np.sin(theta_rad)
    T_horizontal = T * np.cos(theta_rad)

    # Calculate acceleration components
    a_vertical = (-g + drag_vertical + lift_vertical + T_vertical) / mass
    a_horizontal = (drag_horizontal + lift_horizontal + T_horizontal) / mass

    return [a_horizontal, a_vertical]  # Return [horizontal acceleration, vertical acceleration]


# Main function
def main():
    while True:
        try:
            # Prompt the user for input values
            velocity_mag = float(input("Enter the initial velocity magnitude (m/s) ex: 100 m/s would be the minimum to be within the edge of beleivability for Ramjet operation : "))
            angle_of_attack = float(input("Enter the angle of attack (degrees): "))
            mass = float(input(
                "Enter the mass of the craft (kg) ex: for Nasa's space shuttle (template used for drag calculation) use a mass of 70000 kg for mass when its carrying 2 tons of load: "))
            lifting_area = float(input("Enter the lifting area (m^2) ex: f104 starfighter had a lifting area of 18.2 m^2 *should presumably be small since we are trying to get out of the atmosphere*: "))
            intake_area = float(input("Enter the intake area (m^2) *realistically should be somewhere between 1-2.5 based on scaling nasas xf43 experimental ramjet craft to size of the space shuttle but is purely an estimate* : "))
        except ValueError:
            print("Invalid input. Please enter numeric values.")
            continue

        # Calculate initial velocity components
        v_horizontal = velocity_mag * np.cos(np.radians(angle_of_attack))
        v_vertical = velocity_mag * np.sin(np.radians(angle_of_attack))

        # Define initial vertical position
        y_initial = 0.0  # Assume starting from sea level

        # Define initial state
        state_initial = [v_horizontal, v_vertical]

        # Time span for integration (0 to 100 seconds)
        t_span = [0, 100]

        # Solve the ODE
        sol = solve_ivp(lambda t, state: acceleration_function(t, state, angle_of_attack, mass, lifting_area, intake_area),
                        t_span,
                        state_initial,
                        method='RK45',
                        t_eval=np.linspace(t_span[0], t_span[1], 100000))

        # Extract velocity and position from solution
        v_values = sol.y[:2]

        # Calculate acceleration values
        acceleration_values = np.array([acceleration_function(t, sol.y[:, i], angle_of_attack, mass, lifting_area, intake_area) for i, t in enumerate(sol.t)])

        # Plot the velocity and position graphs
        plt.figure(figsize=(12, 8))

        # Velocity plots
        plt.subplot(2, 2, 1)
        plt.plot(sol.t, v_values[0], label='Horizontal Velocity')
        plt.xlabel('Time (s)')
        plt.ylabel('Horizontal Velocity (m/s)')
        plt.title('Horizontal Velocity vs Time')
        plt.grid(True)
        plt.legend()

        plt.subplot(2, 2, 2)
        plt.plot(sol.t, v_values[1], label='Vertical Velocity')
        plt.xlabel('Time (s)')
        plt.ylabel('Vertical Velocity (m/s)')
        plt.title('Vertical Velocity vs Time')
        plt.grid(True)
        plt.legend()

        # Acceleration plots
        plt.subplot(2, 2, 3)
        plt.plot(sol.t, acceleration_values[:, 0], label='Horizontal Acceleration', color='blue')
        plt.xlabel('Time (s)')
        plt.ylabel('Horizontal Acceleration (m/s^2)')
        plt.title('Horizontal Acceleration vs Time')
        plt.grid(True)
        plt.legend()

        plt.subplot(2, 2, 4)
        plt.plot(sol.t, acceleration_values[:, 1], label='Vertical Acceleration', color='green')
        plt.xlabel('Time (s)')
        plt.ylabel('Vertical Acceleration (m/s^2)')
        plt.title('Vertical Acceleration vs Time')
        plt.grid(True)
        plt.legend()

        plt.tight_layout()
        plt.show()

        # Ask the user if they want to continue or exit
        choice = input("Do you want to input another set of parameters? (yes/no): ").lower()
        if choice != 'yes':
            break


# Execute the main function
if __name__ == "__main__":
    main()
