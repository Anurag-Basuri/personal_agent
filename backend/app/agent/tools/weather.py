"""Weather tool — fetches current weather using Open-Meteo API (free, no API key needed)."""

import httpx
from langchain_core.tools import tool


# Open-Meteo uses WMO weather codes
_WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


async def _geocode(city: str) -> dict | None:
    """Resolve city name to lat/lon using Open-Meteo's geocoding API."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
        )
        data = res.json()
        results = data.get("results")
        if results:
            return results[0]
    return None


@tool
async def weather_tool(city: str) -> str:
    """Get the current weather and 3-day forecast for any city worldwide.
    Provide the city name (e.g., 'Delhi', 'New York', 'London')."""
    try:
        # 1. Geocode the city
        location = await _geocode(city)
        if not location:
            return f'Could not find location "{city}". Try a more specific city name.'

        lat = location["latitude"]
        lon = location["longitude"]
        display_name = f"{location.get('name', city)}, {location.get('country', '')}"

        # 2. Fetch weather
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
                    "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                    "timezone": "auto",
                    "forecast_days": 3,
                },
            )
            weather = res.json()

        # 3. Format current weather
        current = weather.get("current", {})
        code = current.get("weather_code", 0)
        condition = _WMO_CODES.get(code, "Unknown")

        result = f"☁️ Weather for {display_name}\n\n"
        result += f"Current: {condition}\n"
        result += f"Temperature: {current.get('temperature_2m', 'N/A')}°C (feels like {current.get('apparent_temperature', 'N/A')}°C)\n"
        result += f"Humidity: {current.get('relative_humidity_2m', 'N/A')}%\n"
        result += f"Wind: {current.get('wind_speed_10m', 'N/A')} km/h\n"

        # 4. Format forecast
        daily = weather.get("daily", {})
        dates = daily.get("time", [])
        if dates:
            result += "\n3-Day Forecast:\n"
            for i, date in enumerate(dates):
                d_code = daily["weather_code"][i]
                d_cond = _WMO_CODES.get(d_code, "Unknown")
                hi = daily["temperature_2m_max"][i]
                lo = daily["temperature_2m_min"][i]
                rain = daily.get("precipitation_probability_max", [None])[i]
                rain_str = f", {rain}% rain chance" if rain is not None else ""
                result += f"  {date}: {d_cond} — {lo}°C / {hi}°C{rain_str}\n"

        return result

    except httpx.TimeoutException:
        return "Weather API timed out. Please try again in a moment."
    except Exception as e:
        return f"Error fetching weather data: {e}"
