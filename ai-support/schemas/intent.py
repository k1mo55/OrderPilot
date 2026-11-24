from pydantic import BaseModel
from typing import Literal

class SupportTask(BaseModel):
    id: str
    intent : Literal["GET_ORDERS", "CANCEL_ORDER", "UNKNOWN" , "CHECK_CANCELLATION_ELIGIBILITY"]
    order_id: int | None
    order_selector: Literal["MOST_RECENT", "OLDEST"] | None
    depends_on:list[str]
class IntentClassification(BaseModel):
    tasks : list[SupportTask]
    
