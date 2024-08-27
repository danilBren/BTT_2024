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

    def sortByLabels(self, Xs, labels, chipNum, Vs = None):
        """
        sorts list of labels and reorders Xs and chipNum accordingly
        """
        sortedInd = np.argsort(labels)
        self.Xs = [Xs[i] for i in sortedInd]
        self.chipNums = np.array([chipNum[i] for i in sortedInd])
        self.labels = np.array([labels[i] for i in sortedInd])
        if (Vs != None):
            self.Vs = [Vs[i] for i in sortedInd]

    def makeBaselineMap(self):
        self.bs_map = {n : 1 for n in self.chipNums}
        for i in range(0, len(self.chipNums)):
            if (self.chipNums[i] in self.bs_map and self.labels[i] == 0):
                if (self.bs_map[self.chipNums[i]] != 1):
                    print("2 values for baseine")
                    self.bs_map[self.chipNums[i]] = -1
                else: 
                    self.bs_map[self.chipNums[i]] = self.x[i] 
 

    def featureAmpDiff(self, Xs, labels, chipNums):
        # sort lists so that values labelled with 0 are first
        self.sortByLabels(Xs, labels, chipNums)

        # self.x is an array of differences between top and bottom for each measurement
        I_top, I_bottom = zip(*[getAvgMinMax(I) for I in Xs])
        I_top, I_bottom = np.array(I_top), np.array(I_bottom)
        F = np.vectorize(diffFunc)
        self.x = F(I_top, I_bottom)

    def featureMaxVal(self, Xs, labels, chipNums):
        self.sortByLabels(Xs, labels, chipNums)
        X_max = [max(x) for x in self.Xs]
        self.x = np.array(X_max)

    def featureFarFetched(self, Xs, labels, chipNums, Vs = None):
        self.sortByLabels(Xs, labels, chipNums, Vs)
        target = -0.3
        self.x = []
        for i in range(len(self.Vs)):
            V = self.Vs[i]
            differences = np.abs(V - target)
            ind = np.argmin(differences)
            self.x.append(self.Xs[i][ind])
        
    def makePolyn(self, deg):
        # make a map from chip number to base value measurement
        self.makeBaselineMap()
        # for each value divide it by the base value measurement on the same chip
        # for i in range(0, len(self.x)):
        #     if (self.labels[i] != 0):
        #         self.x[i] = self.x[i]/(self.bs_map[self.chipNums[i]])
        # normalzie resulting values for each chip
        self.x_max, self.x_min = np.max(self.x), np.min(self.x)
        # self.x_norm = (self.x - self.x_min)/(self.x_max - self.x_min)
        # self.x_norm = self.x
        print(len(self.x), len(self.labels))
        self.coeff = np.polyfit(self.x, self.labels, deg=deg)
        self.polyn = np.poly1d(self.coeff)
        
    
    def calculateConcentration(self, Xs, chipNum):
        """
        calculates concentration of the sample 
        and appends it to the list of results
        """
        self.points.append(Xs)
        if (False and self.bs_map[chipNum] != -1):
            res = self.polyn(self.points[len(self.points)-1]/self.bs_map[chipNum])   
        else:
            res = self.polyn(self.points[len(self.points)-1])
        self.results.append(res) 
        return res    

    
    def plotCalibAndPoints(self, fs=16):
        """
        plots data from x_norm using labels as Y value and data from 
        points_normalized using results as Y value. 
        Both should be plotted with dots using different colors.
        Alongside that plots coeff as a line
        """
        plt.figure(figsize=(16, 9))
        plt.scatter(self.x, self.labels, color='blue', label='Calibration Data')
    
        # Plot concentration data
        # plt.scatter(self.points_normalized, self.results, color='red', label='Concentration Data')
        
        # Generate a range of x values
        x_range = np.linspace(self.x_min, self.x_max, 100)
        # Normalize the x_range
        # x_range_norm = (x_range - self.x_min) / (self.x_max - self.x_min)
        # Calculate y values using the polynomial
        y_range = self.polyn(x_range)
        
        # # Plot the polynomial line
        plt.plot(x_range, y_range, color='green', label='Polynomial Fit')
        
        # Adding labels and legend
        plt.xlabel('Normalized signal', fontsize=fs)
        plt.ylabel('Concentration', fontsize=fs)
        plt.title('Calibration and Concentration Plot', fontsize=fs+2)
        plt.legend(fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)

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

def getData(filePath: str, Volts, Curr, inval, labels, chipnum):
    """
    adds voltage and current from the file to Volts and Curr array
    returns indexes of invalid entries
    """
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

        # for _ in range(40):
        #     next(reader)
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

        V = [v[:len(v)//2] for v in V]
        I = [i[:len(i)//2] for i in I]

        Volts += (V)
        Curr += (I)
        inval += inval_new
        labels += getLables(labels_str, n)
        chipnum += getChipNum(labels_str, n)
        
def plotData(V, I, inv, labels, chipNums, fs=26):
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'orange']
    # colors = plt.get_cmap('viridis', len(I)*3) 
    # colors = list(colors_css.CSS4_COLORS.keys())

    plt.figure(figsize=(16, 9))
    for i in range(len(V)):
        color = colors[i % len(colors)]
        if not i in inv:
            try:
                plt.plot(V[i], I[i], label=str(labels[i]) + " on chip " + str(chipNums[i]), color=color)
            except:
                pass
    plt.xlabel("Volts", fontsize=fs)
    plt.ylabel("microAmp", fontsize=fs)
    plt.legend(fontsize=fs)
    plt.tick_params(axis='both', which='major', labelsize=fs)

if __name__ == "__main__":
    c = Calibration()
    V, I, inv, labels, chipNum = [], [], [], [], []
    mapOverFolder("csv_files", getData, V, I, inv, labels, chipNum)
    noize = list(map(getNoizeAmplitude, I))
    I_filt = [savgol_filter(i, 25, 2) for i in I] # change 2nd parameter to the filter to change window size
    # print(I_filt)
    # c.featureAmpDiff(I_filt, labels, chipNum)
    # c.featureMaxVal(I_filt, labels, chipNum)
    c.featureFarFetched(I_filt, labels, chipNum, V)
    c.makePolyn(1)
    for i in range(0, len(labels)):
        print(f"exp: {labels[i]}\tgot: {c.calculateConcentration(max(I_filt[i]), chipNum[i])}")
    # inv += [0, 1, 2, 4, 5, 6]
    # plotData(V, I, inv, labels, chipNum)
    plotData(V, I_filt, inv, labels, chipNum)
    c.plotCalibAndPoints()
    plt.show()
    