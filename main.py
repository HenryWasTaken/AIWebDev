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

# Initialize session state for conversations
if "conversations" not in st.session_state:
    st.session_state.conversations = []

# Initialize current conversation
if "current_conversation" not in st.session_state:
    st.session_state.current_conversation = []

# Adding Sidebar
st.sidebar.markdown("## Previous Conversations")

# Add each previous conversation to the sidebar
for i, convo in enumerate(st.session_state.conversations):
    if st.sidebar.button(f"Conversation {i+1}"):
        # Load the selected conversation into current chat
        st.session_state.current_conversation = convo

# New Chat button to start a new conversation
if st.sidebar.button("🆕 New Chat"):
    # Save the current conversation
    if st.session_state.current_conversation:
        st.session_state.conversations.append(st.session_state.current_conversation)
    
    # Start a new conversation
    st.session_state.current_conversation = [
        {"role": "system", "content": system_prompt},  # Include system prompt
        {"role": "assistant", "content": "Hey there, how can I help you today?"}  # AI's initial greeting
    ]

# Initialize session state for the OpenAI model
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4"

# Display conversation history (excluding the system prompt)
for message in st.session_state.current_conversation:
    if message["role"] != "system":  # Skip system messages
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Input field for the user to ask a question
user_input = st.chat_input("Throw a question!")

# Process user input when it's submitted
if user_input:
    # Add the user input to the current conversation
    st.session_state.current_conversation.append({"role": "user", "content": user_input})

    # Display user input in the chat interface
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate AI response using the OpenAI API
    with st.chat_message("assistant"):
        # Call the OpenAI API
        completion = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=st.session_state.current_conversation,
            temperature=0.5,
        )
        response = completion.choices[0].message.content
        st.markdown(response)

    # Add the AI's response to the current conversation
    st.session_state.current_conversation.append({"role": "assistant", "content": response})

    # Optionally generate and display images based on user input
    # image_url = generate_image(user_input)
    # st.image(image_url, caption="Generated Image")

    # Optionally display the image URL
    # st.write(f"Image URL: {image_url}")
