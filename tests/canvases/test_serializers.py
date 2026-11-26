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


@pytest.mark.django_db
def test_canvas_graph_import_serializer_success():
    from canvases.serializers import CanvasGraphImportSerializer
    canvas = Canvas.objects.create(title="Import Canvas")

    payload = {
        "canvas_id": str(canvas.id),
        "nodes": [
            {
                "temp_id": "node_a",
                "label": "Node A",
                "node_type": "CONCEPT",
                "position": {"x": 100, "y": 200}
            },
            {
                "temp_id": "node_b",
                "label": "Node B",
                "node_type": "CONCEPT",
                "position": {"x": 300, "y": 400}
            }
        ],
        "edges": [
            {
                "source": "node_a",
                "target": "node_b",
                "edge_type": "LINK",
                "label": "Link A-B"
            }
        ]
    }

    serializer = CanvasGraphImportSerializer(data=payload, context={'canvas_id': canvas.id})
    assert serializer.is_valid(), serializer.errors
    result = serializer.save()

    assert isinstance(result, dict)
    assert result.get("canvas") == canvas
    assert len(result.get("persisted_nodes", [])) == 2
    assert len(result.get("persisted_edges", [])) == 1

    # Check NodeHandles were created (8 handles per node: 2 handle types * 4 positions)
    for node in result.get("persisted_nodes", []):
        assert NodeHandle.objects.filter(node=node).count() == 8


@pytest.mark.django_db
def test_canvas_graph_import_serializer_invalid_canvas():
    import uuid
    from rest_framework.exceptions import ValidationError
    from canvases.serializers import CanvasGraphImportSerializer

    payload = {
        "canvas_id": str(uuid.uuid4()),
        "nodes": [
            {
                "temp_id": "node_a",
                "label": "Node A",
                "node_type": "CONCEPT",
                "position": {"x": 0, "y": 0}
            }
        ]
    }

    serializer = CanvasGraphImportSerializer(data=payload, context={'canvas_id': payload['canvas_id']})
    assert serializer.is_valid()
    with pytest.raises(ValidationError):
        serializer.save()


@pytest.mark.django_db
def test_canvas_graph_import_serializer_invalid_edge_reference():
    from rest_framework.exceptions import ValidationError
    from canvases.serializers import CanvasGraphImportSerializer

    canvas = Canvas.objects.create(title="Import Canvas 2")
    payload = {
        "canvas_id": str(canvas.id),
        "nodes": [
            {
                "temp_id": "node_a",
                "label": "Node A",
                "node_type": "CONCEPT",
                "position": {"x": 0, "y": 0}
            }
        ],
        "edges": [
            {
                "source": "node_a",
                "target": "non_existent_node",
                "edge_type": "LINK"
            }
        ]
    }

    serializer = CanvasGraphImportSerializer(data=payload, context={'canvas_id': canvas.id})
    assert serializer.is_valid()
    with pytest.raises(ValidationError):
        serializer.save()


@pytest.mark.django_db
def test_canvas_graph_import_serializer_edge_with_existing_node():
    from canvases.serializers import CanvasGraphImportSerializer
    canvas = Canvas.objects.create(title="Existing Canvas")

    # Pre-create an existing node in the canvas
    existing_node = Node.objects.create(
        canvas=canvas,
        label="Existing Node",
        node_type="CONCEPT",
        pos_x=0.0,
        pos_y=0.0
    )

    payload = {
        "canvas_id": str(canvas.id),
        "nodes": [
            {
                "temp_id": "node_new",
                "label": "New Node",
                "node_type": "CONCEPT",
                "position": {"x": 100, "y": 100}
            }
        ],
        "edges": [
            {
                "source": str(existing_node.id),
                "target": "node_new",
                "edge_type": "LINK",
                "label": "Existing to New"
            }
        ]
    }

    serializer = CanvasGraphImportSerializer(data=payload, context={'canvas_id': canvas.id})
    assert serializer.is_valid(), serializer.errors
    result = serializer.save()

    assert isinstance(result, dict)
    assert len(result.get("persisted_nodes", [])) == 1
    assert len(result.get("persisted_edges", [])) == 1
    edges = result.get("persisted_edges")
    assert edges is not None
    assert len(edges) == 1
    edge = edges[0]
    assert edge.source == existing_node
    assert edge.target.label == "New Node"


@pytest.mark.django_db
def test_canvas_graph_import_serializer_handles():
    from canvases.serializers import CanvasGraphImportSerializer
    canvas = Canvas.objects.create(title="Import Canvas with Handles")

    payload = {
        "canvas_id": str(canvas.id),
        "nodes": [
            {
                "temp_id": "node_a",
                "label": "Node A",
                "node_type": "CONCEPT",
                "position": {"x": 100, "y": 200}
            },
            {
                "temp_id": "node_b",
                "label": "Node B",
                "node_type": "CONCEPT",
                "position": {"x": 300, "y": 400}
            }
        ],
        "edges": [
            {
                "source": "node_a",
                "target": "node_b",
                "edge_type": "LINK",
                "label": "Link A to B"
            }
        ]
    }

    serializer = CanvasGraphImportSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors
    result = serializer.save()

    assert isinstance(result, dict)
    edges = result.get("persisted_edges")
    assert edges is not None
    assert len(edges) == 1
    edge = edges[0]
    assert edge.source_handle is not None
    assert edge.target_handle is not None

    # Verify handles exist on the respective nodes
    source_handle = NodeHandle.objects.get(id=edge.source_handle)
    target_handle = NodeHandle.objects.get(id=edge.target_handle)
    assert source_handle.node == edge.source
    assert target_handle.node == edge.target


