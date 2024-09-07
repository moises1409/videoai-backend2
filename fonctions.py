import os
from openai import OpenAI
from pydantic import BaseModel
#from dotenv import load_dotenv

# Load environment variables
#load_dotenv('.env')

# API Clients and keys
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize API client
client = OpenAI(api_key=openai_api_key)

# Constants
PROMPT_SYSTEM = """Write an engaging, great 5 scenes children's animated history. Each scene should have 1-2 sentences. 
            Generate appropriate prompt to generate a coherent image for each scene. Limit of 5 scenes,
            do not exceed 2 sentences per scene. Do not exceed 5 scenes."""
PROMPT_USER1 = "Story is about"
PROMPT_USER2 = "Create the story in the following language:"

class Scene(BaseModel):
    sentences: str
    image_prompt: str

class Story(BaseModel):
    scenes: list[Scene]
    complete_story: str

def generate_story(topic, language):
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
        return response_dict
    except Exception as e:
        print(f"Failed to generate story: {e}")
        return None