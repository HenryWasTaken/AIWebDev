import os
from openai import OpenAI
from dotenv import load_dotenv
from prompt import system_prompt
from AIImage import generate_image
import streamlit as st
# from prompt import system_prompt  # Assuming you have a predefined system prompt
# from AIImage import generate_image  # Assuming this is your image generation function

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Placeholder database functions (replace with actual database queries)
chat_history_db = []  # This will simulate the database for now

def save_message_with_embedding(user_message, assistant_message):
    # Generate embeddings
    user_embedding = get_embedding(user_message)
    assistant_embedding = get_embedding(assistant_message)
    
    # Simulate saving to a database
    chat_data = {
        "user_message": user_message,
        "user_embedding": user_embedding,
        "assistant_message": assistant_message,
        "assistant_embedding": assistant_embedding
    }
    chat_history_db.append(chat_data)  # Simulating saving to a database

def fetch_saved_chats():
    # Simulate fetching from a database (this would be a query in real-life)
    return chat_history_db

def get_embedding(message):
    embedding_response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=message
    )
    return embedding_response["data"][0]["embedding"]

def load_chat_history():
    saved_chats = fetch_saved_chats()
    for chat in saved_chats:
        st.session_state.messages.append({"role": "user", "content": chat["user_message"]})
        st.session_state.messages.append({"role": "assistant", "content": chat["assistant_message"]})

# Streamlit App Title with different text styles
st.markdown("<h1 style='color:white;'>StudyGPT</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:grey; font-size: small;'>StudyGPT uses a set of prompts designed to help students. To use, simply type the thing you need help with. The model will then guide you to solving your problems! This is still a prototype. Still check important info</p>", unsafe_allow_html=True)
st.markdown("<p style='color:white;'>This model is not intended to give a 'quick' answer to your last-minute homework, and would not be a substitute for a teacher.</p>", unsafe_allow_html=True)
st.markdown("<p style='color:white;'>Important: This GPT does not log or store any data.</p>", unsafe_allow_html=True)

# Add the contact information
st.markdown("<p style='color:white;'>Under the development of:  <a href='mailto:henry.sun@abingdon.org.uk' style='color:white;'>Abingdon AI Web Development Club</a></p>", unsafe_allow_html=True)
st.markdown("Pre-alpha, Here's a bouquet &mdash;\
            :tulip::cherry_blossom::rose::hibiscus::sunflower::blossom:")

# Add the dropdown box to show the system prompt
with st.expander("The GPT's Mission!"):
    st.markdown(f"<p style='color:white;'>{system_prompt}</p>", unsafe_allow_html=True)

# Initialize session state for model and messages
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": system_prompt},  # Include system prompt
        {"role": "assistant", "content": "Hey there, how can I help you today?"}  # AI's initial greeting
    ]

# Load the chat history from the database when the app loads
load_chat_history()

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

    # Save chat history and embeddings in the database
    save_message_with_embedding(user_input, response)

    # Optionally generate and display images based on user input
    # image_url = generate_image(user_input)
    # st.image(image_url, caption="Generated Image")

    # Optionally display the image URL
    # st.write(f"Image URL: {image_url}")
