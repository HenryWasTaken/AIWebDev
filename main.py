import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from prompt import system_prompt
from AIImage import generate_image
import streamlit as st
#Made by Henry Sun at Abingdon AI Web Development Club

# Load environment variables
# load_dotenv()
# api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Function to load conversations from a file with error handling
def load_conversations():
    try:
        with open('conversations.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return default conversation if file is missing or contains invalid JSON
        return [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": "Hey there, how can I help you today?"}
        ]

# Function to save conversations to a file
def save_conversations(conversations):
    with open('conversations.json', 'w') as f:
        json.dump(conversations, f)
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

st.sidebar.title("Settings & Features")
st.sidebar.write("Adjust settings, explore features, or access additional tools.")

# Custom Prompt Categories
category = st.sidebar.selectbox("Choose a Category", ["General", "Homework Help", "Programming", "Math/Science", "Exam Prep"])

# Advanced Model Tuning
temperature = st.sidebar.slider("Response Creativity (Temperature)", 0.0, 1.0, 0.5)
st.sidebar.markdown("### Model Parameters Adjusted")

# Notes Section
with st.sidebar.expander("My Notes"):
    notes = load_notes()  # Load saved notes
    if notes:
        for i, note in enumerate(notes):
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.markdown(f"- {note}")
            with col2:
                if st.button("❌", key=f"delete_note_{i}"):  # Add delete button
                    notes.pop(i)  # Remove the note
                    with open('notes.json', 'w') as f:
                        json.dump(notes, f)  # Save updated notes
                    st.experimental_rerun()  # Refresh the app to reflect changes
    else:
        st.markdown("No notes saved.")

    # Add a new note
    new_note = st.text_input("Add a Note", key="note_input")
    if st.button("Save Note"):
        if new_note:
            notes.append(new_note)
            with open('notes.json', 'w') as f:
                json.dump(notes, f)  # Save updated notes
            st.success("Note saved! Refresh the page.")

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

# Display conversation history (excluding the system prompt)
for message in st.session_state.messages:
    if message["role"] != "system":  # Skip system messages
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Input
user_input = st.chat_input("Throw a question!")

# Process user input
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

    # Save updated conversation history to file
    save_conversations(st.session_state.messages)

    
