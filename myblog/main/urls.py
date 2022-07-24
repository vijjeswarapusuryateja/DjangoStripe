from django.urls import path
from . import views
from main.views import (
    CheckoutView,
    StripeIntentView,  
)

app_name = "main"   

urlpatterns = [
    path("", views.home, name="home"),
    path("register", views.register, name="register"), #add this
    path("login", views.login_request, name ="login"),
    path("logout", views.logout_request, name="logout"),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('create_subscription/<pk>/', StripeIntentView.as_view(), name='create_subscription'),
    path("profile/", views.profile, name="profile"), 
    path('products/', views.product, name='product'),
    path("cancel", views.cancel, name="cancel"),
]