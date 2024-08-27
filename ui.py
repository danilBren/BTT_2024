from flask import Flask, jsonify, render_template, request
from enum import Enum
import threading
import logging
import webbrowser
import pump

app = Flask(__name__)

# Disable Flask's default logging for GET requests
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

off_button_pressed = False
my_variable = 0
measuring = False
input_requested = threading.Event()
value_updated = threading.Event()



# def read_value():
#     global my_variable, measuring
#     while True:
#         input_requested.wait()  # Block until a value is requested
#         input_value = input("Enter a value for the concentration: ")
#         try:
#             my_variable = int(input_value)
#             measuring = False
#             input_requested.clear()
#             value_updated.set()  # Signal that the value has been updated
#             print(f"Value {my_variable} received and displayed.")
#         except ValueError:
#             print("Please enter a valid number.")

log_storage = []

class LogLevels(Enum):
    ERROR = "ERROR", 
    INFO = "INFO"


def web_logger(message, level = LogLevels.INFO):
    msg = message
    if level == LogLevels.INFO:
        msg = "{}: \t{}".format("INFO", message)
    elif level == LogLevels.ERROR:
        msg = "{}: \t{}".format("ERROR", message)
    log_storage.append(msg)
    print(msg)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_value')
def get_value():
    global my_variable, measuring
    value_updated.clear()  # Clear the flag after the value has been fetched
    return jsonify(value=my_variable, measuring=measuring)

@app.route('/sample_introduced')
def sample_introduced():
    global measuring
    measuring = True
    input_requested.set()
    value_updated.clear()
    web_logger("Sample Introduced button pressed, measuring...")
    value_updated.wait()  # Block until a new value is entered
    return jsonify(result="Measuring")

@app.route('/fast_flow')
def fast_flow():
    """
    because timing for the pump is unknown - directly change pressure of the pump
    """
    web_logger("Start flow")
    pump.setPressure(100)
    return jsonify(result="Flow started")

@app.route('/slow_flow')
def slow_flow():
    """
    because timing for the pump is unknown - directly change pressure of the pump
    """
    web_logger("Slow flow")
    pump.setPressure(35)
    return jsonify(result="Slow flow")

@app.route('/stop_flow')
def stop_flow():
    """
    because timing for the pump is unknown - directly change pressure of the pump
    """
    web_logger("Stop flow")
    pump.setPressure(0)
    return jsonify(result="Flow stopped")

@app.route('/debug_info')
def debug_info():
    # Replace this with actual debug information retrieval logic
    debug_data = "\n".join(log_storage)
    return debug_data


@app.route('/device_off')
def turn_off():
    global off_button_pressed
    off_button_pressed = True
    return jsonify(result="Turning off")


def run_flask():
    app.run(host='0.0.0.0', port=8080, debug=True)

if __name__ == '__main__':
    pump.init()
    run_flask()
