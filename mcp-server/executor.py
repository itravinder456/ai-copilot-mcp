from registry import TOOL_REGISTRY
from tools.jira_tool import create_jira_ticket
from tools.db_tool import query_db

TOOL_MAP = {"create_jira_ticket": create_jira_ticket, "query_db": query_db}


def execute_tool(tool_name, payload):
    try:
        tool_function = TOOL_MAP.get(tool_name)
        if not tool_function:
            print(f"Tool function for '{tool_name}' not implemented")
            return {
                "status": "error",
                "message": f"Tool function for '{tool_name}' not implemented",
            }

        # Validate payload against the tool's schema
        tool_schema = TOOL_REGISTRY[tool_name]["schema"]
        validated_payload = tool_schema(**payload)

        # Assuming payload is a dict of parameters for the tool
        result = tool_function(**validated_payload.dict())
        return {"status": "success", "result": result}
    except Exception as e:
        print(f"Error executing tool '{tool_name}': {str(e)}")
        return {"status": "error", "message": str(e)}
