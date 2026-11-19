"""Disposable in-memory commerce backend for local LangGraph experiments."""

from copy import deepcopy
from enum import Enum

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class Customer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str


class Order(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    customer_id: int
    status: OrderStatus
    total_amount: float


class CancellationEligibility(BaseModel):
    order_id: int
    eligible: bool


class ResetResponse(BaseModel):
    message: str
    customers_restored: int
    orders_restored: int


ORIGINAL_CUSTOMERS = [
    {"id": 1, "name": "Alice Johnson"},
    {"id": 2, "name": "Bob Smith"},
    {"id": 3, "name": "Carol Williams"},
]

ORIGINAL_ORDERS = [
    {"id": 101, "customer_id": 1, "status": "PENDING", "total_amount": 49.99},
    {"id": 102, "customer_id": 1, "status": "SHIPPED", "total_amount": 120.00},
    {"id": 103, "customer_id": 2, "status": "PROCESSING", "total_amount": 75.50},
    {"id": 104, "customer_id": 2, "status": "DELIVERED", "total_amount": 210.25},
    {"id": 105, "customer_id": 3, "status": "CANCELLED", "total_amount": 18.00},
]

customers = deepcopy(ORIGINAL_CUSTOMERS)
orders = deepcopy(ORIGINAL_ORDERS)

app = FastAPI(
    title="Mock Commerce Backend",
    description="A disposable in-memory API for LangGraph learning projects.",
    version="1.0.0",
)


def find_order(order_id: int) -> dict:
    order = next((item for item in orders if item["id"] == order_id), None)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )
    return order


def can_cancel(order: dict) -> bool:
    return order["status"] in {
        OrderStatus.PENDING.value,
        OrderStatus.PROCESSING.value,
    }


@app.get("/customers/{customer_id}/orders", response_model=list[Order])
def get_customer_orders(customer_id: int) -> list[dict]:
    customer_exists = any(item["id"] == customer_id for item in customers)
    if not customer_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found",
        )
    return [order for order in orders if order["customer_id"] == customer_id]


@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int) -> dict:
    return find_order(order_id)


@app.get(
    "/orders/{order_id}/cancellation-eligibility",
    response_model=CancellationEligibility,
)
def get_cancellation_eligibility(order_id: int) -> CancellationEligibility:
    order = find_order(order_id)
    return CancellationEligibility(order_id=order_id, eligible=can_cancel(order))


@app.post("/orders/{order_id}/cancel", response_model=Order)
def cancel_order(order_id: int) -> dict:
    order = find_order(order_id)
    if not can_cancel(order):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Order {order_id} cannot be cancelled because it is {order['status']}",
        )
    print("we canceled")
    order["status"] = OrderStatus.CANCELLED.value
    return order


@app.post("/reset", response_model=ResetResponse)
def reset_data() -> ResetResponse:
    customers[:] = deepcopy(ORIGINAL_CUSTOMERS)
    orders[:] = deepcopy(ORIGINAL_ORDERS)
    return ResetResponse(
        message="Mock data restored",
        customers_restored=len(customers),
        orders_restored=len(orders),
    )
