import threading
import ui

def start():
    threading.Thread(target=ui.run_flask, daemon=True).start()
    nextState = waitingForSample
    pass

def waitingForSample():
    ui.input_requested.clear()
    ui.input_requested.wait()
    nextState = pumping
    pass

def measureBaseline():
    pass

def pumping():
    # turn the pump on, wait for timeout
    nextState = measuring
    pass

def measuring():
    """
    turn on slower flow

    start measuring concentration with potentiostat

    at the end - stop the flow
    """

    
    nextState = measComplete
    pass

def measComplete():
    """
    wait for user to insert a new sample.
    """
    pass

def unbinding():
    """
    in case we have an unbinding step - code it here
    """
    prevState = unbinding
    nextState = waitingForSample
    pass

def cleaning():
    """
    enable turning the pump off and on
    """
    pass

states = [ start
         , measureBaseline
         , waitingForSample
         , pumping
         , measuring
         , measComplete
         , cleaning
         , unbinding]

nextState = start
curState = start
prevState = start

def run():
    pass

if __name__ == "__main__":
    pass