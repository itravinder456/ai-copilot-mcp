import json

from mcp_client.client import MCPClient
from services.llm import invoke


class Agent:
    def __init__(self):
        self.mcp_client = MCPClient()

    async def handle_request(self, query: str):
        # Step 1: Fetch available tools from MCP server
        tools = await self.mcp_client.get_tools()
        print("Available tools from MCP:", tools)

        messages = [
            {
                "role": "system",
                "content": "You are an AI assistant that can use tools.",
            },
            {"role": "user", "content": query},
        ]

        # Step 2: Ask LLM (with tools)
        response = invoke(messages, tools=tools)
        message = response.choices[0].message
        print("LLM response:", message)

        # Step 3: If LLM decided to call a tool, execute it via MCP
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            print(f"LLM wants to call tool: {tool_name} with args: {tool_args}")

            tool_response = await self.mcp_client.execute_tool(tool_name, tool_args)
            print("Tool response from MCP:", tool_response)
            return tool_response

        # Step 4: No tool call — return plain LLM response
        return {"response": message.content}
