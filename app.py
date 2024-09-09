from flask import Flask, jsonify
from flask_cors import CORS
#from fonctions import *
from dotenv import load_dotenv
import os
from openai import OpenAI
from pydantic import BaseModel

app = Flask(__name__)
CORS(app)

# API Clients and keys
#openai_api_key = os.getenv("OPENAI_API_KEY")

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("Missing OpenAI API key in environment variables.")

client = OpenAI(api_key=api_key)



# Initialize API client
#client = OpenAI(api_key=openai_api_key)

#client = OpenAI()

# Constants
PROMPT_SYSTEM = """Write an engaging, great 5 scenes children's animated history. Each scene should have 1-2 sentences. 
            Generate appropriate prompt to generate a coherent image for each scene. Limit of 5 scenes,
            do not exceed 2 sentences per scene. Do not exceed 5 scenes."""
PROMPT_USER1 = "Story is about"
PROMPT_USER2 = "Create the story in the following language:"



@app.route("/", methods=['GET'])
def get_test():
    return "holas4s mundo"

@app.route("/get_test", methods=['GET'])
def get_test2():
    return "que pacha"




#@app.route("/get_story", methods=['GET'])
#def get_story():
 #   topic= "una nina llamada Isabel tiene super poderes"
 #   language = "Spanish"
 #   response = generate_story(topic, language)
 #   return jsonify(response)
    
    
    

if __name__ == "__main__":
    app.run