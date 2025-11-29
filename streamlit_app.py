import streamlit as st
from openai import OpenAI

# --- Login Logic ---
if "user_name" not in st.session_state:
    st.session_state.user_name = None

if not st.session_state.user_name:
    st.title("👋 Welcome")
    name_input = st.text_input("Please enter your name to login:")
    
    if st.button("Join Chat"):
        if name_input.strip():
            st.session_state.user_name = name_input
            st.rerun()
        else:
            st.warning("Name cannot be empty.")
    st.stop()  # Stop the app here until the user logs in

st.title("🤖 GPT-5 Nano Chatbot")
st.success(f"Thanks {st.session_state.user_name} for joining!")
st.caption("Powered by OpenAI's gpt-5-nano model")

# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
# You can also use prompt for getting the API key
# openai_api_key = st.text_input("OpenAI API Key", type="password")

openai_api_key = st.secrets["GPT5_MINI_API_KEY"]

# Create an OpenAI client.
client = OpenAI(api_key=openai_api_key)

# Create a session state variable to store the chat messages. This ensures that the
# messages persist across reruns.
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display the existing chat messages via `st.chat_message`.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Create a chat input field to allow the user to enter a message. This will display
# automatically at the bottom of the page.
if prompt := st.chat_input("What is up?"):

    # Store and display the current prompt.
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate a response using the OpenAI API.
    stream = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ],
        stream=True,
    )

    # Stream the response to the chat using `st.write_stream`, then store it in 
    # session state.
    with st.chat_message("assistant"):
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
