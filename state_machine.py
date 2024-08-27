import os
import shutil
import threading
import ui
import potentiostat
import pump
import calibration as calib
from scipy.signal import savgol_filter
import random

meas_number = 0
current_filename = ""
running = False
res_path = potentiostat.file_dir
file_header = potentiostat.file_header
calibration_data_dir = 'calibration/'
chipNumber = 5
old_measurements = 'archive'
call_count = 0
previous_number = 30
c = calib.Calibration()

POTENTIOSTAT_CONNECTED = False
PUMP_CONNECTED = True

def generate_random_number():
    """
    Generates a random float number between 30 and 300, increasing gradually for the first 12 calls.
    """
    global call_count, previous_number
    
    return random.uniform(30, 300)
    if call_count < 10:
        # Calculate the step increment based on the number of calls
        step = (300 - 30) / 12
        min_val = previous_number
        max_val = min_val + step
        number = random.uniform(min_val, max_val)
        previous_number = number
    else:
        number = random.uniform(30, 300)
    
    call_count += 1
    return number

def fit_model():
    """
    fits a model stored as calibration class using data from the calibration directory.
    """
    V, I, inv, labels, chipNum = [], [], [], [], []
    calib.mapOverFolder(calibration_data_dir, calib.getData, V, I, inv, labels, chipNum)
    # noize = list(map(calib.getNoizeAmplitude, I)) if we're using noize as a parameter
    I_filt = [savgol_filter(i, 50, 2) for i in I]
    c.featureMaxVal(I_filt, labels, chipNum)
    c.makePolyn(deg=1)

def calculate_from_file(filePath):
    """
    reads the file and calculates concentration based on previously fit model
    """
    V, I = [], []
    calib.getData(filePath, V, I)
    I_filt = [savgol_filter(i, 50, 2) for i in I]
    return c.calculateConcentration(I_filt[0], chipNumber)

def start():
    global prevState, nextState
    # moves all filees that may be left from previous measurements to the "archive"
    # move_all_files(res_path, old_measurements)
    fit_model()
    
    if PUMP_CONNECTED:
        pump.init()

    prevState = start
    #exit
    nextState = waitingForSample
    ui.web_logger("Finished start")

def waitingForSample():
    global prevState, nextState
    ui.web_logger("Waiting for sample")
    prevState = waitingForSample
    ui.input_requested.clear()
    ui.input_requested.wait()

    #exit
    nextState = pumping

def pumping():
    global prevState, nextState
    if prevState != pumping:
        # turn the pump on, wait for timeout
        pass
    prevState = pumping

    # exit
    nextState = measuring
    pass

def measuring():
    """
    turn on slower flow

    start measuring concentration with potentiostat

    at the end - stop the flow
    """

    global prevState, nextState, meas_number
    if prevState != measuring:
        ui.web_logger("started measuring")
        potentiostat.measurement_complete = False
        # start measurement on the potentiostat
        # it will be stored in the "results/meas_<N>.csv"
        # threading.Thread(target=potentiostat.measure, args=(meas_number))
        
        # to be able to run it without anything connected
        meas_number += 1
        if POTENTIOSTAT_CONNECTED:
            current_filename = potentiostat.measure(meas_number)
        else: 
            # just to skip over to check if stuff works
            potentiostat.measurement_complete = True
    
    
    prevState = measuring

    # exit
    if potentiostat.measurement_complete:
        nextState = measComplete
        ui.value_updated.set()
        ui.web_logger("measurement complete")
    pass

def measComplete():
    """
    read value from the file and display it

    wait for user to insert a new sample.
    """
    global prevState, nextState, meas_number
    if prevState != measComplete:
        try:
            val = calculate_from_file(current_filename)
            ui.my_variable = val
        except:
            ui.my_variable = generate_random_number()
        ui.web_logger("Result is " + str(val))
        ui.value_updated.set()

    prevState = measComplete

    # exit
    nextState = unbinding

def unbinding():
    """
    in case we have an unbinding step - code it here
    """
    global prevState, nextState
    prevState = unbinding
    nextState = waitingForSample
    pass

states = [ start
         , waitingForSample
         , pumping
         , measuring
         , measComplete
         , unbinding]

nextState = start
prevState = start

def move_all_files(src_dir, dest_dir):
    # Ensure the destination directory exists
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    # List all files in the source directory
    for filename in os.listdir(src_dir):
        src_file = os.path.join(src_dir, filename)
        dest_file = os.path.join(dest_dir, filename)
        
        # Move each file to the destination directory
        if os.path.isfile(src_file):
            shutil.move(src_file, dest_file)

def run():
    global prevState, nextState
    while(running):
        nextState()

if __name__ == "__main__":
    running = True

    threading.Thread(target=run, daemon=True).start()
    ui.run_flask()