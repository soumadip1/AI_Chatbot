import streamlit as st
from openai import OpenAI
from datetime import datetime
import requests

# --- Login Logic ---
if "user_name" not in st.session_state:
    st.session_state.user_name = None

if not st.session_state.user_name:
    st.title("👋 Soumadip welcomes you 👋")
    name_input = st.text_input("Please enter your name to login:")
    location_input = st.text_input("Enter your city (e.g., Amsterdam):")
    
    if st.button("Join Chat"):
        #Check if name is empty
        if not name_input.strip():
            st.warning("Name cannot be empty.")
        #Check if location is empty
        elif not location_input.strip(): 
            st.warning("Location cannot be empty.")
        #Set both name and location
        else:
            st.session_state.user_name = name_input.strip()
            st.session_state.location = location_input.strip()
            st.rerun()

    st.stop()  # Stop the app here until the user logs in

st.title("🤖 GPT-5 Nano Chatbot")
st.success(f"Thanks {st.session_state.user_name} for joining!")
st.caption("Powered by OpenAI's gpt-5-nano model")

#Function to get current date and time
def get_current_time():
    return datetime.now().strftime("%A, %d %B %Y, %H:%M")

#Function to get current server location
def get_user_location():
    try:
        res = requests.get("https://ipinfo.io/json").json()
        return res.get("city", "Unknown")
    except:
        return "Unknown"

#Function to call Serpex.dev Search API for news    
def web_search(query: str):
    st.write("****************** Inside web search *******************")
    """Use Serpex.dev Search API"""
    url = "https://api.serpex.dev/api/search"
    
    #Get the API Key from secrets
    serpex_api_key = st.secrets["SERPEX_KEY"]

    #Add header information with the API key
    headers = {
               "Authorization": f"Bearer {serpex_api_key}"
              }
    
    #Pass the query parameters
    params = {
              "q": f"{query}",
              "engine": "auto"
             }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    results = []
    for item in data.get("results", []):
        #Get the title information
        title = item.get("title", "")
        
        #Get the snippet or description or content from the response
        snippet = item.get("snippet") or item.get("description") or item.get("content") or ""
        
        #Only append the relevant results when snippet is not blank
        if snippet =="" or snippet is None:
            False
        else:
            results.append(f"{title}: {snippet}")

    st.write("\n".join(results) if results else "No results found.")
    return "\n".join(results) if results else "No results found."

def needs_search(prompt: str) -> bool:
    keywords = ["news", "headline", "weather", "latest", "current", "today"]
    return any(word in prompt.lower() for word in keywords)

#Fetch co-ordinates from city name
def get_coordinates(city: str):
    """Convert city name to latitude and longitude using OpenStreetMap Nominatim"""
    url = f"https://nominatim.openstreetmap.org/search?q={city}&format=json&limit=1"
    try:
        res = requests.get(url, headers={"User-Agent": "streamlit-weather-app"}).json()
        if res:
            lat = float(res[0]["lat"])
            lon = float(res[0]["lon"])
            return lat, lon
        else:
            return None, None
    except Exception as e:
        print("DEBUG: Geocoding error:", e)
        return None, None

#Fetch weather from Open‑Meteo using latitude and logitude co-ordinates
def get_weather(city: str):
    """Fetch current weather for a city using Open-Meteo"""
    lat, lon = get_coordinates(city)
    if not lat or not lon:
        return f"Could not determine coordinates for {city}."
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    try:
        res = requests.get(url).json()
        current = res.get("current_weather", {})
        if not current:
            return f"No weather data available for {city}."
        temp = current.get("temperature")
        wind = current.get("windspeed")
        return f"The current weather in {city} is {temp}°C with wind speed {wind} km/h."
    except Exception as e:
        return f"Weather error: {e}"

#Add current time in context
st.session_state.current_time = get_current_time()

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
if prompt := st.chat_input("What is on your mind?"):

    # Store and display the current prompt.
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # New: Build enriched context with time, location, and search results
    context_msgs = [
        {"role": "system", "content": f"The current time is {st.session_state.current_time}."},
        {"role": "system", "content": f"The user is located in {st.session_state.location}."}
    ]

    if needs_search(prompt):
        if "weather" in prompt.lower():
            weather_info = get_weather(st.session_state.location) 
            context_msgs.append({"role": "system", "content": weather_info})
        else:
            search_results = web_search(prompt)
            context_msgs.append({
                                 "role": "assistant"
                                 , "content": f"Here are the latest headlines:\n{search_results}"
                                }
                            )

    # New: Combine context with chat history
    api_messages = context_msgs \
                   + [ 
                       {"role": m["role"], "content": m["content"]}
                          for m in st.session_state.messages
                     ]        

    # Generate a response using the OpenAI API.
    # Add current context to message
    stream = client.chat.completions.create(
                                             model="gpt-5-nano",
                                             messages=api_messages,
                                             stream=True,
                                            )

    # Stream the response to the chat using `st.write_stream`, then store it in 
    # session state.
    with st.chat_message("assistant"):
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
