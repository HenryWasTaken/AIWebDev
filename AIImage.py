import os
import openai  
from dotenv import load_dotenv

load_dotenv()
openai.api_key = st.secrets["OPENAI_API_KEY"]




def generate_image(prompt):
    try:
        dalle_response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="512x512"
        )
        return dalle_response["data"][0]["url"]
    except Exception as e:
        raise RuntimeError(f"Error generating image: {e}")
