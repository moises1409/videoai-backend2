import uuid
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
from openai import OpenAI
from pydantic import BaseModel
from typing import List
import replicate
import requests
from azure.storage.blob import BlobServiceClient
from urllib.parse import urlparse
from moviepy.editor import *
from threading import Thread
from PIL import Image
import math
import numpy
import moviepy.config as mp_config

# Set the path to ImageMagick
#mp_config.change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/magick"})
#mp_config.change_settings({"IMAGEMAGICK_BINARY": "C:/Program Files/ImageMagick-7.1.1-Q16-HDRI/magick.exe"})

# Get the ImageMagick binary path from environment variable
#imagemagick_path = os.getenv("IMAGEMAGICK_BINARY", "magick")
# Log the path to verify if it's correctly set
#print(f"ImageMagick binary path: {imagemagick_path}")

# Set the ImageMagick path for MoviePy
#mp_config.change_settings({"IMAGEMAGICK_BINARY": imagemagick_path})

app = Flask(__name__)
CORS(app)

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("Missing OpenAI API key in environment variables.")
eleven_labs_api_key = os.getenv("ELEVENLABS_API_KEY")
creatomate_api_key = os.getenv("CREATOMATE_API_KEY")

client = OpenAI(api_key=api_key)

# Keep track of task statuses
task_status = {}

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
        
        return upload_to_blob_storage(file_name, "audio")
        #return "hola"
    except Exception as e:
        print(f"Error generating audio: {e}")
        return None
    
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


def upload_to_blob_storage(local_file_path, type):
    connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    unique_id = uuid.uuid4()  # Generates a unique UUID
    if type == "video":
        container_name = 'video-files'
        blob_name = f"{unique_id}.mp4"  # Create a unique blob name
    if type == "audio":
        container_name = 'audio-files'
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

@app.route('/auto_editor', methods=['POST'])
def auto_editor():
    scene_data = request.json.get('scene_data')
    if not scene_data:
        return jsonify({"error": "No scene data provided"}), 400
    
    # Generate a unique task ID
    task_id = str(uuid.uuid4())
    task_status[task_id] = {"status": "processing"}

    # Start the video generation process in a background thread
    thread = Thread(target=generate_video_in_background, args=(task_id, scene_data))
    thread.start()

    # Return the task ID immediately
    return jsonify({"task_id": task_id}), 202

@app.route('/task_status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    # Check the status of the task
    if task_id in task_status:
        return jsonify(task_status[task_id])
    else:
        return jsonify({"error": "Invalid task ID"}), 404

def generate_video_in_background(task_id, scenes_data):
    try:
        output_path = f"final_video_{uuid.uuid4()}.mp4"
        scenes = []

        for scene_data in scenes_data:
            image_path = scene_data[0]
            audio_path = scene_data[1]
            #text = scene_data["text"]
            text ="Hola que tal"
            scenes.append(create_scene(image_path, audio_path, text))

        create_video_with_scenes(scenes, output_path)
        video_url = upload_to_blob_storage(output_path, "video")

        # Update task status to completed
        task_status[task_id] = {"status": "completed", "video_url": video_url}
    except Exception as e:
        # If an error occurs, update the status to failed
        task_status[task_id] = {"status": "failed", "error": str(e)}

def create_scene(image_path_or_url, audio_path, text, duration=None):
    image_path = image_path_or_url
    size = (1280, 720)
    # Load the image and create an ImageClip object
    image_clip = ImageClip(image_path)
    image_clip.set_fps(25).resize(size)
    # Apply a zoom effect
    #image_clip = zoom_in_effect(image_clip, 0.04)

    # Load the audio file
    audio_clip = AudioFileClip(audio_path)
    
    # Set the duration of the scene based on the audio length or provided duration
    if duration is None:
        duration = audio_clip.duration
    
    # Set the duration of the image clip
    image_clip = image_clip.set_duration(duration)
    
    # Set the audio for the image clip
    image_clip = image_clip.set_audio(audio_clip)

    # Set the audio for the video clip
    #video_clip_with_text = video_clip_with_text.set_audio(audio_clip)
    
    return image_clip

def create_video_with_scenes(scenes, output_path):
    # Combine all the scenes into one video
    final_video = concatenate_videoclips(scenes)

    final_video = final_video.set_fps(24)  # Reduce frame rate to 24fps for optimization
    
    # Export the video to MP4
    final_video.write_videofile(output_path, codec='libx264', fps=24)


def zoom_in_effect(clip, zoom_ratio=0.04):
    def effect(get_frame, t):
        img = Image.fromarray(get_frame(t))
        base_size = img.size

        new_size = [
            math.ceil(img.size[0] * (1 + (zoom_ratio * t))),
            math.ceil(img.size[1] * (1 + (zoom_ratio * t)))
        ]

        # The new dimensions must be even.
        new_size[0] = new_size[0] + (new_size[0] % 2)
        new_size[1] = new_size[1] + (new_size[1] % 2)

        img = img.resize(new_size, Image.LANCZOS)

        x = math.ceil((new_size[0] - base_size[0]) / 2)
        y = math.ceil((new_size[1] - base_size[1]) / 2)

        img = img.crop([
            x, y, new_size[0] - x, new_size[1] - y
        ]).resize(base_size, Image.LANCZOS)

        result = numpy.array(img)
        img.close()

        return result

    return clip.fl(effect)

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


if __name__ == "__main__":
    # Get the port from the environment (use 8000 if not set)
    port = int(os.environ.get("PORT", 8000))
    
    # Run the app on 0.0.0.0 to accept requests from any IP address
    app.run(host="0.0.0.0", port=port)