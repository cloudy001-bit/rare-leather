# from django.urls import path
# from . import views

# urlpatterns = [
#     path("initialize/<int:order_id>/", views.initialize_payment, name="initialize_payment"),
#     path("verify-payment/<str:reference>/", views.verify_payment, name="verify_payment"),
# ]

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('initialize/<int:order_id>/', views.initialize_payment, name='initialize_payment'),
    path('verify/<str:reference>/', views.verify_payment, name='verify_payment'),
]
