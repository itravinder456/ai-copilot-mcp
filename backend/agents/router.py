from services.llm import invoke


def determine_agent(state):
    query = state["query"]
    prompt = f"""
Classify the user query into one of these:
- greeting
- rag
- sql
- jira
- out_of_scope

Query: {query}

Return ONLY the label.
"""

    response_agent = invoke([{"role": "user", "content": prompt}])
    label = response_agent["choices"][0]["message"]["content"].strip()
    return {"route": label}
