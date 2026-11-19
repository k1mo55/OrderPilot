import httpx

class CommerceClient :
    def __init__(self , BaseUrl :str , client : httpx.AsyncClient ):
        self.BaseUrl = BaseUrl
        self.client = client
        
    async def get_customer_orders(self, customer_id: int) -> list[dict]:
        try:
            response = await self.client.get(
            f"{self.BaseUrl}/customers/{customer_id}/orders"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            raise
            
    async def check_cancellation_eligibility(self , order_id : int) -> dict:
        try:
            response = await self.client.get(
                f"{self.BaseUrl}/orders/{order_id}/cancellation-eligibility"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            raise
    
    
    async def cancel_order(self , order_id : int ) -> dict :
        try:
            response = await self.client.post(
                f"{self.BaseUrl}/orders/{order_id}/cancel"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            raise
    