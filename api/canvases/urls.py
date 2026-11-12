from django.urls import path

from .views import CanvasBatchPositionUpdateAPIView, CanvasGraphAPIView

urlpatterns = [
    path('<uuid:canvasId>/', CanvasGraphAPIView.as_view(), name='canvas-graph'),
    path('<uuid:canvasId>/nodes/batch-position/', CanvasBatchPositionUpdateAPIView.as_view(), name='canvas-nodes-batch-position'),
]
