from web_weather_fallback import smart_weather_fallback, get_location_from_coords, create_fallback_response
from constants import NWS_API_BASE
from utils import make_nws_request
import asyncio


def register_web_enhanced_tools(mcp):
    """Register web-enhanced weather tools with intelligent fallback"""
    
    @mcp.tool()
    async def get_comprehensive_weather(latitude: float, longitude: float) -> str:
        """Get comprehensive weather information with automatic web fallback.
        
        This tool tries multiple data sources and provides the best available information.
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
        """
        location = get_location_from_coords(latitude, longitude)
        
        async def _get_comprehensive_api():
            try:
                # Try to get multiple types of data
                results = []
                
                # Get basic forecast
                points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
                points_data = await make_nws_request(points_url)
                
                if points_data:
                    # Get current conditions
                    forecast_url = points_data["properties"]["forecast"]
                    forecast_data = await make_nws_request(forecast_url)
                    
                    if forecast_data:
                        current_period = forecast_data["properties"]["periods"][0]
                        results.append(f"""
🌤️ Current Conditions:
{current_period['name']}: {current_period['temperature']}°{current_period['temperatureUnit']}
Wind: {current_period['windSpeed']} {current_period['windDirection']}
Conditions: {current_period['shortForecast']}
Details: {current_period['detailedForecast']}
""")
                    
                    # Get alerts if available
                    county = points_data["properties"].get("county")
                    if county:
                        county_code = county.split("/")[-1]
                        alerts_url = f"{NWS_API_BASE}/alerts/active/zone/{county_code}"
                        alerts_data = await make_nws_request(alerts_url)
                        
                        if alerts_data and alerts_data.get("features"):
                            alert_count = len(alerts_data["features"])
                            results.append(f"""
⚠️ Active Alerts: {alert_count} alert(s) for this area
(Use get_weather_watches_warnings for details)
""")
                        else:
                            results.append("✅ No active weather alerts")
                    
                    # Add location info
                    results.append(f"""
📍 Location Info:
Forecast Office: {points_data["properties"]["cwa"]}
Grid Point: {points_data["properties"]["gridId"]} ({points_data["properties"]["gridX"]},{points_data["properties"]["gridY"]})
Time Zone: {points_data["properties"]["timeZone"]}
""")
                
                if results:
                    return "\n".join(results)
                else:
                    return "Unable to fetch comprehensive weather data."
                    
            except Exception as e:
                return f"Error fetching weather data: {str(e)}"
        
        # Use smart fallback
        return await smart_weather_fallback(
            location=location,
            tool_name="Comprehensive Weather",
            api_function=_get_comprehensive_api
        )
    
    @mcp.tool()
    async def get_weather_with_context(latitude: float, longitude: float, context: str = "") -> str:
        """Get weather information with specific context (travel, outdoor activity, etc.) and web fallback.
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            context: Context for weather request (e.g., "travel", "hiking", "outdoor event")
        """
        location = get_location_from_coords(latitude, longitude)
        
        async def _get_contextual_weather():
            try:
                # Get basic weather data
                points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
                points_data = await make_nws_request(points_url)
                
                if not points_data:
                    return "Unable to fetch weather data for contextual analysis."
                
                forecast_url = points_data["properties"]["forecast"]
                forecast_data = await make_nws_request(forecast_url)
                
                if not forecast_data:
                    return "Unable to fetch forecast for contextual analysis."
                
                periods = forecast_data["properties"]["periods"][:3]  # Next 3 periods
                
                # Create context-specific analysis
                context_analysis = []
                
                for period in periods:
                    temp = period.get("temperature", 0)
                    conditions = period.get("shortForecast", "").lower()
                    wind = period.get("windSpeed", "")
                    
                    period_info = f"""
{period['name']}:
🌡️ {temp}°{period['temperatureUnit']} | 💨 {wind}
☁️ {period['shortForecast']}
"""
                    
                    # Add context-specific advice
                    if context.lower() in ["travel", "driving"]:
                        if "rain" in conditions or "storm" in conditions:
                            period_info += "🚗 Driving: Use caution, wet roads expected\n"
                        elif "snow" in conditions or "ice" in conditions:
                            period_info += "🚗 Driving: HAZARDOUS - Winter conditions\n"
                        else:
                            period_info += "🚗 Driving: Good conditions expected\n"
                    
                    elif context.lower() in ["hiking", "outdoor", "camping"]:
                        if temp < 40:
                            period_info += "🥾 Outdoor: Dress warmly, layer clothing\n"
                        elif temp > 85:
                            period_info += "🥾 Outdoor: Stay hydrated, sun protection\n"
                        
                        if "rain" in conditions:
                            period_info += "🥾 Outdoor: Bring rain gear\n"
                        elif "clear" in conditions or "sunny" in conditions:
                            period_info += "🥾 Outdoor: Excellent conditions\n"
                    
                    elif context.lower() in ["event", "wedding", "party"]:
                        if "rain" in conditions:
                            period_info += "🎉 Event: Consider indoor backup plans\n"
                        elif temp < 50:
                            period_info += "🎉 Event: Provide heating/warm areas\n"
                        elif temp > 80:
                            period_info += "🎉 Event: Provide shade/cooling areas\n"
                        else:
                            period_info += "🎉 Event: Great weather for outdoor events\n"
                    
                    context_analysis.append(period_info)
                
                result = f"🎯 Weather Analysis for {context or 'General'} Context:\n"
                result += "\n---\n".join(context_analysis)
                
                return result
                
            except Exception as e:
                return f"Error in contextual weather analysis: {str(e)}"
        
        return await smart_weather_fallback(
            location=location,
            tool_name=f"Contextual Weather ({context})",
            api_function=_get_contextual_weather
        )
    
    @mcp.tool()
    async def get_weather_summary(location_name: str) -> str:
        """Get a weather summary for a named location with web fallback.
        
        Args:
            location_name: Name of city, state, or location (e.g., "San Francisco, CA")
        """
        async def _get_summary_api():
            # This is a simplified implementation
            # In a real scenario, you'd geocode the location first
            return f"""
Weather Summary for {location_name}:

⚠️ Note: This tool requires coordinates for full NWS API access.
Please use get_forecast or get_comprehensive_weather with latitude/longitude for detailed information.

Alternative: Check https://weather.gov/ and search for "{location_name}"
"""
        
        return await smart_weather_fallback(
            location=location_name,
            tool_name="Weather Summary",
            api_function=_get_summary_api
        )
    
    @mcp.tool()
    async def check_weather_service_status() -> str:
        """Check the status of weather services and suggest alternatives if needed."""
        
        async def _check_service_status():
            try:
                # Try a simple API call to check NWS service
                test_url = f"{NWS_API_BASE}/alerts/active?status=actual&limit=1"
                result = await make_nws_request(test_url)
                
                if result:
                    return """
✅ Weather Services Status:
• National Weather Service API: ONLINE
• All weather tools should function normally
• Real-time data available

🔧 Service Details:
• API Base: https://api.weather.gov
• Status: Operational
• Last Check: Just now
"""
                else:
                    return """
⚠️ Weather Services Status:
• National Weather Service API: OFFLINE or SLOW
• Web fallback mode will be used
• Alternative sources recommended

🌐 Alternative Sources:
• Weather.gov: https://weather.gov/
• Weather.com: https://weather.com/
• NOAA Weather Radio
• Local weather apps
"""
            except Exception as e:
                return f"""
❌ Weather Services Status:
• National Weather Service API: ERROR
• Error: {str(e)}
• Web fallback mode active

🆘 Recommended Actions:
• Check internet connection
• Try alternative weather sources
• Use local weather apps
• Monitor service status at weather.gov
"""
        
        return await _check_service_status()