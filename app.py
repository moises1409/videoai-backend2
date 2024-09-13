from flask import Flask, jsonify, request
from flask_cors import CORS
#from fonctions import *
from dotenv import load_dotenv
import os
from openai import OpenAI
from pydantic import BaseModel
from typing import List
import replicate
import requests

app = Flask(__name__)
CORS(app)

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("Missing OpenAI API key in environment variables.")
eleven_labs_api_key = os.getenv("ELEVENLABS_API_KEY")

client = OpenAI(api_key=api_key)

class Scene(BaseModel):
   sentences: str
   image_prompt: str

class Story(BaseModel):
    scenes: List[Scene]
    complete_story: str

# Constants
PROMPT_SYSTEM = """Write an engaging, great 5 scenes children's animated history. Each scene should have 1-2 sentences. 
            Generate appropriate prompt to generate a coherent image for each scene. Limit of 5 scenes,
            do not exceed 2 sentences per scene. Do not exceed 5 scenes."""
PROMPT_USER1 = "Story is about"
PROMPT_USER2 = "Create the story in the following language:"
CHUNK_SIZE = 1024
SCOPES = ['https://www.googleapis.com/auth/drive.file']
VOICE_ID_ES = "Ir1QNHvhaJXbAGhT50w3"
VOICE_ID_DEFAULT = "pNInz6obpgDQGcFmaJgB"
VOICE_ID_FR = "hFgOzpmS0CMtL2to8sAl"
VOICE_ID_EN = "jsCqWAovK2LkecY7zXl4"


@app.route("/", methods=['GET'])
def get_test():
    return "holas4s mundos"


@app.route("/get_story", methods=['GET'])
def generate_story():
    topic = request.args.get('topic')
    language = request.args.get('language')
    if topic and language:
        try:
            completion = client.beta.chat.completions.parse(
            #model="gpt-4o-2024-08-06",
            model = "gpt-4o-mini",
            
            messages=[
                {"role": "system", "content": PROMPT_SYSTEM},
                {"role": "user", "content": PROMPT_USER1 + topic},
                {"role": "user", "content": PROMPT_USER2 +language}
            ],
            response_format=Story,
            )
            response = completion.choices[0].message.parsed
            response_dict = response.model_dump()
            return jsonify(response_dict)
        except Exception as e:
            print(f"Failed to generate story: {e}")
            return None
    else:
        return jsonify({'error': 'No topic provided'}), 400
    
@app.route("/get_image", methods=['GET'])
def generate_image():
    prompt = request.args.get('prompt')
    try:
        output = replicate.run(
            #"black-forest-labs/flux-pro",
            "black-forest-labs/flux-schnell",
            input={"steps": 25,"prompt": prompt,"output_format": "jpg"}
        )
        return output[0]
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

@app.route("/get_audio", methods=['GET'])
def generate_audio():
    text = request.args.get('text')
    language = request.args.get('language')

    if language == "Spanish":
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID_ES}"
    if language == "French":
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID_ES}"
    if language == "English":
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID_ES}"
    else:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID_ES}"  
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": eleven_labs_api_key
    }
    data = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.5
        }
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        file_name = "audio.mp3"
        with open(file_name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
        
        #return upload_file_to_gd(file_name)
        return "hola, buenassss"
    except Exception as e:
        print(f"Error generating audio: {e}")
        return None

#@app.route("/get_story", methods=['GET'])
#def get_story():
 #   topic= "una nina llamada Isabel tiene super poderes"
 #   language = "Spanish"
 #   response = generate_story(topic, language)
 #   return jsonify(response)
    
    
    

if __name__ == "__main__":
    app.run