"""Webhook routes: Stripe webhook handler + billing API."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

router = APIRouter(prefix="/api", tags=["billing"])


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Stripe Webhook: checkout.session.completed, customer.subscription.deleted.

    Production:
        1. Проверить подпись (stripe-signature header)
        2. Извлечь event type
        3. Обновить subscription_tier/subscription_id в БД
    """
    # TODO: stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    # payload = await request.body()
    return JSONResponse({"status": "ok", "mode": "stub"})


@router.post("/subscribe")
async def create_checkout():
    """Создать Stripe Checkout Session → редирект на страницу оплаты.

    TODO:
        - Извлечь user_id из JWT
        - Определить price_id по плану (premium_monthly / premium_yearly)
        - StripeStub.create_checkout_session(...)
        - Вернуть redirect URL
    """
    return RedirectResponse(url="/pricing", status_code=302)


@router.get("/subscribe/success")
async def checkout_success():
    """Callback после успешной оплаты."""
    return RedirectResponse(url="/team-builder?upgraded=1", status_code=302)


@router.get("/billing/portal")
async def billing_portal():
    """Stripe Customer Portal — управление подпиской."""
    # TODO: StripeStub.create_portal_session(customer_id, return_url="/account/billing")
    return RedirectResponse(url="/account/billing", status_code=302)
