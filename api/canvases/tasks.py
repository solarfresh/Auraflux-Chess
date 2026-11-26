import logging
from typing import cast

from asgiref.sync import async_to_sync
from canvases.models import Node
from canvases.serializers import (CanvasGraphImportSerializer, EdgeSerializer,
                                  NodeSerializer)
from channels.layers import get_channel_layer
from core.celery_app import celery_app
from core.constants import ProcessStatus
from messaging.constants import (AgentRequest, NodeActionPersistence,
                                 NodeActionRequest)
from messaging.tasks import publish_event
from realtime.constants import RealtimeEventType
from realtime.utils import broadcast_event
from services.agent_service import AgentConfigService

logger = logging.getLogger(__name__)


@celery_app.task(name=NodeActionRequest.name, ignore_result=True)
def handle_node_action_request(event_type: str, payload: dict):
    node_id = payload.get('node_id')
    canvas_id = payload.get('canvas_id')
    action_type = payload.get('action_type')
    session_id = payload.get('session_id')

    valid_actions = [
        "DecompositionAgent",
        "HypothesisAnalysisAgent",
        "LogicCritiqueAgent",
        "BoundaryAgent"
    ]

    if action_type not in valid_actions:
        logger.error(f"Invalid action type: {action_type}")
        return

    task_id = handle_node_action_request.request.id
    logger.info("Task %s: Handling node action request for node %s on canvas %s with action type %s.", task_id, node_id, canvas_id, action_type)

    try:
        node = Node.objects.get(id=node_id, canvas_id=canvas_id)
    except Node.DoesNotExist:
        logger.error(f"Node {node_id} not found on canvas {canvas_id}")
        return

    # Retrieve agent configuration via AgentConfigService with fallback support
    agent_config = AgentConfigService.get_agent_config(action_type)

    payload = {
        "type": action_type,
        "config": {
            "model": agent_config.model,
            "provider": agent_config.provider,
            "lang": agent_config.lang
        },
        "payload": {
            "source_node": {
                "id": str(node.id),
                "label": node.label,
                "type": node.node_type,
                "content": node.content
            }
        },
        "next_event_type": NodeActionPersistence.name,
        "next_event_payload": {
            "canvas_id": canvas_id,
            "session_id": session_id
        },
        "next_event_queue": NodeActionPersistence.queue
    }

    publish_event.delay(
        event_type=AgentRequest.name,
        payload=payload,
        queue=AgentRequest.queue
    )


@celery_app.task(name=NodeActionPersistence.name, ignore_result=True)
def handle_node_action_persistence(event_type: str, payload: dict):
    canvas_id = payload.get('canvas_id')
    session_id = payload.get('session_id')
    agent_output = payload.get('agent_output', {})

    if not canvas_id:
        logger.error("Missing canvas_id in NodeActionPersistence payload")
        return

    task_id = handle_node_action_persistence.request.id
    logger.info("Task %s: Handling node action persistence for canvas %s with session %s.", task_id, canvas_id, session_id)

    nodes_data = agent_output.get('nodes', {})
    edges_data = agent_output.get('edges', [])

    if isinstance(nodes_data, dict):
        nodes_data = list(nodes_data.values())

    formatted_nodes = []
    for n_data in nodes_data:
        temp_id = n_data.get('id')
        formatted_nodes.append({
            "temp_id": str(temp_id) if temp_id else None,
            "label": n_data.get('label', 'Untitled'),
            "node_type": n_data.get('type', 'CONCEPT'),
            "position": n_data.get("position") or {"x": 0.0, "y": 0.0},
            "content": n_data.get('content', ''),
            "status": 'REVIEW',
            "rationale": n_data.get('rationale', '')
        })

    formatted_edges = []
    for e_data in edges_data:
        formatted_edges.append({
            "source": str(e_data.get('source')),
            "target": str(e_data.get('target')),
            "edge_type": e_data.get('type', 'LINK'),
            "weight": e_data.get('weight', 1.0),
            "label": e_data.get('label', ''),
            "status": 'REVIEW',
            "evidence": e_data.get('evidence', ''),
            "rationale": e_data.get('rationale', ''),
            "metadata": e_data.get('metadata', {}),
            "sourceHandle": e_data.get('source_handle'),
            "targetHandle": e_data.get('target_handle')
        })

    import_payload = {
        "canvas_id": str(canvas_id),
        "nodes": formatted_nodes,
        "edges": formatted_edges
    }

    try:
        serializer = CanvasGraphImportSerializer(data=import_payload)
        if not serializer.is_valid():
            raise ValueError(f"Invalid import payload: {serializer.errors}")

        result = cast(dict, serializer.save())
        persisted_nodes = NodeSerializer(result["persisted_nodes"], many=True).data
        persisted_edges = EdgeSerializer(result["persisted_edges"], many=True).data

        logger.info(f"Successfully persisted {len(persisted_nodes)} nodes and {len(persisted_edges)} edges for canvas {canvas_id}")

        broadcast_event(
            group_name=f"canvas_{canvas_id}",
            event_type=RealtimeEventType.NODE_ACTION_PERSISTED,
            payload={
                "status": ProcessStatus.SUCCESS.value.lower(),
                "payload": {
                    "canvas_id": str(canvas_id),
                    "session_id": session_id,
                    "persisted_nodes": persisted_nodes,
                    "persisted_edges": persisted_edges
                }
            }
        )

    except Exception as e:
        logger.error(f"Failed to persist node action output for canvas {canvas_id}: {str(e)}")

        broadcast_event(
            group_name=f"canvas_{canvas_id}",
            event_type=RealtimeEventType.NODE_ACTION_PERSISTED,
            payload={
                "status": ProcessStatus.ERROR.value.lower(),
                "payload": {
                    "error": str(e),
                    "canvas_id": str(canvas_id)
                }
            }
        )
        raise
