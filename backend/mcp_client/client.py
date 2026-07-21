import os

import httpx


class MCPClientError(Exception):
    """Base exception for MCPClient errors."""

    pass


class MCPClient:
    def __init__(self):
        self.base_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001")

    async def get_tools(self):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/tools")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise MCPClientError(f"Error fetching tools: {str(e)}")

    async def execute_tool(self, tool_name, payload):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/execute/{tool_name}", json=payload
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise MCPClientError(f"Error executing tool '{tool_name}': {str(e)}")
