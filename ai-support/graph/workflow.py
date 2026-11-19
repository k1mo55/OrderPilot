from graph.nodes import SupportNodes
from graph.state import SupportState
from langgraph.graph import START , END , StateGraph
from langgraph.checkpoint.memory import MemorySaver

class SupportGraph:
    def __init__(self , nodes :SupportNodes ):
        self.nodes = nodes
    
    def build_graph(self):
        builder = StateGraph( SupportState )
        
        ## Nodes
        builder.add_node("classify_intent" , self.nodes.classify_intent)
        builder.add_node( "get_orders" , self.nodes.get_orders )            
        builder.add_node("check_cancellation_eligibility" , self.nodes.check_cancellation_eligibility)
        builder.add_node("request_approval" , self.nodes.request_approval)
        builder.add_node("cancel_order" , self.nodes.cancel_order)
        
        ## edges
        builder.add_edge(START , "classify_intent")
        builder.add_conditional_edges(
            "classify_intent" , 
            self._router,
            {
                "get_orders" : "get_orders" , 
                "check_cancellation_eligibility":"check_cancellation_eligibility" ,
                "end" : END
            }
        )
        builder.add_edge("get_orders" , END)
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
        
        checkPointer = MemorySaver()
        graph = builder.compile(checkpointer=checkPointer)
        return graph
    
    def _router(self , state :SupportState) :
        if state["intent"] == "GET_ORDERS":
            return "get_orders"
        elif state["intent"] == "CANCEL_ORDER":
            return "check_cancellation_eligibility"
        else:
            return "end"
    
    def _eligibility_router(self , state:SupportState):
        if state["cancellation_eligibility"].get("eligible"):
            return "request_approval"
        else:
            return "end"
    def _approval_router(self , state:SupportState):
        if state["approval_decision"]:
            return "cancel_order"
        else:
            return "end"