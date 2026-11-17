import os
import httpx
from openai import AsyncOpenAI
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from pydantic import BaseModel
from dotenv import load_dotenv

from services.commerce_client import CommerceClient
from graph.nodes import SupportNodes
from graph.workflow import SupportGraph

load_dotenv()

base_url = os.environ["BASE_URL"]


class ChatRequest(BaseModel):
    customer_id: int
    message: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient() as client , AsyncOpenAI() as llm_client:
        commerce_client = CommerceClient(base_url, client)
        support_nodes = SupportNodes(commerce_client ,llm_client )
        support_graph = SupportGraph(support_nodes)

        app.state.graph = support_graph.build_graph()

        yield


app = FastAPI(lifespan=lifespan)


@app.post("/chat")
async def chat(data: ChatRequest, request: Request):
    initial_state = {
        "customer_id": data.customer_id,
        "user_message": data.message,
        "orders": []
    }
    
    result = await request.app.state.graph.ainvoke(initial_state)

    return result