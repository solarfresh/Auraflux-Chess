from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Canvas
from .serializers import CanvasGraphSerializer


class CanvasGraphAPIView(APIView):
    async def get(self, request, canvasId):
        cache_key = f'canvas_graph_{canvasId}'
        data = await sync_to_async(cache.get)(cache_key)

        if not data:
            try:
                canvas = await sync_to_async(get_object_or_404)(
                    Canvas.objects.prefetch_related('nodes', 'edges'),
                    pk=canvasId
                )
                # Ensure serialization is also run in a thread to keep it async-friendly
                serializer = await sync_to_async(CanvasGraphSerializer)(canvas)
                data = serializer.data
                await sync_to_async(cache.set)(cache_key, data, 60 * 15)
            except Exception:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(data)
