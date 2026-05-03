import streamlit as st
import requests
import json

# --- Configuration ---
# FastAPI backend URL (will be http://localhost:8000 when run locally, or the service name in Docker Compose/Kubernetes)
BACKEND_URL = "http://localhost:8000/chat"

st.set_page_config(page_title="FoodHub Chatbot", page_icon=":fork_and_knife:")

# --- Streamlit UI ---
st.title(":fork_and_knife: FoodHub Customer Support")
st.markdown("Hello! I am ChefByte, your friendly AI assistant. I can help you with your food order queries.")

# Initialize chat history in session state if not already present
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What is your order ID?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Prepare the payload for the FastAPI backend
    payload = {
        "question": prompt,
        "history": st.session_state.messages
    }

    try:
        # Make a POST request to the FastAPI backend
        response = requests.post(BACKEND_URL, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        bot_response = response.json()["answer"]
    except requests.exceptions.ConnectionError:
        bot_response = "I'm having trouble connecting to the backend service. Please try again later."
    except requests.exceptions.RequestException as e:
        bot_response = f"An error occurred: {e}"

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(bot_response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": bot_response})
