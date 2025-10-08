from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


app_name = 'accounts'

urlpatterns = [
    # path('signup/', views.signup, name='signup'),
    # path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    # path('logout/', auth_views.LogoutView.as_view(), name='logout'),



    path('signup/', views.signup_view, name='register'),
    
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    path('verify/<uuid:token>/', views.verify_email, name='verify'),
    path('set-password/', views.set_password_view, name='set_password'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    

]
