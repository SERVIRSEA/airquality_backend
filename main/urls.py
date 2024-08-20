from django.urls import path
from . import api
from .views import RequestDataAPIView
urlpatterns = [
    path('mapclient/', api.api),
    path('requests/', RequestDataAPIView.as_view()),
]
