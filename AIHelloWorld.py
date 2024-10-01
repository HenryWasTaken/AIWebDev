import os
from openai import OpenAI
from dotenv import load_dotenv
from prompt import system_prompt
from AIImage import generate_image
import streamlit as st

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# System prompt
messages = [{"role": "system", "content": system_prompt}]

while True:
    user_input = input("Enter something you want to ask: ('exit' to exit): ")
    
    if user_input.lower() == "exit":
        print("Exited.")
        break
    
    messages.append({"role": "user", "content": user_input})
    
    # Generate the completion
    completion = client.chat.completions.create(
        model="gpt-4",  # Using the correct model name
        temperature=0.5,
        messages=messages
    )
    
    response = completion.choices[0].message.content
    print(f"{response}")

    # Call the image generation function with user input as the prompt
    image_response = generate_image(user_input)
    print(f"Image URL: {image_response}")

    # Add the AI's response to the conversation history
    messages.append({"role": "assistant", "content": response})
