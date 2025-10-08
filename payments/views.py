import uuid
import requests
import logging
from django.conf import settings
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.utils import timezone
from django.template.loader import render_to_string

from orders.models import Order
from .models import Payment

logger = logging.getLogger(__name__)


@login_required
def initialize_payment(request, order_id):
    """Start or restart a Paystack transaction for an order."""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # 🔒 Prevent duplicate payments
    if order.payment_status == 'paid':
        messages.info(request, "This order has already been paid for.")
        return redirect('orders:order_confirmation', order_id=order.id)

    # ✅ Generate a unique reference
    reference = f"ORD-{order.id}-{uuid.uuid4().hex[:8]}"
    order.reference = reference
    order.save(update_fields=["reference"])

    # ✅ Create or update Payment
    payment, _ = Payment.objects.update_or_create(
        order=order,
        defaults={
            "user": request.user,
            "amount": order.total_price,
            "reference": reference,
            "verified": False,
        },
    )

    # ✅ Prepare Paystack initialization
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "email": order.email,
        "amount": int(order.total_price * 100),  # Paystack expects kobo
        "reference": reference,
        "callback_url": request.build_absolute_uri(f"/payments/verify/{reference}/"),
    }

    try:
        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            json=data,
            headers=headers,
            timeout=10,
        )
        res_data = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Paystack init failed: {e}")
        messages.error(request, "Network error connecting to Paystack.")
        return redirect('orders:order_confirmation', order_id=order.id)

    if res_data.get("status") and "authorization_url" in res_data["data"]:
        return redirect(res_data["data"]["authorization_url"])

    messages.error(request, "Payment initialization failed. Please try again.")
    return redirect('orders:order_confirmation', order_id=order.id)


@login_required
def verify_payment(request, reference):
    """Verify Paystack transaction and update order/payment status."""
    reference = reference or request.GET.get('trxref') or request.GET.get('reference')
    order = get_object_or_404(Order, reference=reference, user=request.user)
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}

    try:
        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers=headers,
            timeout=10,
        )
        res_data = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Paystack verification failed: {e}")
        messages.error(request, "Network error verifying payment.")
        return redirect('orders:order_confirmation', order_id=order.id)

    payment = Payment.objects.filter(reference=reference).first()

    if res_data.get("status") and res_data["data"]["status"] == "success":
        # ✅ Update order and payment
        order.payment_status = "paid"
        order.status = "processing"
        order.save(update_fields=["payment_status", "status"])

        if payment:
            payment.verified = True
            payment.save(update_fields=["verified"])

        # === 📧 SEND RECEIPT TO CUSTOMER ===
        try:
            subject = f"Payment Receipt — Order #{order.id}"
            context = {"order": order}
            message = render_to_string("emails/payment_receipt.html", context)
            email = EmailMessage(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [order.email],
            )
            email.content_subtype = "html"
            email.send(fail_silently=False)
        except Exception as e:
            logger.error(f"Error sending customer receipt: {e}")

        # === 📧 SEND EMAIL TO ADMIN ===
        try:
                admin_subject = f"🟢 New Paid Order — #{order.id}"
                admin_context = {
                    "order": order,
                    "admin_url": request.build_absolute_uri(f"/admin/orders/order/{order.id}/"),
                    "now": timezone.now(),
                }
                admin_message = render_to_string("emails/admin_new_order.html", admin_context)
                email = EmailMessage(
                    subject=admin_subject,
                    body=admin_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[settings.ADMIN_EMAIL],
                )
                email.content_subtype = "html"  # Important to render HTML
                email.send(fail_silently=True)
        except Exception as e:
            logger.error(f"Error sending admin notification: {e}")

        # === 💬 TELEGRAM NOTIFICATION ===
        if getattr(settings, "TELEGRAM_BOT_TOKEN", None) and getattr(settings, "TELEGRAM_CHAT_ID", None):
            telegram_message = (
                f"✅ *New Paid Order!*\n"
                f"📦 Order ID: {order.id}\n"
                f"👤 Customer: {order.full_name}\n"
                f"💰 Amount: ₦{order.total_price:,.2f}\n"
                f"📧 {order.email}\n"
                f"🔗 Ref: {order.reference}"
            )
            try:
                requests.post(
                    f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                    data={
                        "chat_id": settings.TELEGRAM_CHAT_ID,
                        "text": telegram_message,
                        "parse_mode": "Markdown",
                    },
                    timeout=5,
                )
            except Exception as e:
                logger.error(f"Telegram notification failed: {e}")

        messages.success(request, "Payment verified successfully! Your order is now processing.")
        return redirect('orders:order_confirmation', order_id=order.id)

    # ❌ Payment failed
    order.payment_status = "failed"
    order.save(update_fields=["payment_status"])
    messages.warning(request, "Payment verification failed or was incomplete.")
    return redirect('orders:order_confirmation', order_id=order.id)
