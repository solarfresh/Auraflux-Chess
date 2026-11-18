import pytest
from canvases.models import Canvas, Edge, Node, NodeHandle
from canvases.serializers import BatchDeleteNodeSerializer, NodeSerializer


@pytest.mark.django_db
def test_batch_delete_node_serializer():
    canvas = Canvas.objects.create(title="Test Canvas")

    # Create nodes
    node_review1 = Node.objects.create(canvas=canvas, label="Review 1", status='REVIEW', pos_x=0, pos_y=0)
    node_review2 = Node.objects.create(canvas=canvas, label="Review 2", status='REVIEW', pos_x=0, pos_y=0)
    node_active = Node.objects.create(canvas=canvas, label="Active 1", status='ACTIVE', pos_x=0, pos_y=0)

    # Create edges
    # Edge between REVIEW nodes
    Edge.objects.create(canvas=canvas, source=node_review1, target=node_review2, status='ACTIVE')
    # Edge between REVIEW and ACTIVE nodes
    Edge.objects.create(canvas=canvas, source=node_review1, target=node_active, status='ACTIVE')
    # Edge between ACTIVE nodes
    edge_active = Edge.objects.create(canvas=canvas, source=node_active, target=node_active, status='ACTIVE')

    serializer = BatchDeleteNodeSerializer()
    deleted_nodes, deleted_edges = serializer.delete_nodes(canvas.id) # type: ignore

    # Assertions
    assert len(deleted_nodes) == 2
    assert set(deleted_nodes) == {node_review1.id, node_review2.id}
    assert len(deleted_edges) == 2 # The two edges involving review nodes

    # Database check
    assert Node.objects.filter(id__in=deleted_nodes).count() == 0
    assert Edge.objects.filter(id__in=deleted_edges).count() == 0
    assert Node.objects.filter(id=node_active.id).exists()
    assert Edge.objects.filter(id=edge_active.id).exists()

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
    NodeHandle.objects.filter(node=node).delete()

    serializer = NodeSerializer(node)
    data = serializer.data

    data_dict = dict(data)
    assert "handles" in data_dict
    assert data_dict["handles"] == []
