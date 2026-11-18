import uuid

from adrf.views import APIView
from asgiref.sync import sync_to_async
from core.utils import (create_serialized_data, execute_serializer_method,
                        get_serialized_data_by_id,
                        update_serialized_data_by_id)
from django.core.cache import cache
from django.db import transaction
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Canvas, Edge, Node
from .serializers import (BatchDeleteNodeSerializer,
                          BatchNodePositionUpdateSerializer,
                          CanvasGraphSerializer, EdgeCreateSerializer,
                          EdgeSerializer, EdgeUpdateSerializer,
                          NodeCreateSerializer, NodeSerializer,
                          NodeUpdateSerializer)
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


class NodeListView(APIView):
    async def post(self, request, canvasId):
        try:
            canvas = await sync_to_async(Canvas.objects.get)(pk=canvasId)
        except Canvas.DoesNotExist:
            return Response({"detail": "Canvas not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            response_data = await sync_to_async(create_serialized_data)(
                data=request.data,
                serializer_class=NodeSerializer,
                create_serializer_class=NodeCreateSerializer,
                canvas=canvas
            )
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        await sync_to_async(cache.delete)(f'canvas_graph_{canvasId}')

        return Response(response_data, status=status.HTTP_201_CREATED)


class NodeDetailView(APIView):
    async def put(self, request, canvasId, nodeId):
        try:
            canvas = await sync_to_async(Canvas.objects.get)(pk=canvasId)
        except Canvas.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            node = await sync_to_async(Node.objects.get)(pk=nodeId, canvas=canvas)
        except Node.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            response_data = await sync_to_async(update_serialized_data_by_id)(
                id=node.pk,
                data=request.data,
                model_class=Node,
                serializer_class=NodeSerializer,
                update_serializer_class=NodeUpdateSerializer
            )
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        await sync_to_async(cache.delete)(f'canvas_graph_{canvasId}')

        return Response(response_data, status=status.HTTP_200_OK)

    async def delete(self, request, canvasId, nodeId):
        try:
            canvas = await sync_to_async(Canvas.objects.get)(pk=canvasId)
        except Canvas.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            node = await sync_to_async(Node.objects.get)(pk=nodeId, canvas=canvas)
        except Node.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        await sync_to_async(node.delete)()
        await sync_to_async(cache.delete)(f'canvas_graph_{canvasId}')

        return Response(status=status.HTTP_204_NO_CONTENT)


class ReviewNodeDeleteView(APIView):
    async def delete(self, request, canvasId):
        try:
            canvas = await sync_to_async(Canvas.objects.get)(pk=canvasId)
        except Canvas.DoesNotExist:
            return Response({"detail": "Canvas not found."}, status=status.HTTP_404_NOT_FOUND)

        @sync_to_async
        @transaction.atomic
        def perform_delete():
            return execute_serializer_method(BatchDeleteNodeSerializer, 'delete_nodes', canvas.id)

        node_ids, edge_ids = await perform_delete()

        await sync_to_async(cache.delete)(f'canvas_graph_{canvasId}')

        return Response({
            "deletedNodeIds": node_ids,
            "deletedEdgeIds": edge_ids
        }, status=status.HTTP_200_OK)


class EdgeListView(APIView):
    async def post(self, request, canvasId):
        try:
            canvas = await sync_to_async(Canvas.objects.get)(pk=canvasId)
        except Canvas.DoesNotExist:
            return Response({"detail": "Canvas not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            response_data = await sync_to_async(create_serialized_data)(
                data=request.data,
                serializer_class=EdgeSerializer,
                create_serializer_class=EdgeCreateSerializer,
                context={'canvas_id': canvasId},
                canvas=canvas
            )
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        await sync_to_async(cache.delete)(f'canvas_graph_{canvasId}')

        return Response(response_data, status=status.HTTP_201_CREATED)


class EdgeDetailView(APIView):
    async def put(self, request, canvasId, edgeId):
        try:
            canvas = await sync_to_async(Canvas.objects.get)(pk=canvasId)
        except Canvas.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            edge = await sync_to_async(Edge.objects.get)(pk=edgeId, source__canvas=canvas)
        except Edge.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            response_data = await sync_to_async(update_serialized_data_by_id)(
                id=edge.pk,
                data=request.data,
                model_class=Edge,
                serializer_class=EdgeSerializer,
                update_serializer_class=EdgeUpdateSerializer
            )
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        await sync_to_async(cache.delete)(f'canvas_graph_{canvasId}')

        return Response(response_data, status=status.HTTP_200_OK)

    async def delete(self, request, canvasId, edgeId):
        try:
            canvas = await sync_to_async(Canvas.objects.get)(pk=canvasId)
        except Canvas.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            edge = await sync_to_async(Edge.objects.get)(pk=edgeId, source__canvas=canvas)
        except Edge.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        await sync_to_async(edge.delete)()
        await sync_to_async(cache.delete)(f'canvas_graph_{canvasId}')

        return Response(status=status.HTTP_204_NO_CONTENT)


class NodeActionView(APIView):
    async def post(self, request, canvasId, nodeId):
        action_type = request.data.get('actionType')
        session_id = request.headers.get('X-Session-ID') or str(uuid.uuid4())

        valid_actions = [
            "DecompositionAgent",
            "HypothesisAnalysisAgent",
            "LogicCritiqueAgent",
            "BoundaryAgent"
        ]

        if action_type not in valid_actions:
            return Response(
                {"error": "Invalid action type", "code": "INVALID_ACTION"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            canvas = await sync_to_async(Canvas.objects.get)(pk=canvasId)
            node = await sync_to_async(Node.objects.get)(pk=nodeId, canvas=canvas)
        except (Canvas.DoesNotExist, Node.DoesNotExist):
            return Response(
                {"error": "Node not found or not in canvas", "code": "NODE_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND
            )

        if node.status != 'active':
            return Response(
                {"error": "Node is not active", "code": "INVALID_STATUS"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # TODO: Trigger Celery Task here
        # task = some_celery_task.delay(nodeId, action_type, session_id))
        task_id = "00000000-0000-0000-0000-000000000000"

        return Response({
            "status": "accepted",
            "taskId": task_id,
            "sessionId": session_id
        }, status=status.HTTP_202_ACCEPTED)
