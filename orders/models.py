from django.db import models
from django.conf import settings
from catalog.models import Product
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


import resend
from django.utils.html import strip_tags
from django.conf import settings

resend.api_key = settings.RESEND_API_KEY

class Order(models.Model):
    ORDER_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=100, blank=True, null=True, help_text="Paystack transaction reference")

    def __str__(self):
        return f"Order #{self.id} - {self.user.email} ({self.payment_status})"

    def get_total(self):
        return sum(item.get_subtotal() for item in self.items.all())

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.PositiveIntegerField(default=40)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.title} x {self.quantity}"

    def get_subtotal(self):
        return self.price * self.quantity


@receiver(post_save, sender=Order)
def send_order_completed_email(sender, instance, **kwargs):
    """
    Sends an email to the user when an order is marked as completed.
    """
    if instance.status == "completed":
        subject = f"Your Order #{instance.id} is Completed 🎉"
        
        # Prepare HTML and plain-text versions
        context = {"order": instance}
        html_content = render_to_string("emails/order_completed.html", context)
        text_content = strip_tags(html_content)

        try:
            resend.Emails.send({
                "from": "Rare Leather <noreply@rareleather.com.ng>",  # your verified sender domain in Resend
                "to": [instance.email],
                "subject": subject,
                "html": html_content,
                "text": text_content
            })
        except Exception as e:
            # Optional: log this error
            print(f"Error sending order completed email: {e}")
