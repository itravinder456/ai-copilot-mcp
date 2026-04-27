import os
import groq


def invoke(messages: list, tools: list = None):
    client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))
    kwargs = {
        "model": os.getenv("GROQ_MODEL"),
        "messages": messages,
    }
    if tools:
        kwargs["tools"] = tools

    return client.chat.completions.create(**kwargs)
