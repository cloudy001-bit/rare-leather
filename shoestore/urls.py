"""
URL configuration for shoestore project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

from django.conf.urls import handler400, handler403, handler404, handler500
from django.conf import settings
from django.conf.urls.static import static

# from django.conf.urls import handler404
# from django.shortcuts import render

# def custom_404(request, exception):
#     return render(request, "404.html", status=404)

# handler404 = custom_404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/', include('accounts.urls', namespace="accounts" )),
    path('products/', include('catalog.urls', namespace="catalog" )),
    path('cart/', include('cart.urls', namespace='cart')),
    path('payments/', include(('payments.urls', 'payments'), namespace='payments')),
    path('orders/', include(('orders.urls', 'orders'), namespace='orders')),
    path('', views.home, name= "home"),
    path("about/", views.about_view, name="about"),
    path("contact/", views.contact_view, name="contact")
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# else:
#     # 👇 allow serving media manually on Render
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = 'shoestore.views.bad_request'
handler403 = 'shoestore.views.permission_denied'
handler404 = 'shoestore.views.page_not_found'
handler500 = 'shoestore.views.server_error'