from registry import TOOL_REGISTRY, get_ai_tools


def test_get_ai_tools_returns_openai_function_schema_for_every_registered_tool():
    tools = get_ai_tools()

    assert len(tools) == len(TOOL_REGISTRY)

    names = {tool["function"]["name"] for tool in tools}
    assert names == set(TOOL_REGISTRY)

    for tool in tools:
        assert tool["type"] == "function"
        parameters = tool["function"]["parameters"]
        assert parameters["type"] == "object"
        assert "properties" in parameters


def test_db_query_tool_requires_query_field():
    tools = {tool["function"]["name"]: tool["function"] for tool in get_ai_tools()}

    db_query = tools["db_query"]
    assert "query" in db_query["parameters"]["properties"]
    assert "query" in db_query["parameters"]["required"]
