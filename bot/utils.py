from __future__ import annotations
from dataclasses import dataclass
from typing import List

@dataclass
class CartItem:
    product_id: str
    title: str
    qty: int
    price_rub: float

def calc_total(items: List[CartItem]) -> float:
    return sum(i.qty * i.price_rub for i in items)

def human_rub(amount: float) -> str:
    return f"{amount:,.0f} ₽".replace(",", " ")
