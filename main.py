import csv
import numpy as np
import os
import matplotlib.pyplot as plt

P_S = os.path.sep

def remove_false_min(vals):
    cut = 0
    count = 0
    for i in range(len(vals)):
        if vals[i] > vals[i+1]:
            count += 1
            if (count == 1):
                cut = i
            if (count == 2):
                break
        else: 
            count = 0



    return vals[cut:]

file_all = 'csv_files'+P_S+'CalibrationChip6_2.csv'
file_base = 'csv_files'+P_S+'chip 3 CAL baseline.csv'

vals = [0, 97, 165, 300, 30, 97.00000001, 165.00000001]

vals_map = {val: [] for val in vals}

volts_map = {val: [] for val in vals}

vals_min_max = {val: (0, 0) for val in vals}

vals_diff = {val: 0 for val in vals}

mA = []

with open(file_base, 'r', encoding='utf-16') as file:
    csv_reader = csv.reader(file)
    
    # Skip the first 6 lines
    for _ in range(6):
        next(csv_reader)
    
    for row in csv_reader:  
        vals_map[vals[0]].append(float(row[1]))
        volts_map[vals[0]].append(float(row[0]))
    

with open(file_all, 'r', encoding='utf-16') as file:
    csv_reader = csv.reader(file)
    
    # Skip the first 6 lines
    for _ in range(6):
        next(csv_reader)
    
    for row in csv_reader:  
        for i in range(6):
            vals_map[vals[1+i]].append(float(row[i*2+1]))
            volts_map[vals[1+i]].append(float(row[i*2]))

for key in vals_map.keys():
    x = volts_map[key]  # X-axis values from volts_map
    y = vals_map[key]   # Y-axis values from vals_map
    
    plt.figure(figsize=(10, 6))  # Optional: Adjust figure size
    plt.plot(x, y, marker='o', linestyle='-', label=key)  # Plot with markers and lines
    plt.title(f"Plot for {key}")  # Title with the current key
    plt.xlabel("Volts")  # X-axis label
    plt.ylabel("microAmps")   # Y-axis label
    plt.legend()         # Show legend with the key label
    
plt.show()  
    
for key, value in vals_map.items():
    value = remove_false_min(value)
    vals_min_max[key] = (min(value), max(value))
    vals_diff[key] = (max(value) - min(value))

x_data = np.array(list(vals_diff.keys()), dtype=float)
y_data = np.array(list(vals_diff.values()), dtype=float)

x_std = np.std(x_data)
y_std = np.std(y_data)

x_mean = np.mean(x_data)
y_mean = np.mean(y_data)

coeff = np.polyfit((x_data - x_mean)/x_std, (y_data - x_mean)/x_std, 2)

polyn = np.poly1d(coeff)

# csv_files/chip 3 CAL 232.5.csv

file_data = 'csv_files'+P_S+'chip 3 CAL 232.5.csv'

with open(file_data, 'r', encoding='utf-16') as file:
    csv_reader = csv.reader(file)

    V = []
    
    # Skip the first 6 lines
    for _ in range(6):
        next(csv_reader)
    
    for row in csv_reader:  
        V.append(float(row[1]))
    
    V = remove_false_min(V)
    print(polyn((max(V) - min(V)) - x_mean)/x_std)