from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives, BadHeaderError
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth import login, logout
from django.utils import timezone
from .models import User
from .utils import redirect_authenticated_user
from orders.models import Order
import uuid
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from settings.models import SiteSettings
import resend

# Initialize the Resend client
resend.api_key = settings.RESEND_API_KEY

def logout_view(request):
    logout(request)
    return redirect('catalog:product_list')


@redirect_authenticated_user
def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        # check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered.")
            return redirect('accounts:register')

        # create inactive user with token
        user = User.objects.create(
            email=email,
            is_active=False,
            signup_token=str(uuid.uuid4()),
            created_at=timezone.now()
        )

        # generate absolute verification link
        signup_link = request.build_absolute_uri(f"/account/verify/{user.signup_token}/")

        # Render HTML email
        html_content = render_to_string("emails/signup_verification.html", {
            "user": user,
            "signup_link": signup_link,
        })
        text_content = strip_tags(html_content)

        subject = "Verify your email - Welcome to Rare Leather"

        try:
            # Send email via Resend
            resend.Emails.send({
                "from": "onboarding@resend.dev",
                "to": [email],
                "subject": subject,
                "html": html_content,
                "text": text_content
            })

            messages.success(request, f"A verification link has been sent to {email}. Check your inbox.")
        except Exception as e:
            messages.error(request, f"Error sending email: {e}")

        return redirect('accounts:register')

    return render(request, 'accounts/signup.html')


@redirect_authenticated_user
def verify_email(request, token):
    try:
        user = User.objects.get(signup_token=token, is_active=False)
        user.is_active = True
        user.signup_token = None
        user.save()
        login(request, user)
        messages.success(request, "Email verified! Now set your password.")
        return redirect('accounts:set_password')
    except User.DoesNotExist:
        messages.error(request, "Invalid or expired verification link.")
        return redirect('accounts:signup')


@login_required
def set_password_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        password = request.POST.get('password')
        confirm = request.POST.get('confirm_password')

        # Handle name
        if full_name:
            request.user.full_name = full_name

        # Check passwords match
        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/set_password.html')

        # Validate password strength
        try:
            validate_password(password, user=request.user)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'accounts/set_password.html')

        # Save user details
        request.user.set_password(password)
        request.user.save()

        messages.success(request, "Password set successfully! You can now log in.")
        return redirect('accounts:login')

    return render(request, 'accounts/set_password.html')


@login_required
def dashboard_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    site_settings = SiteSettings.objects.first()
    delivery_fee = site_settings.delivery_fee if site_settings else 3500

    return render(request, 'accounts/dashboard.html', {'orders': orders, 'delivery_fee': delivery_fee,})
