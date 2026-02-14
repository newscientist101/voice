import os
import httpx
import urllib.parse

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
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
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

    except httpx.HTTPStatusError as e:
        await params.result_callback({"error": f"API request failed with status {e.response.status_code}"})
    except httpx.RequestError as e:
        await params.result_callback({"error": f"API request failed: {e}"})
    except (KeyError, IndexError) as e:
        await params.result_callback({"error": f"Failed to parse weather data: {e}"})
    except Exception as e:
        await params.result_callback({"error": f"An unexpected error occurred: {e}"})

async def wolframalpha_query(params: FunctionCallParams, query: str):
    """Perform a WolframAlpha query. This can be used for complex calculations and fact lookups like local time for a specific location. Convert your query to simplified keyword queries whenever possible (e.g. convert "how many people live in France" to "France population").

    Args:
        query: The query string to send to WolframAlpha.
    """
    api_key = os.environ.get("WOLFRAMALPHAAPI")
    if not api_key:
        await params.result_callback({"error": "WOLFRAMALPHAAPI key not set"})
        return
    url = f"https://www.wolframalpha.com/api/v1/llm-api?input={query}&appid={api_key}&format=plaintext&units=nonmetric&reinterpret=true"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.text

        if "Result" in data:
            await params.result_callback({"result": data})
        else:
            await params.result_callback({"error": "No result found in WolframAlpha response"})

    except httpx.HTTPStatusError as e:
        await params.result_callback({"error": f"API request failed with status {e.response.status_code}"})
    except httpx.RequestError as e:
        await params.result_callback({"error": f"API request failed: {e}"})
    except (KeyError, IndexError) as e:
        await params.result_callback({"error": f"Failed to parse WolframAlpha data: {e}"})

async def wikipedia_summary(params: FunctionCallParams, topic: str):
    """Get a concise summary of a topic from Wikipedia. Use this when the user asks for general information, history, or a description of a person, place, or concept.

    Args:
        topic: The topic to search for on Wikipedia.
    """
    encoded_topic = urllib.parse.quote(topic.replace(' ', '_'))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_topic}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 404:
                await params.result_callback({"error": f"No Wikipedia article found for '{topic}'"})
                return
            response.raise_for_status()
            data = response.json()

        result = {
            "title": data.get("title"),
            "summary": data.get("extract"),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page")
        }
        await params.result_callback(result)

    except httpx.HTTPStatusError as e:
        await params.result_callback({"error": f"Wikipedia API error: {e.response.status_code}"})
    except httpx.RequestError as e:
        await params.result_callback({"error": f"Wikipedia request failed: {e}"})
    except Exception as e:
        await params.result_callback({"error": f"An unexpected error occurred: {e}"})

async def hangup(params: FunctionCallParams):
    """Hang up the current call.
    Alias: "End Call", "Disconnect the call", "Terminate Call"
    """
    await params.llm.push_frame(TTSSpeakFrame("Hanging up now."))

    # Signal that the task should end after processing this frame
    await params.llm.push_frame(EndTaskFrame(), FrameDirection.UPSTREAM)
async def get_news_headlines(params: FunctionCallParams, category: str = "World"):
    """Get the latest news headlines for a specific category.

    Args:
        category: The category of news to retrieve. Options: "Business", "Entertainment", "Health", "Science", "Sports", "Technology", "US", "World". Default is "World".
    """
    url = "https://ok.surf/api/v1/cors/news-feed"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        if category not in data:
            await params.result_callback({"error": f"Category '{category}' not found. Available categories: {', '.join(data.keys())}"})
            return

        headlines = []
        for article in data[category][:5]:  # Get top 5 headlines
            headlines.append({
                "title": article.get("title"),
                "source": article.get("source")
            })

        await params.result_callback({"category": category, "headlines": headlines})

    except httpx.HTTPStatusError as e:
        await params.result_callback({"error": f"News API error: {e.response.status_code}"})
    except httpx.RequestError as e:
        await params.result_callback({"error": f"News request failed: {e}"})
    except Exception as e:
        await params.result_callback({"error": f"An unexpected error occurred: {e}"})

async def convert_currency(params: FunctionCallParams, amount: float, from_currency: str, to_currency: str):
    """Convert an amount from one currency to another using real-time exchange rates.

    Args:
        amount: The amount of money to convert.
        from_currency: The source currency code (e.g., "USD", "EUR", "GBP").
        to_currency: The target currency code (e.g., "JPY", "CAD", "AUD").
    """
    url = f"https://open.er-api.com/v6/latest/{from_currency.upper()}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        if data.get("result") == "error":
            error_type = data.get("error-type", "unknown error")
            await params.result_callback({"error": f"Currency API error: {error_type}"})
            return

        rates = data.get("rates", {})
        target_code = to_currency.upper()
        if target_code not in rates:
            await params.result_callback({"error": f"Target currency '{to_currency}' not found."})
            return

        rate = rates[target_code]
        converted_amount = amount * rate

        result = {
            "from": from_currency.upper(),
            "to": target_code,
            "amount": amount,
            "converted_amount": round(converted_amount, 2),
            "rate": rate,
            "last_updated": data.get("time_last_update_utc")
        }
        await params.result_callback(result)

    except httpx.HTTPStatusError as e:
        await params.result_callback({"error": f"Currency API error: {e.response.status_code}"})
    except httpx.RequestError as e:
        await params.result_callback({"error": f"Currency request failed: {e}"})
    except Exception as e:
        await params.result_callback({"error": f"An unexpected error occurred: {e}"})

async def get_ip_info(params: FunctionCallParams, ip_or_domain: str = ""):
    """Get geolocation and network information for an IP address or domain name.

    Args:
        ip_or_domain: The IP address or domain name to look up. If empty, the bot's current public IP will be used.
    """
    url = f"http://ip-api.com/json/{ip_or_domain}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        if data.get("status") == "fail":
            await params.result_callback({"error": f"IP lookup failed: {data.get('message')}"})
            return

        # Return relevant fields
        result = {
            "query": data.get("query"),
            "status": data.get("status"),
            "country": data.get("country"),
            "countryCode": data.get("countryCode"),
            "regionName": data.get("regionName"),
            "city": data.get("city"),
            "zip": data.get("zip"),
            "timezone": data.get("timezone"),
            "isp": data.get("isp"),
            "org": data.get("org"),
            "as": data.get("as")
        }
        await params.result_callback(result)

    except httpx.HTTPStatusError as e:
        await params.result_callback({"error": f"IP API error: {e.response.status_code}"})
    except httpx.RequestError as e:
        await params.result_callback({"error": f"IP request failed: {e}"})
    except Exception as e:
        await params.result_callback({"error": f"An unexpected error occurred: {e}"})

async def get_github_stats(params: FunctionCallParams, owner: str, repo: str):
    """Get statistics for a GitHub repository, including stars, forks, and open issues.

    Args:
        owner: The owner of the repository (e.g., "pipecat-ai").
        repo: The name of the repository (e.g., "pipecat").
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 404:
                await params.result_callback({"error": f"Repository '{owner}/{repo}' not found."})
                return
            response.raise_for_status()
            data = response.json()

        result = {
            "name": data.get("full_name"),
            "description": data.get("description"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "open_issues": data.get("open_issues_count"),
            "language": data.get("language"),
            "url": data.get("html_url"),
            "last_updated": data.get("updated_at")
        }
        await params.result_callback(result)

    except httpx.HTTPStatusError as e:
        await params.result_callback({"error": f"GitHub API error: {e.response.status_code}"})
    except httpx.RequestError as e:
        await params.result_callback({"error": f"GitHub request failed: {e}"})
    except Exception as e:
        await params.result_callback({"error": f"An unexpected error occurred: {e}"})
