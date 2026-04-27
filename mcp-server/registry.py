from schemas import (
    JiraTicketRequestSchema,
    SQLQueryRequestSchema,
    convert_to_openai_schema,
)

TOOL_REGISTRY = {
    "create_jira_ticket": {
        "name": "create_jira_ticket",
        "description": "Create a Jira ticket with the given title and description.",
        "parameters": {
            "title": "The title of the Jira ticket.",
            "description": "The description of the Jira ticket.",
        },
        "schema": JiraTicketRequestSchema,
    },
    "db_query": {
        "name": "db_query",
        "description": "Execute a SQL query against the database and return the results.",
        "parameters": {"query": "The SQL query to execute."},
        "schema": SQLQueryRequestSchema,
    },
}


def get_ai_tools():
    tools = []

    for name, meta in TOOL_REGISTRY.items():
        schema_model = meta["schema"]

        tool = {
            "type": "function",
            "function": {
                "name": name,
                "description": meta["description"],
                "parameters": convert_to_openai_schema(schema_model),
            },
        }

        tools.append(tool)

    return tools
