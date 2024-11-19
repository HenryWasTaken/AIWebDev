import os
import openai  
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def generate_image(prompt):
    # Use the new OpenAI API for DALL·E image generation
    response = openai.Image.create(
        prompt=prompt,
        n=1,  # Generate one image
        size="1024x1024"  # You can choose different sizes like "256x256", "512x512", etc.
    )
    # Extract the URL of the generated image
    image_url = response['data'][0]['url']
    return image_url
