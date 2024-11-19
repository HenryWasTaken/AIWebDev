import os
import openai  
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key

def generate_image(prompt):
    try:
        response = client.images.generate(
  model="dall-e-3",
  prompt="a white siamese cat",
  size="1024x1024",
  quality="standard",
  n=1,
        )
        return dalle_response["data"][0]["url"]
    except Exception as e:
        raise RuntimeError(f"Error generating image: {e}")
