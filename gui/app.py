from flask import Flask, send_from_directory
app = Flask(__name__)

@app.route('/')
def mainpage():
    return send_from_directory('modules', 'index.html')

@app.route('/modules/<path:filename>')
def send_module(filename):
    return send_from_directory('modules', filename)
