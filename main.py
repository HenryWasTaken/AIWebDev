import openai
import streamlit as st
import pinecone
from pypdf import PdfReader

# Function to get embeddings using OpenAI
def get_embedding(text, engine="text-embedding-ada-002"):
    response = openai.Embedding.create(input=text, model=engine)
    return response['data'][0]['embedding']

# Initialize Pinecone and OpenAI
pinecone.init(api_key=st.secrets["PINECONE_API_KEY"], environment="us-west1-gcp")
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Constants
INDEX_NAME = "study-gpt-index"
SYSTEM_PROMPT = (
    "You are StudyGPT, a helpful AI assistant designed to help students learn and solve problems. "
    "Provide detailed explanations and guide users to understand concepts."
)

# Initialize Pinecone index
if INDEX_NAME not in pinecone.list_indexes():
    pinecone.create_index(INDEX_NAME, dimension=3072)
index = pinecone.Index(INDEX_NAME)

# Utility Functions
def load_json_file(file_name, default_data):
    try:
        with open(file_name, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default_data

def save_json_file(file_name, data):
    with open(file_name, 'w') as f:
        json.dump(data, f)

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    return "".join(page.extract_text() for page in reader.pages)

def split_text_into_chunks(text, chunk_size=500):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def generate_and_store_embeddings(chunks):
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk, engine="text-embedding-ada-002")
        index.upsert([(f"chunk-{i}", embedding, {"text": chunk})])

def retrieve_relevant_chunks(query, top_k=3):
    query_embedding = get_embedding(query, engine="text-embedding-ada-002")
    results = index.query(query_embedding, top_k=top_k, include_metadata=True)
    return [match["metadata"]["text"] for match in results["matches"]]

# Load conversations and notes
conversations = load_json_file("conversations.json", [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "assistant", "content": "Hey there, how can I help you today?"}
])
notes = load_json_file("notes.json", [])

# Streamlit UI
st.markdown("<h1 style='color:white;'>StudyGPT</h1>", unsafe_allow_html=True)
st.markdown("""
<p style='color:grey; font-size: small;'>StudyGPT helps students learn by providing detailed explanations. 
It's not intended for quick homework solutions or as a teacher substitute. This prototype does not log or store any data.</p>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Choose a file (PDF only)")
if uploaded_file and uploaded_file.type == "application/pdf":
    text = extract_text_from_pdf(uploaded_file)
    chunks = split_text_into_chunks(text)
    generate_and_store_embeddings(chunks)
    st.success("File uploaded and processed successfully!")
elif uploaded_file:
    st.error("Only PDF files are supported.")

# Sidebar
st.sidebar.title("Settings & Features")
st.sidebar.markdown(f"Temperature: 0.1")
st.sidebar.expander("My Notes").markdown(
    "\n".join(f"- {note}" for note in notes) if notes else "No notes saved."
)

new_note = st.sidebar.text_input("Add a Note")
if st.sidebar.button("Save Note") and new_note:
    notes.append(new_note)
    save_json_file("notes.json", notes)
    st.sidebar.success("Note saved!")

st.expander("The GPT's Mission").markdown(SYSTEM_PROMPT)

# Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = conversations

if st.button("Reset Chat"):
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": "Hey there, how can I help you today?"}
    ]
    save_json_file("conversations.json", st.session_state.messages)

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

user_input = st.chat_input("Ask a question!")
if user_input:
    relevant_chunks = retrieve_relevant_chunks(user_input)
    context = "\n\n".join(relevant_chunks)
    augmented_prompt = f"Context:\n{context}\n\nQuestion: {user_input}"

    st.session_state.messages.append({"role": "user", "content": augmented_prompt})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="gpt-4",
            messages=st.session_state.messages,
            temperature=0.1
        ).choices[0].message.content
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

    save_json_file("conversations.json", st.session_state.messages)
