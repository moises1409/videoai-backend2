from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/", methods=['GET'])
def get_test():
    return "holass mundo"

if __name__ == "__main__":
    app.run