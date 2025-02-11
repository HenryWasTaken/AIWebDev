import os
import json
import streamlit as st
from pypdf import PdfReader
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

# Initialize OpenAI and Pinecone clients
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
pc = Pinecone(api_key=st.secrets["PINECONE_API_KEY"])

# Pinecone index name
index_name = "study-gpt-index"

# Check if the index exists, and create it if it doesn't
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,  # OpenAI embedding dimension
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

# Connect to the index
index = pc.Index(index_name)

# System prompt
system_prompt = "You are StudyGPT, a helpful AI assistant designed to help students learn and solve problems. Provide detailed explanations and guide users to understand concepts. If the question involves math, format equations using LaTeX."

# Function to load conversations from a file
def load_conversations():
    try:
        with open('conversations.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": "Hey there, how can I help?"}
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

# Function to save notes to a file
def save_notes(notes):
    with open('notes.json', 'w') as f:
        json.dump(notes, f)

# Function to extract text from a PDF
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Function to split text into chunks
def split_text_into_chunks(text, chunk_size=500):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

# Function to generate embeddings
def get_embedding(text, engine="text-embedding-ada-002"):
    response = client.embeddings.create(input=text, model=engine)
    return response.data[0].embedding

# Function to generate and store embeddings
def generate_and_store_embeddings(chunks):
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        index.upsert([(f"chunk-{i}", embedding, {"text": chunk})])

# Function to clear context from the index
def clear_context():
    try:
        index.delete(delete_all=True)
        st.success("Successfully cleared all data from the index!")
    except Exception as e:
        if "Namespace not found" in str(e):
            st.warning("Nothing to clear. The index or namespace is already empty.")
        else:
            st.error(f"Failed to clear context: {e}")

# Function to retrieve relevant chunks
def retrieve_relevant_chunks(query, top_k=3):
    query_embedding = get_embedding(query)
    try:
        results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
        return [match["metadata"]["text"] for match in results["matches"]]
    except Exception as e:
        st.error(f"Error querying Pinecone: {e}")
        return []

# Streamlit App Title
st.markdown("<h1 style='color:white;'>StudyGPT</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:grey; font-size: small;'>StudyGPT uses RAG (Retrieval-augmented generation) to help students. Avoid entering sensitive information as data is stored in a vector database.</p>", unsafe_allow_html=True)

# File Uploader
uploaded_file = st.file_uploader("Upload a PDF or TXT file", type=["pdf", "txt"])
if uploaded_file:
    if uploaded_file.type == "application/pdf":
        text = extract_text_from_pdf(uploaded_file)
    elif uploaded_file.type == "text/plain":
        text = uploaded_file.read().decode("utf-8")
    else:
        st.error("Unsupported file type.")

    chunks = split_text_into_chunks(text)
    generate_and_store_embeddings(chunks)
    st.success("File processed and stored successfully!")

# Sidebar for Settings & Features
st.sidebar.title("Settings & Features")
if st.sidebar.button("Clear Context"):
    clear_context()

# Notes Section
with st.sidebar.expander("My Notes"):
    notes = load_notes()
    for i, note in enumerate(notes):
        st.markdown(f"- {note}")
        if st.button("❌", key=f"delete_note_{i}"):
            notes.pop(i)
            save_notes(notes)
            st.experimental_rerun()

    new_note = st.text_input("Add a Note")
    if st.button("Save Note") and new_note:
        notes.append(new_note)
        save_notes(notes)
        st.experimental_rerun()

# Display conversation history
if "messages" not in st.session_state:
    st.session_state.messages = load_conversations()

if st.button("Reset Chat"):
    st.session_state.messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": "Hey there, how can I help?"}
    ]
    save_conversations(st.session_state.messages)
    st.experimental_rerun()

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Process user input
user_input = st.chat_input("Throw a question!")
if user_input:
    # Retrieve relevant chunks
    relevant_chunks = retrieve_relevant_chunks(user_input)
    context = "\n\n".join(relevant_chunks)

    # Augment the user's query with the retrieved context
    augmented_prompt = (
        "You are a helpful assistant. Use the following context to answer the user's question.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {user_input}\n\n"
    )

    # Add the augmented prompt to the conversation history
    st.session_state.messages.append({"role": "user", "content": augmented_prompt})

    # Display user input in the chat interface
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate AI response using the OpenAI API
    with st.chat_message("assistant"):
        try:
            completion = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=st.session_state.messages,
                temperature=chosen_temperature,
            )
            response = completion.choices[0].message.content

            # Check if the response contains LaTeX math content
            if "$$" in response or "\\(" in response or "\\[" in response:
                # Extract LaTeX portion and render it
                st.markdown(response)  # Render the entire response as markdown
                if "$$" in response:
                    latex_content = response.split("$$")[1]
                    st.latex(latex_content)
            else:
                st.markdown(response)  # Render normal text response

        except Exception as e:
            st.error(f"An error occurred: {e}")
            response = "Sorry, I couldn't generate a response. Please try again."

        # Add the AI's response to the conversation history
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Save updated conversation history to file
    save_conversations(st.session_state.messages)
