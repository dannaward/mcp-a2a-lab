from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Import tools to register them
from tools import get_weather, get_forecast