import os
from dotenv import load_dotenv
import google.genai as genai
from google.genai import errors

load_dotenv()

api_key = os.environ["GEMINI_API_KEY"] #create a .env file and write GEMINI_API_KEY="yourapikey"
client = genai.Client(api_key=api_key)

def generate_patch(prompt:str):
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model = "gemini-3.8-flash",
                contents = prompt
            )

            if not response.text:
                raise Exception("LLM returned an empty response")

            return response.text
        
        except errors.ServerError as e:

            if e.code!=503 or attempt==2:
                print("Could not connect to the Agent")
                raise
        
