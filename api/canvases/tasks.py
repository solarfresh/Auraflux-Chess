import logging

from canvases.models import Node
from core.celery_app import celery_app
from messaging.constants import (AgentRequest, NodeActionPersistence,
                                 NodeActionRequest)
from messaging.tasks import publish_event

logger = logging.getLogger(__name__)


@celery_app.task(name=NodeActionRequest.name, ignore_result=True)
def handle_node_action_request(event_type: str, payload: dict):
    node_id = payload.get('node_id')
    canvas_id = payload.get('canvas_id')
    action_type = payload.get('action_type')
    session_id = payload.get('session_id')

    try:
        node = Node.objects.get(id=node_id, canvas_id=canvas_id)
    except Node.DoesNotExist:
        logger.error(f"Node {node_id} not found on canvas {canvas_id}")
        return

    payload = {
        "type": action_type,
        "config": {
            "model": "gpt-4",
            "provider": "experiment",
            "lang": "default"
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

