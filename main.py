import os
import json
from openai import OpenAI
import streamlit as st
from pypdf import PdfReader
from pinecone import Pinecone, ServerlessSpec

# Initialize OpenAI and Pinecone clients
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
pc = Pinecone(api_key=st.secrets["PINECONE_API_KEY"])

# Pinecone index name
index_name = "study-gpt-index"

# Check if the index exists, and create it only if it doesn't
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,  # OpenAI embedding dimension
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"  # Virginia
        )
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

# Function to generate embeddings
def get_embedding(text, engine="text-embedding-ada-002"):
    response = client.embeddings.create(
        input=text,
        model=engine
    )
    return response.data[0].embedding

# Function to generate and store embeddings
def generate_and_store_embeddings(chunks):
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        index.upsert([(f"chunk-{i}", embedding, {"text": chunk})])

# Function to retrieve relevant chunks
def retrieve_relevant_chunks(query, top_k=3):
    query_embedding = get_embedding(query)
    if not isinstance(query_embedding, list) or len(query_embedding) != 1536:
        st.error("Invalid query embedding. Expected a list of 1536 floats.")
        return []

    try:
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        relevant_chunks = [match["metadata"]["text"] for match in results["matches"]]
        return relevant_chunks
    except Exception as e:
        st.error(f"Error querying Pinecone: {e}")
        return []

# Function to clear context from the Pinecone index
def clear_context():
    try:
        index = pc.Index(host=st.secrets["INDEX_HOST"])
        index.delete(delete_all=True, namespace='default')
        
        st.success("All context has been cleared from the Pinecone index.")
    except:
        st.error(f"Error clearing context: {e}")



# Streamlit App Title
st.markdown("<h1 style='color:white;'>StudyGPT</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:grey; font-size: small;'>StudyGPT uses a set of prompts designed to help students. To use, simply type the thing you need help with. The model will then guide you to solving your problems! This is still a prototype. Still check important info</p>", unsafe_allow_html=True)
st.markdown("<p style='color:white;'>This model is not intended to give a 'quick' answer to your last-minute homework, and would not be a substitute for a teacher.</p>", unsafe_allow_html=True)
st.markdown("<p style='color:white;'>Important: This GPT is still under development and uses RAG (Retrieval-augmented generation) which may store data in a vector database. Avoid entering sensitive information.</p>", unsafe_allow_html=True)

# File Uploader
uploaded_file = st.file_uploader("Choose a file (PDF or TXT)", type=["pdf", "txt"])
if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        # Extract text from PDF
        text = extract_text_from_pdf(uploaded_file)
        chunks = split_text_into_chunks(text)
        generate_and_store_embeddings(chunks)
        st.success("PDF file uploaded and processed successfully!")
    elif uploaded_file.type == "text/plain":
        # Extract text from TXT
        text = uploaded_file.read().decode("utf-8")  # Decode bytes to string
        chunks = split_text_into_chunks(text)
        generate_and_store_embeddings(chunks)
        st.success("TXT file uploaded and processed successfully!")
    else:
        st.error("Unsupported file type. Please upload a PDF or TXT file.")

# Sidebar for Settings & Features
st.sidebar.title("Settings & Features")
st.sidebar.write("Adjust settings, explore features, or access additional tools.")

# Clear Context Button
if st.sidebar.button("Clear Context"):
    clear_context()


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
    if not any(msg["role"] == "system" for msg in st.session_state.messages):
        st.session_state.messages.insert(0, {"role": "system", "content": system_prompt})

# Reset Chat button
if st.button("Reset Chat"):
    st.session_state.messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": "Hey there, how can I help?"}
    ]
    save_conversations(st.session_state.messages)
    st.success("Chat history has been reset.")

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
                temperature=0.5,
            )
            response = completion.choices[0].message.content

            # Check if the response contains LaTeX math content
            if "$$" in response or "\\(" in response or "\\[" in response:
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
