from pydantic import BaseModel
from typing import Literal


class IntentClassification(BaseModel):
    intent : Literal["GET_ORDERS", "CANCEL_ORDER", "UNKNOWN"]
    order_id: int | None
    
