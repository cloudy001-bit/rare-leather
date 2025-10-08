from django.shortcuts import redirect
from django.core.mail import send_mail
from django.conf import settings





def redirect_authenticated_user(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('catalog:product_list')  # or wherever you want to send them
        return view_func(request, *args, **kwargs)
    return wrapper

def send_magic_link(email, link):
    subject = "Complete your signup - Magic Link"
    message = f"Click the link below to complete your signup:\n\n{link}\n\nThis link will expire soon."
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]

    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
