from rest_framework.generics import RetrieveAPIView

from .models import Canvas
from .serializers import CanvasGraphSerializer


class CanvasGraphAPIView(RetrieveAPIView):
    queryset = Canvas.objects.prefetch_related('nodes', 'edges')
    serializer_class = CanvasGraphSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'canvasId'
