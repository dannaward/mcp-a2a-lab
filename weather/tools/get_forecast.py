from constants import NWS_API_BASE
from utils import make_nws_request
from web_weather_fallback import smart_weather_fallback, get_location_from_coords


def register_forecast_tools(mcp):
    @mcp.tool()
    async def get_forecast(latitude: float, longitude: float) -> str:
        """Get weather forecast for a location with web fallback.

        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
        """
        async def _get_forecast_api():
            # First get the forecast grid endpoint
            points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
            points_data = await make_nws_request(points_url)

            if not points_data:
                return "Unable to fetch forecast data for this location."

            # Get the forecast URL from the points response
            forecast_url = points_data["properties"]["forecast"]
            forecast_data = await make_nws_request(forecast_url)

            if not forecast_data:
                return "Unable to fetch detailed forecast."

            # Format the periods into a readable forecast
            periods = forecast_data["properties"]["periods"]
            forecasts = []
            for period in periods[:5]:  # Only show next 5 periods
                forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
                forecasts.append(forecast)

            return "\n---\n".join(forecasts)
        
        # Use smart fallback wrapper
        return await smart_weather_fallback(
            location=get_location_from_coords(latitude, longitude),
            tool_name="Weather Forecast",
            api_function=_get_forecast_api
        )