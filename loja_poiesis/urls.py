from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('biblioteca', views.biblioteca, name='biblioteca'),
    path('atendimento', views.atendimento, name='atendimento'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
    path('create-checkout-session', views.create_checkout_session, name='create_checkout_session'),
]