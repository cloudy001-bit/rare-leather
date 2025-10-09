from django.urls import path
from .views import checkout_view, order_confirmation_view, cancel_order_view
from payments.views import initialize_payment  # verify is handled inside payments

app_name = 'orders'

urlpatterns = [
    path('checkout/', checkout_view, name='checkout'),
    path('confirmation/<int:order_id>/', order_confirmation_view, name='order_confirmation'),
    path('payment/initialize/<int:order_id>/', initialize_payment, name='initialize_payment'),
    path('cancel/<int:order_id>/', cancel_order_view, name='cancel_order'),
]
