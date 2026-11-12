from adrf.views import APIView
from asgiref.sync import sync_to_async
from core.utils import get_serialized_data_by_id
from django.core.cache import cache
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response

from .models import Canvas
from .serializers import CanvasGraphSerializer


class CanvasGraphAPIView(APIView):
    async def get(self, request, canvasId):
        cache_key = f'canvas_graph_{canvasId}'
        data = await sync_to_async(cache.get)(cache_key)

        if not data:
            try:
                data = await sync_to_async(get_serialized_data_by_id)(
                    id=canvasId,
                    model_class=Canvas,
                    serializer_class=CanvasGraphSerializer,
                    prefetch_related=['nodes', 'edges']
                )
                await sync_to_async(cache.set)(cache_key, data, 60 * 15)
            except Http404:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            except Canvas.DoesNotExist:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(data)
