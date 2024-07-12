import csv
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

SEP = os.path.sep
PATH = "cal_12"+SEP+"SWV"





def get_data(filePath: str) -> (np.ndarray, np.ndarray): # type: ignore
    """
    Returns array of arrays of voltage and current readings from the 
    """
    with open(filePath, 'r', encoding='utf-16') as f:
        reader = csv.reader(f)

        # skip first 6 lines
        # for _ in range(6):
        #     next(reader)

        ln = next(reader)
        l = len(ln) // 2
        V_list = [[] for _ in range(l)]
        I_list = [[] for _ in range(l)]

        for r in reader:
            for i in range(l):
                try:
                    V_list[i].append(float(r[i]))
                    I_list[i].append(float(r[i+1]))
                except ValueError:
                    # some datapoints are not recorded and are instead an empty string
                    pass
        
        V = [np.array(v, dtype=float) for v in V_list]
        I = [np.array(i, dtype=float) for i in I_list]

        return V, I

def plot_file(filePath: str):
    V, I = get_data(filePath)
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']

    plt.figure(figsize=(12, 7))
    for i in range(len(V)):

        V[i] = V[i][:len(I[i])]
        I[i] = I[i][:len(V[i])]
        # Cycle through colors using modulo to avoid index out of range
        color = colors[i % len(colors)]

        plt.plot(V[i], I[i], label=i, color=color)
        
    plt.xlabel("Voltage")
    plt.ylabel("Current")
    plt.title(filePath)
    plt.show()


if __name__ == "__main__":
    plot_file("cal_12/SWV/Chip 12 SWV sample 30.csv")
    
# file_all = 'csv_files'+SEP+'CalibrationChip6_2.csv'
# file_base = 'csv_files'+SEP+'chip 3 CAL baseline.csv'

# vals = [0, 97, 165, 300, 30, 97.00000001, 165.00000001]

# vals_map = {val: [] for val in vals}

# volts_map = {val: [] for val in vals}

# vals_min_max = {val: (0, 0) for val in vals}

# vals_diff = {val: 0 for val in vals}

# mA = []

# with open(file_base, 'r', encoding='utf-16') as file:
#     csv_reader = csv.reader(file)
    
#     # Skip the first 6 lines
#     for _ in range(6):
#         next(csv_reader)
    
#     for row in csv_reader:  
#         vals_map[vals[0]].append(float(row[1]))
#         volts_map[vals[0]].append(float(row[0]))
    

# with open(file_all, 'r', encoding='utf-16') as file:
#     csv_reader = csv.reader(file)
    
#     # Skip the first 6 lines
#     for _ in range(6):
#         next(csv_reader)
    
#     for row in csv_reader:  
#         for i in range(6):
#             vals_map[vals[1+i]].append(float(row[i*2+1]))
#             volts_map[vals[1+i]].append(float(row[i*2]))

# for key in vals_map.keys():
#     x = volts_map[key]  # X-axis values from volts_map
#     y = vals_map[key]   # Y-axis values from vals_map
    
#     plt.figure(figsize=(10, 6))  # Optional: Adjust figure size
#     plt.plot(x, y, marker='o', linestyle='-', label=key)  # Plot with markers and lines
#     plt.title(f"Plot for {key}")  # Title with the current key
#     plt.xlabel("Volts")  # X-axis label
#     plt.ylabel("microAmps")   # Y-axis label
#     plt.legend()         # Show legend with the key label
    
# plt.show()  
    
# for key, value in vals_map.items():
#     value = remove_false_min(value)
#     vals_min_max[key] = (min(value), max(value))
#     vals_diff[key] = (max(value) - min(value))

# x_data = np.array(list(vals_diff.keys()), dtype=float)
# y_data = np.array(list(vals_diff.values()), dtype=float)

# x_std = np.std(x_data)
# y_std = np.std(y_data)

# x_mean = np.mean(x_data)
# y_mean = np.mean(y_data)

# coeff = np.polyfit((x_data - x_mean)/x_std, (y_data - x_mean)/x_std, 2)

# polyn = np.poly1d(coeff)

# # csv_files/chip 3 CAL 232.5.csv

# file_data = 'csv_files'+SEP+'chip 3 CAL 232.5.csv'

# with open(file_data, 'r', encoding='utf-16') as file:
#     csv_reader = csv.reader(file)

#     V = []
    
#     # Skip the first 6 lines
#     for _ in range(6):
#         next(csv_reader)
    
#     for row in csv_reader:  
#         V.append(float(row[1]))
    
#     V = remove_false_min(V)
#     print(polyn((max(V) - min(V)) - x_mean)/x_std)