import os
import json
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from AIImage import generate_image
from prompt import system_prompt

# Load environment variables
# load_dotenv()
# api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Function to load conversations
def load_conversations():
    try:
        with open('conversations.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return [{"role": "system", "content": system_prompt}]

# Function to save conversations
def save_conversations(conversations):
    with open('conversations.json', 'w') as f:
        json.dump(conversations, f)

# Function to save personal notes
def save_notes(note):
    try:
        with open('notes.json', 'r') as f:
            notes = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        notes = []
    notes.append(note)
    with open('notes.json', 'w') as f:
        json.dump(notes, f)

# Load saved notes
def load_notes():
    try:
        with open('notes.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Streamlit App Title
st.markdown("<h1 style='color:white;'>StudyGPT</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:grey; font-size: small;'>StudyGPT uses a set of prompts designed to help students. To use, simply type the thing you need help with. The model will then guide you to solving your problems! This is still a prototype. Still check important info</p>", unsafe_allow_html=True)
st.markdown("<p style='color:white;'>This model is not intended to give a 'quick' answer to your last-minute homework, and would not be a substitute for a teacher.</p>", unsafe_allow_html=True)
st.markdown("<p style='color:white;'>Important: This GPT does not log or store any data.</p>", unsafe_allow_html=True)


#dropdown box
with st.expander("The GPT's Mission!"):
    st.markdown(f"<p style='color:white;'>{system_prompt}</p>", unsafe_allow_html=True)

# Initialize session state for model and messages
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4"

if "messages" not in st.session_state:
    # Load conversation history
    st.session_state.messages = load_conversations()

# New Chat button
if st.button("Reset Chat"):
    # Reset the conversation history
    st.session_state.messages = [
        {"role": "system", "content": system_prompt},  # Include system prompt
        {"role": "assistant", "content": "Hey there, how can I help you today?"}  # AI's initial greeting
    ]
    save_conversations(st.session_state.messages)  # Save reset conversation to file
    
st.sidebar.title("Settings & Features")
st.sidebar.write("Adjust settings, explore features, or access additional tools.")

# Custom Prompt Categories
category = st.sidebar.selectbox("Choose a Category", ["General", "Homework Help", "Programming", "Math/Science", "Exam Prep"])

# Advanced Model Tuning
temperature = st.sidebar.slider("Response Creativity (Temperature)", 0.0, 1.0, 0.5)
st.sidebar.markdown("### Model Parameters Adjusted")

# Notes Section
with st.sidebar.expander("My Notes"):
    for note in load_notes():
        st.markdown(f"- {note}")
    new_note = st.text_input("Add a Note", key="note_input")
    if st.button("Save Note"):
        if new_note:
            save_notes(new_note)
            st.success("Note saved!")

# Load conversations
if "messages" not in st.session_state:
    st.session_state.messages = load_conversations()

# Reset Chat Button
if st.sidebar.button("Reset Chat"):
    st.session_state.messages = [{"role": "system", "content": system_prompt}]
    save_conversations(st.session_state.messages)

# Chat Display
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# User Input
user_input = st.chat_input("Ask a question...")
if user_input:
    # Add user input to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate AI response
    with st.chat_message("assistant"):
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=st.session_state.messages,
            temperature=temperature,
        )
        response = completion.choices[0].message.content
        st.markdown(response)

        # Save conversation
        st.session_state.messages.append({"role": "assistant", "content": response})
        save_conversations(st.session_state.messages)

