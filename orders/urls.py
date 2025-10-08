from django.urls import path
from .views import checkout_view, order_confirmation_view, cancel_order_view
from payments.views import verify_payment, initialize_payment # import from payments app

app_name = 'orders'

urlpatterns = [
    path('checkout/', checkout_view, name='checkout'),
    path('confirmation/<int:order_id>/', order_confirmation_view, name='order_confirmation'),

    # Payment-related routes
    path('payment/initialize/<int:order_id>/', initialize_payment, name='initialize_payment'),
    path('payment/verify/<str:reference>/', verify_payment, name='verify_payment'),

    path('cancel/<int:order_id>/', cancel_order_view, name='cancel_order'),

]
