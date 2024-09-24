import uuid
import time
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
from azure.storage.blob import BlobServiceClient
from urllib.parse import urlparse
from moviepy.editor import ImageClip, AudioFileClip, TextClip, concatenate_videoclips
from io import BytesIO
from PIL import Image

app = Flask(__name__)
CORS(app)

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("Missing OpenAI API key in environment variables.")
eleven_labs_api_key = os.getenv("ELEVENLABS_API_KEY")
creatomate_api_key = os.getenv("CREATOMATE_API_KEY")

client = OpenAI(api_key=api_key)

class Scene(BaseModel):
   sentences: str
   image_prompt: str

class Story(BaseModel):
    scenes: List[Scene]
    complete_story: str

# Constants
PROMPT_SYSTEM = """Write an engaging, great 5 scenes children's animated history. Each scene should have 1-2 sentences.  
Generate appropriate prompt to generate a coherent image for each scene. 
The styles of all the images in the story are: Cartoon, vibrant, Pixar style. 
Characters description should be detailed, like hair and color eyes and face. Main character in the story should be the same for all scenes. 
Characters description must be consistent in all the scenes.
Please add the styles in each prompt for images. Be sure that all the prompts are consistent in all the story. For example characters descriptions.
Please respect the styles in all the scenes.
Limit of 5 scenes, do not exceed 2 sentences per scene. Do not exceed 5 scenes."""
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
    return "holas4s mundos2322"


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
        
        return upload_to_blob_storage(file_name)
        #return "hola"
    except Exception as e:
        print(f"Error generating audio: {e}")
        return None


@app.route("/get_video_id", methods=['POST'])
def generate_video_id():
    scene_data = request.json.get('scene_data')

    if not scene_data:
        return jsonify({"error": "No scene data provided"}), 400
    
    for data in scene_data:
          print("Image:", data[0])
          print("Audio", data[1])
    url = "https://api.creatomate.com/v1/renders"
    headers = {
        "Authorization": f"Bearer {creatomate_api_key}","Content-Type": "application/json"}
    data = {
        "template_id": "076cc0f8-ea7a-4bd9-819a-dd6d3e6e64a1",
        "modifications": {"Image-1": "","Voiceover-1": "","Image-2": "","Voiceover-2": "","Image-3": "","Voiceover-3": "","Image-4": "","Voiceover-4": "","Image-5": "","Voiceover-5": ""}
    }
    try:
        for i in range(min(len(scene_data), 6)):
            image, audio = scene_data[i]
            data['modifications'][f'Image-{i+1}'] = image
            data['modifications'][f'Voiceover-{i+1}'] = audio
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        get_url = url+"/"+response.json()[0]['id']
        return jsonify({"video_url": get_url})
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return "0"

@app.route("/get_video_final", methods=['GET'])
def generate_video_final():
    video_url_id = request.args.get('video_url_id')

    if not video_url_id:
        return jsonify({"error": "No video_url_id data provided"}), 400
    
    headers = {
        "Authorization": f"Bearer {creatomate_api_key}","Content-Type": "application/json"}
    try: 
        response2 = requests.get(video_url_id, headers=headers)
        video = response2.json()
        return jsonify(video)
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return "0"   
    
@app.route('/delete_audio_files', methods=['POST'])
def delete_audio_files():
    data = request.json
    audio_urls = data.get('audio_urls', [])
    
    if not audio_urls:
        return jsonify({"error": "No audio URLs provided"}), 400

    results = []
    for url in audio_urls:
        result = delete_from_blob_storage(url)
        results.append({"url": url, "deleted": result})
    
    return jsonify({"results": results}), 200

def upload_to_blob_storage(local_file_path):
    connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_name = 'audio-files'
    unique_id = uuid.uuid4()  # Generates a unique UUID
    blob_name = f"{unique_id}.mp3"  # Create a unique blob name
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    with open(local_file_path, "rb") as data:
        blob_client.upload_blob(data)

    blob_url = blob_client.url
    return blob_url

# Function to delete a single file from Azure Blob Storage
def delete_from_blob_storage(blob_url):
    connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    
    parsed_url = urlparse(blob_url)
    path_parts = parsed_url.path.lstrip('/').split('/')
    container_name = path_parts[0]
    blob_name = '/'.join(path_parts[1:])
    
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    try:
        blob_client.delete_blob()
        print(f"Blob {blob_name} deleted successfully from container {container_name}.")
        return True
    except Exception as e:
        print(f"Failed to delete blob: {blob_name}. Error: {str(e)}")
        return False


if __name__ == "__main__":
    app.run