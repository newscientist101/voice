import os
import requests
from pipecat.services.llm_service import FunctionCallParams
from pipecat.frames.frames import EndTaskFrame,TTSSpeakFrame
from pipecat.processors.frame_processor import FrameDirection

from dotenv import load_dotenv

load_dotenv(override=True)

# Define a direct function
async def get_current_weather(params: FunctionCallParams, location: str, format: str = "fahrenheit"):
    """Get the current weather. If the user only requests a specific weather property like temperature or humidity, do not provide additional information.

    Args:
        location: The city, state and country, e.g. "San Francisco, CA, USA".
        format: The temperature unit to use, "fahrenheit" is selected by default.
    """
    api_key = os.environ.get("OPENWEATHERAPI")
    if not api_key:
        await params.result_callback({"error": "OPENWEATHERAPI key not set"})
        return
    if 0 < location.count(",") < 2:
        parts = location.split(",")
        if parts[1].strip() in ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH" , "OK" , "OR" , "PA" , 	"RI" , 	"SC" , 	"SD" , 	"TX" , 	"UT" , 	"VT" , 	"VA" , 	"WA" , 	"WV" , 	"WI"]:
            location += ",USA"
        elif parts[1].strip() in ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin"]:
            location += ",USA"
    units = "imperial" if format == "fahrenheit" else "metric"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units={units}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()

        temp_unit = "°F" if units == "imperial" else "°C"
        wind_unit = "mph" if units == "imperial" else "m/s"

        weather_data = {
            "conditions": data["weather"][0]["description"],
            "temperature": f"{data['main']['temp']}{temp_unit}",
            "humidity": f"{data['main']['humidity']}%",
            "wind_speed": f"{data['wind']['speed']} {wind_unit}",
        }
        await params.result_callback(weather_data)
    except requests.exceptions.RequestException as e:
        await params.result_callback({"error": f"API request failed: {e}"})
    except (KeyError, IndexError) as e:
        await params.result_callback({"error": f"Failed to parse weather data: {e}"})

async def define_word(params: FunctionCallParams, word: str):
    """Lookup the definition of a word.

    Args:
        word: The word to lookup.
    """
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        response = requests.get(url)
        if response.status_code == 404:
            await params.result_callback({"error": f"Word '{word}' not found."})
            return
        response.raise_for_status()
        data = response.json()

        # Simplify the response
        meanings = []
        for entry in data:
            for meaning in entry.get("meanings", []):
                part_of_speech = meaning.get("partOfSpeech")
                definitions = [d.get("definition") for d in meaning.get("definitions", [])[:2]]
                meanings.append({
                    "part_of_speech": part_of_speech,
                    "definitions": definitions
                })

        phonetic = data[0].get("phonetic") or (data[0].get("phonetics")[0].get("text") if data[0].get("phonetics") else None)

        result = {
            "word": word,
            "phonetic": phonetic,
            "meanings": meanings[:3]  # Limit to 3 parts of speech for brevity
        }
        await params.result_callback(result)
    except Exception as e:
        await params.result_callback({"error": f"Failed to lookup word: {str(e)}"})

async def hangup(params: FunctionCallParams):
    """Hang up the current call.
    Alias: "End Call", "Disconnect the call", "Terminate Call"
    """
    await params.llm.push_frame(TTSSpeakFrame("Hanging up now."))

    # Signal that the task should end after processing this frame
    await params.llm.push_frame(EndTaskFrame(), FrameDirection.UPSTREAM)