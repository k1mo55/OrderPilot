"""Disposable in-memory commerce backend for local LangGraph experiments."""

import os
from copy import deepcopy
from enum import Enum
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict


load_dotenv(Path(__file__).resolve().parent.parent / ".env")


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


class CheckpointCleanupResponse(BaseModel):
    message: str
    checkpoints_deleted: int
    writes_deleted: int
    blobs_deleted: int


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
    {"id": 106, "customer_id": 1, "status": "PROCESSING", "total_amount": 34.75},
    {"id": 107, "customer_id": 1, "status": "DELIVERED", "total_amount": 89.99},
    {"id": 108, "customer_id": 1, "status": "CANCELLED", "total_amount": 15.50},
    {"id": 109, "customer_id": 2, "status": "PENDING", "total_amount": 63.20},
    {"id": 110, "customer_id": 2, "status": "SHIPPED", "total_amount": 145.00},
    {"id": 111, "customer_id": 2, "status": "CANCELLED", "total_amount": 27.80},
    {"id": 112, "customer_id": 3, "status": "PENDING", "total_amount": 52.45},
    {"id": 113, "customer_id": 3, "status": "PROCESSING", "total_amount": 99.95},
    {"id": 114, "customer_id": 3, "status": "SHIPPED", "total_amount": 175.30},
    {"id": 115, "customer_id": 3, "status": "DELIVERED", "total_amount": 240.00},
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


@app.delete("/admin/checkpoints", response_model=CheckpointCleanupResponse)
def delete_all_checkpoints() -> CheckpointCleanupResponse:
    """Delete saved LangGraph runs while preserving checkpoint schema metadata."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DATABASE_URL is not configured",
        )

    try:
        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM checkpoint_writes")
                writes_deleted = cursor.rowcount
                cursor.execute("DELETE FROM checkpoint_blobs")
                blobs_deleted = cursor.rowcount
                cursor.execute("DELETE FROM checkpoints")
                checkpoints_deleted = cursor.rowcount
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not clear the checkpoint database",
        ) from exc

    return CheckpointCleanupResponse(
        message="All LangGraph checkpoint data deleted",
        checkpoints_deleted=checkpoints_deleted,
        writes_deleted=writes_deleted,
        blobs_deleted=blobs_deleted,
    )
