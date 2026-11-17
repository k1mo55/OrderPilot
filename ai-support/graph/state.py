from typing import TypedDict


class SupportState( TypedDict ):
    customer_id : int 
    user_message : str
    orders : list[dict]
    intent: str | None
    order_id : int | None
    cancellation_eligibility: dict | None
        