from constants import NWS_API_BASE
from utils import make_nws_request
import json
from typing import Dict, List


def register_weather_recommendation_tools(mcp):
    @mcp.tool()
    async def get_clothing_recommendations(latitude: float, longitude: float) -> str:
        """Get clothing recommendations based on current and forecast weather conditions.
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
        """
        # Get current conditions and forecast
        points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
        points_data = await make_nws_request(points_url)
        
        if not points_data:
            return "Unable to fetch weather data for clothing recommendations."
            
        # Get forecast
        forecast_url = points_data["properties"]["forecast"]
        forecast_data = await make_nws_request(forecast_url)
        
        if not forecast_data:
            return "Unable to fetch forecast for clothing recommendations."
            
        current_period = forecast_data["properties"]["periods"][0]
        next_period = forecast_data["properties"]["periods"][1] if len(forecast_data["properties"]["periods"]) > 1 else current_period
        
        # Extract weather info
        temp = current_period.get("temperature", 70)
        temp_unit = current_period.get("temperatureUnit", "F")
        wind_speed = current_period.get("windSpeed", "")
        conditions = current_period.get("shortForecast", "").lower()
        
        # Convert to Celsius if needed for calculations
        temp_c = temp if temp_unit == "C" else (temp - 32) * 5/9
        
        # Extract wind speed number
        wind_mph = 0
        if wind_speed and "mph" in wind_speed:
            try:
                wind_mph = int(wind_speed.split()[0])
            except:
                wind_mph = 0
                
        # Calculate wind chill/heat index effects
        feels_like = temp
        if temp_c < 10 and wind_mph > 5:  # Wind chill
            feels_like = temp - (wind_mph * 0.7)
        elif temp_c > 27 and "humid" in conditions:  # Heat index approximation
            feels_like = temp + 5
            
        # Clothing recommendations based on temperature and conditions
        clothing_layers = []
        accessories = []
        footwear = []
        
        # Base layer recommendations
        if feels_like >= 80:
            clothing_layers.append("Light, breathable clothing (cotton/linen)")
            clothing_layers.append("Short sleeves or tank tops")
            footwear.append("Sandals or breathable sneakers")
        elif feels_like >= 65:
            clothing_layers.append("Light long sleeves or short sleeves")
            clothing_layers.append("Light pants or shorts")
            footwear.append("Comfortable sneakers")
        elif feels_like >= 50:
            clothing_layers.append("Long sleeves with light jacket/sweater")
            clothing_layers.append("Long pants")
            footwear.append("Closed-toe shoes")
        elif feels_like >= 35:
            clothing_layers.append("Warm sweater or fleece")
            clothing_layers.append("Warm jacket")
            clothing_layers.append("Warm pants")
            footwear.append("Insulated shoes or boots")
            accessories.append("Light gloves and hat")
        elif feels_like >= 20:
            clothing_layers.append("Thermal underwear")
            clothing_layers.append("Heavy sweater")
            clothing_layers.append("Winter coat")
            clothing_layers.append("Warm pants or thermals")
            footwear.append("Insulated winter boots")
            accessories.append("Warm gloves, hat, and scarf")
        else:
            clothing_layers.append("Multiple thermal layers")
            clothing_layers.append("Heavy winter coat")
            clothing_layers.append("Insulated pants")
            footwear.append("Heavy winter boots")
            accessories.append("Warm gloves, hat, scarf, and face protection")
            
        # Weather condition specific additions
        if any(keyword in conditions for keyword in ["rain", "shower", "drizzle"]):
            accessories.append("Umbrella or rain jacket")
            footwear.append("Waterproof shoes")
            
        if any(keyword in conditions for keyword in ["snow", "sleet", "ice"]):
            accessories.append("Waterproof gloves")
            footwear.append("Non-slip winter boots")
            
        if "sunny" in conditions and temp > 70:
            accessories.append("Sunglasses and sunscreen")
            accessories.append("Hat for sun protection")
            
        if wind_mph > 15:
            accessories.append("Windproof outer layer")
            
        recommendation = f"""
👕 Clothing Recommendations for {latitude}, {longitude}

Current Conditions:
• Temperature: {temp}°{temp_unit} (feels like {feels_like:.0f}°{temp_unit})
• Wind: {wind_speed}
• Conditions: {current_period.get('shortForecast', 'Unknown')}

Recommended Clothing:
{chr(10).join(f"• {item}" for item in clothing_layers)}

Footwear:
{chr(10).join(f"• {item}" for item in footwear)}

Accessories:
{chr(10).join(f"• {item}" for item in accessories)}

Next Period ({next_period.get('name', 'Later')}):
• Temperature: {next_period.get('temperature', 'Unknown')}°{temp_unit}
• Conditions: {next_period.get('shortForecast', 'Unknown')}
• Consider layering if temperature will change significantly
"""
        
        return recommendation.strip()

    @mcp.tool()
    async def get_activity_recommendations(latitude: float, longitude: float) -> str:
        """Get outdoor activity recommendations based on weather conditions.
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
        """
        # Get forecast data
        points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
        points_data = await make_nws_request(points_url)
        
        if not points_data:
            return "Unable to fetch weather data for activity recommendations."
            
        forecast_url = points_data["properties"]["forecast"]
        forecast_data = await make_nws_request(forecast_url)
        
        if not forecast_data:
            return "Unable to fetch forecast for activity recommendations."
            
        # Analyze next few periods
        periods = forecast_data["properties"]["periods"][:4]  # Next 2 days
        
        recommendations = []
        
        for i, period in enumerate(periods):
            period_name = period.get("name", f"Period {i+1}")
            temp = period.get("temperature", 70)
            temp_unit = period.get("temperatureUnit", "F")
            conditions = period.get("shortForecast", "").lower()
            wind_speed = period.get("windSpeed", "")
            
            # Extract wind speed
            wind_mph = 0
            if wind_speed and "mph" in wind_speed:
                try:
                    wind_mph = int(wind_speed.split()[0])
                except:
                    wind_mph = 0
                    
            # Activity recommendations based on conditions
            excellent_activities = []
            good_activities = []
            fair_activities = []
            avoid_activities = []
            
            # Temperature-based activities
            if temp >= 75:
                excellent_activities.extend(["Swimming", "Beach activities", "Water sports"])
                good_activities.extend(["Hiking", "Cycling", "Outdoor sports"])
                if temp > 85:
                    avoid_activities.extend(["Strenuous outdoor exercise during peak heat"])
            elif temp >= 60:
                excellent_activities.extend(["Hiking", "Cycling", "Running", "Outdoor sports"])
                good_activities.extend(["Walking", "Photography", "Gardening"])
            elif temp >= 45:
                good_activities.extend(["Hiking with layers", "Outdoor photography"])
                fair_activities.extend(["Walking", "Outdoor sports with warm gear"])
            elif temp >= 32:
                good_activities.extend(["Winter hiking", "Snow activities (if snowy)"])
                fair_activities.extend(["Brief outdoor walks"])
                avoid_activities.extend(["Extended outdoor activities without proper gear"])
            else:
                avoid_activities.extend(["Extended outdoor exposure"])
                fair_activities.extend(["Winter sports (properly equipped)"])
                
            # Weather condition adjustments
            if any(keyword in conditions for keyword in ["clear", "sunny", "fair"]):
                excellent_activities.extend(["Photography", "Sightseeing", "Picnics"])
                
            if any(keyword in conditions for keyword in ["partly cloudy", "mostly sunny"]):
                excellent_activities.extend(["Most outdoor activities"])
                
            if any(keyword in conditions for keyword in ["rain", "shower", "storm"]):
                avoid_activities.extend(["Most outdoor activities"])
                fair_activities.extend(["Indoor rock climbing", "Museum visits"])
                
            if any(keyword in conditions for keyword in ["snow", "blizzard"]):
                if temp > 25:
                    excellent_activities.extend(["Skiing", "Snowboarding", "Snow hiking"])
                else:
                    avoid_activities.extend(["Extended outdoor activities"])
                    
            if wind_mph > 20:
                avoid_activities.extend(["Cycling", "Small boat activities"])
                fair_activities.extend(["Sheltered hiking"])
            elif wind_mph > 10:
                fair_activities.extend(["Cycling (expect headwinds)"])
                
            # Remove duplicates and organize
            excellent_activities = list(set(excellent_activities))
            good_activities = list(set(good_activities))
            fair_activities = list(set(fair_activities))
            avoid_activities = list(set(avoid_activities))
            
            period_rec = f"""
{period_name} - {temp}°{temp_unit}, {period.get('shortForecast', 'Unknown')}
Wind: {wind_speed}

✅ Excellent: {', '.join(excellent_activities) if excellent_activities else 'None'}
👍 Good: {', '.join(good_activities) if good_activities else 'None'}  
⚠️  Fair: {', '.join(fair_activities) if fair_activities else 'None'}
❌ Avoid: {', '.join(avoid_activities) if avoid_activities else 'None'}
"""
            recommendations.append(period_rec.strip())
            
        return f"🏃 Activity Recommendations for {latitude}, {longitude}:\n\n" + "\n---\n".join(recommendations)

    @mcp.tool()
    async def get_travel_weather_advice(latitude: float, longitude: float) -> str:
        """Get travel-specific weather advice and preparations needed.
        
        Args:
            latitude: Latitude of the location  
            longitude: Longitude of the location
        """
        # Get extended forecast and alerts
        points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
        points_data = await make_nws_request(points_url)
        
        if not points_data:
            return "Unable to fetch weather data for travel advice."
            
        # Get forecast and alerts
        forecast_url = points_data["properties"]["forecast"]
        forecast_data = await make_nws_request(forecast_url)
        
        # Get alerts for the area
        county = points_data["properties"].get("county")
        alerts_data = None
        if county:
            county_code = county.split("/")[-1]
            alerts_url = f"{NWS_API_BASE}/alerts/active/zone/{county_code}"
            alerts_data = await make_nws_request(alerts_url)
            
        travel_advice = f"✈️ Travel Weather Advice for {latitude}, {longitude}:\n\n"
        
        # Check for travel-impacting alerts
        if alerts_data and alerts_data.get("features"):
            travel_alerts = []
            for feature in alerts_data["features"]:
                event = feature["properties"].get("event", "").lower()
                if any(keyword in event for keyword in ["warning", "watch", "advisory"]):
                    if any(travel_impact in event for travel_impact in 
                          ["winter", "snow", "ice", "flood", "wind", "fog", "storm"]):
                        travel_alerts.append(feature["properties"].get("event", "Unknown"))
                        
            if travel_alerts:
                travel_advice += "🚨 TRAVEL ALERTS:\n"
                for alert in travel_alerts:
                    travel_advice += f"• {alert}\n"
                travel_advice += "\n"
                
        if forecast_data:
            periods = forecast_data["properties"]["periods"][:6]  # Next 3 days
            
            travel_conditions = []
            packing_suggestions = []
            driving_conditions = []
            
            for period in periods:
                temp = period.get("temperature", 70)
                conditions = period.get("shortForecast", "").lower()
                wind_speed = period.get("windSpeed", "")
                
                # Analyze travel impact
                if any(keyword in conditions for keyword in ["rain", "shower", "storm"]):
                    driving_conditions.append(f"{period.get('name')}: Wet roads, reduced visibility")
                    packing_suggestions.append("Rain gear, umbrella")
                    
                if any(keyword in conditions for keyword in ["snow", "ice", "sleet"]):
                    driving_conditions.append(f"{period.get('name')}: HAZARDOUS - Snow/ice conditions")
                    packing_suggestions.append("Winter emergency kit, extra clothing")
                    travel_conditions.append(f"{period.get('name')}: Consider delaying travel")
                    
                if "fog" in conditions:
                    driving_conditions.append(f"{period.get('name')}: Dense fog, severely reduced visibility")
                    
                if wind_speed and "mph" in wind_speed:
                    try:
                        wind_mph = int(wind_speed.split()[0])
                        if wind_mph > 25:
                            driving_conditions.append(f"{period.get('name')}: High winds - difficult driving")
                            travel_conditions.append(f"{period.get('name')}: Avoid high-profile vehicles")
                    except:
                        pass
                        
                if temp < 32:
                    packing_suggestions.append("Heavy winter clothing, ice scraper")
                elif temp > 85:
                    packing_suggestions.append("Light clothing, extra water, sun protection")
                    
            # Compile advice sections
            if travel_conditions:
                travel_advice += "⚠️ TRAVEL CONDITIONS:\n"
                for condition in list(set(travel_conditions)):
                    travel_advice += f"• {condition}\n"
                travel_advice += "\n"
                
            if driving_conditions:
                travel_advice += "🚗 DRIVING CONDITIONS:\n"
                for condition in list(set(driving_conditions)):
                    travel_advice += f"• {condition}\n"
                travel_advice += "\n"
                
            if packing_suggestions:
                travel_advice += "🧳 PACKING SUGGESTIONS:\n"
                for suggestion in list(set(packing_suggestions)):
                    travel_advice += f"• {suggestion}\n"
                travel_advice += "\n"
                
            # General travel tips
            travel_advice += """📋 GENERAL TRAVEL TIPS:
• Check road conditions before departure
• Keep emergency supplies in vehicle
• Allow extra travel time in poor weather
• Consider travel insurance for severe weather delays
• Monitor weather updates during travel
• Have backup accommodation plans"""
            
        return travel_advice