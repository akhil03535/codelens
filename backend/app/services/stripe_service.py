"""
Stripe Payment Service
Handles all payment operations
"""

import logging
from typing import Optional, Dict, Any
import stripe
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service for Stripe payment operations"""

    # Subscription plans configuration
    PLANS = {
        "free": {
            "name": "Free",
            "price": 0,
            "currency": "inr",
            "features": {
                "max_repositories": 1,
                "max_chats_per_day": 20,
                "priority_processing": False,
            },
        },
        "pro": {
            "name": "Pro",
            "price": 999,  # ₹9.99/month in paise
            "currency": "inr",
            "stripe_price_id": settings.STRIPE_PRICE_ID_PRO,
            "features": {
                "max_repositories": 10,
                "max_chats_per_month": 500,
                "priority_processing": True,
            },
        },
    }

    @staticmethod
    def create_customer(email: str, name: Optional[str] = None, user_id: Optional[str] = None) -> str:
        """
        Create Stripe customer

        Args:
            email: Customer email
            name: Customer name
            user_id: Internal user ID for metadata

        Returns:
            Stripe customer ID
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name or email.split("@")[0],
                metadata={"user_id": user_id},
                description=f"CodeLens User: {email}",
            )
            logger.info(f"Created Stripe customer: {customer.id}")
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {str(e)}")
            raise

    @staticmethod
    def create_subscription(
        customer_id: str, plan: str = "pro", interval: str = "month"
    ) -> Dict[str, Any]:
        """
        Create subscription for customer

        Args:
            customer_id: Stripe customer ID
            plan: Plan name ('free', 'pro')
            interval: Billing interval ('month', 'year')

        Returns:
            Subscription data
        """
        try:
            if plan not in StripeService.PLANS:
                raise ValueError(f"Invalid plan: {plan}")

            plan_config = StripeService.PLANS[plan]

            if plan == "free":
                # Free plan doesn't require Stripe subscription
                return {
                    "id": f"free_{customer_id}",
                    "customer_id": customer_id,
                    "plan": plan,
                    "status": "active",
                    "price": 0,
                    "currency": "inr",
                }

            price_id = plan_config.get("stripe_price_id")
            if not price_id:
                raise ValueError(f"No Stripe price ID configured for plan: {plan}")

            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"],
            )

            logger.info(f"Created subscription: {subscription.id}")
            return {
                "id": subscription.id,
                "customer_id": subscription.customer,
                "plan": plan,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "price": plan_config["price"],
                "currency": plan_config["currency"],
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription: {str(e)}")
            raise

    @staticmethod
    def cancel_subscription(subscription_id: str, at_period_end: bool = True) -> Dict[str, Any]:
        """
        Cancel subscription

        Args:
            subscription_id: Stripe subscription ID
            at_period_end: Cancel at end of billing period if True

        Returns:
            Canceled subscription data
        """
        try:
            if subscription_id.startswith("free_"):
                return {"id": subscription_id, "status": "canceled"}

            subscription = stripe.Subscription.delete(
                subscription_id,
                invoke_at_period_end=at_period_end if not at_period_end else None,
            )
            logger.info(f"Canceled subscription: {subscription_id}")
            return {
                "id": subscription.id,
                "status": subscription.status,
                "canceled_at": subscription.canceled_at,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {str(e)}")
            raise

    @staticmethod
    def get_subscription(subscription_id: str) -> Dict[str, Any]:
        """
        Get subscription details

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Subscription data
        """
        try:
            if subscription_id.startswith("free_"):
                return {"id": subscription_id, "plan": "free", "status": "active"}

            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "customer_id": subscription.customer,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "canceled_at": subscription.canceled_at,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve subscription: {str(e)}")
            raise

    @staticmethod
    def create_payment_intent(
        customer_id: str, amount_cents: int, currency: str = "inr", metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create payment intent

        Args:
            customer_id: Stripe customer ID
            amount_cents: Amount in smallest currency unit
            currency: Currency code
            metadata: Additional metadata

        Returns:
            Payment intent data
        """
        try:
            intent = stripe.PaymentIntent.create(
                customer=customer_id,
                amount=amount_cents,
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True},
            )
            logger.info(f"Created payment intent: {intent.id}")
            return {
                "id": intent.id,
                "customer_id": intent.customer,
                "amount": intent.amount,
                "currency": intent.currency,
                "status": intent.status,
                "client_secret": intent.client_secret,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment intent: {str(e)}")
            raise

    @staticmethod
    def get_payment_intent(intent_id: str) -> Dict[str, Any]:
        """
        Get payment intent details

        Args:
            intent_id: Payment intent ID

        Returns:
            Payment intent data
        """
        try:
            intent = stripe.PaymentIntent.retrieve(intent_id)
            return {
                "id": intent.id,
                "amount": intent.amount,
                "currency": intent.currency,
                "status": intent.status,
                "customer_id": intent.customer,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve payment intent: {str(e)}")
            raise

    @staticmethod
    def list_invoices(customer_id: str, limit: int = 10) -> list:
        """
        List invoices for customer

        Args:
            customer_id: Stripe customer ID
            limit: Maximum number of invoices to return

        Returns:
            List of invoice data
        """
        try:
            invoices = stripe.Invoice.list(customer=customer_id, limit=limit)
            return [
                {
                    "id": invoice.id,
                    "number": invoice.number,
                    "date": invoice.created,
                    "amount": invoice.amount_paid,
                    "currency": invoice.currency,
                    "status": invoice.status,
                    "pdf_url": invoice.invoice_pdf,
                }
                for invoice in invoices.data
            ]
        except stripe.error.StripeError as e:
            logger.error(f"Failed to list invoices: {str(e)}")
            return []

    @staticmethod
    def get_webhook_event(payload: bytes, signature: str) -> Optional[Dict[str, Any]]:
        """
        Verify and get webhook event

        Args:
            payload: Request body
            signature: Stripe signature header

        Returns:
            Event data if valid, None otherwise
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError:
            logger.error("Invalid webhook payload")
            return None
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            return None


stripe_service = StripeService()
