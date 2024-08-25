import threading
import ui
import potentiostat
import calibration as calib
from scipy.signal import savgol_filter

meas_number = 1
running = False
res_path = potentiostat.file_dir
file_header = potentiostat.file_header
calibration_data_dir = 'calibration/'
chipNumber = 0
c = calib.Calibration()

def fit_model():
    V, I, inv, labels, chipNum = [], [], [], [], []
    calib.mapOverFolder(calibration_data_dir, calib.getData, V, I, inv, labels, chipNum)
    # noize = list(map(calib.getNoizeAmplitude, I)) if we're using noize as a parameter
    I_filt = [savgol_filter(i, 50, 2) for i in I]
    # fit a model using difference between min and max as a feature
    c.polynAmpDiff(I_filt, labels, chipNum, 1)

def measure_file(filePath):
    """
    reads the file and calculates concentration based on previously fit model
    """
    V, I = [], []
    calib.getData(filePath, V, I)
    I_filt = [savgol_filter(i, 50, 2) for i in I]
    return c.calculateConcentration(I_filt[0], chipNumber)


def start():
    fit_model()
    # start the frontend
    threading.Thread(target=ui.run_flask, daemon=True).start()

    prevState = start
    #exit
    nextState = waitingForSample

def waitingForSample():

    prevState = waitingForSample
    ui.input_requested.clear()
    ui.input_requested.wait()

    #exit
    nextState = pumping

def pumping():
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
    global meas_number
    if prevState != measuring:
        potentiostat.measurement_complete = False
        # start measurement on the potentiostat
        # it will be stored in the "results/meas_<N>.csv"
        threading.Thread(target=potentiostat.measure, args=(meas_number))
        meas_number += 1
    
    
    prevState = measuring

    # exit
    if potentiostat.measurement_complete:
        nextState = measComplete
    pass

def measComplete():
    """
    read value from the file and display it

    wait for user to insert a new sample.
    """
    global meas_number
    if prevState != measComplete:
        val = measure_file(res_path + file_header + str(meas_number) + '.csv')
        meas_number += 1
        ui.my_variable = val
        ui.value_updated.set()

    prevState = measComplete

    # exit
    nextState = unbinding

def unbinding():
    """
    in case we have an unbinding step - code it here
    """
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
curState = start
prevState = start

def run():
    while(running):
        nextState()

if __name__ == "__main__":
    running = True
    run()