from pydantic import BaseModel


class SQLQueryRequestSchema(BaseModel):
    query: str


class JiraTicketRequestSchema(BaseModel):
    title: str
    description: str


def convert_to_openai_schema(schema_model):
    schema = schema_model.model_json_schema()

    properties = schema.get("properties", {})
    required = schema.get("required", [])

    return {"type": "object", "properties": properties, "required": required}
