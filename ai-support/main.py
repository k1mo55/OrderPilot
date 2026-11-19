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
from langgraph.types import Command
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
load_dotenv()

base_url = os.environ["BASE_URL"]
database_url = os.environ["DATABASE_URL"]
class ApprovalRequest(BaseModel):
    thread_id: str
    approved: bool

class ChatRequest(BaseModel):
    customer_id: int
    message: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with (httpx.AsyncClient() as client , AsyncOpenAI() as llm_client , 
                AsyncPostgresSaver.from_conn_string(database_url) as checkpointer
                ):
        await checkpointer.setup()
        
        commerce_client = CommerceClient(base_url, client)
        support_nodes = SupportNodes(commerce_client ,llm_client )
        support_graph = SupportGraph(support_nodes , checkpointer)
        
        app.state.graph = support_graph.build_graph()

        yield


app = FastAPI(lifespan=lifespan)


@app.post("/chat")
async def chat(data: ChatRequest, request: Request):
    initial_state = {
        "customer_id": data.customer_id,
        "user_message": data.message,
        "orders": [],
        "intent": None,
        "order_id": None,
        "cancellation_eligibility": None,
        "approval_decision": None,
        "cancellation_result": None,
    }
    config = {
    "configurable": {
        "thread_id": f"customer-{data.customer_id}"
    }
    }
    result = await request.app.state.graph.ainvoke(
        initial_state , 
        config = config
        )

    return result



@app.post("/approve")
async def approve(data: ApprovalRequest, request: Request):
    config = {
    "configurable": {
        "thread_id": f"customer-{data.thread_id}"
    }
    }
    result = await request.app.state.graph.ainvoke(
    Command(resume=data.approved),
    config=config
    )
    return result