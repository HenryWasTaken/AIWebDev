import os
import json
from openai import OpenAI
from prompt import system_prompt
import streamlit as st
import pandas as pd
from io import StringIO
from pypdf import PdfReader
from pinecone import Pinecone, ServerlessSpec

#Made by Henry Sun at Abingdon AI Web Development Club

# Load environment variables
# load_dotenv()
# api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize Pinecone
pc = Pinecone(api_key=st.secrets["PINECONE_API_KEY"])
index_name = "study-gpt-index"

pc.create_index(
    name=index_name,
    dimension=1536, # Replace with your model dimensions, 1536 is OpenAI small text embeddings
    metric="cosine", # Replace with your model metric
    spec=ServerlessSpec(
        cloud="aws",
        region="eu-west-2" #London for AWS
    ) 
)

# System prompt (replace with your own)
system_prompt = "You are StudyGPT, a helpful AI assistant designed to help students learn and solve problems. Provide detailed explanations and guide users to understand concepts."

# Function to load conversations from a file
def load_conversations():
    try:
        with open('conversations.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": "Hey there, how can I help you today?"}
        ]

# Function to save conversations to a file
def save_conversations(conversations):
    with open('conversations.json', 'w') as f:
        json.dump(conversations, f)

# Function to load notes from a file
def load_notes():
    try:
        with open('notes.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Function to extract text from a PDF
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Function to split text into chunks
def split_text_into_chunks(text, chunk_size=500):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks

# Function to generate and store embeddings
def generate_and_store_embeddings(chunks):
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk, engine="text-embedding-ada-002")
        index.upsert([(f"chunk-{i}", embedding, {"text": chunk})])

# Function to retrieve relevant chunks
def retrieve_relevant_chunks(query, top_k=3):
    query_embedding = get_embedding(query, engine="text-embedding-ada-002")
    results = index.query(query_embedding, top_k=top_k, include_metadata=True)
    relevant_chunks = [match["metadata"]["text"] for match in results["matches"]]
    return relevant_chunks

# Streamlit App Title
st.markdown("<h1 style='color:white;'>StudyGPT</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:grey; font-size: small;'>StudyGPT uses a set of prompts designed to help students. To use, simply type the thing you need help with. The model will then guide you to solving your problems! This is still a prototype. Still check important info</p>", unsafe_allow_html=True)
st.markdown("<p style='color:white;'>This model is not intended to give a 'quick' answer to your last-minute homework, and would not be a substitute for a teacher.</p>", unsafe_allow_html=True)
st.markdown("<p style='color:white;'>Important: This GPT does not log or store any data.</p>", unsafe_allow_html=True)

# File Uploader
uploaded_file = st.file_uploader("Choose a file (PDF only)")
if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        text = extract_text_from_pdf(uploaded_file)
        chunks = split_text_into_chunks(text)
        generate_and_store_embeddings(chunks)
        st.success("File uploaded and processed successfully!")
    else:
        st.error("Only PDF files are supported at the moment.")

# Sidebar for Settings & Features
st.sidebar.title("Settings & Features")
st.sidebar.write("Adjust settings, explore features, or access additional tools.")

# Advanced Model Tuning
chosen_temperature = 0.1
st.sidebar.markdown(f"Temperature is {chosen_temperature} ")

# Notes Section
with st.sidebar.expander("My Notes"):
    notes = load_notes()
    if notes:
        for i, note in enumerate(notes):
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.markdown(f"- {note}")
            with col2:
                if st.button("❌", key=f"delete_note_{i}"):
                    notes.pop(i)
                    with open('notes.json', 'w') as f:
                        json.dump(notes, f)
    else:
        st.markdown("No notes saved.")

    # Add a new note
    new_note = st.text_input("Add a Note", key="note_input")
    if st.button("Save Note"):
        if new_note:
            notes.append(new_note)
            with open('notes.json', 'w') as f:
                json.dump(notes, f)
            st.success("Click again to confirm")

# Dropdown box for GPT's Mission
with st.expander("The GPT's Mission!"):
    st.markdown(f"<p style='color:white;'>{system_prompt}</p>", unsafe_allow_html=True)

# Initialize session state for model and messages
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4"

if "messages" not in st.session_state:
    st.session_state.messages = load_conversations()

# Reset Chat button
if st.button("Reset Chat"):
    st.session_state.messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": "Hey there, how can I help you today?"}
    ]
    save_conversations(st.session_state.messages)

# Display conversation history (excluding system messages)
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# User input
user_input = st.chat_input("Throw a question!")

# Process user input
if user_input:
    # Retrieve relevant chunks
    relevant_chunks = retrieve_relevant_chunks(user_input)
    context = "\n\n".join(relevant_chunks)

    # Augment the user's query with the retrieved context
    augmented_prompt = f"Context:\n{context}\n\nQuestion: {user_input}"

    # Add the augmented prompt to the conversation history
    st.session_state.messages.append({"role": "user", "content": augmented_prompt})

    # Display user input in the chat interface
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate AI response using the OpenAI API
    with st.chat_message("assistant"):
        completion = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=st.session_state.messages,
            temperature=chosen_temperature,
        )
        response = completion.choices[0].message.content
        st.markdown(response)

        # Add the AI's response to the conversation history
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Save updated conversation history to file
    save_conversations(st.session_state.messages)
