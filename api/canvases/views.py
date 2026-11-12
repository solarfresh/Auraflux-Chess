from adrf.views import APIView
from asgiref.sync import sync_to_async
from core.utils import get_serialized_data_by_id
from django.core.cache import cache
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Canvas, Node
from .serializers import (BatchNodePositionUpdateSerializer,
                          CanvasGraphSerializer)
from .utils import update_node_positions_by_serializer


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

class CanvasBatchPositionUpdateAPIView(APIView):
    async def patch(self, request, canvasId):
        try:
            canvas = await sync_to_async(Canvas.objects.get)(pk=canvasId)
        except Canvas.DoesNotExist:
            return Response({"detail": "Canvas not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            updated_count = await sync_to_async(update_node_positions_by_serializer)(
                request.data, canvas, Node, BatchNodePositionUpdateSerializer
            )
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        if updated_count is None:
            return Response({"detail": "Some nodes do not exist or do not belong to this canvas."}, status=status.HTTP_400_BAD_REQUEST)

        await sync_to_async(cache.delete)(f'canvas_graph_{canvasId}')

        return Response({"status": "success", "updated_count": updated_count})
