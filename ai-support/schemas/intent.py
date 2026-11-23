from pydantic import BaseModel
from typing import Literal

class SupportTask(BaseModel):
    intent : Literal["GET_ORDERS", "CANCEL_ORDER", "UNKNOWN" , "CHECK_CANCELLATION_ELIGIBILITY"]
    order_id: int | None

class IntentClassification(BaseModel):
    tasks : list[SupportTask]
    
