from flask import Flask, jsonify
from flask_cors import CORS
#from fonctions import *
from dotenv import load_dotenv
import os
from openai import OpenAI
from pydantic import BaseModel

app = Flask(__name__)
CORS(app)


@app.route("/", methods=['GET'])
def get_test():
    return "holas4s mundo"

#@app.route("/get_story", methods=['GET'])
#def get_story():
 #   topic= "una nina llamada Isabel tiene super poderes"
 #   language = "Spanish"
 #   response = generate_story(topic, language)
 #   return jsonify(response)
    
    
    

if __name__ == "__main__":
    app.run