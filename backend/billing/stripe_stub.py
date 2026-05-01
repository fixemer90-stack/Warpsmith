"""Stripe stub — заглушка для локальной разработки без Stripe SDK.

Когда Stripe подключен реально:
    1. pip install stripe
    2. Задать STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET в .env
    3. Раскомментировать реальные вызовы stripe
"""

import os
from dataclasses import dataclass
from typing import ClassVar, Optional


@dataclass
class StripeSession:
    id: str
    url: str
    mode: str = "subscription"


class StripeStub:
    """Заглушка Stripe — возвращает тестовые данные."""

    PRICE_IDS: ClassVar[dict] = {
        "premium_monthly": "price_premium_monthly_stub",
        "premium_yearly": "price_premium_yearly_stub",
    }

    @classmethod
    def create_checkout_session(
        cls,
        price_id: str,
        user_id: int,
        success_url: str,
        cancel_url: str,
    ) -> StripeSession:
        """Создать Checkout Session (заглушка)."""
        return StripeSession(
            id=f"cs_test_{user_id}",
            url=f"/subscribe/success?session_id=cs_test_{user_id}",
        )

    @classmethod
    def create_portal_session(cls, customer_id: str, return_url: str) -> str | None:
        """Создать Customer Portal (заглушка)."""
        return return_url + "?portal=test"
