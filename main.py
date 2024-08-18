from flask import Flask, jsonify, render_template, request
import threading
import logging

app = Flask(__name__)

# Disable Flask's default logging for GET requests
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

my_variable = 0
measuring = False
input_requested = threading.Event()
value_updated = threading.Event()

def read_value():
    global my_variable, measuring
    while True:
        input_requested.wait()  # Block until a value is requested
        input_value = input("Enter a value for the concentration: ")
        try:
            my_variable = int(input_value)
            measuring = False
            input_requested.clear()
            value_updated.set()  # Signal that the value has been updated
            print(f"Value {my_variable} received and displayed.")
        except ValueError:
            print("Please enter a valid number.")

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
    print("Sample Introduced button pressed, measuring...")
    value_updated.wait()  # Block until a new value is entered
    return jsonify(result="Measuring")

@app.route('/cleanup')
def cleanup():
    print("Cleanup button pressed")
    return jsonify(result="Cleanup started")

@app.route('/stop_cleanup')
def stop_cleanup():
    print("Stop Cleanup button pressed")
    return jsonify(result="Cleanup stopped")

@app.route('/debug')
def debug():
    print("Debug button pressed") #change to variable change
    return jsonify(result="Debugging mode")

if __name__ == '__main__':
    threading.Thread(target=read_value, daemon=True).start()
    app.run(host='0.0.0.0', port=8080, debug=True)
