from django.urls import path
from .views import Analyze

urlpatterns = [
    path("getChance/", Analyze.as_view())
]
