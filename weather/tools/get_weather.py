from constants import NWS_API_BASE
from utils import make_nws_request, format_alert
from web_weather_fallback import smart_weather_fallback, get_location_from_coords, create_fallback_response


def register_weather_tools(mcp):
    @mcp.tool()
    async def get_alerts(state: str) -> str:
        """Get weather alerts for a US state with web fallback.

        Args:
            state: Two-letter US state code (e.g. CA, NY)
        """
        async def _get_alerts_api():
            url = f"{NWS_API_BASE}/alerts/active/area/{state}"
            data = await make_nws_request(url)

            if not data or "features" not in data:
                return "Unable to fetch alerts or no alerts found."

            if not data["features"]:
                return "No active alerts for this state."

            alerts = [format_alert(feature) for feature in data["features"]]
            return "\n---\n".join(alerts)
        
        # Use smart fallback wrapper
        return await smart_weather_fallback(
            location=f"State: {state}",
            tool_name="Weather Alerts",
            api_function=_get_alerts_api
        )