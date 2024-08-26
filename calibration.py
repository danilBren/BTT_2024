import csv
import numpy as np
import os
import matplotlib.pyplot as plt
import re
from matplotlib import colors as colors_css
from pathlib import Path
from scipy.signal import savgol_filter
from scipy.interpolate import *


SEP = os.path.sep
PATH = "cal_12"+SEP+"SWV"
N_DP = 10 #number of data points to use for low and high average
diffFunc = lambda a, b: a-b

class Calibration: 

    def __init__(self):
        self.points = []
        self.points_normalized = []
        self.results = []

    def sortByLabels(self, Xs, labels, chipNum):
        """
        sorts list of labels and reorders Xs and chipNum accordingly
        """
        sortedInd = np.argsort(labels)
        self.Xs = [Xs[i] for i in sortedInd]
        self.chipNums = np.array([chipNum[i] for i in sortedInd])
        self.labels = np.array([labels[i] for i in sortedInd])

    def makeBaselineMap(self):
        self.bs_map = {n : 1 for n in self.chipNums}
        for i in range(0, len(self.chipNums)):
            if (self.chipNums[i] in self.bs_map and self.labels[i] == 0):
                if (self.bs_map[self.chipNums[i]] != 1):
                    print("2 values for baseine")
                else: 
                    self.bs_map[self.chipNums[i]] = self.x[i] 
 

    def polynAmpDiff(self, Xs, labels, chipNums, deg):
        # sort lists so that values labelled with 0 are first
        self.sortByLabels(Xs, labels, chipNums)

        # self.x is an array of differences between top and bottom for each measurement
        I_top, I_bottom = zip(*[getAvgMinMax(I) for I in Xs])
        I_top, I_bottom = np.array(I_top), np.array(I_bottom)
        F = np.vectorize(diffFunc)
        self.x = F(I_top, I_bottom)

        # make a map from chip number to base value measurement
        self.makeBaselineMap()
        # for each value divide it by the base value measurement on the same chip
        # print(self.x)
        # print(self.labels)
        # print(self.chipNums)
        # print(self.bs_map)
        for i in range(0, len(self.x)):
            if (self.labels[i] != 0):
                self.x[i] = self.x[i]/(self.bs_map[self.chipNums[i]])
        print(self.x)
        # normalzie resulting values for each chip
        self.x_max, self.x_min = np.max(self.x), np.min(self.x)
        self.x_norm = (self.x - self.x_min)/(self.x_max - self.x_min)
        self.x_norm = self.x
        self.coeff = np.polyfit(self.x_norm, self.labels, deg=deg)
        self.polyn = np.poly1d(self.coeff)
    
    def polynNoizeAmpl(self, Xs, labels, chinNum, deg):
        self.sortByLabels(Xs, labels, chipNum)
        self.x = np.array(list(map(np.average, Xs)))
        self.x_max, self.x_min = np.max(self.x), np.min(self.x)
        self.x_norm = (self.x - self.x_min)/(self.x_max - self.x_min)
        self.coeff = np.polyfit(self.x_norm, self.labels, deg=deg)
        self.polyn = np.poly1d(self.coeff)

    def calculateConcentration(self, Is, chipNum):
        """
        calculates concentration of the sample 
        and appends it to the list of results
        """
        t, b = getAvgMinMax(Is)
        self.points.append(diffFunc(t, b))
        self.points_normalized.append((diffFunc(t, b)/(self.bs_map[chipNum])-self.x_min)/(self.x_max-self.x_min))
        res = self.polyn(self.points[len(self.points)-1])   
        self.results.append(res) 
        return res    

    
    def plotCalibAndPoints(self):
        """
        plots data from x_norm using labels as Y value and data from 
        points_normalized using results as Y value. 
        Both should be plotted with dots using different colors.
        Alongside that plots coeff as a line
        """
        plt.figure(figsize=(16, 9))
        plt.scatter(self.x_norm, self.labels, color='blue', label='Calibration Data')
    
        # Plot concentration data
        # plt.scatter(self.points_normalized, self.results, color='red', label='Concentration Data')
        
        # Generate a range of x values
        x_range = np.linspace(self.x_min, self.x_max, 100)
        # Normalize the x_range
        x_range_norm = (x_range - self.x_min) / (self.x_max - self.x_min)
        # Calculate y values using the polynomial
        y_range = self.polyn(x_range_norm)
        
        # Plot the polynomial line
        # plt.plot(x_range_norm, y_range, color='green', label='Polynomial Fit')
        
        # Adding labels and legend
        plt.xlabel('Normalized signal')
        plt.ylabel('Concentration')
        plt.title('Calibration and Concentration Plot')
        plt.legend()

def getNoizeAmplitude(I):
    WINDOW = 10
    noize_amp = []
    for i in range(0, len(I)):
        noize_amp.append(np.std(I[i:i+WINDOW]))
    return np.array(noize_amp)

def getLables(line, n):
    """
    returns a numpy array of labels in the line
    matched by "sample <LABEL>:"
    """
    labels = []
    pattern = r"sample:? ?((\d+)(.\d+)?):?"
    # pattern = r"hip ?(\d+)"
    for i in range(0, n):
        match = re.search(pattern, line[i*2])
        if (match):
            labels.append(float(match.group(1)))
    return labels

def getChipNum(line, n):
    """
    returns a numpy array of labels in the line
    matched by "chip <number>:"
    """
    chipnum = []
    pattern = r"hip ?(\d+)"
    for i in range(0, n):
        match = re.search(pattern, line[i*2])
        if (match):
            chipnum.append(int(match.group(1)))
    return chipnum

def mapOverFolder(dir: str, func, *args):
    """
    maps function func over all files in dir with arguments args
    """
    directory = Path(dir)

    for file_path in directory.iterdir():
        if file_path.is_file():
            func(file_path, *args)

def getAvgMinMax(I):
    """
    returns average of N_DP biggest and N_DP smallest elements of the array
    """
    biggest = np.average(np.partition(I, -N_DP)[-N_DP:])
    smallest = np.average(np.partition(I, N_DP)[:N_DP])
    return biggest, smallest

def getData(filePath: str, Volts, Curr, inval = [], labels = [], chipnum = []):
    """
    adds voltage and current from the file to Volts and Curr array
    returns indexes of invalid entries
    """
    
    try:
        with open(filePath, 'r', encoding='utf-16') as f:
            reader = csv.reader(f)

            # skip first 3 lines
            for _ in range(3):
                next(reader)
            
            labels_str = next(reader)
            _ = next(reader) # date
            ln = next(reader)
            next(reader) # skip the first point because it is always too low 
            li = len(Volts)
            n = len(ln) // 2

            V_list = [[] for _ in range(n)]
            I_list = [[] for _ in range(n)]
            inval_new = []

            for _ in range(40):
                next(reader)
            for r in reader:
                for i in range(n):
                    try:
                        if r[2*i] != '' and r[2*i+1] != '':
                            V_list[i].append(float(r[2*i]))
                            I_list[i].append(float(r[2*i+1]))
                        elif not (i + li in inval_new):
                            inval_new.append(i + li)
                    except IndexError:
                        break
            
            V = [np.array(v, dtype=float) for v in V_list]
            I = [np.array(i, dtype=float) for i in I_list]

            Volts += (V)
            Curr += (I)
            inval += inval_new
            labels += getLables(labels_str, n)
            chipnum += getChipNum(labels_str, n)
    except UnicodeDecodeError:
         remove_last_line(filePath)
         getData(filePath, Volts, Curr, inval, labels, chipnum)

        
def plotData(V, I, inv, labels, chipNums):
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'orange']

    plt.figure(figsize=(16, 9))
    for i in range(len(V)):
        color = colors[i % len(colors)]
        if not i in inv:
            plt.plot(V[i], I[i], label=str(labels[i]) + " on chip " + str(chipNums[i]), color=color)
        
    plt.xlabel("Volts")
    plt.ylabel("micraAmp")
    plt.legend()

def remove_last_line(file_path):
    # Step 1: Read all lines from the file
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # Step 2: Remove the last line
    if lines:
        lines = lines[:-1]
    
    # Step 3: Write the remaining lines back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(lines)

if __name__ == "__main__":
    c = Calibration()
    V, I, inv, labels, chipNum = [], [], [], [], []
    mapOverFolder("calibration", getData, V, I, inv, labels, chipNum)
    noize = list(map(getNoizeAmplitude, I))
    I_filt = [savgol_filter(i, 50, 2) for i in I]
    # print(I_filt)
    c.polynAmpDiff(I_filt, labels, chipNum, 1)
    # c.polynNoizeAmpl(noize, labels, chipNum, 1)
    for i in range(0, len(labels)):
        print(f"exp: {labels[i]}\tgot: {c.calculateConcentration(I_filt[i], chipNum[i])}")
    # inv += [0, 1, 2, 4, 5, 6]
    plotData(V, I, inv, labels, chipNum)
    plotData(V, I_filt, inv, labels, chipNum)
    c.plotCalibAndPoints()
    plt.show()
    