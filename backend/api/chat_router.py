from fastapi.routing import APIRouter
from pydantic import BaseModel
from services.agent import Agent


class ChatRequest(BaseModel):
    prompt: str


chat_router = APIRouter()
agent = Agent()


@chat_router.post("/")
async def user_prompt(request: ChatRequest):
    response = await agent.handle_request(request.prompt)
    return {"response": response}
