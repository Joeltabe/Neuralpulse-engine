import os
import logging
import stripe
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_session_maker, User, TokenPackage, TokenTransaction, TransactionType
from api.auth import user_to_dict
from api.auth import get_current_user

def get_session():
    return get_session_maker()()

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

router = APIRouter(prefix="/billing", tags=["Billing"])

class PackagesResponse(BaseModel):
    success: bool
    packages: Optional[list] = None
    error: Optional[str] = None

class BalanceResponse(BaseModel):
    success: bool
    balance: Optional[int] = None
    user: Optional[dict] = None
    error: Optional[str] = None

class PurchaseRequest(BaseModel):
    package_id: int

class PurchaseResponse(BaseModel):
    success: bool
    checkout_url: Optional[str] = None
    transaction: Optional[dict] = None
    error: Optional[str] = None

class TransactionHistoryResponse(BaseModel):
    success: bool
    transactions: Optional[list] = None
    error: Optional[str] = None

class TokenUsageResponse(BaseModel):
    success: bool
    deduction: Optional[int] = None
    balance_after: Optional[int] = None
    error: Optional[str] = None

@router.get("/packages", response_model=PackagesResponse)
async def get_packages():
    async with get_session() as session:
        result = await session.execute(select(TokenPackage).order_by(TokenPackage.price_cents))
        packages = result.scalars().all()
        return PackagesResponse(
            success=True,
            packages=[{
                "id": p.id,
                "name": p.name,
                "tokens": p.tokens,
                "price_cents": p.price_cents,
                "price_display": p.price_display,
                "popular": p.popular,
                "description": p.description,
            } for p in packages]
        )

@router.get("/balance", response_model=BalanceResponse)
async def get_balance(user: User = Depends(get_current_user)):
    return BalanceResponse(success=True, balance=user.token_balance, user=user_to_dict(user))

@router.post("/purchase", response_model=PurchaseResponse)
async def purchase_package(request: PurchaseRequest, user: User = Depends(get_current_user)):
    async with get_session() as session:
        result = await session.execute(select(TokenPackage).where(TokenPackage.id == request.package_id))
        pkg = result.scalar_one_or_none()
        if not pkg:
            return PurchaseResponse(success=False, error="Package not found")

        if stripe.api_key:
            try:
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    line_items=[{
                        "price_data": {
                            "currency": "usd",
                            "product_data": {"name": f"{pkg.name} - {pkg.tokens} Tokens"},
                            "unit_amount": pkg.price_cents,
                        },
                        "quantity": 1,
                    }],
                    mode="payment",
                    success_url=os.getenv("FRONTEND_URL", "http://localhost:8000/app") + "/dashboard.html?payment=success",
                    cancel_url=os.getenv("FRONTEND_URL", "http://localhost:8000/app") + "/pricing.html?payment=cancelled",
                    metadata={
                        "user_id": str(user.id),
                        "package_id": str(pkg.id),
                        "tokens": str(pkg.tokens),
                    },
                )
                return PurchaseResponse(success=True, checkout_url=checkout_session.url)
            except Exception as e:
                logger.error(f"Stripe error: {e}")
                return PurchaseResponse(success=False, error="Payment processing error")

        result = await session.execute(select(User).where(User.id == user.id))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return PurchaseResponse(success=False, error="User not found")

        db_user.token_balance += pkg.tokens
        db_user.total_tokens_purchased += pkg.tokens
        tx = TokenTransaction(
            user_id=db_user.id,
            transaction_type=TransactionType.purchase.value,
            amount=pkg.tokens,
            balance_after=db_user.token_balance,
            description=f"Purchased {pkg.name} package ({pkg.tokens} tokens)",
        )
        session.add(tx)
        await session.commit()
        await session.refresh(db_user)
        return PurchaseResponse(
            success=True,
            transaction={
                "id": tx.id,
                "amount": tx.amount,
                "balance_after": tx.balance_after,
                "description": tx.description,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
            }
        )

@router.post("/deduct", response_model=TokenUsageResponse)
async def deduct_tokens(
    media_type: str,
    user: User = Depends(get_current_user),
):
    from api.database import get_token_cost
    cost = get_token_cost(media_type)

    if user.token_balance < cost:
        return TokenUsageResponse(
            success=False,
            error=f"Insufficient tokens. Need {cost}, have {user.token_balance}. Please purchase more tokens."
        )

    async with get_session() as session:
        result = await session.execute(select(User).where(User.id == user.id))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return TokenUsageResponse(success=False, error="User not found")

        db_user.token_balance -= cost
        db_user.total_tokens_used += cost
        tx = TokenTransaction(
            user_id=db_user.id,
            transaction_type=TransactionType.usage.value,
            amount=-cost,
            balance_after=db_user.token_balance,
            description=f"{media_type} analysis ({cost} tokens)",
        )
        session.add(tx)
        await session.commit()
        await session.refresh(db_user)

    return TokenUsageResponse(
        success=True,
        deduction=cost,
        balance_after=db_user.token_balance,
    )

@router.get("/history", response_model=TransactionHistoryResponse)
async def get_transaction_history(user: User = Depends(get_current_user)):
    async with get_session() as session:
        result = await session.execute(
            select(TokenTransaction)
            .where(TokenTransaction.user_id == user.id)
            .order_by(TokenTransaction.created_at.desc())
            .limit(100)
        )
        txs = result.scalars().all()
        return TransactionHistoryResponse(
            success=True,
            transactions=[{
                "id": tx.id,
                "type": tx.transaction_type,
                "amount": tx.amount,
                "balance_after": tx.balance_after,
                "description": tx.description,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
            } for tx in txs]
        )

@router.post("/stripe-webhook")
async def stripe_webhook(payload: dict):
    import json
    event = None
    try:
        event = stripe.Event.construct_from(payload, stripe.api_key)
    except ValueError:
        return {"error": "Invalid payload"}

    if event.type == "checkout.session.completed":
        session_obj = event.data.object
        metadata = session_obj.get("metadata", {})
        user_id = int(metadata.get("user_id", 0))
        package_id = int(metadata.get("package_id", 0))
        tokens = int(metadata.get("tokens", 0))
        payment_id = session_obj.get("payment_intent", "")

        async with get_session() as db_session:
            result = await db_session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.token_balance += tokens
                user.total_tokens_purchased += tokens
                tx = TokenTransaction(
                    user_id=user.id,
                    transaction_type=TransactionType.purchase.value,
                    amount=tokens,
                    balance_after=user.token_balance,
                    description=f"Stripe purchase: {tokens} tokens",
                    stripe_payment_id=payment_id,
                )
                db_session.add(tx)
                await db_session.commit()

    return {"received": True}
