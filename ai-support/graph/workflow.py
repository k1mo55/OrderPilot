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
        builder.add_node("schedule_tasks" , self.nodes.schedule_tasks)
        
        ## edges
        builder.add_edge(START , "classify_intent")
        builder.add_edge("classify_intent" , "schedule_tasks")
        builder.add_conditional_edges(
            "schedule_tasks", 
            self._dispatch_tasks,
            ["process_task", "cancellation", "aggregate_results"]
        )
        builder.add_edge("process_task" , "schedule_tasks")
        builder.add_edge("cancellation", "schedule_tasks")
        builder.add_edge("aggregate_results" , END)
        checkPointer = self.checkpointer
        graph = builder.compile(checkpointer=checkPointer)
        return graph
    
        
    
    def _dispatch_tasks(self, state: SupportState) -> list[Send] | str:
        ready_tasks = self._get_ready_tasks(state)
        sends = []
        for task in ready_tasks:
            if task["intent"] == "GET_ORDERS":
                sends.append(
                    Send(
                        "process_task",
                        {
                            "id":task["id"],
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
                            "id":task["id"],
                            "customer_id": state["customer_id"],
                            "intent": task["intent"],
                            "order_id": task["order_id"]
                        }
                    )
                )
            elif task["intent"] == "CANCEL_ORDER":
                order_id = self._resolve_order_id(state, task)
                valid = True
                if order_id is None:
                    continue

                for dep_id in task["depends_on"]:
                    dependency = next(
                        (t for t in state["tasks"] if t["id"] == dep_id),
                        None
                    )

                    if dependency and dependency["intent"] == "GET_ORDERS":
                        task_result = self._get_task_result(state, dep_id)

                        if task_result is None or not any(
                            order["id"] == order_id
                            for order in task_result["result"]
                        ):
                            valid = False
                            break

                if valid and order_id is not None:
                    sends.append(
                        Send(
                            "cancellation",
                            {
                                "id": task["id"],
                                "customer_id": state["customer_id"],
                                "intent": task["intent"],
                                "order_id": order_id,
                                "cancellation_eligibility": None,
                                "approval_decision": None,
                                "cancellation_result": None
                            }
                        )
                    )
                        

        if sends:
            return sends
        return "aggregate_results"

    
    async def _process_cancellation(self, state: CancellationState) -> dict:
        result = await self.cancellation_graph.ainvoke( state )
        return{
            "task_results":[
                {
                    "id":state['id'],
                    "intent":"CANCEL_ORDER" ,
                    "status": (
                                "COMPLETED"
                                if result["cancellation_result"] is not None
                                else "SKIPPED"
                            ),
                    "order_id": state["order_id"],
                    "result":{
                            "approved": result["approval_decision"],
                            "cancellation_result": result["cancellation_result"]
                    }
                    
                }
            ]
        }
        
        
    def _get_ready_tasks(self, state: SupportState) -> list[dict]:
        tasks = state["tasks"]
        results = state.get("task_results", [])

        completed_ids = {
            result["id"]
            for result in results
            if result["status"] == "COMPLETED"
        }

        executed_ids = {
            result["id"]
            for result in results
        }

        ready_tasks = []

        for task in tasks:
            if task["id"] in executed_ids:
                continue

            if all(dep in completed_ids for dep in task["depends_on"]):
                ready_tasks.append(task)

        return ready_tasks
    def _get_task_result( self, state: SupportState, task_id: str) -> dict | None:
        for task in state['task_results']:
            if task_id == task['id']:
                return task
        return None
    
    def _resolve_order_id( self,state: SupportState,task: dict) -> int | None:
        if task["order_id"] is not None:
            return task["order_id"]

        selector = task.get("order_selector")

        if selector is None:
            return None

        for dep_id in task["depends_on"]:
            dependency = next(
                (
                    t for t in state["tasks"]
                    if t["id"] == dep_id and t["intent"] == "GET_ORDERS"
                ),
                None
            )

            if dependency is None:
                continue

            task_result = self._get_task_result(state, dep_id)

            if task_result is None or task_result["status"] != "COMPLETED":
                continue

            orders = task_result["result"]

            if not orders:
                return None

            if selector == "MOST_RECENT":
                selected_order = max(
                    orders,
                    key=lambda order: order["created_at"]
                )

            elif selector == "OLDEST":
                selected_order = min(
                    orders,
                    key=lambda order: order["created_at"]
                )

            else:
                return None

            return selected_order["id"]

        return None