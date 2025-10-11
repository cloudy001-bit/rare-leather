from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import resend
from catalog.models import Product
from django.db.models.functions import Random

# Initialize Resend
resend.api_key = settings.RESEND_API_KEY


def about_view(request):
    return render(request, "about.html")


def contact_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        subject = f"New Contact Message from {name}"

        # Render a proper HTML email template if you have one (optional)
        html_content = render_to_string("emails/contact_message.html", {
            "name": name,
            "email": email,
            "message": message,
        })
        text_content = strip_tags(html_content)

        try:
            # Send email via Resend
            resend.Emails.send({
                "from": "noreply@rareleather.com.ng",
                "to": "rareleatherteam@gmail.com",  # Send to your admin inbox
                "reply_to": [email],  # So you can reply directly to the sender
                "subject": subject,
                "html": html_content,
                "text": text_content,
            })

            messages.success(request, "Your message has been sent successfully!")
        except Exception as e:
            messages.error(request, f"There was an error sending your message: {e}")

        return redirect("contact")

    return render(request, "contact.html")


def home(request):
    # Get 4 random featured products
    featured_products = Product.objects.order_by(Random())[:4]

    context = {
        'featured_products': featured_products,
    }
    return render(request, "home.html", context)


def bad_request(request, exception):
    return render(request, "errors/400.html", status=400)


def permission_denied(request, exception):
    return render(request, "errors/403.html", status=403)


def page_not_found(request, exception):
    return render(request, "errors/404.html", status=404)


def server_error(request):
    return render(request, "errors/500.html", status=500)
