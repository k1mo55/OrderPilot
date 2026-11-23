import asyncio
import os
import httpx

from dotenv import load_dotenv
from openai import AsyncOpenAI

from services.commerce_client import CommerceClient
from graph.nodes import SupportNodes
from graph.cancellation_workflow import CancellationGraph

load_dotenv()


async def main():
    async with httpx.AsyncClient() as client, AsyncOpenAI() as llm_client:
        commerce_client = CommerceClient(os.environ["BASE_URL"], client)
        nodes = SupportNodes(commerce_client, llm_client)

        graph = CancellationGraph(nodes).build_graph()

        initial_state = {
            "customer_id": 1,
            "intent": "CANCEL_ORDER",
            "order_id": 102,
            "cancellation_eligibility": None,
            "approval_decision": None,
            "cancellation_result": None
        }

        result = await graph.ainvoke(initial_state)
        print(result)


if __name__ == "__main__":
    asyncio.run(main())