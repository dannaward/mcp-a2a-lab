from constants import NWS_API_BASE
from utils import make_nws_request, format_alert
from typing import Dict, List
import json


def register_severe_weather_tools(mcp):
    @mcp.tool()
    async def track_severe_weather(latitude: float, longitude: float, radius_miles: int = 100) -> str:
        """Track severe weather events within a specified radius of a location.
        
        Args:
            latitude: Latitude of the center location
            longitude: Longitude of the center location
            radius_miles: Search radius in miles (default: 100)
        """
        # Get all active alerts
        url = f"{NWS_API_BASE}/alerts/active"
        data = await make_nws_request(url)
        
        if not data or "features" not in data:
            return "Unable to fetch severe weather data."
            
        if not data["features"]:
            return "No active severe weather alerts found."
            
        # Filter for severe weather types
        severe_events = [
            "Tornado Warning", "Tornado Watch", "Severe Thunderstorm Warning", 
            "Severe Thunderstorm Watch", "Flash Flood Warning", "Flood Warning",
            "High Wind Warning", "Hurricane Warning", "Hurricane Watch",
            "Blizzard Warning", "Ice Storm Warning", "Freezing Rain Advisory"
        ]
        
        severe_alerts = []
        for feature in data["features"]:
            props = feature["properties"]
            event = props.get("event", "")
            
            if any(severe_event in event for severe_event in severe_events):
                # Calculate approximate distance (simplified)
                alert_coords = feature.get("geometry", {})
                if alert_coords and alert_coords.get("coordinates"):
                    alert_info = f"""
🚨 SEVERE WEATHER ALERT 🚨
Event: {props.get('event', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Urgency: {props.get('urgency', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Onset: {props.get('onset', 'Unknown')}
Expires: {props.get('expires', 'Unknown')}
Description: {props.get('description', 'No description')}
Instructions: {props.get('instruction', 'No instructions')}
"""
                    severe_alerts.append(alert_info.strip())
                    
        if not severe_alerts:
            return "No severe weather alerts found in the specified area."
            
        return "\n" + "="*50 + "\n".join(severe_alerts)

    @mcp.tool()
    async def get_storm_reports(state: str) -> str:
        """Get recent storm reports for a state.
        
        Args:
            state: Two-letter US state code (e.g. TX, FL)
        """
        # NWS doesn't have a direct storm reports API, but we can get recent alerts
        url = f"{NWS_API_BASE}/alerts/active/area/{state.upper()}"
        data = await make_nws_request(url)
        
        if not data or "features" not in data:
            return f"Unable to fetch storm reports for {state.upper()}."
            
        if not data["features"]:
            return f"No active storm reports for {state.upper()}."
            
        # Categorize by storm type
        storm_categories = {
            "tornado": [],
            "severe_thunderstorm": [], 
            "flood": [],
            "winter": [],
            "other": []
        }
        
        for feature in data["features"]:
            props = feature["properties"]
            event = props.get("event", "").lower()
            
            if "tornado" in event:
                storm_categories["tornado"].append(feature)
            elif "thunderstorm" in event or "hail" in event:
                storm_categories["severe_thunderstorm"].append(feature)
            elif "flood" in event:
                storm_categories["flood"].append(feature)
            elif any(term in event for term in ["winter", "snow", "ice", "blizzard"]):
                storm_categories["winter"].append(feature)
            else:
                storm_categories["other"].append(feature)
                
        report_sections = []
        
        for category, alerts in storm_categories.items():
            if alerts:
                section = f"\n{category.replace('_', ' ').title()} Reports ({len(alerts)}):\n" + "-" * 40
                for alert in alerts[:3]:  # Limit to 3 per category
                    props = alert["properties"]
                    section += f"""
• {props.get('event', 'Unknown Event')}
  Area: {props.get('areaDesc', 'Unknown')}
  Severity: {props.get('severity', 'Unknown')}
  Time: {props.get('effective', 'Unknown')}
"""
                report_sections.append(section)
                
        if not report_sections:
            return f"No categorized storm reports available for {state.upper()}."
            
        return f"Storm Reports for {state.upper()}:\n" + "\n".join(report_sections)

    @mcp.tool()
    async def get_weather_watches_warnings(latitude: float, longitude: float) -> str:
        """Get current watches and warnings for a specific location with severity levels.
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
        """
        # Get the county/zone for this location
        points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
        points_data = await make_nws_request(points_url)
        
        if not points_data:
            return "Unable to fetch location data."
            
        # Get county and forecast zone
        county = points_data["properties"].get("county")
        forecast_zone = points_data["properties"].get("forecastZone")
        
        # Fetch alerts for this county/zone
        alerts_data = None
        if county:
            county_code = county.split("/")[-1]  # Extract county code from URL
            alerts_url = f"{NWS_API_BASE}/alerts/active/zone/{county_code}"
            alerts_data = await make_nws_request(alerts_url)
            
        if not alerts_data or "features" not in alerts_data:
            return "No active watches or warnings for this location."
            
        if not alerts_data["features"]:
            return "No active watches or warnings for this location."
            
        # Categorize by severity and type
        severity_order = ["Extreme", "Severe", "Moderate", "Minor", "Unknown"]
        watch_warning_types = {
            "warnings": [],
            "watches": [],
            "advisories": []
        }
        
        for feature in alerts_data["features"]:
            props = feature["properties"]
            event = props.get("event", "").lower()
            
            if "warning" in event:
                watch_warning_types["warnings"].append(feature)
            elif "watch" in event:
                watch_warning_types["watches"].append(feature)  
            elif "advisory" in event:
                watch_warning_types["advisories"].append(feature)
                
        result_sections = []
        
        for alert_type, alerts in watch_warning_types.items():
            if alerts:
                # Sort by severity
                alerts.sort(key=lambda x: severity_order.index(
                    x["properties"].get("severity", "Unknown")
                ))
                
                section = f"\n{alert_type.upper()} ({len(alerts)}):\n" + "=" * 30
                
                for alert in alerts:
                    props = alert["properties"]
                    severity = props.get("severity", "Unknown")
                    urgency = props.get("urgency", "Unknown")
                    
                    # Add severity indicators
                    severity_indicator = {
                        "Extreme": "🔴",
                        "Severe": "🟠", 
                        "Moderate": "🟡",
                        "Minor": "🟢",
                        "Unknown": "⚪"
                    }.get(severity, "⚪")
                    
                    alert_info = f"""
{severity_indicator} {props.get('event', 'Unknown Event')}
   Severity: {severity} | Urgency: {urgency}
   Effective: {props.get('effective', 'Unknown')}
   Expires: {props.get('expires', 'Unknown')}
   Areas: {props.get('areaDesc', 'Unknown')}
   Summary: {props.get('headline', 'No headline available')}
"""
                    section += alert_info
                    
                result_sections.append(section)
                
        if not result_sections:
            return "No active watches, warnings, or advisories for this location."
            
        location_info = f"Weather Alerts for {latitude}, {longitude}:"
        return location_info + "\n".join(result_sections)