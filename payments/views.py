import uuid
import requests
import logging
import resend
from django.conf import settings
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from orders.models import Order
from .models import Payment

logger = logging.getLogger(__name__)

# Initialize Resend client
resend.api_key = settings.RESEND_API_KEY


@login_required
def initialize_payment(request, order_id):
    """Start or restart a Paystack transaction for an order."""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.payment_status == 'paid':
        messages.info(request, "This order has already been paid for.")
        return redirect('orders:order_confirmation', order_id=order.id)

    # Generate unique reference
    reference = f"ORD-{order.id}-{uuid.uuid4().hex[:8]}"
    order.reference = reference
    order.save(update_fields=["reference"])

    # Create or update payment record
    Payment.objects.update_or_create(
        order=order,
        defaults={
            "user": request.user,
            "amount": order.total_price,
            "reference": reference,
            "verified": False,
        },
    )

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "email": order.email,
        "amount": int(order.total_price * 100),
        "reference": reference,
        "callback_url": request.build_absolute_uri("/payments/verify/"),
    }

    try:
        response = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers, timeout=10)
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
def verify_payment(request):
    """Verify Paystack transaction and send notifications via Resend."""
    reference = request.GET.get('reference') or request.GET.get('trxref')

    if not reference:
        messages.error(request, "Invalid payment reference.")
        return redirect('orders:order_list')

    order = get_object_or_404(Order, reference=reference, user=request.user)
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}

    try:
        response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers, timeout=10)
        res_data = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Paystack verification failed: {e}")
        messages.error(request, "Network error verifying payment.")
        return redirect('orders:order_confirmation', order_id=order.id)

    payment = Payment.objects.filter(reference=reference).first()

    # ✅ Successful Payment
    if res_data.get("status") and res_data["data"]["status"] == "success":
        order.payment_status = "paid"
        order.status = "processing"
        order.save(update_fields=["payment_status", "status"])

        if payment:
            payment.verified = True
            payment.save(update_fields=["verified"])

        # === 📧 CUSTOMER RECEIPT (Resend) ===
        try:
            subject = f"Payment Receipt — Order #{order.id}"
            html_content = render_to_string("emails/payment_receipt.html", {"order": order})
            text_content = strip_tags(html_content)

            resend.Emails.send({
                "from": "onboarding@resend.dev",
                "to": [order.email],
                "subject": subject,
                "html": html_content,
                "text": text_content
            })
        except Exception as e:
            logger.error(f"Error sending customer receipt via Resend: {e}")

        # === 📧 ADMIN ALERT (Resend) ===
        try:
            admin_subject = f"🟢 New Paid Order — #{order.id}"
            admin_context = {
                "order": order,
                "admin_url": request.build_absolute_uri(f"/admin/orders/order/{order.id}/"),
                "now": timezone.now(),
            }
            admin_html = render_to_string("emails/admin_new_order.html", admin_context)
            admin_text = strip_tags(admin_html)

            resend.Emails.send({
                "from": "onboarding@resend.dev",
                "to": [settings.ADMIN_EMAIL],
                "subject": admin_subject,
                "html": admin_html,
                "text": admin_text
            })
        except Exception as e:
            logger.error(f"Error sending admin notification via Resend: {e}")

        # === 💬 Telegram Alert (Optional) ===
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

    # ❌ Failed Payment
    order.payment_status = "failed"
    order.save(update_fields=["payment_status"])
    messages.warning(request, "Payment verification failed or was incomplete.")
    return redirect('orders:order_confirmation', order_id=order.id)
