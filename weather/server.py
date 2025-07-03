from mcp.server.fastmcp import FastMCP
from tools import (
    register_weather_tools, 
    register_forecast_tools,
    register_weather_map_tools,
    register_severe_weather_tools,
    register_weather_recommendation_tools
)

# Initialize FastMCP server
mcp = FastMCP("weather")

# Register all weather tools
register_weather_tools(mcp)
register_forecast_tools(mcp)
register_weather_map_tools(mcp)
register_severe_weather_tools(mcp)
register_weather_recommendation_tools(mcp)