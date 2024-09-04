from django.urls import path
from . import api
from .views import RequestDataAPIView, VisitorCountView
urlpatterns = [
    path('mapclient/', api.api),
    path('requests/', RequestDataAPIView.as_view()),
    path('visitor-count/', VisitorCountView.as_view(), name='visitor-count'),
]
