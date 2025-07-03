from constants import NWS_API_BASE
from utils import make_nws_request
import json


def register_weather_map_tools(mcp):
    @mcp.tool()
    async def get_radar_stations(latitude: float, longitude: float, radius_km: int = 50) -> str:
        """Get nearby radar stations for weather visualization.
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location  
            radius_km: Search radius in kilometers (default: 50)
        """
        # Convert km to miles for NWS API
        radius_miles = radius_km * 0.621371
        
        url = f"{NWS_API_BASE}/radar/stations?lat={latitude}&lon={longitude}&range={radius_miles}"
        data = await make_nws_request(url)
        
        if not data or "features" not in data:
            return "Unable to fetch radar station data."
            
        if not data["features"]:
            return "No radar stations found in the specified area."
            
        stations = []
        for feature in data["features"]:
            props = feature["properties"]
            station_info = f"""
Station: {props.get('stationIdentifier', 'Unknown')}
Name: {props.get('name', 'Unknown')}
Distance: {props.get('distance', 'Unknown')} km
Type: {props.get('type', 'Unknown')}
Radar URL: https://radar.weather.gov/ridge/standard/{props.get('stationIdentifier', '').lower()}_loop.gif
"""
            stations.append(station_info.strip())
            
        return "\n---\n".join(stations)

    @mcp.tool()  
    async def get_satellite_imagery(region: str = "us") -> str:
        """Get current satellite imagery URLs for weather visualization.
        
        Args:
            region: Region for satellite imagery (us, conus, alaska, hawaii, pr, guam)
        """
        # NWS satellite imagery endpoints
        satellite_urls = {
            "us": "https://cdn.star.nesdis.noaa.gov/GOES16/ABI/CONUS/GEOCOLOR/",
            "conus": "https://cdn.star.nesdis.noaa.gov/GOES16/ABI/CONUS/GEOCOLOR/",
            "alaska": "https://cdn.star.nesdis.noaa.gov/GOES17/ABI/ALASKA/GEOCOLOR/",
            "hawaii": "https://cdn.star.nesdis.noaa.gov/GOES17/ABI/HAWAII/GEOCOLOR/",
            "pr": "https://cdn.star.nesdis.noaa.gov/GOES16/ABI/MESO/GEOCOLOR/",
            "guam": "https://cdn.star.nesdis.noaa.gov/GOES17/ABI/GUAM/GEOCOLOR/"
        }
        
        if region not in satellite_urls:
            return f"Invalid region. Available regions: {', '.join(satellite_urls.keys())}"
            
        base_url = satellite_urls[region]
        
        # Generate common satellite imagery URLs
        imagery_info = f"""
Satellite Imagery for {region.upper()}:

Latest Color Image:
{base_url}latest.jpg

Latest Infrared:
{base_url.replace('GEOCOLOR', 'Band13')}/latest.jpg

Animation (Last 24 hours):
{base_url}20241203_loop.gif

Real-time Updates:
- Images update every 10-15 minutes
- Best viewed during daylight hours for visible imagery
- Infrared shows cloud temperatures (useful at night)

Usage: Copy URLs to view current satellite imagery in your browser
"""
        
        return imagery_info.strip()

    @mcp.tool()
    async def get_weather_map_layers(latitude: float, longitude: float) -> str:
        """Get available weather map layers and overlays for a location.
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
        """
        # First get the forecast office for this location
        points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
        points_data = await make_nws_request(points_url)
        
        if not points_data:
            return "Unable to fetch location data for weather maps."
            
        cwa = points_data["properties"]["cwa"]
        
        map_layers = f"""
Weather Map Layers for {latitude}, {longitude}:

Regional Forecast Office: {cwa}

Available Map Layers:
1. Doppler Radar: 
   - Base: https://radar.weather.gov/ridge/standard/{cwa.lower()}_loop.gif
   - Velocity: https://radar.weather.gov/ridge/standard/{cwa.lower()}_vel_loop.gif

2. Temperature Maps:
   - Current: https://graphical.weather.gov/images/conus/MaxT1_conus.png
   - Forecast: https://graphical.weather.gov/images/conus/MaxT3_conus.png

3. Precipitation Maps:
   - 24hr Forecast: https://graphical.weather.gov/images/conus/QtPf1_conus.png
   - 48hr Forecast: https://graphical.weather.gov/images/conus/QtPf2_conus.png

4. Wind Maps:
   - Surface Winds: https://graphical.weather.gov/images/conus/WxSfc_conus.png
   - Wind Speed: https://graphical.weather.gov/images/conus/WindSpd_conus.png

5. Pressure Maps:
   - Sea Level Pressure: https://graphical.weather.gov/images/conus/mslp_conus.png

Interactive Maps:
- NWS Interactive: https://forecast.weather.gov/
- Radar Interactive: https://radar.weather.gov/
"""
        
        return map_layers.strip()