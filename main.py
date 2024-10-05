import os
from openai import OpenAI
from dotenv import load_dotenv
from prompt import system_prompt
from AIImage import generate_image
import streamlit as st

# Load environment variables
#load_dotenv()
#api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Streamlit App Title with different text styles
st.markdown("<h1 style='color:white;'>StudyGPT</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:grey; font-size: small;'>StudyGPT uses a set of prompts designed to help students. To use, simply type the thing you need help with. The model will then guide you to solving your problems! This is still a prototype. Still check important info</p>", unsafe_allow_html=True)
st.markdown("<p style='color:white;'>This model is not intended to give a 'quick' answer to your last-minute homework, and would not be a substitute for a teacher.</p>", unsafe_allow_html=True)
st.markdown("<p style='color:white;'>Important: This GPT does not log or store any data.</p>", unsafe_allow_html=True)

# Add the dropdown box to show the system prompt
with st.expander("The GPT's Mission!"):
    st.markdown(f"<p style='color:white;'>{system_prompt}</p>", unsafe_allow_html=True)

# Adding Sidebar
st.sidebar.markdown("## Sidebar")
st.sidebar.markdown("This is where you can provide extra functionality like links, tools, and more information.")
st.sidebar.markdown("Feel free to add more options here.")

# New Chat button at the top of the sidebar
if st.sidebar.button("🆕 New Chat"):
    # Reset the conversation history
    st.session_state.messages = [
        {"role": "system", "content": system_prompt},  # Include system prompt
        {"role": "assistant", "content": "Hey there, how can I help you today?"}  # AI's initial greeting
    ]

# Initialize session state for model and messages
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": system_prompt},  # Include system prompt
        {"role": "assistant", "content": "Hey there, how can I help you today?"}  # AI's initial greeting
    ]

# Display conversation history (excluding the system prompt)
for message in st.session_state.messages:
    if message["role"] != "system":  # Skip system messages
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Input field for the user to ask a question
user_input = st.chat_input("Throw a question!")

# Process user input when it's submitted
if user_input:
    # Add the user input to the conversation history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Display user input in the chat interface
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate AI response using the OpenAI API
    with st.chat_message("assistant"):
        # Call the OpenAI API
        completion = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=st.session_state.messages,
            temperature=0.5,
        )
        response = completion.choices[0].message.content
        st.markdown(response)

    # Add the AI's response to the conversation history
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Optionally generate and display images based on user input
    # image_url = generate_image(user_input)
    # st.image(image_url, caption="Generated Image")

    # Optionally display the image URL
    # st.write(f"Image URL: {image_url}")
