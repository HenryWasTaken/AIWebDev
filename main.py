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
st.markdown("<h1 style='color:white;'>StudyGPT Demo</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:grey; font-size: small;'>This is a demo of StudyGPT, a set of prompts designed to help students. To use, simply type the thing you need help with. The model will then guide you to solving your problems!</p>", unsafe_allow_html=True)
st.markdown("<p style='color:white;'>This model is not intended to give a 'quick' answer to your last-minute homework, and is not a substitute for a teacher.</p>", unsafe_allow_html=True)

# Add the contact information
st.markdown("<p style='color:white;'>Contact: <a href='mailto:henry.sun@abingdon.org.uk' style='color:white;'>Henry Sun</a></p>", unsafe_allow_html=True)

# Add the dropdown box to show the system prompt
with st.expander("The GPT's Mission!"):
    st.markdown(f"<p style='color:white;'>{system_prompt}</p>", unsafe_allow_html=True)

# Initialize session state for model and messages
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4"

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]  # Include system prompt

# Display conversation history (excluding the system prompt)
for message in st.session_state.messages:
    if message["role"] != "system":  # Skip system messages
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Input field for user to ask a question
user_input = st.chat_input("Throw a question!")

# Comment under the input box
st.markdown("<p style='color:grey; font-size: small;'>This is still a prototype. Still check important info.</p>", unsafe_allow_html=True)

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

    # Generate and display image based on user input
    # image_url = generate_image(user_input)
    # st.image(image_url, caption="Generated Image")

    # Optionally display the image URL
    # st.write(f"Image URL: {image_url}")

# Add a small comment at the middle bottom of the webpage
st.markdown(
    """
    <style>
    .middle-bottom-comment {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 12px;
        color: grey;
    }
    </style>
    <div class="middle-bottom-comment">This is still a prototype. Still check important info.</div>
    """,
    unsafe_allow_html=True
)

# Add a small comment on the bottom right for version 1.0 alpha
st.markdown(
    """
    <style>
    .small-comment {
        position: fixed;
        bottom: 10px;
        right: 10px;
        font-size: 12px;
        color: grey;
    }
    </style>
    <div class="small-comment">1.0 alpha</div>
    """,
    unsafe_allow_html=True
)
