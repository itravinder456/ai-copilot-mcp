from executor import execute_tool


def test_execute_db_query_succeeds():
    result = execute_tool("db_query", {"query": "SELECT 1"})

    assert result["status"] == "success"
    assert result["result"] == {"status": "success", "results": []}


def test_execute_create_jira_ticket_succeeds():
    result = execute_tool(
        "create_jira_ticket", {"title": "Bug", "description": "Something broke"}
    )

    assert result["status"] == "success"
    assert result["result"]["ticket_id"] == "JIRA-1234"


def test_execute_unknown_tool_returns_error():
    result = execute_tool("not_a_real_tool", {})

    assert result["status"] == "error"
    assert "not implemented" in result["message"]


def test_execute_with_invalid_payload_returns_error():
    result = execute_tool("db_query", {})

    assert result["status"] == "error"
