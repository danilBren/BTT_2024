import csv
import numpy as np
import os
import matplotlib.pyplot as plt
import re
from pathlib import Path
from scipy.signal import savgol_filter

SEP = os.path.sep
PATH = "cal_12"+SEP+"SWV"

def getLables(line, n):
    labels = []
    pattern = r"sample ((\d+)(.\d+)?):"
    for i in range(0, n):
        match = re.search(pattern, line[i*2])
        if (match):
            labels.append(float(match.group(1)))
    return labels
        


def getData(filePath: str, Volts, Curr, inval, labels) -> int:
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
    
    
def mapOverFolder(dir: str, func, *args):
    """
    maps function func over all files in dir with arguments args
    """
    directory = Path(dir)

    for file_path in directory.iterdir():
        if file_path.is_file():
            func(file_path, *args)


def plotData(V, I, inv, labels):
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']

    plt.figure(figsize=(12, 7))
    for i in range(len(V)):
        color = colors[i % len(colors)]
        if not i in inv:
            plt.plot(V[i], I[i], label=labels[i], color=color)
        
    plt.xlabel("Volts")
    plt.ylabel("micraAmp")
    plt.legend()
    

if __name__ == "__main__":
    V, I, inv, labels = [], [], [], []
    mapOverFolder("csv_files", getData, V, I, inv, labels)

    plotData(V, I, inv, labels)
    I_filt = []
    for I_e in I:
        I_filt.append(savgol_filter(I_e, 101, 2))

    plotData(V, I_filt, inv, labels)
    plt.show()
    