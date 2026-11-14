import pytest
from canvases.models import Canvas, Node, NodeHandle
from canvases.serializers import NodeSerializer

@pytest.mark.django_db
def test_node_serializer_with_handles():
    canvas = Canvas.objects.create(title="Test Canvas")
    node = Node.objects.create(canvas=canvas, label="Node 1", pos_x=0, pos_y=0)

    # Create handles. Note: NodeCreateSerializer automatically creates handles
    # but for unit test control we can create them manually.
    handle1 = NodeHandle.objects.create(node=node, handle_type="source", position="top")
    handle2 = NodeHandle.objects.create(node=node, handle_type="target", position="bottom")

    serializer = NodeSerializer(node)
    data = serializer.data

    data_dict = dict(data)
    assert "handles" in data_dict
    # Note: If NodeCreateSerializer ran, there might be more handles.
    # Check if handle1 and handle2 are present in the serialized handles list.
    serialized_handle_ids = [h["id"] for h in data_dict["handles"]]
    assert str(handle1.id) in serialized_handle_ids
    assert str(handle2.id) in serialized_handle_ids

@pytest.mark.django_db
def test_node_serializer_without_handles():
    canvas = Canvas.objects.create(title="Test Canvas")
    # For a completely new node, it might have handles created by post_save or serializer.
    # We create a node without automatic handle generation by directly using the model.
    node = Node.objects.create(canvas=canvas, label="Node 2", pos_x=10, pos_y=10)

    # Clear any potential handles if auto-created
    node.handles.all().delete()

    serializer = NodeSerializer(node)
    data = serializer.data

    data_dict = dict(data)
    assert "handles" in data_dict
    assert data_dict["handles"] == []
