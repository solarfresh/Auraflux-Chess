import pytest
from unittest.mock import patch
from canvases.models import Canvas, Node
from canvases.tasks import handle_node_action_request
from messaging.constants import AgentRequest, NodeActionPersistence

@pytest.mark.django_db
@patch("messaging.tasks.publish_event.delay")
def test_handle_node_action_request_success(mock_publish_delay):
    # Setup Canvas and Node
    canvas = Canvas.objects.create(title="Test Canvas")
    node = Node.objects.create(
        canvas=canvas,
        label="Test Node",
        node_type="llm",
        content="Hello world",
        pos_x=0.0,
        pos_y=0.0
    )

    payload = {
        "canvas_id": str(canvas.id),
        "node_id": str(node.id),
        "action_type": "DecompositionAgent",
        "session_id": "sess-123"
    }

    handle_node_action_request("NodeActionRequest", payload)

    mock_publish_delay.assert_called_once()
    called_args = mock_publish_delay.call_args[1]

    assert called_args["event_type"] == AgentRequest.name
    assert called_args["queue"] == AgentRequest.queue

    published_payload = called_args["payload"]
    assert published_payload["type"] == "DecompositionAgent"
    assert published_payload["payload"]["source_node"]["id"] == str(node.id)
    assert published_payload["payload"]["source_node"]["label"] == "Test Node"
    assert published_payload["payload"]["source_node"]["type"] == "llm"
    assert published_payload["payload"]["source_node"]["content"] == "Hello world"
    assert published_payload["next_event_type"] == NodeActionPersistence.name
    assert published_payload["next_event_payload"]["canvas_id"] == str(canvas.id)
    assert published_payload["next_event_payload"]["session_id"] == "sess-123"

@pytest.mark.django_db
@patch("messaging.tasks.publish_event.delay")
def test_handle_node_action_request_node_not_found(mock_publish_delay):
    canvas = Canvas.objects.create(title="Test Canvas")

    payload = {
        "canvas_id": str(canvas.id),
        "node_id": "00000000-0000-0000-0000-000000000000",
        "action_type": "DecompositionAgent",
        "session_id": "sess-123"
    }

    # Should not raise exception, should handle Node.DoesNotExist and log error
    handle_node_action_request("NodeActionRequest", payload)

    mock_publish_delay.assert_not_called()
