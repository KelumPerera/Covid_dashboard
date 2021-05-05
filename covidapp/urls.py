from django.contrib import admin
from django.urls import path
from .views import covidView

urlpatterns = [
    path('', covidView),
]