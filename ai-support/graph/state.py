from typing import TypedDict , Annotated
import operator


class SupportState( TypedDict ):
    customer_id : int 
    user_message : str
    orders : list[dict]
    intent: str | None
    order_id : int | None
    cancellation_eligibility: dict | None
    approval_decision : bool   | None
    cancellation_result:dict | None
    
    
    tasks:list[dict]
    task_results: Annotated[ list[dict], operator.add]
    
    final_response: str | None
    
class TaskState(TypedDict):
    customer_id : int 
    intent: str
    order_id : int  | None
    
class CancellationState(TypedDict):
    customer_id : int 
    intent: str | None
    order_id : int
    cancellation_eligibility: dict | None
    approval_decision : bool   | None
    cancellation_result:dict | None
        