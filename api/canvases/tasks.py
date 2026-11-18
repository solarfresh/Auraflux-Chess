import logging

from canvases.models import Node
from core.celery_app import celery_app
from messaging.constants import (AgentRequest, NodeActionPersistence,
                                 NodeActionRequest)
from messaging.tasks import publish_event
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
        }
    }

    publish_event.delay(
        event_type=AgentRequest.name,
        payload=payload,
        queue=AgentRequest.queue
    )
