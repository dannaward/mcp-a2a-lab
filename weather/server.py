from mcp.server.fastmcp import FastMCP
from tools import register_weather_tools, register_forecast_tools

# Initialize FastMCP server
mcp = FastMCP("weather")

# Register tools
register_weather_tools(mcp)
register_forecast_tools(mcp)