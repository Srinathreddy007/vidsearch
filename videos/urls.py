from rest_framework import routers
from django.urls import path, include
from .views import VideoViewSet

router = routers.DefaultRouter()
router.register(r"videos", VideoViewSet, basename="video")

urlpatterns = [path("", include(router.urls))]
