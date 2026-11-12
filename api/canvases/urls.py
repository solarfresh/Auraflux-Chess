from django.urls import path

from .views import CanvasGraphAPIView

urlpatterns = [
    path('<uuid:canvasId>/', CanvasGraphAPIView.as_view(), name='canvas-graph'),
]
