from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from registry import get_ai_tools
from executor import execute_tool


app = FastAPI(
    name="AI Copilot MCP Server",
    description="A server for the AI Copilot MCP, providing endpoints for tool execution and management.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"status": "MCP Server running"}


# 🔍 Discover tools
@app.get("/tools")
def get_tools():
    return get_ai_tools()


# ⚡ Execute tool
@app.post("/execute/{tool_name}")
def run_tool(tool_name: str, payload: dict = Body(...)):
    print(f"Received request to execute tool '{tool_name}' with payload: {payload}")
    return execute_tool(tool_name, payload)


@app.exception_handler(Exception)
def global_exception_handler(request, exc):
    print(f"An error occurred: {str(exc)}")
    return {"status": "error", "message": str(exc)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
