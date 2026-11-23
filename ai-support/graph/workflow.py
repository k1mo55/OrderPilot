from graph.nodes import SupportNodes
from graph.state import SupportState , CancellationState
from langgraph.graph import START , END , StateGraph
from langgraph.types import Send
from graph.cancellation_workflow import CancellationGraph
class SupportGraph:
    def __init__(self , nodes :SupportNodes , checkPointer):
        self.nodes = nodes
        self.checkpointer = checkPointer
    def build_graph(self):
        builder = StateGraph( SupportState )
        self.cancellation_graph = CancellationGraph(self.nodes).build_graph()
        
        ## Nodes
        builder.add_node("classify_intent", self.nodes.classify_intent)
        builder.add_node("process_task", self.nodes.process_task)
        builder.add_node("aggregate_results", self.nodes.aggregate_results)
        builder.add_node("cancellation", self._process_cancellation)
        
        ## edges
        builder.add_edge(START , "classify_intent")
        builder.add_conditional_edges(
            "classify_intent" , 
            self._dispatch_tasks
        )
        builder.add_edge("process_task" , "aggregate_results")
        builder.add_edge("cancellation", "aggregate_results")
        builder.add_edge("aggregate_results" , END)
        checkPointer = self.checkpointer
        graph = builder.compile(checkpointer=checkPointer)
        return graph
    
        
    
    def _dispatch_tasks(self, state: SupportState) -> list[Send]:
        sends = []

        for task in state["tasks"]:
            if task["intent"] == "GET_ORDERS":
                sends.append(
                    Send(
                        "process_task",
                        {
                            "customer_id": state["customer_id"],
                            "intent": task["intent"],
                            "order_id": task["order_id"]
                        }
                    )
                )
            elif task["intent"] == "CHECK_CANCELLATION_ELIGIBILITY":
                sends.append(
                    Send(
                        "process_task",
                        {
                            "customer_id": state["customer_id"],
                            "intent": task["intent"],
                            "order_id": task["order_id"]
                        }
                    )
                )
            elif task["intent"] == "CANCEL_ORDER":
                sends.append(
                    Send(
                        "cancellation",
                        {
                            "customer_id": state["customer_id"],
                            "intent": task["intent"],
                            "order_id": task["order_id"],
                            "cancellation_eligibility": None,
                            "approval_decision": None,
                            "cancellation_result": None
                        }
                    )
                )
                        

        return sends

    
    async def _process_cancellation(self, state: CancellationState) -> dict:
        result = await self.cancellation_graph.ainvoke( state )
        return{
            "task_results":[
                {
                    "intent":"CANCEL_ORDER" , 
                    "order_id": state["order_id"],
                    "result":{
                            "approved": result["approval_decision"],
                            "cancellation_result": result["cancellation_result"]
                    }
                    
                }
            ]
        }