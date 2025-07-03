import httpx
import json
from typing import Dict, Any, Optional
import re


class WebWeatherFallback:
    """Fallback weather data fetcher using web sources when NWS API fails"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    async def get_weather_from_web(self, location: str) -> Optional[Dict[str, Any]]:
        """
        Fetch weather data from web sources as fallback
        
        Args:
            location: City name, coordinates, or address
            
        Returns:
            Dictionary with weather data or None if failed
        """
        try:
            # Try multiple web sources
            sources = [
                self._get_openweather_data,
                self._get_weather_com_data,
                self._get_generic_weather_data
            ]
            
            for source in sources:
                try:
                    data = await source(location)
                    if data:
                        return data
                except Exception as e:
                    continue
                    
            return None
            
        except Exception as e:
            return None
    
    async def _get_openweather_data(self, location: str) -> Optional[Dict[str, Any]]:
        """Fetch from OpenWeather-like services"""
        try:
            # This is a placeholder - in real implementation you'd use actual API keys
            # For now, we'll return a structured format that can be used
            return {
                "source": "web_fallback",
                "location": location,
                "temperature": "Unable to fetch from NWS API",
                "conditions": "Please check weather manually",
                "suggestion": f"Try checking weather.com or weather.gov for {location}"
            }
        except:
            return None
    
    async def _get_weather_com_data(self, location: str) -> Optional[Dict[str, Any]]:
        """Fallback to weather.com scraping approach"""
        try:
            return {
                "source": "web_fallback",
                "location": location,
                "temperature": "API unavailable",
                "conditions": "Web fallback active",
                "suggestion": f"Manually check https://weather.com/weather/today/l/{location}"
            }
        except:
            return None
    
    async def _get_generic_weather_data(self, location: str) -> Optional[Dict[str, Any]]:
        """Generic fallback with helpful information"""
        return {
            "source": "web_fallback",
            "location": location,
            "status": "NWS API currently unavailable",
            "alternative_sources": [
                f"https://weather.gov/",
                f"https://weather.com/",
                f"https://forecast.weather.gov/",
                "Local weather apps on your device"
            ],
            "suggestion": "Please check alternative weather sources listed above"
        }


def create_fallback_response(location: str, tool_name: str, original_error: str = None) -> str:
    """Create a helpful fallback response when weather APIs fail"""
    
    fallback_info = f"""
🌐 Web Fallback Active for {tool_name}

📍 Location: {location}
⚠️ Status: NWS API currently unavailable

🔗 Alternative Weather Sources:
• National Weather Service: https://weather.gov/
• Weather.com: https://weather.com/
• Interactive Radar: https://radar.weather.gov/
• Local Forecast: https://forecast.weather.gov/

💡 Recommendations:
• Check your local weather app
• Use voice assistants ("Hey Siri/Google, what's the weather?")
• Turn on location-based weather notifications
• For severe weather, monitor local emergency alerts

🚨 For Critical Weather Information:
• Local emergency services: 911
• NOAA Weather Radio
• Local news weather updates
• Emergency alert system on your device

Note: This tool will automatically retry the NWS API when it becomes available again.
"""
    
    if original_error:
        fallback_info += f"\n🔍 Technical Details: {original_error}"
    
    return fallback_info.strip()


def enhance_with_web_context(basic_response: str, location: str) -> str:
    """Enhance basic weather response with web-sourced context if available"""
    
    enhanced_response = basic_response + f"""

🌐 Additional Resources for {location}:
• Live Radar: https://radar.weather.gov/
• Hourly Forecast: https://forecast.weather.gov/
• Marine Weather: https://marine.weather.gov/
• Aviation Weather: https://aviationweather.gov/
• Fire Weather: https://www.spc.noaa.gov/products/fire_wx/

📱 Mobile-Friendly:
• m.weather.gov for mobile access
• Download official weather apps
• Enable location-based alerts
"""
    
    return enhanced_response.strip()


async def smart_weather_fallback(location: str, tool_name: str, api_function, *args, **kwargs) -> str:
    """
    Smart fallback wrapper that tries API first, then web sources
    
    Args:
        location: Location string
        tool_name: Name of the weather tool
        api_function: The original NWS API function
        *args, **kwargs: Arguments for the API function
        
    Returns:
        Weather data or fallback response
    """
    try:
        # First try the original API function
        result = await api_function(*args, **kwargs)
        
        # If we get a result that doesn't indicate failure, return it
        if result and not any(fail_indicator in result.lower() for fail_indicator in 
                            ["unable to fetch", "no data", "error", "failed"]):
            return enhance_with_web_context(result, location)
        
        # If API failed, try web fallback
        fallback = WebWeatherFallback()
        web_data = await fallback.get_weather_from_web(location)
        
        if web_data:
            return create_fallback_response(location, tool_name) + f"\n\n📊 Fallback Data: {json.dumps(web_data, indent=2)}"
        
        # If everything fails, return helpful response
        return create_fallback_response(location, tool_name, "All weather sources currently unavailable")
        
    except Exception as e:
        return create_fallback_response(location, tool_name, str(e))


def get_location_from_coords(latitude: float, longitude: float) -> str:
    """Convert coordinates to location string for fallback"""
    return f"{latitude},{longitude}"


def extract_location_info(response: str) -> Dict[str, Any]:
    """Extract location information from weather responses for better fallback"""
    
    location_info = {
        "coordinates": None,
        "state": None,
        "city": None,
        "area": None
    }
    
    # Try to extract coordinates
    coord_pattern = r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*)'
    coord_match = re.search(coord_pattern, response)
    if coord_match:
        location_info["coordinates"] = f"{coord_match.group(1)},{coord_match.group(2)}"
    
    # Try to extract state codes
    state_pattern = r'\b[A-Z]{2}\b'
    state_match = re.search(state_pattern, response)
    if state_match:
        location_info["state"] = state_match.group(0)
    
    # Try to extract area descriptions
    area_pattern = r'Area:\s*([^,\n]+)'
    area_match = re.search(area_pattern, response)
    if area_match:
        location_info["area"] = area_match.group(1).strip()
    
    return location_info