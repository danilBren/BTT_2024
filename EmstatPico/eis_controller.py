# Standard library imports
import datetime
import logging
import os
import os.path
import sys
import datetime

import plotly.graph_objects as go
import plotly.io as pio

# Third-party imports
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use the 'Agg' backend

# Local imports
import palmsens.instrument
import palmsens.mscript
import palmsens.serial

###############################################################################
# Start of configuration
###############################################################################

# COM port of the device (None = auto detect).
DEVICE_PORT = None

CURRENT_PATH = os.getcwd()
# Location of MethodSCRIPT file to use.
MSCRIPT_FILE_PATH = CURRENT_PATH + '/EmstatPico/palmsens/eis_twentus.mscr'
# MSCRIPT_FILE_PATH = '/home/twentus/TwentUs/twentus/MethodSCRIPTExample_Python/MethodSCRIPTExample_Python/scripts/example_eis.mscr'

# Location of output files. Directory will be created if it does not exist.
OUTPUT_PATH = CURRENT_PATH + '/EmstatPico/output'

###############################################################################
# End of configuration
###############################################################################
LOG = logging.getLogger(__name__)


class EISController:
    
    def __init__(self):
        self.port = DEVICE_PORT


    def open_connection(self):
        if self.port is None:
            self.port = palmsens.serial.auto_detect_port()

    def execute_mscr(self):
        
        # Create and open serial connection to the device.
        with palmsens.serial.Serial(self.port, 1) as comm:
            self.device = palmsens.instrument.Instrument(comm)
            self.device_type = self.device.get_device_type()

            print("...")
            # Read and send the MethodSCRIPT file.
            self.device.send_script(MSCRIPT_FILE_PATH)
            
            print("...")
            # Read the result lines.
            self.result_lines = self.device.readlines_until_end()
            
    def therest(self):
        
        # Store results in file.
        os.makedirs(OUTPUT_PATH, exist_ok=True)
        result_file_name = datetime.datetime.now().strftime('ms_plot_eis_%Y%m%d-%H%M%S.txt')
        result_file_path = os.path.join(OUTPUT_PATH, result_file_name)
        with open(result_file_path, 'wt', encoding='ascii') as file:
            file.writelines(self.result_lines)

        # Parse the result.
        self.curves = palmsens.mscript.parse_result_lines(self.result_lines)

        # Log the results.
        for curve in self.curves:
            for package in curve:
                LOG.info([str(value) for value in package])

        # Get the applied frequencies.
        self.applied_frequency = palmsens.mscript.get_values_by_column(self.curves, 0)
        # Get the measured real part of the complex impedance.
        self.measured_z_real = palmsens.mscript.get_values_by_column(self.curves, 1)
        # Get the measured imaginary part of the complex impedance.
        self.measured_z_imag = palmsens.mscript.get_values_by_column(self.curves, 2)

        # Calculate Z and phase.
        # Invert the imaginary part for the electrochemist convention.
        self.measured_z_imag = -self.measured_z_imag
        # Compose the complex impedance.
        self.z_complex = self.measured_z_real + 1j * self.measured_z_imag
        # Get the phase from the complex impedance in degrees.
        self.z_phase = np.angle(self.z_complex, deg=True)
        # Get the impedance value.
        self.z = np.abs(self.z_complex)


        # Find indices of NaN and infinite values in self.measured_z_real
        nan_indices_real = np.where(np.isnan(self.measured_z_real) | np.isinf(self.measured_z_real))[0]

        # Find indices of NaN and infinite values in self.measured_z_imag
        nan_indices_imag = np.where(np.isnan(self.measured_z_imag) | np.isinf(self.measured_z_imag))[0]

        # Combine the indices to be removed
        indices_to_remove = np.union1d(nan_indices_real, nan_indices_imag)

        # Remove the corresponding rows from both arrays
        self.measured_z_real = np.delete(self.measured_z_real, indices_to_remove)
        self.measured_z_imag = np.delete(self.measured_z_imag, indices_to_remove)

        # Find indices of NaN and infinite values in self.measured_z_real
        nan_indices_real = np.where(np.isnan(self.measured_z_real) | np.isinf(self.measured_z_real))[0]

        # Find indices of NaN and infinite values in self.measured_z_imag
        nan_indices_imag = np.where(np.isnan(self.measured_z_imag) | np.isinf(self.measured_z_imag))[0]

        # Combine the indices to be removed
        indices_to_remove = np.union1d(nan_indices_real, nan_indices_imag)

        # Remove the corresponding values from both arrays
        self.measured_z_real = np.delete(self.measured_z_real, indices_to_remove)
        self.measured_z_imag = np.delete(self.measured_z_imag, indices_to_remove)

        # # Plot the results.
        # # Show the Nyquist plot as figure 1.
        # plt.figure(1)
        # plt.plot(self.measured_z_real, self.measured_z_imag)
        # # Get the current hour and minute
        # current_time = datetime.datetime.now().strftime("%H:%M")

        # # Set the title with the current hour and minute
        # plt.title(f'Nyquist plot - Time: {current_time}')
        # plt.axis('equal')
        # plt.grid()
        # plt.xlabel("Z'")
        # plt.ylabel("-Z''")
        # plt.savefig('/home/twentus/TwentUs/twentus/EmstatPico/output/nyquist_plot.png')

        # # Show the Bode plot as dual y axis (sharing the same x axis).
        # fig, ax1 = plt.subplots()
        # ax2 = ax1.twinx()

        # ax1.set_xlabel('Frequency (Hz)')
        # ax1.grid(which='major', axis='x', linestyle='--', linewidth=0.5, alpha=0.5)
        # ax1.set_ylabel('Z', color=AX1_COLOR)
        # # Make x axis logarithmic.
        # ax1.semilogx(self.applied_frequency, self.z, color=AX1_COLOR)
        # # Show ticks.
        # ax1.tick_params(axis='y', labelcolor=AX1_COLOR)
        # # Turn on the minor ticks, which are required for the minor grid.
        # ax1.minorticks_on()
        # # Customize the major grid.
        # ax1.grid(which='major', axis='y', linestyle='--', linewidth=0.5, alpha=0.5, color=AX1_COLOR)

        # # We already set the x label with ax1.
        # ax2.set_ylabel('-Phase (degrees)', color=AX2_COLOR)
        # ax2.semilogx(self.applied_frequency, self.z_phase, color=AX2_COLOR)
        # ax2.tick_params(axis='y', labelcolor=AX2_COLOR)
        # ax2.minorticks_on()
        # ax2.grid(which='major', axis='y', linestyle='--', linewidth=0.5, alpha=0.5, color=AX2_COLOR)

        # fig.suptitle(f'Bode plot - Time: {current_time}')
        # fig.tight_layout()
        # fig.savefig('/home/twentus/TwentUs/twentus/EmstatPico/output/bode_plot.png')

    

    def test(self):
        # put file in output, include date and time in the name
        date_time = datetime.now()
        file_path = CURRENT_PATH + f'/EmstatPico/output/ms_plot_eis_{date_time}.txt'

        # Open the file in read mode using the full path
        with open(file_path, 'r') as file:
            # Read the lines and strip whitespace and newline characters
            self.result_lines = file.readlines()

        # print(items)  # This will print: ['item1', 'item2', 'item3']

  
        # Parse the result.
        self.curves = palmsens.mscript.parse_result_lines(self.result_lines)

        # Log the results.
        for curve in self.curves:
            for package in curve:
                LOG.info([str(value) for value in package])

        # Get the applied frequencies.
        self.applied_frequency = palmsens.mscript.get_values_by_column(self.curves, 0)
        # Get the measured real part of the complex impedance.
        self.measured_z_real = palmsens.mscript.get_values_by_column(self.curves, 1)
        # Get the measured imaginary part of the complex impedance.
        self.measured_z_imag = palmsens.mscript.get_values_by_column(self.curves, 2)

        # Calculate Z and phase.
        # Invert the imaginary part for the electrochemist convention.
        self.measured_z_imag = -self.measured_z_imag
        # Compose the complex impedance.
        self.z_complex = self.measured_z_real + 1j * self.measured_z_imag
        # Get the phase from the complex impedance in degrees.
        self.z_phase = np.angle(self.z_complex, deg=True)
        # Get the impedance value.
        self.z = np.abs(self.z_complex)


        # Find indices of NaN and infinite values in self.measured_z_real
        nan_indices_real = np.where(np.isnan(self.measured_z_real) | np.isinf(self.measured_z_real))[0]

        # Find indices of NaN and infinite values in self.measured_z_imag
        nan_indices_imag = np.where(np.isnan(self.measured_z_imag) | np.isinf(self.measured_z_imag))[0]

        # Combine the indices to be removed
        indices_to_remove = np.union1d(nan_indices_real, nan_indices_imag)

        # Remove the corresponding rows from both arrays
        self.measured_z_real = np.delete(self.measured_z_real, indices_to_remove)
        self.measured_z_imag = np.delete(self.measured_z_imag, indices_to_remove)

        # Find indices of NaN and infinite values in self.measured_z_real
        nan_indices_real = np.where(np.isnan(self.measured_z_real) | np.isinf(self.measured_z_real))[0]

        # Find indices of NaN and infinite values in self.measured_z_imag
        nan_indices_imag = np.where(np.isnan(self.measured_z_imag) | np.isinf(self.measured_z_imag))[0]

        # Combine the indices to be removed
        indices_to_remove = np.union1d(nan_indices_real, nan_indices_imag)

        # Remove the corresponding values from both arrays
        self.measured_z_real = np.delete(self.measured_z_real, indices_to_remove)
        self.measured_z_imag = np.delete(self.measured_z_imag, indices_to_remove)


        # Plot the results.
        # Show the Nyquist plot as figure 1.
        plt.figure(1)
        plt.plot(self.measured_z_real, self.measured_z_imag)
        # Get the current hour and minute
        current_time = datetime.datetime.now().strftime("%H:%M")

        # Set the title with the current hour and minute
        plt.title(f'Nyquist plot - Time: {current_time}')
        plt.axis('equal')
        plt.grid()
        plt.xlabel("Z'")
        plt.ylabel("-Z''")
        plt.savefig(CURRENT_PATH + '/EmstatPico/output/nyquist_plot.png')

        # # Show the Bode plot as dual y axis (sharing the same x axis).
        # fig, ax1 = plt.subplots()
        # ax2 = ax1.twinx()

        # ax1.set_xlabel('Frequency (Hz)')
        # ax1.grid(which='major', axis='x', linestyle='--', linewidth=0.5, alpha=0.5)
        # ax1.set_ylabel('Z', color=AX1_COLOR)
        # # Make x axis logarithmic.
        # ax1.semilogx(self.applied_frequency, self.z, color=AX1_COLOR)
        # # Show ticks.
        # ax1.tick_params(axis='y', labelcolor=AX1_COLOR)
        # # Turn on the minor ticks, which are required for the minor grid.
        # ax1.minorticks_on()
        # # Customize the major grid.
        # ax1.grid(which='major', axis='y', linestyle='--', linewidth=0.5, alpha=0.5, color=AX1_COLOR)

        # # We already set the x label with ax1.
        # ax2.set_ylabel('-Phase (degrees)', color=AX2_COLOR)
        # ax2.semilogx(self.applied_frequency, self.z_phase, color=AX2_COLOR)
        # ax2.tick_params(axis='y', labelcolor=AX2_COLOR)
        # ax2.minorticks_on()
        # ax2.grid(which='major', axis='y', linestyle='--', linewidth=0.5, alpha=0.5, color=AX2_COLOR)

        # fig.suptitle(f'Bode plot - Time: {current_time}')
        # fig.tight_layout()
        # fig.savefig('/home/twentus/TwentUs/twentus/EmstatPico/output/bode_plot.png')


# Plot colors.
AX1_COLOR = 'tab:red'   # Color for impedance (Z)
AX2_COLOR = 'tab:blue'  # Color for phase   

EXECUTE_MSCR = False
if __name__ == "__main__":
    
    eis = EISController()
    eis.open_connection()
    if (EXECUTE_MSCR) :
        eis.execute_mscr()
    else :
        pass
    eis.therest()