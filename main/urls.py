from django.urls import path
from . import api

urlpatterns = [
    path('mapclient/', api.api)
]
