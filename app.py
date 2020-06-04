from flask import Flask, send_from_directory, request, jsonify
from NewTranslator import TranslationWalk, InvalidTranslationWalk
from Context import Context, ContextFromJSON
app = Flask(__name__)


@app.route('/')
def mainpage():
    return send_from_directory('gui/modules', 'index.html')


@app.route('/modules/<path:filename>')
def send_module(filename):
    return send_from_directory('gui/modules', filename)


@app.route('/api', methods=['POST'])
def simapi():
    data = request.get_json()
    # print('API called,', data)
    mgr = ContextFromJSON(data)
    d = mgr.jsonify()
    # print(d)
    return jsonify(d)


if __name__ == "__main__":
    app.run("0.0.0.0", port=8080, debug=True)
