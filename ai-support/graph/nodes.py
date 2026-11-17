from services.commerce_client import CommerceClient
from graph.state import SupportState
from openai import AsyncOpenAI
from schemas.intent import IntentClassification

class SupportNodes:
    def __init__(self , commerce_client : CommerceClient , llmClient : AsyncOpenAI  ):
        self.commerce_client = commerce_client
        self.llmClient = llmClient
        
        
    async def get_orders(self , state : SupportState):
        orders = await self.commerce_client.get_customer_orders(
            state['customer_id']
        )
        return {
            "orders":orders
        }
        
    async def check_cancellation_eligibility(self , state:SupportState) -> dict :
        order_id = state["order_id"]

        if order_id is None:
            raise ValueError("Order ID is required")

        check = await self.commerce_client.check_cancellation_eligibility(
            order_id
        )
        return{
            "cancellation_eligibility": check
        }

    async def request_approval(self , state:SupportState)-> dict:
        print("placeholderNode")
        return {}
        
    
    async def classify_intent(self , state:SupportState):
        response = await self.llmClient.responses.parse(
            model="gpt-4o-mini" ,
            instructions="you are a classifier that chooses one of these according to the user question[GET_ORDERS, CANCEL_ORDER, UNKNOWN]",
            input= state["user_message"] , 
            text_format= IntentClassification
        )
        result = response.output_parsed
        print("inside the llm class" ,result)
        if result is None:
            raise ValueError("Failed to classify user Intent")
        return {
            "intent": result.intent, 
            "order_id":result.order_id
        }