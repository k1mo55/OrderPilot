from graph.nodes import SupportNodes
from langgraph.graph import START , END ,StateGraph
from graph.state import CancellationState


class CancellationGraph:
    def __init__(self, nodes: SupportNodes):
        self.nodes = nodes

    def build_graph(self):
        builder = StateGraph(CancellationState)
        
        #nodes
        builder.add_node("check_cancellation_eligibility" , self.nodes.check_cancellation_eligibility)
        builder.add_node("request_approval" , self.nodes.request_approval)
        builder.add_node("cancel_order" , self.nodes.cancel_order)
        
        
        #edges
        builder.add_edge(START,"check_cancellation_eligibility")
        builder.add_conditional_edges(
                "check_cancellation_eligibility" , 
                self._eligibility_router ,
                {
                    "request_approval":"request_approval",
                    "end": END
                }
            )
        
        builder.add_conditional_edges(
            "request_approval" , 
            self._approval_router,
            {
                "cancel_order":"cancel_order" , 
                "end":END
            }
        )
        builder.add_edge("cancel_order" , END)
        return builder.compile()
    
    
    
    
        
    def _eligibility_router(self, state: CancellationState) -> str:
        eligibility = state["cancellation_eligibility"]

        if eligibility and eligibility.get("eligible") is True:
            return "request_approval"

        return "end"
    def _approval_router(self , state:CancellationState):
        if state["approval_decision"]:
            return "cancel_order"
        else:
            return "end"