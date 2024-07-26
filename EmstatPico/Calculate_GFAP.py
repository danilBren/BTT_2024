import numpy as np
import matplotlib.pyplot as plt

from scipy.optimize import minimize
from scipy.optimize import least_squares
from scipy.optimize import curve_fit
from scipy.linalg import lstsq
from scipy.optimize import nnls
from sympy import factorint
from sklearn.linear_model import HuberRegressor
from sympy import primerange



class GFAPCalc:
    def __init__(self, blanc, gfap):
        self.blanc_measurement = blanc
        self.gfap_measurement = gfap
    
    def circlefit(self, data, solverflag=0):
        # # test the argument
        # if (len(data) < 1) or (len(data) > 2):
        #     raise ValueError('Accepts only one or two arguments')
        # if len(data) == 1:
        #     solverflag = 0
        # elif solverflag not in [0, 1]:
        #     raise ValueError('If supplied, robustflag must be 0 or 1')
        
        n, p = data.shape
        if p < 2:
            raise ValueError('The data must lie in a p-dimensional space, where p >= 2')
        elif n <= p:
            raise ValueError('There must be at least p+1 data points (rows of data)')
        
        if n == 3:
            I2 = np.array([3, 1, 2, 2, 3, 1])
            I1 = np.tile(np.arange(1, n+1), 2)
            k = 2
        elif n <= 5:
            I2 = np.arange(1, n+1)
            I2 = np.concatenate([np.roll(I2, 1), np.roll(I2, 2), np.roll(I2, 3)])
            I1 = np.tile(np.arange(1, n+1), 3)
            k = 3
        else:
            # trying to be tricky here...
            coprimes = np.array([2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97])
            coprimes = np.setdiff1d(coprimes, np.unique(list(factorint(n).keys())))
            I2 = 1 + np.mod(np.arange(1, n+1) * coprimes[0], n)
            I2 = np.concatenate([I2, 1 + np.mod(I2 * coprimes[1], n), 1 + np.mod(np.roll(I2, 1) * coprimes[2], n)])
            I1 = np.tile(np.arange(1, n+1), 3)
            k = 3
        
    
        # build the linear least squares problem for
        # the center coordinates of the sphere.
        A = np.zeros((k*n, p))
        rhs = np.zeros((k*n, 1))
        rhs1 = np.zeros((k*n, 1))
        rhs2 = np.zeros((k*n, 1))
        I1t = I1 - 1
        I2t = I2 - 1

        A[:, 0] = 2 * (data[I1-1, 0] - data[I2-1, 0])
        
        data1 = (data[I1-1, 0] ** 2)
        data2 = (data[I2-1, 0] ** 2)
        rhs1 = data1 - data2
        
        A[:, 1] = 2 * (data[I1-1, 1] - data[I2-1, 1])
        
        data1 = (data[I1-1, 1] ** 2)
        data2 = (data[I2-1, 1] ** 2)
        rhs = rhs1 + data1 - data2
        
        
        # solve using backslash for the center
        C = np.linalg.lstsq(A, rhs, rcond=None)[0].T

        # recover the radius
        R = np.sqrt(np.mean(np.sum((data - np.tile(C, (n, 1)))**2, axis=1)))
        
        # a measure of the errors, in terms of the distance from each
        # point to the estimated circle
        resids = np.sqrt(np.sum((data - np.tile(C, (n, 1)))**2, axis=1)) - R
        rmse = np.sqrt(np.mean(resids**2))
        
        return C, R, rmse
    
    def calculate_gfap(self):
        ZRealArray = [self.blanc_measurement[0], self.gfap_measurement[0]]
        ZImgArray = [self.blanc_measurement[1], self.gfap_measurement[1]]

        # Plot the Nyquist graphs and fitted circles
        plt.figure(figsize=(10, 5))
        intercepts_alt = [[0,0],[0,0]]
        intercepts = []
        for i in range(2):
            X = ZRealArray[i]
            Y = ZImgArray[i]

            xy = np.column_stack((X, Y))  # Combine X and Y arrays
            C, R, rmse = self.circlefit(xy)
            theta = np.linspace(0, np.pi, 100)
            
            print("centre: ", C, " radius: ",R, " rmse: ", rmse)
            xc = C[0]/1 + (R/1) * np.cos(theta)
            yc = C[1]/1 + (R/1) * np.sin(theta)

            # alternative the intercept at zero
            temp = xc[yc > 0]
            intercepts_alt[i] = [temp[0], temp[-1]]
            plt.plot(temp[0], 0, "rx")
            plt.plot(temp[-1], 0, "rx")
            plt.plot(xc, yc, color='grey', linestyle='dashed', label=f'Fitted Circle {i+1}')

        Rs_blank_alt = intercepts_alt[0][0] - intercepts_alt[0][1]
        Rs_sample_alt = intercepts_alt[1][0] - intercepts_alt[1][1]
        deltaRs_alt = ((Rs_sample_alt - Rs_blank_alt) / Rs_blank_alt)

        print("Delta Rs (alternative):", deltaRs_alt)

        # Plot Nyquist graphs
        for i in range(2):
            plt.plot(ZRealArray[i], ZImgArray[i], label=f'Data Set {i+1}')

        plt.xlabel('Real Part')
        plt.ylabel('Imaginary Part')
        plt.title('Nyquist Plots and Fitted Circles')
        plt.legend()
        plt.grid(True)
        plt.axis('equal')  # Equal aspect ratio
        # plt.show()
        plt.savefig('/home/twentus/TwentUs/twentus/EmstatPico/output/curve_fit_plot.png')

        # values for y-axis (-0.5 to 2.5)
        # possible_Rct = np.linspace(-0.5, 2.5, 100)

        # Concentrations for x-axis (0 to 10k)
        concentrations = np.linspace(1, 10000, 1000)

        # Calculate y values for the linear line equation
        power_line = 2.92307 - 1.02396 * concentrations ** 0.108956

        Calculated_conc = ((2.92307 + deltaRs_alt)/2.92307) ** (1 / 0.108956)
        print("concetration is (alternative):", Calculated_conc)

        plt.figure()

        # Create the logarithmic plot
        # plt.semilogx(concentrations, possible_Rct, marker='o', linestyle='-', color='b', label='ΔR_c_t data')
        # plt.semilogx(concentrations, power_line, linestyle='--', color='r', label='calibline')

        concentr = np.array([50, 50, 500, 500, 2500, 50, 500, 2500, 5000, 5000, 7500, 7500, 10000, 10000, 5000, 500, 50, 500])
        deltaRs_prev = np.array([1.3103, 1.3876, 0.4785, 0.1798, 0.2558, 2.0609, 1.3427, -0.2328, 0.6489, -0.3035 , -0.1596, -0.2211, -0.1358, 0.0600, 0.3650 , 1.3757, 1.9070, 0.3796])

        x = np.log(concentrations)
        y_fit = -0.3349 * x + 2.905

        plt.semilogx(concentrations, y_fit, linestyle='--', color='r', label='calibline')
        # Given equation parameters
        slope = -0.3349
        intercept = 2.905

        # Given y_fit value
        y_fit_value = deltaRs_alt
        # Calculate corresponding x value
        x_value = (y_fit_value - intercept) / slope

        # Calculate corresponding concentration using the inverse of the logarithm operation
        gfap_value = np.exp(x_value)

        plt.scatter(concentr,deltaRs_prev, marker='o', color='purple', label='Data Points')
        plt.scatter([gfap_value], [y_fit_value], color='red', s=100, label='Given y_fit value')

        print("Corresponding concentration:", gfap_value)
        # Vertical lines
        plt.axvline(x=0.05*1e3, linestyle='--', color='grey', label='VERY LOW upper lim')
        plt.axvline(x=0.5*1e3, linestyle='--', color='green', label='LOW upper lim')
        plt.axvline(x=2.5*1e3, linestyle='--', color='cyan', label='MEDIUM LOW upper lim')
        plt.axvline(x=5*1e3, linestyle='--', color='blue', label='MEDIUM upper lim')
        plt.axvline(x=7.5*1e3, linestyle='--', color='magenta', label='HIGH upper lim')
        plt.axvline(x=10*1e3, linestyle='--', color='red', label='VERY HIGH upper lim')

        plt.axhline(y=y_fit_value, color='grey', linestyle='--', label='Horizontal Line y=0.5')

        # Customize the axis ranges
        plt.xlim(1, 18000)  # x-axis range from 1 to 10000 (10k)
        plt.ylim(-0.5, 2.5)  # y-axis range from -0.5 to 2.5

        # Add labels and title
        plt.xlabel("GFAP Concentration (pg/mL)")
        plt.ylabel("ΔR_c_t (Ω)")
        plt.title("Logarithmic Plot of ΔR_c_t vs. GFAP Concentration")

        plt.grid(True)
        # plt.show()
        plt.savefig('/home/twentus/TwentUs/twentus/EmstatPico/output/clibration_plot.png')

        return gfap_value



# Usage example
if __name__ == "__main__":
    # Get the Data
    ZRealArray = [[...], [...]]
    ZImgArray = [[...], [...]]

    plt.figure(figsize=(10, 5))
    
    # Create an instance of CircleFitter
    circle_fitter = CircleFitter(np.column_stack((ZRealArray[0], ZImgArray[0])))

    # Fit the circle and get the results
    C, R, rmse = circle_fitter.fit()

    # ... (continue with the rest of the plotting code)
