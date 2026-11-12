from django.urls import path

from .views import (CanvasBatchPositionUpdateAPIView, CanvasGraphAPIView,
                    EdgeDetailView, NodeDetailView)

urlpatterns = [
    path('<uuid:canvasId>/', CanvasGraphAPIView.as_view(), name='canvas-graph'),
    path('<uuid:canvasId>/nodes/batch-position/', CanvasBatchPositionUpdateAPIView.as_view(), name='canvas-nodes-batch-position'),
    path('<uuid:canvasId>/nodes/<uuid:nodeId>/', NodeDetailView.as_view(), name='canvas-node-detail'),
    path('<uuid:canvasId>/edges/<uuid:edgeId>/', EdgeDetailView.as_view(), name='canvas-edge-detail'),
]
