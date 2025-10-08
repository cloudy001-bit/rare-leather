from django.shortcuts import render
from django.db.models.functions import Random
from catalog.models import Product  # Adjust import based on your app name


from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings



def about_view(request):
    return render(request, "about.html")

def contact_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        # Send email to site admin
        try:
            send_mail(
                f"New Contact Message from {name}",
                f"Email: {email}\n\nMessage:\n{message}",
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
            messages.success(request, "Your message has been sent successfully!")
        except Exception:
            messages.error(request, "There was an error sending your message. Please try again later.")

        return redirect("contact")

    return render(request, "contact.html")


def home(request):
    # Get 4 latest products for featured section
    featured_products = Product.objects.order_by(Random())[:4]

    # Alternatively, if you have a 'featured' boolean field:
    # featured_products = Product.objects.filter(featured=True, is_active=True)[:4]

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

